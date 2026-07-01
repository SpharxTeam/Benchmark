# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""core_benchmark.config — 配置文件加载

提供 Benchmark 库的配置管理:
    - load_config(): 加载默认 + 用户配置(深度合并)
    - Config: 顶层配置模型(pydantic 校验)
    - 各子域配置模型(BenchmarkConfig/MetricsConfig/ReportingConfig/LoggingConfig)

使用示例:
    from core_benchmark.config import load_config

    config = load_config()                    # 默认配置
    config = load_config("./my_config.yaml")  # 用户覆盖
"""

from core_benchmark.config.loader import (
    AccuracyConfig,
    BenchmarkConfig,
    Config,
    DEFAULT_CONFIG_PATH,
    LatencyConfig,
    LoggingConfig,
    MemoryConfig,
    MetricsConfig,
    ReportingConfig,
    ThroughputConfig,
    get_default_config,
    load_config,
)

__all__ = [
    "Config",
    "BenchmarkConfig",
    "MetricsConfig",
    "LatencyConfig",
    "ThroughputConfig",
    "MemoryConfig",
    "AccuracyConfig",
    "ReportingConfig",
    "LoggingConfig",
    "load_config",
    "get_default_config",
    "DEFAULT_CONFIG_PATH",
]
