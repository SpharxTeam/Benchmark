# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.config.loader — 配置加载器

提供 Benchmark 库的配置管理:
    - 从 YAML 文件加载配置(默认 + 用户覆盖)
    - 深度合并用户配置到默认配置
    - pydantic 模型校验配置结构与类型
    - 支持 ConfigurationError 错误隔离

配置加载顺序:
    1. 加载 default.yaml 作为基线
    2. 若提供用户路径,深度合并用户配置
    3. pydantic 校验生成 Config 实例

使用示例:
    from core_benchmark.config import load_config, Config

    # 使用默认配置
    config = load_config()
    print(config.benchmark.iterations)  # 100

    # 加载用户配置(覆盖默认)
    config = load_config("./my_config.yaml")
    print(config.benchmark.iterations)  # 用户指定值
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator

from core_benchmark.core.abstractions import ConfigurationError, ErrorCode


# =============================================================================
# 默认配置路径
# =============================================================================

DEFAULT_CONFIG_PATH: Path = Path(__file__).parent / "default.yaml"


# =============================================================================
# 配置模型 (pydantic v2)
# =============================================================================

class LatencyConfig(BaseModel):
    """延迟度量配置"""
    unit: str = Field(default="ns", description="延迟单位: ns/us/ms/s")

    @field_validator("unit")
    @classmethod
    def _validate_unit(cls, v: str) -> str:
        allowed = {"ns", "us", "ms", "s"}
        if v not in allowed:
            raise ValueError(f"延迟单位必须是 {allowed} 之一,实际为 '{v}'")
        return v


class ThroughputConfig(BaseModel):
    """吞吐度量配置"""
    window_size: int = Field(
        default=100, ge=1, description="滑动窗口大小(样本数,>=1)"
    )


class MemoryConfig(BaseModel):
    """内存度量配置"""
    enabled: bool = Field(default=True, description="是否默认启用内存度量")


class AccuracyConfig(BaseModel):
    """准确度度量配置"""
    enabled: bool = Field(default=False, description="是否默认启用准确度度量")


class MetricsConfig(BaseModel):
    """度量收集器聚合配置"""
    latency: LatencyConfig = Field(default_factory=LatencyConfig)
    throughput: ThroughputConfig = Field(default_factory=ThroughputConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    accuracy: AccuracyConfig = Field(default_factory=AccuracyConfig)


class ReportingConfig(BaseModel):
    """报告生成配置"""
    output_dir: str = Field(default="./produce/reports", description="报告输出目录")
    default_format: str = Field(default="json", description="默认报告格式")
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    timestamp_format: str = Field(
        default="%Y%m%d_%H%M%S", description="输出文件名时间戳格式"
    )

    @field_validator("default_format")
    @classmethod
    def _validate_format(cls, v: str) -> str:
        allowed = {"json", "csv", "markdown"}
        if v not in allowed:
            raise ValueError(f"报告格式必须是 {allowed} 之一,实际为 '{v}'")
        return v


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        description="日志格式字符串",
    )

    @field_validator("level")
    @classmethod
    def _validate_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"日志级别必须是 {allowed} 之一,实际为 '{v}'")
        return v_upper


class BenchmarkConfig(BaseModel):
    """基准执行参数"""
    iterations: int = Field(default=100, ge=1, description="正式迭代次数(>=1)")
    warmup: int = Field(default=5, ge=0, description="预热迭代次数(>=0)")
    parallel: bool = Field(default=False, description="是否并行执行")
    max_workers: Optional[int] = Field(
        default=None, ge=1, description="并行最大线程数(None=自动)"
    )


class Config(BaseModel):
    """
    Benchmark 顶层配置

    聚合所有子配置域:
        - benchmark: 基准执行参数
        - metrics: 度量收集器配置
        - reporting: 报告生成配置
        - logging: 日志配置
    """
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# =============================================================================
# 深度合并工具
# =============================================================================

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并两个字典 — override 中的值覆盖 base 中的同名值。

    对于嵌套字典,递归合并而非整体替换。
    对于非字典值(包括列表),override 的值直接替换 base 的值。

    Args:
        base: 基线字典(默认配置)
        override: 覆盖字典(用户配置)

    Returns:
        合并后的新字典(不修改输入)
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


# =============================================================================
# YAML 加载工具
# =============================================================================

def _load_yaml(path: Path) -> Dict[str, Any]:
    """
    安全加载 YAML 文件为字典

    Args:
        path: YAML 文件路径

    Returns:
        解析后的字典

    Raises:
        ConfigurationError: 文件不存在 / 解析失败 / 顶层非字典
    """
    if not path.exists():
        raise ConfigurationError(
            code=ErrorCode.CONFIG_FILE_NOT_FOUND,
            message=f"配置文件未找到: {path}",
            config_key=str(path),
        )

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            code=ErrorCode.CONFIG_PARSE_ERROR,
            message=f"配置文件解析失败: {path} — {e}",
            config_key=str(path),
        ) from e
    except OSError as e:
        raise ConfigurationError(
            code=ErrorCode.CONFIG_NOT_FOUND,
            message=f"配置文件读取失败: {path} — {e}",
            config_key=str(path),
        ) from e

    if data is None:
        # 空文件视为空字典
        return {}

    if not isinstance(data, dict):
        raise ConfigurationError(
            code=ErrorCode.CONFIG_INVALID_FORMAT,
            message=(
                f"配置文件顶层必须是字典/映射,实际为 {type(data).__name__}: {path}"
            ),
            config_key=str(path),
        )

    return data


# =============================================================================
# 配置加载主入口
# =============================================================================

def load_config(path: Optional[Union[str, Path]] = None) -> Config:
    """
    加载 Benchmark 配置

    加载顺序:
        1. 加载 default.yaml 作为基线
        2. 若 path 提供,深度合并用户配置到基线
        3. pydantic 校验生成 Config 实例

    Args:
        path: 用户配置文件路径(可选)。若为 None,仅使用默认配置。

    Returns:
        Config: 校验后的配置实例

    Raises:
        ConfigurationError: 配置文件未找到 / 解析失败 / 校验失败

    Example:
        >>> config = load_config()  # 默认配置
        >>> config.benchmark.iterations
        100

        >>> config = load_config("./my_config.yaml")  # 用户覆盖
        >>> config.benchmark.iterations
        500
    """
    # 1. 加载默认配置基线
    default_data = _load_yaml(DEFAULT_CONFIG_PATH)

    # 2. 若提供用户路径,深度合并
    if path is not None:
        user_path = Path(path)
        user_data = _load_yaml(user_path)
        merged = _deep_merge(default_data, user_data)
    else:
        merged = default_data

    # 3. pydantic 校验
    try:
        return Config(**merged)
    except Exception as e:
        raise ConfigurationError(
            code=ErrorCode.CONFIG_VALIDATION_ERROR,
            message=f"配置校验失败: {e}",
            config_key=str(path) if path else "default",
        ) from e


def get_default_config() -> Config:
    """
    获取默认配置(等价于 load_config(None))

    Returns:
        Config: 默认配置实例
    """
    return load_config(None)


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
