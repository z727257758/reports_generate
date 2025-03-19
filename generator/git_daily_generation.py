import os
import dashscope
import subprocess
import datetime
import argparse
from typing import Optional, List, Dict, Union
from pathlib import Path


class GitReportGenerator:
    def __init__(self, api_key: str = 'sk-6c7638170cb84af48685a33370a5e8d9'):
        """
        初始化报告生成器
        Args:
            api_key: DashScope API密钥
        """
        self.api_key = api_key

    @staticmethod
    def parse_date_range(start_date: str, end_date: Optional[str] = None) -> tuple[str, str]:
        """
        解析日期范围
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        Returns:
            tuple: (start_datetime, end_datetime)
        """
        try:
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d')

            if end_date:
                end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end = start

            if start > end:
                start, end = end, start

            start_str = start.strftime('%Y-%m-%d 00:00:00')
            end_str = end.strftime('%Y-%m-%d 23:59:59')

            return start_str, end_str

        except ValueError as e:
            raise ValueError("日期格式错误，请使用YYYY-MM-DD格式") from e

    @staticmethod
    def is_git_repo(path: str) -> bool:
        """
        检查路径是否为Git仓库
        Args:
            path: 要检查的路径
        Returns:
            bool: 是否为Git仓库
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_repo_name(repo_path: str) -> str:
        """
        获取仓库名称
        Args:
            repo_path: 仓库路径
        Returns:
            str: 仓库名称
        """
        return os.path.basename(os.path.abspath(repo_path))

    @staticmethod
    def format_commit(commit_str: str) -> Optional[Dict]:
        """
        格式化提交记录
        Args:
            commit_str: 原始提交记录字符串
        Returns:
            Dict: 格式化后的提交记录
        """
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

    def get_commits_from_repo(self, repo_path: str, start_date: str, end_date: str) -> List[Dict]:
        """
        获取指定仓库的提交记录
        Args:
            repo_path: 仓库路径
            start_date: 开始日期时间
            end_date: 结束日期时间
        Returns:
            List[Dict]: 提交记录列表
        """
        if not self.is_git_repo(repo_path):
            print(f"警告: {repo_path} 不是有效的Git仓库")
            return []

        cmd = f'git log --since="{start_date}" --until="{end_date}" --date=format:"%Y-%m-%d %H:%M:%S" --pretty=format:"%ad | %an | %B%n%n"'
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode != 0:
                print(f"获取 {repo_path} 的git日志失败: {result.stderr}")
                return []

            commits = result.stdout.split('\n\n\n')
            formatted_commits = []
            repo_name = self.get_repo_name(repo_path)

            for commit in commits:
                commit_info = self.format_commit(commit)
                if commit_info:
                    commit_info['repo'] = repo_name
                    formatted_commits.append(commit_info)

            return formatted_commits

        except subprocess.CalledProcessError as e:
            print(f"获取 {repo_path} 的git日志失败: {e}")
            return []

    def generate_report(self, commits: List[Dict]) -> str:
        """
        生成工作日报
        Args:
            commits: 提交记录列表
        Returns:
            str: 生成的日报内容
        """
        if not commits:
            return "未找到指定日期范围的提交记录"

        # 按仓库组织提交记录
        formatted_commits = ""
        commits_by_repo = {}
        for commit in commits:
            repo = commit['repo']
            if repo not in commits_by_repo:
                commits_by_repo[repo] = []
            commits_by_repo[repo].append(commit)

        # 格式化每个仓库的提交记录
        for repo, repo_commits in commits_by_repo.items():
            formatted_commits += f"\n仓库：{repo}\n"
            formatted_commits += "-" * 50 + "\n"
            for commit in repo_commits:
                formatted_commits += f"时间：{commit['date']}\n"
                formatted_commits += f"作者：{commit['author']}\n"
                formatted_commits += f"主题：{commit['subject']}\n"
                if commit['body']:
                    formatted_commits += f"详细说明：\n{commit['body']}\n"
                formatted_commits += "\n"

        prompt = f"""请基于以下git提交记录生成工作日报:

        {formatted_commits}

        请按照以下格式生成日报：
        1. 工作日志-日期（YYYY-MM-DD）
        2. 总结今日主要工作内容
        3. 重要的工作进展
        4. 待解决的问题

        要求:
        1.总体字数控制在200-300字左右
        2.使用专业且简洁的描述
        3.突出重要的工作内容
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
                return "No content generated"

            first_choice = choices[0]
            message = first_choice.get('message', {})
            content = message.get('content', '')

            return content

        except Exception as e:
            print(f"Error calling API: {e}")
            return "Error generating report"

    def generate_report_for_dates(
            self,
            repos: List[str],
            start_date: str,
            end_date: Optional[str] = None,
            output_file: Optional[str] = None
    ) -> str:
        """
        为指定日期生成报告
        Args:
            repos: 仓库路径列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            output_file: 输出文件路径
        Returns:
            str: 生成的报告内容
        """
        start_datetime, end_datetime = self.parse_date_range(start_date, end_date)

        # 收集所有仓库的提交记录
        all_commits = []
        for repo_path in repos:
            repo_path = os.path.abspath(repo_path)
            if not os.path.exists(repo_path):
                print(f"警告: 仓库路径不存在: {repo_path}")
                continue

            commits = self.get_commits_from_repo(repo_path, start_datetime, end_datetime)
            all_commits.extend(commits)

        if not all_commits:
            return "在指定的日期范围内未找到任何提交记录"

        # 按时间排序
        all_commits.sort(key=lambda x: x['date'])

        report = self.generate_report(all_commits)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description='生成多个Git仓库的工作日报')
    parser.add_argument('--start_date', help='开始日期 (YYYY-MM-DD格式)', default=datetime.datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--end_date', help='结束日期 (YYYY-MM-DD格式，可选)', default=None)
    parser.add_argument('--repos', nargs='+', help='Git仓库路径列表', required=True)
    parser.add_argument('--output', help='输出文件名（可选）', default=None)
    parser.add_argument('--api-key', help='DashScope API Key', default='sk-6c7638170cb84af48685a33370a5e8d9')

    args = parser.parse_args()

    try:
        generator = GitReportGenerator(api_key=args.api_key)

        if args.output is None:
            date_str = args.start_date
            if args.end_date:
                date_str += f"_to_{args.end_date}"
            args.output = f'daily_report_{date_str}.txt'

        report = generator.generate_report_for_dates(
            repos=args.repos,
            start_date=args.start_date,
            end_date=args.end_date,
            output_file=args.output
        )

        print(f"日报已生成: {args.output}")

    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()