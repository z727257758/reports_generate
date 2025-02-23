import os
import dashscope
import subprocess
import datetime


def get_today_commits():
    """获取今天commits"""
    cmd = 'git log --since="0:00" --until="23:59" --date=format:"%Y-%m-%d %H:%M:%S" --pretty=format:"%ad | %an | %B%n%n"'
    #    cmd = 'git -v'
    result = subprocess.check_output(cmd, shell=True)
    return result.decode('utf-8').split('\n\n\n')


def extract_report_content(response_data):
    """从API响应中安全地提取日报内容"""
    try:
        # 逐层检查和获取数据
        output = response_data.get('output', {})
        choices = output.get('choices', [])
        if not choices:
            return "No content generated"

        first_choice = choices[0]
        message = first_choice.get('message', {})
        content = message.get('content', '')

        return content
    except Exception as e:
        print(f"Error processing API response: {e}")
        return "Error generating report"


def format_commit(commit_str):
    """格式化单条提交记录"""
    if not commit_str.strip():
        return None

    parts = commit_str.split(' | ', 2)
    if len(parts) < 3:
        return None

    date, author, message = parts
    # 分离提交信息的主题和正文
    message_parts = message.split('\n', 1)
    subject = message_parts[0].strip()
    body = message_parts[1].strip() if len(message_parts) > 1 else ""

    return {
        "date": date,
        "author": author,
        "subject": subject,
        "body": body
    }


def generate_report(commits):
    # 将提交记录格式化为更易读的形式
    formatted_commits = ""
    for commit in commits:
        commit_info = format_commit(commit)
        if commit_info:
            formatted_commits += f"时间：{commit_info['date']}\n"
            formatted_commits += f"作者：{commit_info['author']}\n"
            formatted_commits += f"主题：{commit_info['subject']}\n"
            if commit_info['body']:
                formatted_commits += f"详细说明：\n{commit_info['body']}\n"
            formatted_commits += "\n"

    prompt = f"""请基于以下git提交记录生成工作日报:

    {formatted_commits}
    
    请按照以下格式生成日报：
    1. 总结今日主要工作内容
    2. 按照功能模块分类整理具体工作
    3. 重要的工作进展
    4. 待解决的问题
    
    要求:
    1.200字左右
    2.使用专业且简洁的描述
    3. 突出重要的工作内容
        """

    try:
        messages = [
            {'role': 'user', 'content': prompt},
        ]
        response = dashscope.Generation.call(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key='sk-6c7638170cb84af48685a33370a5e8d9',
            model="qwen-plus",
            # 此处以qwen-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=messages,
            result_format='message'
        )

        response_data = response

        # 提取日报内容
        report_content = extract_report_content(response_data)

        # 可以添加使用统计信息的记录
        if 'usage' in response_data:
            usage = response_data['usage']
            print(f"Token usage: {usage}")

        return report_content

    except Exception as e:
        print(f"Error calling API: {e}")
        return "Error generating report"


def main():
    commits = get_today_commits()
    report = generate_report(commits)

    # 保存日报
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    with open(f'daily_report_{today}.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print("日报已生成!")


if __name__ == "__main__":
    main()
