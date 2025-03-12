import os
import json
import datetime
import dashscope
from typing import Optional, List, Dict, Union
from pathlib import Path


class CustomReportGenerator:
    def __init__(self, api_key: str = 'sk-6c7638170cb84af48685a33370a5e8d9'):
        """
        初始化自定义报告生成器
        Args:
            api_key: DashScope API密钥
        """
        self.api_key = api_key
        # 设置日报保存目录
        self.reports_dir = Path('daily_reports')
        if not self.reports_dir.exists():
            self.reports_dir.mkdir(parents=True)

    @staticmethod
    def parse_date(date_str: Optional[str] = None) -> str:
        """
        解析日期字符串，如果未提供则使用当前日期
        Args:
            date_str: 日期字符串 (YYYY-MM-DD)
        Returns:
            str: 格式化的日期字符串 (YYYY-MM-DD)
        """
        if date_str:
            try:
                date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError as e:
                raise ValueError("日期格式错误，请使用YYYY-MM-DD格式") from e
        else:
            date = datetime.datetime.now()
        
        return date.strftime('%Y-%m-%d')

    def save_report(self, content: str, date_str: str) -> str:
        """
        保存日报到文件
        Args:
            content: 日报内容
            date_str: 日期字符串 (YYYY-MM-DD)
        Returns:
            str: 保存的文件路径
        """
        filename = f"daily_report_{date_str}.md"
        file_path = self.reports_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)

    def load_template(self, template_name: str = 'default') -> str:
        """
        加载日报模板
        Args:
            template_name: 模板名称
        Returns:
            str: 模板内容
        """
        templates_dir = Path('templates')
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True)
        
        template_file = templates_dir / f"{template_name}.md"
        
        # 如果模板不存在，创建默认模板
        if not template_file.exists():
            if template_name == 'git_style':
                default_template = """# 工作日志-{date}

## 今日主要工作内容
{work_content}

## 重要的工作进展
{issues}

## 待解决的问题
{plan}
"""
            else:
                default_template = """# 工作日报 - {date}

## 今日工作内容
{work_content}

## 工作进展
{progress}

## 遇到的问题
{issues}

## 明日计划
{plan}
"""
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(default_template)
        
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()

    def generate_report(self, 
                        work_content: str, 
                        progress: str = "", 
                        issues: str = "", 
                        plan: str = "",
                        date_str: Optional[str] = None,
                        template_name: str = 'default',
                        use_ai: bool = False) -> str:
        """
        生成自定义工作日报
        Args:
            work_content: 工作内容
            progress: 工作进展
            issues: 遇到的问题
            plan: 明日计划
            date_str: 日期字符串 (YYYY-MM-DD)，如果未提供则使用当前日期
            template_name: 模板名称
            use_ai: 是否使用AI优化内容
        Returns:
            str: 生成的日报内容
        """
        date = self.parse_date(date_str)
        template = self.load_template(template_name)
        
        # 填充模板
        report = template.format(
            date=date,
            work_content=work_content,
            progress=progress,
            issues=issues,
            plan=plan
        )
        
        # 如果启用AI优化，使用DashScope API优化内容
        if use_ai:
            report = self.optimize_with_ai(report)
        
        # 保存报告
        file_path = self.save_report(report, date)
        print(f"日报已保存到: {file_path}")
        
        return report

    def optimize_with_ai(self, content: str) -> str:
        """
        使用AI优化日报内容
        Args:
            content: 原始日报内容
        Returns:
            str: 优化后的日报内容
        """
        prompt = f"""请优化以下工作日报内容，使其更加专业、简洁和有条理:

        {content}

        要求:
        1. 保持原有的结构和主要内容
        2. 使用专业且简洁的描述
        3. 修正语法和表达错误
        4. 突出重要的工作内容
        5. 总体字数控制在200-300字左右
        """

        try:
            messages = [
                {'role': 'user', 'content': prompt},
            ]
            response = dashscope.Generation.call(
                api_key=self.api_key,
                model="qwen-plus",
                messages=messages,
                result_format='message'
            )

            output = response.get('output', {})
            choices = output.get('choices', [])
            if not choices:
                print("AI优化失败，返回原始内容")
                return content

            first_choice = choices[0]
            message = first_choice.get('message', {})
            optimized_content = message.get('content', '')

            return optimized_content

        except Exception as e:
            print(f"AI优化过程中出错: {e}")
            return content

    def simple_report(self, work_content: str, date_str: Optional[str] = None, use_ai: bool = False) -> str:
        """
        生成简化版工作日报，只需提供工作内容和日期
        Args:
            work_content: 工作内容
            date_str: 日期字符串 (YYYY-MM-DD)，如果未提供则使用当前日期
            use_ai: 是否使用AI优化内容
        Returns:
            str: 生成的日报内容
        """
        return self.generate_report(
            work_content=work_content,
            progress="",
            issues="",
            plan="",
            date_str=date_str,
            template_name='git_style',
            use_ai=use_ai
        )

    def load_report(self, date_str: Optional[str] = None) -> Optional[str]:
        """
        加载指定日期的日报
        Args:
            date_str: 日期字符串 (YYYY-MM-DD)，如果未提供则使用当前日期
        Returns:
            Optional[str]: 日报内容，如果不存在则返回None
        """
        date = self.parse_date(date_str)
        filename = f"daily_report_{date}.md"
        file_path = self.reports_dir / filename
        
        if not file_path.exists():
            print(f"未找到{date}的日报")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def list_reports(self) -> List[str]:
        """
        列出所有日报文件
        Returns:
            List[str]: 日报文件列表
        """
        if not self.reports_dir.exists():
            return []
        
        return [str(f.name) for f in self.reports_dir.glob("daily_report_*.md")]


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='自定义日报生成工具')
    parser.add_argument('--date', type=str, help='日报日期 (YYYY-MM-DD)，默认为今天')
    parser.add_argument('--work', type=str, help='工作内容')
    parser.add_argument('--progress', type=str, default='', help='工作进展')
    parser.add_argument('--issues', type=str, default='', help='遇到的问题')
    parser.add_argument('--plan', type=str, default='', help='明日计划')
    parser.add_argument('--template', type=str, default='default', help='模板名称')
    parser.add_argument('--ai', action='store_true', help='使用AI优化内容')
    parser.add_argument('--list', action='store_true', help='列出所有日报')
    parser.add_argument('--load', action='store_true', help='加载指定日期的日报')
    parser.add_argument('--simple', action='store_true', help='使用简化模式，只需提供date和work参数，使用git_style模板')
    parser.add_argument('--api_key', help='DashScope API Key', default='sk-6c7638170cb84af48685a33370a5e8d9')
    
    args = parser.parse_args()
    
    generator = CustomReportGenerator(args.api_key)
    
    if args.list:
        reports = generator.list_reports()
        if reports:
            print("已生成的日报列表:")
            for report in reports:
                print(f"  - {report}")
        else:
            print("暂无日报")
        return
    
    if args.load:
        content = generator.load_report(args.date)
        if content:
            print(content)
        return
    
    if not args.work and not args.load:
        parser.print_help()
        return
    
    # 使用简化模式
    if args.simple:
        generator.simple_report(
            work_content=args.work,
            date_str=args.date,
            use_ai=args.ai
        )
        return
    
    # 当只提供date和work参数，且未提供progress、issues、plan和template参数时，自动使用简化模式
    if args.work and not (args.progress or args.issues or args.plan) and args.template == 'default':
        generator.simple_report(
            work_content=args.work,
            date_str=args.date,
            use_ai=args.ai
        )
        return
    
    generator.generate_report(
        work_content=args.work,
        progress=args.progress,
        issues=args.issues,
        plan=args.plan,
        date_str=args.date,
        template_name=args.template,
        use_ai=args.ai
    )


if __name__ == "__main__":
    main() 