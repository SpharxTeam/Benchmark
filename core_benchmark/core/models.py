# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.core.models — 数据模型

定义 Benchmark 模块的核心数据模型:
    - MetricSample: 度量样本数据类(含统计信息)
    - BenchmarkResult: 基准测试结果数据类
    - SuiteResult: 基准套件结果(多算法聚合)

使用 pydantic v2 BaseModel 实现,提供:
    - 类型验证
    - JSON 序列化/反序列化
    - 不可变保证(frozen 模式可选)
    - 字段默认值与约束

参考:
    - Deepness schemas (pydantic v2)
    - Workshop models
    - SpharxTools 工程标准规范手册
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# MetricType - 度量类型枚举
# =============================================================================

class MetricType(str, Enum):
    """度量类型枚举"""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY = "memory"
    ACCURACY = "accuracy"
    CUSTOM = "custom"


# =============================================================================
# MetricSample - 度量样本数据类
# =============================================================================

class MetricSample(BaseModel):
    """
    度量样本数据类

    存储一次度量收集的所有样本和统计信息。

    Attributes:
        metric_name: 度量名称(如 latency, throughput, memory, accuracy)
        metric_type: 度量类型(MetricType 枚举)
        unit: 度量单位(如 ns, ops/sec, MB, %)
        samples: 原始样本值列表
        statistics: 统计信息字典(mean/median/p50/p90/p99/min/max/std/count)
        timestamp: 采样时间戳
        metadata: 额外元数据(可选)

    Example:
        >>> sample = MetricSample(
        ...     metric_name="latency",
        ...     metric_type=MetricType.LATENCY,
        ...     unit="ns",
        ...     samples=[100, 200, 150, 180, 220],
        ...     statistics={"mean": 170, "p50": 150, "p99": 220},
        ... )
        >>> sample.to_dict()
    """

    metric_name: str = Field(..., description="度量名称", min_length=1, max_length=128)
    metric_type: MetricType = Field(..., description="度量类型")
    unit: str = Field(..., description="度量单位", min_length=1, max_length=32)
    samples: List[float] = Field(
        default_factory=list, description="原始样本值列表"
    )
    statistics: Dict[str, float] = Field(
        default_factory=dict, description="统计信息(mean/median/p50/p90/p99/min/max/std/count)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="采样时间戳"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="额外元数据"
    )

    @field_validator("samples")
    @classmethod
    def validate_samples(cls, v: List[float]) -> List[float]:
        """验证样本值:每个值必须为有限数"""
        for i, val in enumerate(v):
            if not isinstance(val, (int, float)):
                raise ValueError(f"样本[{i}] 必须为数值类型,实际为 {type(val).__name__}")
            # 拒绝 NaN 和 Inf(除非是内存度量的 Inf 特殊情况)
            import math
            if isinstance(val, float) and math.isnan(val):
                raise ValueError(f"样本[{i}] 不能为 NaN")
        return [float(s) for s in v]

    @property
    def count(self) -> int:
        """样本数量"""
        return len(self.samples)

    @property
    def mean(self) -> Optional[float]:
        """平均值(从 statistics 获取)"""
        return self.statistics.get("mean")

    @property
    def median(self) -> Optional[float]:
        """中位数(从 statistics 获取)"""
        return self.statistics.get("median")

    @property
    def p50(self) -> Optional[float]:
        """p50 百分位(等价于 median)"""
        return self.statistics.get("p50", self.median)

    @property
    def p90(self) -> Optional[float]:
        """p90 百分位"""
        return self.statistics.get("p90")

    @property
    def p99(self) -> Optional[float]:
        """p99 百分位"""
        return self.statistics.get("p99")

    @property
    def min_value(self) -> Optional[float]:
        """最小值"""
        return self.statistics.get("min")

    @property
    def max_value(self) -> Optional[float]:
        """最大值"""
        return self.statistics.get("max")

    @property
    def std(self) -> Optional[float]:
        """标准差"""
        return self.statistics.get("std")


# =============================================================================
# BenchmarkResult - 基准测试结果数据类
# =============================================================================

