# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.reporting.json_reporter — JSON 报告生成器

将基准测试结果序列化为结构化 JSON 报告。

输出结构:
    {
        "suite_name": "...",          # 套件名(若输入为 SuiteResult)
        "generated_at": "ISO 时间戳",
        "summary": {
            "total": N,
            "success": N,
            "failure": N,
            "success_rate": 0.0,
            "total_duration_seconds": 0.0
        },
        "results": [
            {
                "benchmark_name": "...",
                "algorithm_name": "...",
                "version": "...",
                "iterations": N,
                "duration_seconds": 0.0,
                "success": true,
                "error": null,
                "metrics": {
                    "latency": {"unit": "ns", "count": N, "statistics": {...}}
                },
                "timestamp": "ISO 时间戳"
            }
        ]
    }

使用示例:
    from core_benchmark.reporting.json_reporter import JsonReporter

    reporter = JsonReporter()
    # 返回字符串
    json_str = reporter.generate(suite_result)
    # 写入文件
    reporter.generate(suite_result, "./produce/report.json")
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from core_benchmark.reporting.base_reporter import BaseReporter


class JsonReporter(BaseReporter):
    """JSON 报告生成器"""

    def __init__(
        self,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        """
        初始化 JSON 报告生成器

        Args:
            indent: JSON 缩进空格数(默认 2)
            ensure_ascii: 是否转义非 ASCII 字符(默认 False,保留中文)
        """
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    @property
    def format(self) -> str:
        return "json"

    def _render(self, results: List[Any]) -> str:
        """
        渲染 JSON 报告

        Args:
            results: BenchmarkResult 列表

        Returns:
            JSON 格式的报告字符串
        """
        report: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "summary": self._build_summary(results),
            "results": [r.to_summary_dict() for r in results],
        }

        return json.dumps(
            report,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii,
            default=str,
        )

    def _build_summary(self, results: List[Any]) -> Dict[str, Any]:
        """构建汇总信息"""
        total = len(results)
        success = sum(1 for r in results if r.success)
        failure = total - success
        total_duration = sum(r.duration_seconds for r in results)
        rate = (success / total) if total > 0 else 0.0

        return {
            "total": total,
            "success": success,
            "failure": failure,
            "success_rate": round(rate, 4),
            "total_duration_seconds": round(total_duration, 6),
        }


__all__ = ["JsonReporter"]
