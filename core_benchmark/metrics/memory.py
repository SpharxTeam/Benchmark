# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.metrics.memory — 内存度量收集器

提供内存分配跟踪能力:
    - 基于 tracemalloc 跟踪内存分配
    - 支持 peak/avg/current 内存统计
    - 支持内存泄漏检测(对比 start/end 内存)
    - 单位: bytes(可配置 KB/MB)

使用示例:
    collector = MemoryCollector(unit="bytes")
    collector.start()
    for _ in range(100):
        algorithm.run(data)
        collector.record_current()  # 记录当前内存使用
    collector.stop()
    result = collector.get_result()

    # 内存泄漏检测
    collector = MemoryCollector()
    leak = collector.detect_leak()
    if leak > 0:
        print(f"检测到内存泄漏: {leak} bytes")
"""

from __future__ import annotations

import tracemalloc
from datetime import datetime
from typing import Dict, List, Optional

from core_benchmark.core.abstractions import ErrorCode, MetricError
from core_benchmark.core.interfaces import IMetricCollector
from core_benchmark.core.models import MetricSample, MetricType


class MemoryCollector(IMetricCollector):
    """
    内存度量收集器

    基于 tracemalloc 跟踪内存分配,支持 peak/avg/current 统计和泄漏检测。
    """

    def __init__(self, unit: str = "bytes") -> None:
        """
        初始化内存收集器

        Args:
            unit: 度量单位(默认 bytes)
        """
        self._unit = unit
        self._samples: List[float] = []
        self._started = False
        self._tracemalloc_started = False
        self._start_memory: Optional[float] = None
        self._end_memory: Optional[float] = None
        self._peak_memory: Optional[float] = None

    @property
    def name(self) -> str:
        return "memory"

    @property
    def unit(self) -> str:
        return self._unit

    def start(self) -> None:
        """开始收集内存度量(启动 tracemalloc)"""
        self._samples = []
        self._started = True

        # 启动 tracemalloc(如果尚未启动)
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracemalloc_started = True

        # 重置统计
        tracemalloc.clear_traces()

        # 记录起始内存
        current, _ = tracemalloc.get_traced_memory()
        self._start_memory = float(current)
        self._peak_memory = self._start_memory

    def record(self, value: float) -> None:
        """
        记录一个内存值

        Args:
            value: 内存值(bytes)

        Raises:
            MetricError: 收集器未启动或值无效
        """
        if not self._started:
            raise MetricError(
                code=ErrorCode.METRIC_COLLECTION_FAILED,
                message="内存收集器未启动,请先调用 start()",
                metric_name=self.name,
            )
        if value < 0:
            raise MetricError(
                code=ErrorCode.METRIC_OUT_OF_RANGE,
                message=f"内存值不能为负数,实际为 {value}",
                metric_name=self.name,
            )
        self._samples.append(float(value))

    def record_current(self) -> None:
        """
        记录当前内存使用量(自动从 tracemalloc 获取)

        Raises:
            MetricError: 收集器未启动
        """
        if not self._started:
            raise MetricError(
                code=ErrorCode.METRIC_COLLECTION_FAILED,
                message="内存收集器未启动,请先调用 start()",
                metric_name=self.name,
            )
        current, peak = tracemalloc.get_traced_memory()
        self._samples.append(float(current))
        self._peak_memory = float(peak)

    def stop(self) -> None:
        """停止收集(记录结束内存)"""
        if self._started:
            current, peak = tracemalloc.get_traced_memory()
            self._end_memory = float(current)
            self._peak_memory = float(peak)
        self._started = False

    def detect_leak(self) -> float:
        """
        检测内存泄漏

        通过对比 start() 和 stop() 时的内存使用量,
        判断是否存在内存泄漏。

        Returns:
            泄漏的字节数(正值表示泄漏,负值表示释放,0 表示无变化)

        Raises:
            MetricError: 未完成 start/stop 周期
        """
        if self._start_memory is None or self._end_memory is None:
            raise MetricError(
                code=ErrorCode.METRIC_COLLECTION_FAILED,
                message="内存泄漏检测需要先完成 start/stop 周期",
                metric_name=self.name,
            )
        return self._end_memory - self._start_memory

    def get_result(self) -> MetricSample:
        """
        获取内存度量结果

        Returns:
            MetricSample: 含 peak/avg/current/leak 统计信息

        Raises:
            MetricError: 样本不足
        """
        if not self._samples and self._peak_memory is None:
            raise MetricError(
                code=ErrorCode.METRIC_INSUFFICIENT_SAMPLES,
                message="无内存样本,请先收集数据",
                metric_name=self.name,
            )

        n = len(self._samples)
        if n > 0:
            mean = sum(self._samples) / n
            min_val = min(self._samples)
            max_val = max(self._samples)
        else:
            mean = 0.0
            min_val = 0.0
            max_val = 0.0

        statistics: Dict[str, float] = {
            "count": float(n),
            "mean": mean,
            "min": min_val,
            "max": max_val,
            "peak": float(self._peak_memory or 0.0),
            "current": float(self._end_memory or 0.0),
        }

        # 添加泄漏信息(如果已完成 start/stop 周期)
        if self._start_memory is not None and self._end_memory is not None:
            statistics["leak"] = self._end_memory - self._start_memory
            statistics["start_memory"] = self._start_memory
            statistics["end_memory"] = self._end_memory

        return MetricSample(
            metric_name=self.name,
            metric_type=MetricType.MEMORY,
            unit=self._unit,
            samples=list(self._samples),
            statistics=statistics,
            timestamp=datetime.now(),
        )

    def reset(self) -> None:
        """重置收集器"""
        self._samples = []
        self._started = False
        self._start_memory = None
        self._end_memory = None
        self._peak_memory = None

        # 如果是我们启动的 tracemalloc,停止它
        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False

    def __repr__(self) -> str:
        return f"<MemoryCollector samples={len(self._samples)} unit={self._unit}>"


__all__ = ["MemoryCollector"]
