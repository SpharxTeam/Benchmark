# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""core_benchmark.runners — 基准运行器(单算法 + 多算法批量)"""

from core_benchmark.runners.base_runner import BaseBenchmarkRunner
from core_benchmark.runners.suite_runner import BenchmarkSuiteRunner

__all__ = [
    "BaseBenchmarkRunner",
    "BenchmarkSuiteRunner",
]
