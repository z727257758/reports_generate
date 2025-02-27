from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import logging
import argparse
import configparser
import os


class ZentaoDailyReporter:
    def __init__(self, url, username, password, headless=False):
        """初始化禅道日报提交器

        Args:
            url (str): 禅道系统URL
            username (str): 用户名
            password (str): 密码
            headless (bool, optional): 是否使用无头模式. Defaults to False.
        """
        self.url = url
        self.username = username
        self.password = password
        self.logger = self._setup_logger()
        self.driver = self._setup_driver(headless)

    def _setup_logger(self):
        """配置日志"""
        logger = logging.getLogger("ZentaoReporter")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    def _setup_driver(self, headless):
        """配置WebDriver"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver

    def login(self):
        """登录禅道系统"""
        try:
            self.logger.info("正在登录禅道系统...")
            self.driver.get(self.url)

            # 等待登录页面加载
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "account")))

            # 输入用户名和密码
            self.driver.find_element(By.ID, "account").send_keys(self.username)
            self.driver.find_element(By.NAME, "password").send_keys(self.password)

            # 点击登录按钮
            self.driver.find_element(By.ID, "submit").click()

            # 等待登录成功 - 头部菜单加载完成
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "header")))
            self.logger.info("登录成功")
            return True

        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            return False

    def navigate_to_worklog(self):
        """导航到工作日志页面"""
        try:
            self.logger.info("正在导航到工作日志页面...")

            # 直接访问工作日志创建页面 - 如果有直接URL的话更好
            worklog_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/ypworklog/')]"))
            )
            worklog_link.click()

            # 等待工作日志页面加载完成
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "main"))
            )

            # 查找"创建日志"按钮并点击 - 按钮文本可能不同，需要根据实际情况调整
            create_buttons = self.driver.find_elements(By.XPATH,
                                                       "//a[contains(text(), '创建') or contains(text(), '新建') or contains(text(), '添加')]")

            if create_buttons:
                for button in create_buttons:
                    if "worklog" in button.get_attribute("href") or "日志" in button.text:
                        button.click()
                        break
            else:
                # 尝试其他可能的创建按钮
                action_buttons = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'btn')]")
                for button in action_buttons:
                    if "创建" in button.text or "新建" in button.text or "添加" in button.text:
                        button.click()
                        break

            # 等待日志创建表单加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "title"))
            )
            self.logger.info("已进入日志创建页面")
            return True

        except Exception as e:
            self.logger.error(f"导航到工作日志页面失败: {e}")
            return False

    def submit_daily_report(self, title, content, project=None):
        """提交工作日志

        Args:
            title (str): 日志标题
            content (str): 日志内容
            project (str, optional): 相关项目. Defaults to None.

        Returns:
            bool: 是否提交成功
        """
        try:
            self.logger.info("正在填写工作日志...")

            # 填写标题
            title_field = self.driver.find_element(By.ID, "title")
            title_field.clear()
            title_field.send_keys(title)
            self.logger.info(f"已填写标题: {title}")

            # 选择项目(如果提供了项目名称)
            if project and project != "无":
                try:
                    # 点击选择器打开下拉列表
                    project_selector = self.driver.find_element(By.XPATH, "//div[contains(@id, 'prjid_chosen')]")
                    project_selector.click()
                    time.sleep(1)  # 等待下拉列表打开

                    # 在搜索框中输入项目名称
                    search_input = self.driver.find_element(By.XPATH,
                                                            "//div[contains(@id, 'prjid_chosen')]//div[@class='chosen-search']/input")
                    search_input.clear()
                    search_input.send_keys(project)
                    time.sleep(1)  # 等待搜索结果

                    # 点击匹配的项目
                    project_option = self.driver.find_element(By.XPATH,
                                                              f"//ul[@class='chosen-results']/li[contains(text(), '{project}')]")
                    project_option.click()
                    self.logger.info(f"已选择项目: {project}")
                except Exception as e:
                    self.logger.warning(f"选择项目失败: {e}")

            # 填写内容
            content_field = self.driver.find_element(By.ID, "content")
            content_field.clear()
            content_field.send_keys(content)
            self.logger.info("已填写工作日志内容")

            # 提交表单
            submit_button = self.driver.find_element(By.ID, "submit")
            submit_button.click()

            # 等待提交完成 - 可能是返回列表页或成功提示
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[contains(@class, 'table')] | //div[contains(@class, 'alert')]"))
            )

            self.logger.info("工作日志提交成功!")
            return True

        except Exception as e:
            self.logger.error(f"提交工作日志失败: {e}")
            return False

    def run(self, title, content, project=None):
        """执行完整的工作日志提交流程

        Args:
            title (str): 日志标题
            content (str): 日志内容
            project (str, optional): 相关项目. Defaults to None.

        Returns:
            bool: 是否成功
        """
        try:
            if not self.login():
                return False

            if not self.navigate_to_worklog():
                return False

            if not self.submit_daily_report(title, content, project):
                return False

            return True

        except Exception as e:
            self.logger.error(f"工作日志提交过程中发生错误: {e}")
            return False

        finally:
            # 短暂暂停以便查看结果
            time.sleep(3)
            self.driver.quit()
            self.logger.info("浏览器已关闭")


def load_config(config_file='config.ini'):
    """从配置文件加载设置"""
    config = configparser.ConfigParser()

    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        # 创建默认配置
        config['Zentao'] = {
            'url': 'http://your-zentao-url.com',
            'username': 'your_username',
            'password': 'your_password'
        }

        config['Report'] = {
            'title': '工作日志 - {date}',
            'content': """今日执行的任务包括:
1. 完成了XX功能的开发
2. 修复了YY模块的bug
3. 参加了项目例会

明日计划:
1. 继续开发ZZ功能
2. 测试AA模块
""",
            'project': '无'  # 根据实际项目选择
        }

        # 写入配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)

        print(f"已创建默认配置文件 {config_file}，请修改后再运行程序。")
        return None

    # 读取配置文件
    config.read(config_file, encoding='utf-8')
    return config


def main():
    """主函数"""
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='禅道工作日志自动提交工具')
    parser.add_argument('--config', '-c', default='config.ini', help='配置文件路径')
    parser.add_argument('--headless', '-H', action='store_true', help='使用无头模式（不显示浏览器界面）')
    parser.add_argument('--title', '-t', help='日志标题，默认使用配置文件中的标题')
    parser.add_argument('--project', '-p', help='相关项目，默认使用配置文件中的项目')
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    if config is None:
        return

    # 获取配置信息
    zentao_url = config['Zentao']['url']
    username = config['Zentao']['username']
    password = config['Zentao']['password']

    # 处理标题 - 支持日期格式化
    title = args.title if args.title else config['Report']['title']
    title = title.format(date=datetime.now().strftime("%Y-%m-%d"))

    content = config['Report']['content']
    project = args.project if args.project else config['Report']['project']

    # 创建并运行日志提交器
    reporter = ZentaoDailyReporter(zentao_url, username, password, args.headless)
    success = reporter.run(title, content, project)

    # 输出结果
    if success:
        print("✅ 工作日志提交成功！")
    else:
        print("❌ 工作日志提交失败，请检查日志和配置。")


if __name__ == "__main__":
    main()