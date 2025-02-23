# Git日报生成工具

这是一个基于Git提交记录自动生成工作日报的Python工具。该工具可以分析多个Git仓库在指定日期范围内的提交记录，并利用AI生成结构化的工作日报。

## 功能特点

- 支持多个Git仓库同时分析
- 可指定日期范围生成报告
- 自动提取提交记录的详细信息
- 使用DashScope API生成智能化的工作总结
- 支持输出到文件
- 提供命令行和API两种使用方式

## 文件说明

- `daily_generation.py`: 核心功能实现文件，包含`GitReportGenerator`类
- `generate_range_reports.py`: 批量生成指定日期范围内的日报

## 使用方法

### 1. 命令行使用

```bash
python daily_generation.py --repos /path/to/repo1 /path/to/repo2 --start_date 2025-01-01 [--end_date 2025-01-02] [--output report.txt]
python generate_range_reports.py --repos "D:\projects\project1" "D:\projects\project2" --start-date 2024-02-01 --end-date 2024-02-23 --output-dir my_reports