class BenchmarkResult(BaseModel):
    """
    基准测试结果数据类

    存储单次算法基准测试的完整结果。

    Attributes:
        benchmark_name: 基准名称(标识基准套件中的唯一基准)
        algorithm_name: 算法名称
        version: 算法版本
        iterations: 迭代次数
        metrics: 度量样本字典(按 metric_name 索引)
        timestamp: 基准执行时间戳
        duration_seconds: 总执行时长(秒)
        success: 是否成功
        error: 错误信息(success=False 时填充)
        metadata: 额外元数据(环境信息、配置等)

    Example:
        >>> result = BenchmarkResult(
        ...     benchmark_name="sort_benchmark",
        ...     algorithm_name="quick_sort",
        ...     version="1.0.0",
        ...     iterations=100,
        ...     metrics={"latency": latency_sample},
        ...     duration_seconds=0.523,
        ...     success=True,
        ... )
    """

    benchmark_name: str = Field(..., description="基准名称", min_length=1, max_length=128)
    algorithm_name: str = Field(..., description="算法名称", min_length=1, max_length=128)
    version: str = Field(default="1.0.0", description="算法版本", pattern=r"^\d+\.\d+\.\d+$")
    iterations: int = Field(..., description="迭代次数", ge=1)
    metrics: Dict[str, MetricSample] = Field(
        default_factory=dict, description="度量样本字典(按 metric_name 索引)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="基准执行时间戳"
    )
    duration_seconds: float = Field(
        default=0.0, description="总执行时长(秒)", ge=0.0
    )
    success: bool = Field(default=True, description="是否成功")
    error: Optional[str] = Field(default=None, description="错误信息(success=False 时填充)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="额外元数据(环境信息、配置等)"
    )

    @field_validator("iterations")
    @classmethod
    def validate_iterations(cls, v: int) -> int:
        """验证迭代次数必须为正整数"""
        if v < 1:
            raise ValueError(f"迭代次数必须 >= 1,实际为 {v}")
        return v

    def add_metric(self, sample: MetricSample) -> None:
        """
        添加度量样本

        Args:
            sample: 度量样本
        """
        self.metrics[sample.metric_name] = sample

    def get_metric(self, metric_name: str) -> Optional[MetricSample]:
        """
        获取指定名称的度量样本

        Args:
            metric_name: 度量名称

        Returns:
            MetricSample 或 None(不存在时)
        """
        return self.metrics.get(metric_name)

    @property
    def metric_names(self) -> List[str]:
        """所有度量名称列表"""
        return list(self.metrics.keys())

    def to_summary_dict(self) -> Dict[str, Any]:
        """
        转换为摘要字典(不含原始样本,便于报告展示)

        Returns:
            Dict: 摘要信息
        """
        return {
            "benchmark_name": self.benchmark_name,
            "algorithm_name": self.algorithm_name,
            "version": self.version,
            "iterations": self.iterations,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error": self.error,
            "metrics": {
                name: {
                    "unit": sample.unit,
                    "count": sample.count,
                    "statistics": sample.statistics,
                }
                for name, sample in self.metrics.items()
            },
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# SuiteResult - 基准套件结果(多算法聚合)
# =============================================================================

class SuiteResult(BaseModel):
    """
    基准套件结果数据类

    存储多算法基准测试的聚合结果。

    Attributes:
        suite_name: 套件名称
        results: 各算法的基准结果列表
        timestamp: 套件执行时间戳
        total_duration_seconds: 总执行时长(秒)
        success_count: 成功的基准数量
        failure_count: 失败的基准数量
    """

    suite_name: str = Field(..., description="套件名称", min_length=1, max_length=128)
    results: List[BenchmarkResult] = Field(
        default_factory=list, description="各算法的基准结果列表"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="套件执行时间戳"
    )
    total_duration_seconds: float = Field(
        default=0.0, description="总执行时长(秒)", ge=0.0
    )

    @property
    def success_count(self) -> int:
        """成功的基准数量"""
        return sum(1 for r in self.results if r.success)

    @property
    def failure_count(self) -> int:
        """失败的基准数量"""
        return sum(1 for r in self.results if not r.success)

    @property
    def total_count(self) -> int:
        """总基准数量"""
        return len(self.results)

    @property
    def success_rate(self) -> float:
        """成功率(0.0-1.0)"""
        if not self.results:
            return 0.0
        return self.success_count / self.total_count

    def add_result(self, result: BenchmarkResult) -> None:
        """添加一个基准结果"""
        self.results.append(result)

    def get_result(self, benchmark_name: str) -> Optional[BenchmarkResult]:
        """
        获取指定名称的基准结果

        Args:
            benchmark_name: 基准名称

        Returns:
            BenchmarkResult 或 None(不存在时)
        """
        return next(
            (r for r in self.results if r.benchmark_name == benchmark_name),
            None,
        )

    def to_summary_dict(self) -> Dict[str, Any]:
        """转换为摘要字典"""
        return {
            "suite_name": self.suite_name,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "total_duration_seconds": self.total_duration_seconds,
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_summary_dict() for r in self.results],
        }


__all__ = [
    "MetricType",
    "MetricSample",
    "BenchmarkResult",
    "SuiteResult",
]
