# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.metrics.latency — 延迟度量收集器

提供高精度的延迟度量收集能力:
    - 使用 time.perf_counter_ns() 纳秒级计时
    - 支持 p50/p90/p99 百分位统计
    - 提供上下文管理器自动计时(time() 方法)
    - 支持手动 record() 记录

使用示例:
    # 方式1: 手动计时
    collector = LatencyCollector()
    collector.start()
    for _ in range(100):
        start = time.perf_counter_ns()
        algorithm.run(data)
        collector.record(time.perf_counter_ns() - start)
    collector.stop()
    result = collector.get_result()

    # 方式2: 上下文管理器自动计时
    collector = LatencyCollector()
    collector.start()
    with collector.time():
        algorithm.run(data)
    collector.stop()
    result = collector.get_result()
"""

from __future__ import annotations

import math
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Iterator, List, Optional

from core_benchmark.core.abstractions import ErrorCode, MetricError
from core_benchmark.core.interfaces import IMetricCollector
from core_benchmark.core.models import MetricSample, MetricType


def _percentile(sorted_data: List[float], p: float) -> float:
    """
    计算百分位数(线性插值法)

    Args:
        sorted_data: 已排序的数据列表
        p: 百分位数(0-100)

    Returns:
        百分位值
    """
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    k = (n - 1) * p / 100.0
    f = int(k)
    c = k - f
    if f + 1 < n:
        return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
    return sorted_data[f]


class LatencyCollector(IMetricCollector):
    """
    延迟度量收集器

    使用 time.perf_counter_ns() 提供纳秒级高精度计时,
    支持 p50/p90/p99 百分位统计。
    """

    def __init__(self, unit: str = "ns") -> None:
        """
        初始化延迟收集器

        Args:
            unit: 度量单位(默认 ns,可选 ms/us)
        """
        self._unit = unit
        self._samples: List[float] = []
        self._started = False
        self._start_time: Optional[float] = None
        self._context_start: Optional[float] = None

    @property
    def name(self) -> str:
        return "latency"

    @property
    def unit(self) -> str:
        return self._unit

    def start(self) -> None:
        """开始收集延迟度量"""
        self._samples = []
        self._started = True
        self._start_time = time.perf_counter_ns()

    def record(self, value: float) -> None:
        """
        记录一个延迟值

        Args:
            value: 延迟值(纳秒)

        Raises:
            MetricError: 收集器未启动或值无效
        """
        if not self._started:
            raise MetricError(
                code=ErrorCode.METRIC_COLLECTION_FAILED,
                message="延迟收集器未启动,请先调用 start()",
                metric_name=self.name,
            )
        if value < 0:
            raise MetricError(
                code=ErrorCode.METRIC_OUT_OF_RANGE,
                message=f"延迟值不能为负数,实际为 {value}",
                metric_name=self.name,
            )
        self._samples.append(float(value))

    def stop(self) -> None:
        """停止收集"""
        self._started = False

    @contextmanager
    def time(self) -> Iterator[None]:
        """
        上下文管理器:自动计时代码块

        Example:
            with collector.time():
                algorithm.run(data)
        """
        self._context_start = time.perf_counter_ns()
        try:
            yield
        finally:
            if self._context_start is not None:
                elapsed = time.perf_counter_ns() - self._context_start
                self.record(elapsed)
                self._context_start = None

    def get_result(self) -> MetricSample:
        """
        获取延迟度量结果

        Returns:
            MetricSample: 含 p50/p90/p99 等统计信息

        Raises:
            MetricError: 样本不足
        """
        if not self._samples:
            raise MetricError(
                code=ErrorCode.METRIC_INSUFFICIENT_SAMPLES,
                message="无延迟样本,请先收集数据",
                metric_name=self.name,
            )

        sorted_samples = sorted(self._samples)
        n = len(sorted_samples)
        mean = sum(sorted_samples) / n
        variance = sum((x - mean) ** 2 for x in sorted_samples) / n if n > 0 else 0.0
        std = math.sqrt(variance)

        statistics: Dict[str, float] = {
            "count": float(n),
            "mean": mean,
            "median": _percentile(sorted_samples, 50),
            "p50": _percentile(sorted_samples, 50),
            "p90": _percentile(sorted_samples, 90),
            "p99": _percentile(sorted_samples, 99),
            "min": sorted_samples[0],
            "max": sorted_samples[-1],
            "std": std,
        }

        return MetricSample(
            metric_name=self.name,
            metric_type=MetricType.LATENCY,
            unit=self._unit,
            samples=list(self._samples),
            statistics=statistics,
            timestamp=datetime.now(),
        )

    def reset(self) -> None:
        """重置收集器"""
        self._samples = []
        self._started = False
        self._start_time = None
        self._context_start = None

    def __repr__(self) -> str:
        return f"<LatencyCollector samples={len(self._samples)} unit={self._unit}>"


__all__ = ["LatencyCollector"]
