# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""core_benchmark.reporting — 报告生成器(JSON / CSV / Markdown)

提供三种报告格式的生成器:
    - JsonReporter: 结构化 JSON 报告(含汇总 + 详细结果)
    - CsvReporter: CSV 表格(每个基准一行,度量统计为列)
    - MarkdownReporter: 人类可读 Markdown 报告(含汇总表 + 每基准度量表)

所有报告器实现 IReporter 接口,支持:
    - generate(results, output_path=None) — 生成报告
    - 输入接受 List[BenchmarkResult] / SuiteResult / 单个 BenchmarkResult
    - output_path=None 返回字符串,output_path 提供则写入文件

使用示例:
    from core_benchmark.reporting import JsonReporter

    reporter = JsonReporter()
    reporter.generate(suite_result, "./produce/report.json")
"""

from core_benchmark.reporting.base_reporter import BaseReporter
from core_benchmark.reporting.csv_reporter import CsvReporter
from core_benchmark.reporting.json_reporter import JsonReporter
from core_benchmark.reporting.markdown_reporter import MarkdownReporter

__all__ = [
    "BaseReporter",
    "JsonReporter",
    "CsvReporter",
    "MarkdownReporter",
]
