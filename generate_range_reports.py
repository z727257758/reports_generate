import datetime
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


if __name__ == "__main__":
    # 配置参数
    REPOSITORIES = [
        "D:\project\8yuan\middle",  # 替换为实际的仓库路径
        "D:\project\8yuan\zk_test",
        # 可以添加更多仓库路径
    ]

    START_DATE = "2025-01-25"  # 开始日期
    END_DATE = "2025-02-25"  # 结束日期
    OUTPUT_DIR = "daily_reports"  # 输出目录
    API_KEY = "sk-6c7638170cb84af48685a33370a5e8d9"  # 你的API密钥

    # 生成报告
    generate_reports_for_date_range(
        repos=REPOSITORIES,
        start_date=START_DATE,
        end_date=END_DATE,
        output_dir=OUTPUT_DIR,
        api_key=API_KEY
    )