# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.runners.base_runner — 单算法基准运行器

提供单算法基准测试的执行框架:
    - 自动管理算法生命周期(setup → run → teardown)
    - 自动集成 LatencyCollector 计时每次迭代
    - 支持自定义度量收集器列表
    - 支持预热迭代(warmup)
    - 错误隔离(单次失败不影响整体)

使用示例:
    from core_benchmark.runners.base_runner import BaseBenchmarkRunner
    from core_benchmark.metrics.latency import LatencyCollector
    from core_benchmark.metrics.memory import MemoryCollector

    benchmark = MyAlgorithmBenchmark()
    runner = BaseBenchmarkRunner(
        benchmark=benchmark,
        collectors=[MemoryCollector()],
    )
    result = runner.run(
        input_data=test_data,
        iterations=100,
        warmup=10,
    )
    print(result.to_summary_dict())
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core_benchmark.core.abstractions import AlgorithmError, ErrorCode
from core_benchmark.core.interfaces import IBenchmark, IMetricCollector
from core_benchmark.core.models import BenchmarkResult
from core_benchmark.metrics.latency import LatencyCollector


class BaseBenchmarkRunner:
    """
    单算法基准运行器

    自动管理算法基准的执行流程:
        1. setup() — 初始化算法
        2. warmup 迭代(可选)— 预热,不记录度量
        3. 正式迭代 — 每次用 LatencyCollector 计时
        4. teardown() — 清理资源

    自动添加 LatencyCollector 来计时每次迭代。
    用户可额外提供其他收集器(MemoryCollector, AccuracyCollector 等)。
    """

    def __init__(
        self,
        benchmark: IBenchmark,
        collectors: Optional[List[IMetricCollector]] = None,
    ) -> None:
        """
        初始化基准运行器

        Args:
            benchmark: 算法基准实例(实现 IBenchmark 接口)
            collectors: 额外的度量收集器列表(自动添加 LatencyCollector)
        """
        self._benchmark = benchmark
        self._user_collectors = collectors or []
        # 自动添加的延迟收集器(不与用户提供的重复)
        self._latency_collector = LatencyCollector()

    @property
    def benchmark(self) -> IBenchmark:
        return self._benchmark

    def run(
        self,
        input_data: Any,
        iterations: int = 100,
        warmup: int = 0,
        config: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkResult:
        """
        运行基准测试

        Args:
            input_data: 输入数据
            iterations: 正式迭代次数(必须 >= 1)
            warmup: 预热迭代次数(不记录度量,默认 0)
            config: 算法配置参数

        Returns:
            BenchmarkResult: 基准测试结果(含延迟度量)

        Raises:
            AlgorithmError: 迭代次数无效
        """
        if iterations < 1:
            raise AlgorithmError(
                code=ErrorCode.RUNNER_INVALID_ITERATIONS,
                message=f"迭代次数必须 >= 1,实际为 {iterations}",
                algorithm_name=self._benchmark.name,
            )

        all_collectors: List[IMetricCollector] = [
            self._latency_collector,
            *self._user_collectors,
        ]

        start_time = time.perf_counter()
        success = True
        error_msg: Optional[str] = None

        # 启动所有收集器
        for collector in all_collectors:
            collector.start()

        try:
            # 初始化算法
            self._benchmark.setup(config)

            # 预热迭代(不记录度量)
            for _ in range(warmup):
                self._benchmark.run(input_data)

            # 正式迭代
            for _ in range(iterations):
                try:
                    with self._latency_collector.time():
                        self._benchmark.run(input_data)
                except Exception as e:
                    success = False
                    error_msg = f"迭代执行失败: {e}"
                    break

        except Exception as e:
            success = False
            error_msg = f"基准执行失败: {e}"

        finally:
            # 清理资源
            try:
                self._benchmark.teardown()
            except Exception as e:
                if success:
                    error_msg = f"清理失败: {e}"
                    success = False

            # 停止所有收集器
            for collector in all_collectors:
                try:
                    collector.stop()
                except Exception:
                    pass

        duration = time.perf_counter() - start_time

        # 收集度量结果
        metrics: Dict[str, Any] = {}
        for collector in all_collectors:
            try:
                sample = collector.get_result()
                metrics[sample.metric_name] = sample
            except Exception:
                # 跳过无样本或计算失败的收集器
                pass

        return BenchmarkResult(
            benchmark_name=self._benchmark.name,
            algorithm_name=self._benchmark.name,
            version=self._benchmark.version,
            iterations=iterations,
            metrics=metrics,
            duration_seconds=duration,
            success=success,
            error=error_msg,
            metadata={
                "warmup_iterations": warmup,
                "collector_count": len(all_collectors),
            },
        )

    def __repr__(self) -> str:
        return (
            f"<BaseBenchmarkRunner "
            f"benchmark={self._benchmark.name} "
            f"collectors={len(self._user_collectors) + 1}>"
        )


__all__ = ["BaseBenchmarkRunner"]
