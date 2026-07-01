# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.reporting.markdown_reporter — Markdown 报告生成器

生成人类可读的 Markdown 格式报告,包含:
    - 报告标题与生成时间
    - 汇总摘要表
    - 每个基准的详细度量表

使用示例:
    from core_benchmark.reporting.markdown_reporter import MarkdownReporter

    reporter = MarkdownReporter()
    reporter.generate(suite_result, "./produce/report.md")
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from core_benchmark.reporting.base_reporter import BaseReporter

# Markdown 表格中显示的度量统计列
_DISPLAY_STATS: List[str] = ["count", "mean", "p50", "p90", "p99", "min", "max", "std"]


class MarkdownReporter(BaseReporter):
    """Markdown 报告生成器"""

    def __init__(self, title: str = "Benchmark Report") -> None:
        """
        初始化 Markdown 报告生成器

        Args:
            title: 报告标题(默认 "Benchmark Report")
        """
        self._title = title

    @property
    def format(self) -> str:
        return "markdown"

    def _render(self, results: List[Any]) -> str:
        """
        渲染 Markdown 报告

        Args:
            results: BenchmarkResult 列表

        Returns:
            Markdown 格式的报告字符串
        """
        lines: List[str] = []
        total = len(results)
        success = sum(1 for r in results if r.success)
        failure = total - success
        total_duration = sum(r.duration_seconds for r in results)
        rate = (success / total * 100) if total > 0 else 0.0

        # --- 标题 ---
        lines.append(f"# {self._title}")
        lines.append("")
        lines.append(
            f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append("")

        # --- 汇总摘要 ---
        lines.append("## 汇总摘要")
        lines.append("")
        lines.append("| 指标 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 基准总数 | {total} |")
        lines.append(f"| 成功 | {success} |")
        lines.append(f"| 失败 | {failure} |")
        lines.append(f"| 成功率 | {rate:.1f}% |")
        lines.append(f"| 总耗时 | {total_duration:.4f}s |")
        lines.append("")

        # --- 每个基准的详细结果 ---
        lines.append("## 详细结果")
        lines.append("")

        for idx, r in enumerate(results, 1):
            status = "✅ 成功" if r.success else "❌ 失败"
            lines.append(f"### {idx}. {r.benchmark_name} ({status})")
            lines.append("")
            lines.append("| 属性 | 值 |")
            lines.append("|------|-----|")
            lines.append(f"| 算法 | {r.algorithm_name} |")
            lines.append(f"| 版本 | {r.version} |")
            lines.append(f"| 迭代次数 | {r.iterations} |")
            lines.append(f"| 执行时长 | {r.duration_seconds:.4f}s |")
            if r.error:
                lines.append(f"| 错误 | {r.error} |")
            lines.append(f"| 时间戳 | {r.timestamp.isoformat()} |")
            lines.append("")

            # 度量表
            if r.metric_names:
                lines.append("**度量统计:**")
                lines.append("")
                # 表头
                header = "| 度量 | 单位 | count | mean | p50 | p90 | p99 | min | max | std |"
                separator = "|------|------|-------|------|-----|-----|-----|-----|-----|-----|"
                lines.append(header)
                lines.append(separator)

                for mname in r.metric_names:
                    sample = r.get_metric(mname)
                    if sample is None:
                        continue
                    stats = sample.statistics
                    row_vals = [
                        mname,
                        sample.unit,
                        str(sample.count),
                    ]
                    for stat in ["mean", "p50", "p90", "p99", "min", "max", "std"]:
                        val = stats.get(stat)
                        row_vals.append(f"{val:.4f}" if val is not None else "-")
                    lines.append("| " + " | ".join(row_vals) + " |")

                lines.append("")
            else:
                lines.append("_无度量数据_")
                lines.append("")

        return "\n".join(lines)


__all__ = ["MarkdownReporter"]
