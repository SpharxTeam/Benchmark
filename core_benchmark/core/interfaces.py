# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.core.interfaces — 核心抽象接口

定义 Benchmark 模块的核心抽象接口:
    - IBenchmark: 算法基准抽象基类
    - IMetricCollector: 度量收集器接口

设计原则:
    1. 接口与实现分离(依赖倒置原则)
    2. 生命周期管理: setup → run → teardown
    3. 度量收集与算法执行解耦
    4. 支持上下文管理器协议(with 语句)

参考:
    - Workshop BasePipeline 生命周期模式
    - SpharxTools 工程标准规范手册
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core_benchmark.core.models import BenchmarkResult, MetricSample


# =============================================================================
# IBenchmark - 算法基准抽象基类
# =============================================================================

class IBenchmark(ABC):
    """
    算法基准抽象基类

    定义算法基准的标准生命周期:
        1. setup() — 初始化算法(加载模型、分配资源等)
        2. run(input_data) — 执行算法,返回输出
        3. teardown() — 清理资源

    使用示例:
        class SortBenchmark(IBenchmark):
            def setup(self, config):
                self._data = config.get("data", [])

            def run(self, input_data):
                # 执行排序算法
                return sorted(input_data)

            def teardown(self):
                self._data = None

    上下文管理器协议:
        with MyBenchmark() as bench:
            result = bench.run(data)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """算法基准名称"""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """算法版本"""
        ...

    @property
    def description(self) -> str:
        """算法描述(可选覆盖)"""
        return f"{self.name} benchmark v{self.version}"

    @abstractmethod
    def setup(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化算法

        Args:
            config: 算法配置参数

        Raises:
            AlgorithmError: 初始化失败
        """
        ...

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """
        执行算法

        Args:
            input_data: 输入数据

        Returns:
            算法输出

        Raises:
            AlgorithmError: 执行失败
        """
        ...

    @abstractmethod
    def teardown(self) -> None:
        """清理资源"""
        ...

    # 上下文管理器协议
    def __enter__(self) -> "IBenchmark":
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.teardown()
        # 不抑制异常
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} v{self.version}>"


# =============================================================================
# IMetricCollector - 度量收集器接口
# =============================================================================

class IMetricCollector(ABC):
    """
    度量收集器接口

    定义度量收集的标准生命周期:
        1. start() — 开始收集度量
        2. record(value) — 记录一个度量值
        3. stop() — 停止收集
        4. get_result() — 获取度量结果(MetricSample)
        5. reset() — 重置收集器

    使用示例:
        collector = LatencyCollector()
        collector.start()
        for _ in range(100):
            start = time.perf_counter_ns()
            algorithm.run(data)
            collector.record(time.perf_counter_ns() - start)
        collector.stop()
        result = collector.get_result()

    上下文管理器协议:
        with LatencyCollector() as collector:
            collector.record(value)
            result = collector.get_result()
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """度量名称(如 latency, throughput, memory, accuracy)"""
        ...

    @property
    @abstractmethod
    def unit(self) -> str:
        """度量单位(如 ns, ops/sec, MB, %)"""
        ...

    @abstractmethod
    def start(self) -> None:
        """开始收集度量"""
        ...

    @abstractmethod
    def record(self, value: float) -> None:
        """
        记录一个度量值

        Args:
            value: 度量值

        Raises:
            MetricError: 度量值无效
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """停止收集"""
        ...

    @abstractmethod
    def get_result(self) -> MetricSample:
        """
        获取度量结果

        Returns:
            MetricSample: 度量样本(含统计信息)

        Raises:
            MetricError: 样本不足或计算错误
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """重置收集器,清空所有样本"""
        ...

    # 上下文管理器协议
    def __enter__(self) -> "IMetricCollector":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} unit={self.unit}>"


# =============================================================================
# IReporter - 报告生成器接口(预声明,BM-T10 实现)
# =============================================================================

class IReporter(ABC):
    """
    报告生成器接口

    定义报告生成的标准接口:
        1. generate(results, output_path) — 生成报告文件
        2. format — 报告格式(json/csv/markdown)
    """

    @property
    @abstractmethod
    def format(self) -> str:
        """报告格式(json/csv/markdown)"""
        ...

    @abstractmethod
    def generate(
        self,
        results: List[BenchmarkResult],
        output_path: Optional[str] = None,
    ) -> str:
        """
        生成报告

        Args:
            results: 基准测试结果列表
            output_path: 输出文件路径(None 表示返回字符串)

        Returns:
            报告内容字符串(如果 output_path 为 None)或文件路径

        Raises:
            ReportError: 报告生成失败
        """
        ...


__all__ = [
    "IBenchmark",
    "IMetricCollector",
    "IReporter",
]
