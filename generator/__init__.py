"""
自动日报生成工具包

这个包提供了多种日报生成工具，包括：
1. 基于Git提交记录生成日报
2. 自定义内容生成日报
3. 批量生成日期范围内的日报
"""

from .custom_daily_generation import CustomReportGenerator
from .git_daily_generation import GitReportGenerator
from .generate_range_reports import generate_reports_for_date_range

__all__ = [
    'CustomReportGenerator',
    'GitReportGenerator',
    'generate_reports_for_date_range'
]

# 版本信息
__version__ = '1.0.0'
