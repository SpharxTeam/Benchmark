# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""examples — 示例算法基准

提供三个示例算法基准,展示如何使用 Benchmark 库:
    - sorting_benchmark: 排序算法对比(冒泡/快速/内置)
    - search_benchmark: 搜索算法对比(线性/二分)
    - string_benchmark: 字符串操作对比(拼接/join/f-string)

使用示例:
    from examples.sorting_benchmark import BubbleSortBenchmark, QuickSortBenchmark
    from core_benchmark.runners import BenchmarkSuiteRunner

    suite = BenchmarkSuiteRunner("sort_compare")
    suite.register("bubble", BubbleSortBenchmark())
    suite.register("quick", QuickSortBenchmark())
    result = suite.run_all(input_data=500, iterations=100)
"""
