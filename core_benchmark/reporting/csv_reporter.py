# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.reporting.csv_reporter — CSV 报告生成器

将基准测试结果导出为 CSV 表格格式,每个基准一行,
每个度量的统计值作为独立列。

列结构:
    benchmark_name, algorithm_name, version, iterations, success,
    duration_seconds, error, timestamp,
    <metric>_<stat> (如 latency_mean, latency_p50, memory_peak, ...)

使用示例:
    from core_benchmark.reporting.csv_reporter import CsvReporter

    reporter = CsvReporter()
    reporter.generate(suite_result, "./produce/report.csv")
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Set

from core_benchmark.reporting.base_reporter import BaseReporter

# 固定列顺序(度量列动态追加)
_BASE_COLUMNS: List[str] = [
    "benchmark_name",
    "algorithm_name",
    "version",
    "iterations",
    "success",
    "duration_seconds",
    "error",
    "timestamp",
]

# 度量统计值的输出顺序
_STAT_ORDER: List[str] = [
    "count",
    "mean",
    "median",
    "p50",
    "p90",
    "p99",
    "min",
    "max",
    "std",
    "peak",
    "leak",
]


class CsvReporter(BaseReporter):
    """CSV 报告生成器"""

    def __init__(self, delimiter: str = ",") -> None:
        """
        初始化 CSV 报告生成器

        Args:
            delimiter: 列分隔符(默认逗号)
        """
        self._delimiter = delimiter

    @property
    def format(self) -> str:
        return "csv"

    def _render(self, results: List[Any]) -> str:
        """
        渲染 CSV 报告

        Args:
            results: BenchmarkResult 列表

        Returns:
            CSV 格式的报告字符串
        """
        # 收集所有度量名(保持出现顺序)
        metric_names: List[str] = []
        seen: Set[str] = set()
        for r in results:
            for name in r.metric_names:
                if name not in seen:
                    seen.add(name)
                    metric_names.append(name)

        # 构建列头:基础列 + 度量统计列
        columns = list(_BASE_COLUMNS)
        for mname in metric_names:
            for stat in _STAT_ORDER:
                columns.append(f"{mname}_{stat}")

        # 写入 CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self._delimiter)
        writer.writerow(columns)

        for r in results:
            row: List[str] = [
                r.benchmark_name,
                r.algorithm_name,
                r.version,
                str(r.iterations),
                str(r.success),
                f"{r.duration_seconds:.6f}",
                r.error or "",
                r.timestamp.isoformat(),
            ]
            # 度量统计值
            for mname in metric_names:
                sample = r.get_metric(mname)
                stats: Dict[str, float] = sample.statistics if sample else {}
                for stat in _STAT_ORDER:
                    val = stats.get(stat)
                    row.append("" if val is None else f"{val:.6f}")
            writer.writerow(row)

        return output.getvalue()


__all__ = ["CsvReporter"]
