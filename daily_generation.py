import os
import dashscope
import subprocess
import datetime
import argparse
from typing import Optional, List, Dict


def parse_date_range(start_date: str, end_date: Optional[str] = None) -> tuple[str, str]:
    """Parse and validate date range for git log"""
    try:
        # Parse start date
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d')

        # If end date not provided, use start date
        if end_date:
            end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = start

        # Ensure start date is not after end date
        if start > end:
            start, end = end, start

        # Add time to make it a full day range
        start_str = start.strftime('%Y-%m-%d 00:00:00')
        end_str = end.strftime('%Y-%m-%d 23:59:59')

        return start_str, end_str

    except ValueError as e:
        raise ValueError("日期格式错误，请使用YYYY-MM-DD格式") from e


def get_commits_for_date_range(start_date: str, end_date: str) -> List[str]:
    """获取指定日期范围的commits"""
    cmd = f'git log --since="{start_date}" --until="{end_date}" --date=format:"%Y-%m-%d %H:%M:%S" --pretty=format:"%ad | %an | %B%n%n"'
    try:
        result = subprocess.check_output(cmd, shell=True)
        return result.decode('utf-8').split('\n\n\n')
    except subprocess.CalledProcessError as e:
        print(f"获取git日志失败: {e}")
        return []


def get_token_usage(response_data: Dict) -> Optional[Dict]:
    """获取API调用的token使用情况"""
    try:
        usage = response_data.get('usage', {})
        return {
            'input_tokens': usage.get('input_tokens', 0),
            'output_tokens': usage.get('output_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }
    except Exception:
        return None


def extract_report_content(response_data: Dict) -> str:
    """从API响应中安全地提取日报内容"""
    try:
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


def format_commit(commit_str: str) -> Optional[Dict]:
    """格式化单条提交记录"""
    if not commit_str.strip():
        return None

    parts = commit_str.split(' | ', 2)
    if len(parts) < 3:
        return None

    date, author, message = parts
    message_parts = message.split('\n', 1)
    subject = message_parts[0].strip()
    body = message_parts[1].strip() if len(message_parts) > 1 else ""

    return {
        "date": date,
        "author": author,
        "subject": subject,
        "body": body
    }


def generate_report(commits: List[str]) -> str:
    """生成工作日报"""
    if not commits or commits[0].strip() == '':
        return "未找到指定日期范围的提交记录"

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
            api_key='sk-6c7638170cb84af48685a33370a5e8d9',
            model="qwen-plus",
            messages=messages,
            result_format='message'
        )

        report_content = extract_report_content(response)

        if 'usage' in response:
            usage = get_token_usage(response)
            print(f"Token usage: {usage}")

        return report_content

    except Exception as e:
        print(f"Error calling API: {e}")
        return "Error generating report"


def main():
    parser = argparse.ArgumentParser(description='生成Git提交记录的工作日报')
    parser.add_argument('start_date', help='开始日期 (YYYY-MM-DD格式)')
    parser.add_argument('--end_date', help='结束日期 (YYYY-MM-DD格式，可选)', default=None)
    parser.add_argument('--output', help='输出文件名（可选）', default=None)

    args = parser.parse_args()

    try:
        start_date, end_date = parse_date_range(args.start_date, args.end_date)
        commits = get_commits_for_date_range(start_date, end_date)
        report = generate_report(commits)

        if args.output:
            output_file = args.output
        else:
            date_str = args.start_date
            if args.end_date:
                date_str += f"_to_{args.end_date}"
            output_file = f'daily_report_{date_str}.txt'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"日报已生成: {output_file}")

    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()