# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""core_benchmark.core — 核心抽象层(ErrorCode, 接口, 数据模型)"""

from core_benchmark.core.abstractions import (
    ErrorCode,
    ErrorSeverity,
    ErrorContext,
    BenchmarkError,
    ConfigurationError,
    AlgorithmError,
    MetricError,
    RunnerError,
    BenchmarkIOError,
    ReportError,
    BenchmarkSystemError,
    ErrorCodeManager,
    error_code_manager,
)
from core_benchmark.core.interfaces import (
    IBenchmark,
    IMetricCollector,
    IReporter,
)
from core_benchmark.core.models import (
    MetricType,
    MetricSample,
    BenchmarkResult,
    SuiteResult,
)

__all__ = [
    # 错误码
    "ErrorCode",
    "ErrorSeverity",
    "ErrorContext",
    # 异常基类
    "BenchmarkError",
    # 具体异常(按域)
    "ConfigurationError",
    "AlgorithmError",
    "MetricError",
    "RunnerError",
    "BenchmarkIOError",
    "ReportError",
    "BenchmarkSystemError",
    # 管理器
    "ErrorCodeManager",
    "error_code_manager",
    # 接口
    "IBenchmark",
    "IMetricCollector",
    "IReporter",
    # 数据模型
    "MetricType",
    "MetricSample",
    "BenchmarkResult",
    "SuiteResult",
]
