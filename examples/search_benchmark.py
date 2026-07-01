# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""search_benchmark — 搜索算法基准

对比两种搜索算法的性能:
    - LinearSearchBenchmark: 线性搜索 O(n)
    - BinarySearchBenchmark: 二分搜索 O(log n)(要求有序列表)

使用示例:
    from examples.search_benchmark import LinearSearchBenchmark, BinarySearchBenchmark
    from core_benchmark.runners import BenchmarkSuiteRunner

    suite = BenchmarkSuiteRunner("search_compare")
    suite.register("linear", LinearSearchBenchmark())
    suite.register("binary", BinarySearchBenchmark())
    result = suite.run_all(input_data=5000, iterations=100, warmup=5)
"""

from __future__ import annotations

import random
from typing import Any, List

from core_benchmark.core.interfaces import IBenchmark


def _generate_sorted_data(size: int) -> List[int]:
    """生成有序随机整数列表"""
    return sorted(random.randint(0, size * 10) for _ in range(size))


class LinearSearchBenchmark(IBenchmark):
    """线性搜索基准 — O(n) 复杂度"""

    @property
    def name(self) -> str:
        return "linear_search"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "线性搜索 O(n) — 逐元素遍历查找"

    def setup(self, config: Any = None) -> None:
        self._size = 5000
        if config and isinstance(config, dict):
            self._size = config.get("size", 5000)

    def run(self, input_data: Any) -> int:
        data = _generate_sorted_data(self._size)
        target = data[len(data) // 2]  # 查找中间元素
        for i, val in enumerate(data):
            if val == target:
                return i
        return -1

    def teardown(self) -> None:
        pass


class BinarySearchBenchmark(IBenchmark):
    """二分搜索基准 — O(log n) 复杂度"""

    @property
    def name(self) -> str:
        return "binary_search"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "二分搜索 O(log n) — 有序列表上的分治查找"

    def setup(self, config: Any = None) -> None:
        self._size = 5000
        if config and isinstance(config, dict):
            self._size = config.get("size", 5000)

    def run(self, input_data: Any) -> int:
        data = _generate_sorted_data(self._size)
        target = data[len(data) // 2]  # 查找中间元素
        left, right = 0, len(data) - 1
        while left <= right:
            mid = (left + right) // 2
            if data[mid] == target:
                return mid
            elif data[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1

    def teardown(self) -> None:
        pass


__all__ = [
    "LinearSearchBenchmark",
    "BinarySearchBenchmark",
]
