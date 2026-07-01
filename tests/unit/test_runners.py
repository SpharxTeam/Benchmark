# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""test_runners — BaseBenchmarkRunner / BenchmarkSuiteRunner 测试"""

import pytest

from core_benchmark.core.abstractions import (
    AlgorithmError,
    ErrorCode,
    RunnerError,
)
from core_benchmark.core.interfaces import IBenchmark
from core_benchmark.core.models import BenchmarkResult, SuiteResult
from core_benchmark.metrics import MemoryCollector
from core_benchmark.runners import BaseBenchmarkRunner, BenchmarkSuiteRunner


# =============================================================================
# 测试用 Mock 基准
# =============================================================================

class MockBenchmark(IBenchmark):
    """简单 mock 基准"""

    def __init__(self, name="mock", fail=False):
        self._name = name
        self._fail = fail
        self.setup_called = False
        self.teardown_called = False
        self.run_count = 0

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return "1.0.0"

    def setup(self, config=None):
        self.setup_called = True

    def run(self, input_data):
        self.run_count += 1
        if self._fail:
            raise RuntimeError("模拟失败")
        return sum(range(input_data))

    def teardown(self):
        self.teardown_called = True


# =============================================================================
# BaseBenchmarkRunner 测试
# =============================================================================

class TestBaseBenchmarkRunner:
    """单算法基准运行器测试"""

    def test_basic_run(self):
        bench = MockBenchmark()
        runner = BaseBenchmarkRunner(bench)
        result = runner.run(input_data=100, iterations=10)
        assert result.success is True
        assert result.iterations == 10
        assert result.benchmark_name == "mock"
        assert result.version == "1.0.0"
        assert bench.setup_called is True
        assert bench.teardown_called is True
        assert bench.run_count == 10

    def test_with_warmup(self):
        bench = MockBenchmark()
        runner = BaseBenchmarkRunner(bench)
        result = runner.run(input_data=10, iterations=5, warmup=3)
        assert result.success is True
        # 5 正式 + 3 预热 = 8 次 run
        assert bench.run_count == 8

    def test_with_memory_collector(self):
        bench = MockBenchmark()
        runner = BaseBenchmarkRunner(bench, collectors=[MemoryCollector()])
        result = runner.run(input_data=10, iterations=5)
        assert "latency" in result.metrics
        assert "memory" in result.metrics

    def test_error_isolation(self):
        """单次迭代失败应记录错误"""
        bench = MockBenchmark(fail=True)
        runner = BaseBenchmarkRunner(bench)
        result = runner.run(input_data=10, iterations=5)
        assert result.success is False
        assert result.error is not None
        # teardown 仍应被调用
        assert bench.teardown_called is True

    def test_invalid_iterations(self):
        bench = MockBenchmark()
        runner = BaseBenchmarkRunner(bench)
        with pytest.raises(AlgorithmError) as exc_info:
            runner.run(input_data=10, iterations=0)
        assert exc_info.value.code == ErrorCode.RUNNER_INVALID_ITERATIONS

    def test_with_config(self):
        bench = MockBenchmark()
        runner = BaseBenchmarkRunner(bench)
        result = runner.run(input_data=10, iterations=3, config={"key": "value"})
        assert result.success is True

    def test_repr(self):
        bench = MockBenchmark()
        runner = BaseBenchmarkRunner(bench)
        r = repr(runner)
        assert "mock" in r


# =============================================================================
# BenchmarkSuiteRunner 测试
# =============================================================================

class TestBenchmarkSuiteRunner:
    """多算法批量基准运行器测试"""

    def test_register_and_size(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        suite.register("b", MockBenchmark("b"))
        assert suite.size == 2
        assert "a" in suite.benchmark_names
        assert "b" in suite.benchmark_names

    def test_duplicate_register_raises(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        with pytest.raises(RunnerError) as exc_info:
            suite.register("a", MockBenchmark("a"))
        assert exc_info.value.code == ErrorCode.RUNNER_NOT_CONFIGURED

    def test_unregister(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        assert suite.unregister("a") is True
        assert suite.size == 0
        assert suite.unregister("nonexistent") is False

    def test_clear(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        suite.register("b", MockBenchmark("b"))
        suite.clear()
        assert suite.size == 0

    def test_run_serial(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        suite.register("b", MockBenchmark("b"))
        result = suite.run_all(input_data=10, iterations=5)
        assert isinstance(result, SuiteResult)
        assert result.total_count == 2
        assert result.success_count == 2
        assert result.failure_count == 0
        assert result.success_rate == 1.0

    def test_run_parallel(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        suite.register("b", MockBenchmark("b"))
        result = suite.run_all(
            input_data=10, iterations=5, parallel=True, max_workers=2
        )
        assert result.total_count == 2
        assert result.success_count == 2

    def test_input_provider_callback(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        suite.register("b", MockBenchmark("b"))

        def provider(name):
            return 5 if name == "a" else 20

        result = suite.run_all(input_data=provider, iterations=3)
        assert result.success_count == 2

    def test_empty_suite_raises(self):
        suite = BenchmarkSuiteRunner("empty")
        with pytest.raises(RunnerError) as exc_info:
            suite.run_all(input_data=10, iterations=1)
        assert exc_info.value.code == ErrorCode.RUNNER_SUITE_EMPTY

    def test_mixed_success_failure(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("ok", MockBenchmark("ok"))
        suite.register("fail", MockBenchmark("fail", fail=True))
        result = suite.run_all(input_data=10, iterations=3)
        assert result.total_count == 2
        assert result.success_count == 1
        assert result.failure_count == 1

    def test_suite_name_property(self):
        suite = BenchmarkSuiteRunner("my_suite")
        assert suite.suite_name == "my_suite"

    def test_repr(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        r = repr(suite)
        assert "test" in r
        assert "size=1" in r

    def test_get_result_by_name(self):
        suite = BenchmarkSuiteRunner("test")
        suite.register("a", MockBenchmark("a"))
        result = suite.run_all(input_data=10, iterations=3)
        found = result.get_result("a")
        assert found is not None
        assert found.benchmark_name == "a"
        assert result.get_result("nonexistent") is None
