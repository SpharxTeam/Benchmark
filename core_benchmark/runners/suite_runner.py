# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.runners.suite_runner — 多算法批量基准运行器

提供多算法基准测试的批量执行能力:
    - 注册多个算法基准到套件
    - 支持串行和并行执行(concurrent.futures)
    - 支持每个基准独立的输入数据和迭代次数
    - 返回聚合的 SuiteResult

使用示例:
    from core_benchmark.runners.suite_runner import BenchmarkSuiteRunner

    runner = BenchmarkSuiteRunner()
    runner.register("sort_benchmark", SortBenchmark())
    runner.register("search_benchmark", SearchBenchmark())

    # 串行执行
    suite_result = runner.run_all(
        input_data=test_data,
        iterations=100,
    )

    # 并行执行
    suite_result = runner.run_all(
        input_data=test_data,
        iterations=100,
        parallel=True,
        max_workers=4,
    )

    # 生成报告
    from core_benchmark.reporting.json_reporter import JsonReporter
    reporter = JsonReporter()
    reporter.generate(suite_result.results, "./produce/report.json")
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from core_benchmark.core.abstractions import ErrorCode, RunnerError
from core_benchmark.core.interfaces import IBenchmark, IMetricCollector
from core_benchmark.core.models import BenchmarkResult, SuiteResult
from core_benchmark.runners.base_runner import BaseBenchmarkRunner


# 类型别名:输入数据可以是固定值或按基准名称提供
InputProvider = Union[Any, Callable[[str], Any]]


