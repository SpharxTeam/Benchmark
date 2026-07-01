# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.metrics.throughput — 吞吐度量收集器

提供吞吐量度量收集能力:
    - 支持 ops/sec、items/sec 度量
    - 支持滑动窗口统计(window_size 参数)
    - 统计峰值/平均/最小吞吐量
    - 支持手动 record() 记录

使用示例:
    # 方式1: 直接记录吞吐量值
    collector = ThroughputCollector(unit="ops/sec")
    collector.start()
    for ops in [1000, 1200, 950, 1100]:
        collector.record(ops)
    collector.stop()
    result = collector.get_result()

    # 方式2: 滑动窗口统计
    collector = ThroughputCollector(unit="ops/sec", window_size=10)
    collector.start()
    for _ in range(100):
        ops = measure_throughput()
        collector.record(ops)
    collector.stop()
    result = collector.get_result()  # 只统计最近 10 个样本
"""

from __future__ import annotations

import math
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional

from core_benchmark.core.abstractions import ErrorCode, MetricError
from core_benchmark.core.interfaces import IMetricCollector
from core_benchmark.core.models import MetricSample, MetricType


class ThroughputCollector(IMetricCollector):
    """
    吞吐度量收集器

    支持 ops/sec、items/sec 度量,可选滑动窗口统计。
    """

    def __init__(
        self,
        unit: str = "ops/sec",
        window_size: Optional[int] = None,
    ) -> None:
        """
        初始化吞吐收集器

        Args:
            unit: 度量单位(默认 ops/sec,可选 items/sec)
            window_size: 滑动窗口大小(None 表示统计所有样本,
                         正整数表示只统计最近 N 个样本)

        Raises:
            MetricError: window_size 无效
        """
        if window_size is not None and window_size < 1:
            raise MetricError(
                code=ErrorCode.METRIC_OUT_OF_RANGE,
                message=f"window_size 必须为正整数或 None,实际为 {window_size}",
                metric_name="throughput",
            )
        self._unit = unit
        self._window_size = window_size
        self._samples: Deque[float] = (
            deque(maxlen=window_size) if window_size else deque()
        )
        self._all_samples: List[float] = []
        self._started = False

    @property
    def name(self) -> str:
        return "throughput"

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def window_size(self) -> Optional[int]:
        """滑动窗口大小"""
        return self._window_size

    def start(self) -> None:
        """开始收集吞吐度量"""
        self._samples.clear()
        self._all_samples = []
        self._started = True

    def record(self, value: float) -> None:
        """
        记录一个吞吐量值

        Args:
            value: 吞吐量值(ops/sec)

        Raises:
            MetricError: 收集器未启动或值无效
        """
        if not self._started:
            raise MetricError(
                code=ErrorCode.METRIC_COLLECTION_FAILED,
                message="吞吐收集器未启动,请先调用 start()",
                metric_name=self.name,
            )
        if value < 0:
            raise MetricError(
                code=ErrorCode.METRIC_OUT_OF_RANGE,
                message=f"吞吐量值不能为负数,实际为 {value}",
                metric_name=self.name,
            )
        self._samples.append(float(value))
        self._all_samples.append(float(value))

    def stop(self) -> None:
        """停止收集"""
        self._started = False

    def get_result(self) -> MetricSample:
        """
        获取吞吐度量结果

        Returns:
            MetricSample: 含 peak/mean/min/total 统计信息

        Raises:
            MetricError: 样本不足
        """
        samples_list = list(self._samples)
        if not samples_list:
            raise MetricError(
                code=ErrorCode.METRIC_INSUFFICIENT_SAMPLES,
                message="无吞吐样本,请先收集数据",
                metric_name=self.name,
            )

        n = len(samples_list)
        mean = sum(samples_list) / n
        peak = max(samples_list)
        min_val = min(samples_list)
        variance = sum((x - mean) ** 2 for x in samples_list) / n if n > 0 else 0.0
        std = math.sqrt(variance)

        statistics: Dict[str, float] = {
            "count": float(n),
            "mean": mean,
            "peak": peak,
            "min": min_val,
            "max": peak,
            "std": std,
            "total_samples": float(len(self._all_samples)),
        }

        # 如果使用滑动窗口,添加窗口信息
        if self._window_size is not None:
            statistics["window_size"] = float(self._window_size)

        return MetricSample(
            metric_name=self.name,
            metric_type=MetricType.THROUGHPUT,
            unit=self._unit,
            samples=samples_list,
            statistics=statistics,
            timestamp=datetime.now(),
        )

    def reset(self) -> None:
        """重置收集器"""
        self._samples.clear()
        self._all_samples = []
        self._started = False

    def __repr__(self) -> str:
        window_info = f" window={self._window_size}" if self._window_size else ""
        return (
            f"<ThroughputCollector samples={len(self._samples)} "
            f"unit={self._unit}{window_info}>"
        )


__all__ = ["ThroughputCollector"]
