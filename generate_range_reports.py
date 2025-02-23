import datetime
import argparse
from pathlib import Path
from typing import List
from daily_generation import GitReportGenerator


def generate_reports_for_date_range(
        repos: List[str],
        start_date: str,
        end_date: str,
        output_dir: str = "reports",
        api_key: str = 'sk-6c7638170cb84af48685a33370a5e8d9'
) -> None:
    """
    为日期范围内的每一天生成日报

    Args:
        repos: Git仓库路径列表
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        output_dir: 输出目录
        api_key: DashScope API密钥
    """
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 转换日期字符串为datetime对象
    start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.datetime.strptime(end_date, '%Y-%m-%d')

    # 创建报告生成器实例
    generator = GitReportGenerator(api_key=api_key)

    # 生成日期范围内每一天的报告
    current_date = start
    while current_date <= end:
        date_str = current_date.strftime('%Y-%m-%d')
        output_file = output_path / f'daily_report_{date_str}.txt'

        print(f"正在生成 {date_str} 的日报...")

        try:
            report = generator.generate_report_for_dates(
                repos=repos,
                start_date=date_str,
                output_file=str(output_file)
            )

            print(f"成功生成 {date_str} 的日报")

        except Exception as e:
            print(f"生成 {date_str} 的日报时发生错误: {e}")

        current_date += datetime.timedelta(days=1)

    print(f"\n所有日报已生成完成，保存在目录: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='生成日期范围内的Git提交日报')
    parser.add_argument('--repos', nargs='+', required=True, help='Git仓库路径列表')
    parser.add_argument('--start-date', required=True, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='reports', help='输出目录')
    parser.add_argument('--api-key', help='DashScope API Key')

    args = parser.parse_args()

    generate_reports_for_date_range(
        repos=args.repos,
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=args.output_dir,
        api_key=args.api_key
    )


if __name__ == "__main__":
    main()