class BenchmarkSuiteRunner:
    """
    多算法批量基准运行器

    管理多个算法基准的注册和批量执行,支持串行和并行模式。

    功能:
        - register(): 注册算法基准到套件
        - run_all(): 批量执行所有基准
        - 支持 parallel 模式(基于 ThreadPoolExecutor)
        - 支持每个基准独立的输入数据(InputProvider 回调)
    """

    def __init__(self, suite_name: str = "benchmark_suite") -> None:
        """
        初始化基准套件运行器

        Args:
            suite_name: 套件名称
        """
        self._suite_name = suite_name
        self._benchmarks: Dict[
            str,
            Tuple[IBenchmark, List[IMetricCollector]],
        ] = {}

    @property
    def suite_name(self) -> str:
        return self._suite_name

    @property
    def size(self) -> int:
        """已注册的基准数量"""
        return len(self._benchmarks)

    @property
    def benchmark_names(self) -> List[str]:
        """已注册的基准名称列表"""
        return list(self._benchmarks.keys())

    def register(
        self,
        name: str,
        benchmark: IBenchmark,
        collectors: Optional[List[IMetricCollector]] = None,
    ) -> None:
        """
        注册算法基准到套件

        Args:
            name: 基准名称(唯一标识)
            benchmark: 算法基准实例
            collectors: 该基准的度量收集器列表(可选)

        Raises:
            RunnerError: 名称已存在
        """
        if name in self._benchmarks:
            raise RunnerError(
                code=ErrorCode.RUNNER_NOT_CONFIGURED,
                message=f"基准 '{name}' 已注册,不能重复注册",
                runner_name=self._suite_name,
            )
        self._benchmarks[name] = (benchmark, collectors or [])

    def unregister(self, name: str) -> bool:
        """
        注销算法基准

        Args:
            name: 基准名称

        Returns:
            bool: 是否成功注销
        """
        if name in self._benchmarks:
            del self._benchmarks[name]
            return True
        return False

    def clear(self) -> None:
        """清空所有注册的基准"""
        self._benchmarks.clear()

    def run_all(
        self,
        input_data: InputProvider,
        iterations: int = 100,
        warmup: int = 0,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SuiteResult:
        """
        批量执行所有基准

        Args:
            input_data: 输入数据(固定值)或输入提供者回调(按基准名称提供)
            iterations: 正式迭代次数
            warmup: 预热迭代次数
            parallel: 是否并行执行(默认 False 串行)
            max_workers: 并行模式的最大线程数(None 表示自动)
            config: 算法配置参数

        Returns:
            SuiteResult: 聚合的基准套件结果

        Raises:
            RunnerError: 套件为空
        """
        if not self._benchmarks:
            raise RunnerError(
                code=ErrorCode.RUNNER_SUITE_EMPTY,
                message="基准套件为空,请先注册基准",
                runner_name=self._suite_name,
            )

        start_time = time.perf_counter()

        if parallel:
            results = self._run_parallel(
                input_data, iterations, warmup, max_workers, config
            )
        else:
            results = self._run_sequential(
                input_data, iterations, warmup, config
            )

        duration = time.perf_counter() - start_time

        suite_result = SuiteResult(
            suite_name=self._suite_name,
            results=results,
            total_duration_seconds=duration,
        )

        return suite_result

    def _resolve_input(self, input_data: InputProvider, name: str) -> Any:
        """
        解析输入数据

        如果 input_data 是可调用对象,调用它获取该基准的输入;
        否则直接返回 input_data。

        Args:
            input_data: 输入数据或输入提供者回调
            name: 基准名称(用于回调)

        Returns:
            该基准的输入数据
        """
        if callable(input_data):
            return input_data(name)
        return input_data

    def _run_sequential(
        self,
        input_data: InputProvider,
        iterations: int,
        warmup: int,
        config: Optional[Dict[str, Any]],
    ) -> List[BenchmarkResult]:
        """串行执行所有基准"""
        results: List[BenchmarkResult] = []

        for name, (benchmark, collectors) in self._benchmarks.items():
            runner = BaseBenchmarkRunner(benchmark, collectors)
            bench_input = self._resolve_input(input_data, name)
            result = runner.run(
                input_data=bench_input,
                iterations=iterations,
                warmup=warmup,
                config=config,
            )
            # 覆盖 benchmark_name 为注册的名称
            result.benchmark_name = name
            results.append(result)

        return results

    def _run_parallel(
        self,
        input_data: InputProvider,
        iterations: int,
        warmup: int,
        max_workers: Optional[int],
        config: Optional[Dict[str, Any]],
    ) -> List[BenchmarkResult]:
        """
        并行执行所有基准

        使用 ThreadPoolExecutor 实现并行执行。
        注意: 由于 GIL,纯 Python 算法可能无法获得真正的并行加速;
        适用于 IO 密集型或有 C 扩展的算法。

        Args:
            input_data: 输入数据或输入提供者回调
            iterations: 正式迭代次数
            warmup: 预热迭代次数
            max_workers: 最大线程数
            config: 算法配置参数

        Returns:
            各基准的结果列表(按完成顺序)

        Raises:
            RunnerError: 并行执行失败
        """
        results: List[BenchmarkResult] = []

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_name: Dict[Any, str] = {}

                for name, (benchmark, collectors) in self._benchmarks.items():
                    runner = BaseBenchmarkRunner(benchmark, collectors)
                    bench_input = self._resolve_input(input_data, name)
                    future = executor.submit(
                        runner.run,
                        input_data=bench_input,
                        iterations=iterations,
                        warmup=warmup,
                        config=config,
                    )
                    future_to_name[future] = name

                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        result = future.result()
                        result.benchmark_name = name
                        results.append(result)
                    except Exception as e:
                        # 并行执行中的错误,创建失败结果
                        error_result = BenchmarkResult(
                            benchmark_name=name,
                            algorithm_name=name,
                            iterations=iterations,
                            success=False,
                            error=f"并行执行失败: {e}",
                        )
                        results.append(error_result)

        except Exception as e:
            raise RunnerError(
                code=ErrorCode.RUNNER_PARALLEL_ERROR,
                message=f"并行执行失败: {e}",
                runner_name=self._suite_name,
            )

        return results

    def __repr__(self) -> str:
        return (
            f"<BenchmarkSuiteRunner "
            f"name={self._suite_name} "
            f"size={self.size}>"
        )


__all__ = ["BenchmarkSuiteRunner"]
