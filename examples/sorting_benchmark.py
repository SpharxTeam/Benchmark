# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""sorting_benchmark — 排序算法基准

对比三种排序算法的性能:
    - BubbleSortBenchmark: 冒泡排序 O(n²)
    - QuickSortBenchmark: 快速排序 O(n log n)
    - BuiltInSortBenchmark: Python 内置 sorted() O(n log n)

使用示例:
    from examples.sorting_benchmark import BubbleSortBenchmark, QuickSortBenchmark, BuiltInSortBenchmark
    from core_benchmark.runners import BenchmarkSuiteRunner

    suite = BenchmarkSuiteRunner("sort_compare")
    suite.register("bubble", BubbleSortBenchmark())
    suite.register("quick", QuickSortBenchmark())
    suite.register("builtin", BuiltInSortBenchmark())
    result = suite.run_all(input_data=500, iterations=100, warmup=5)
"""

from __future__ import annotations

import random
from typing import Any, List

from core_benchmark.core.interfaces import IBenchmark


def _generate_data(size: int) -> List[int]:
    """生成指定大小的随机整数列表"""
    return [random.randint(0, 10000) for _ in range(size)]


class BubbleSortBenchmark(IBenchmark):
    """冒泡排序基准 — O(n²) 复杂度"""

    @property
    def name(self) -> str:
        return "bubble_sort"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "冒泡排序 O(n²) — 经典低效排序算法"

    def setup(self, config: Any = None) -> None:
        self._size = 500
        if config and isinstance(config, dict):
            self._size = config.get("size", 500)

    def run(self, input_data: Any) -> List[int]:
        data = _generate_data(self._size)
        n = len(data)
        for i in range(n):
            for j in range(0, n - i - 1):
                if data[j] > data[j + 1]:
                    data[j], data[j + 1] = data[j + 1], data[j]
        return data

    def teardown(self) -> None:
        pass


class QuickSortBenchmark(IBenchmark):
    """快速排序基准 — O(n log n) 平均复杂度"""

    @property
    def name(self) -> str:
        return "quick_sort"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "快速排序 O(n log n) — 分治排序算法"

    def setup(self, config: Any = None) -> None:
        self._size = 500
        if config and isinstance(config, dict):
            self._size = config.get("size", 500)

    def run(self, input_data: Any) -> List[int]:
        data = _generate_data(self._size)
        return self._quicksort(data)

    def _quicksort(self, arr: List[int]) -> List[int]:
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        return self._quicksort(left) + middle + self._quicksort(right)

    def teardown(self) -> None:
        pass


class BuiltInSortBenchmark(IBenchmark):
    """Python 内置排序基准 — O(n log n) C 实现优化"""

    @property
    def name(self) -> str:
        return "builtin_sort"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Python 内置 sorted() — C 实现的 Timsort 算法"

    def setup(self, config: Any = None) -> None:
        self._size = 500
        if config and isinstance(config, dict):
            self._size = config.get("size", 500)

    def run(self, input_data: Any) -> List[int]:
        data = _generate_data(self._size)
        return sorted(data)

    def teardown(self) -> None:
        pass


__all__ = [
    "BubbleSortBenchmark",
    "QuickSortBenchmark",
    "BuiltInSortBenchmark",
]
