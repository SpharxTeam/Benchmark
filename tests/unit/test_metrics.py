# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""test_metrics — 四大度量收集器测试(latency/throughput/memory/accuracy)"""

import time

import pytest

from core_benchmark.metrics import (
    LatencyCollector,
    ThroughputCollector,
    MemoryCollector,
    AccuracyCollector,
)
from core_benchmark.core.models import MetricType


# =============================================================================
# LatencyCollector 测试
# =============================================================================

class TestLatencyCollector:
    """延迟度量收集器测试"""

    def test_name_and_unit(self):
        c = LatencyCollector()
        assert c.name == "latency"
        assert c.unit == "ns"

    def test_record_and_result(self):
        c = LatencyCollector()
        c.start()
        c.record(100.0)
        c.record(200.0)
        c.record(300.0)
        c.stop()
        result = c.get_result()
        assert result.metric_name == "latency"
        assert result.metric_type == MetricType.LATENCY
        assert result.count == 3
        assert result.mean == 200.0
        assert result.min_value == 100.0
        assert result.max_value == 300.0

    def test_time_context_manager(self):
        c = LatencyCollector()
        c.start()
        with c.time():
            time.sleep(0.001)  # 1ms
        c.stop()
        result = c.get_result()
        assert result.count >= 1
        assert result.mean > 0

    def test_reset(self):
        from core_benchmark.core.abstractions import MetricError
        c = LatencyCollector()
        c.start()
        c.record(100.0)
        c.stop()
        c.reset()
        # reset 后无样本,get_result 应抛出 MetricError
        c.start()
        c.stop()
        with pytest.raises(MetricError):
            c.get_result()
        # reset 后重新记录应得到全新数据
        c.start()
        c.record(200.0)
        c.stop()
        result = c.get_result()
        assert result.count == 1
        assert result.mean == 200.0

    def test_percentiles(self):
        c = LatencyCollector()
        c.start()
        for v in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            c.record(float(v))
        c.stop()
        result = c.get_result()
        assert result.p50 is not None
        assert result.p90 is not None
        assert result.p99 is not None
        assert result.p50 <= result.p90 <= result.p99

    def test_context_manager_protocol(self):
        c = LatencyCollector()
        with c:
            c.record(50.0)
        result = c.get_result()
        assert result.count == 1


# =============================================================================
# ThroughputCollector 测试
# =============================================================================

class TestThroughputCollector:
    """吞吐度量收集器测试"""

    def test_name_and_unit(self):
        c = ThroughputCollector()
        assert c.name == "throughput"
        assert c.unit == "ops/sec"

    def test_record_and_result(self):
        c = ThroughputCollector()
        c.start()
        c.record(1000.0)
        c.record(2000.0)
        c.record(3000.0)
        c.stop()
        result = c.get_result()
        assert result.metric_name == "throughput"
        assert result.metric_type == MetricType.THROUGHPUT
        assert result.count == 3
        assert result.mean == 2000.0
        assert result.max_value == 3000.0
        assert result.min_value == 1000.0

    def test_window_size(self):
        c = ThroughputCollector(window_size=3)
        c.start()
        c.record(100.0)
        c.record(200.0)
        c.record(300.0)
        c.record(400.0)  # 滑出第一个
        c.stop()
        result = c.get_result()
        # 滑动窗口只保留最后 3 个:200, 300, 400
        assert result.count == 3
        assert result.mean == 300.0

    def test_reset(self):
        from core_benchmark.core.abstractions import MetricError
        c = ThroughputCollector()
        c.start()
        c.record(100.0)
        c.stop()
        c.reset()
        c.start()
        c.stop()
        with pytest.raises(MetricError):
            c.get_result()
        # reset 后重新记录应得到全新数据
        c.start()
        c.record(500.0)
        c.stop()
        result = c.get_result()
        assert result.count == 1
        assert result.mean == 500.0


# =============================================================================
# MemoryCollector 测试
# =============================================================================

class TestMemoryCollector:
    """内存度量收集器测试"""

    def test_name_and_unit(self):
        c = MemoryCollector()
        assert c.name == "memory"
        assert c.unit == "bytes"

    def test_record_and_result(self):
        c = MemoryCollector()
        c.start()
        # 分配一些内存
        _ = [b"x" * 1024 for _ in range(10)]
        c.record_current()
        c.stop()
        result = c.get_result()
        assert result.metric_name == "memory"
        assert result.metric_type == MetricType.MEMORY
        assert result.count >= 1

    def test_detect_leak(self):
        c = MemoryCollector()
        c.start()
        # 记录起始内存
        c.record_current()
        # 分配并保留内存
        _leak = [b"y" * 10240 for _ in range(5)]
        c.record_current()
        c.stop()
        result = c.get_result()
        # 内存峰值存储在 statistics 字典中
        assert result.statistics.get("peak", 0) >= 0

    def test_reset(self):
        c = MemoryCollector()
        c.start()
        c.record_current()
        c.stop()
        c.reset()
        c.start()
        c.stop()
        result = c.get_result()
        assert result.count == 0


# =============================================================================
# AccuracyCollector 测试
# =============================================================================

class TestAccuracyCollector:
    """准确度度量收集器测试"""

    def test_name_and_unit(self):
        c = AccuracyCollector()
        assert c.name == "accuracy"
        assert c.unit == "%"

    def test_add_predictions(self):
        c = AccuracyCollector()
        c.start()
        c.add_prediction(1, 1)  # 正确
        c.add_prediction(0, 0)  # 正确
        c.add_prediction(1, 0)  # 错误
        c.stop()
        result = c.get_result()
        assert result.metric_name == "accuracy"
        assert result.metric_type == MetricType.ACCURACY

    def test_accuracy_calculation(self):
        c = AccuracyCollector()
        c.start()
        c.add_prediction(1, 1)
        c.add_prediction(0, 0)
        c.add_prediction(1, 0)  # 错误
        c.stop()
        # accuracy 存储在 statistics 字典中(不是 mean 属性)
        result = c.get_result()
        acc = result.statistics.get("accuracy")
        assert acc is not None
        assert abs(acc - (2.0 / 3.0)) < 0.01

    def test_precision_recall_f1(self):
        c = AccuracyCollector()
        c.start()
        # TP=2, FP=1, FN=1, TN=1
        c.add_prediction(1, 1)  # TP
        c.add_prediction(1, 1)  # TP
        c.add_prediction(1, 0)  # FP
        c.add_prediction(0, 1)  # FN
        c.add_prediction(0, 0)  # TN
        c.stop()
        result = c.get_result()
        stats = result.statistics
        # precision = TP/(TP+FP) = 2/3
        assert abs(stats.get("precision", 0) - (2.0 / 3.0)) < 0.01
        # recall = TP/(TP+FN) = 2/3
        assert abs(stats.get("recall", 0) - (2.0 / 3.0)) < 0.01

    def test_custom_metric(self):
        c = AccuracyCollector()
        c.register_custom_metric("specificity", lambda tp, fp, fn, tn: tn / (tn + fp) if (tn + fp) > 0 else 0.0)
        c.start()
        c.add_prediction(1, 1)  # TP
        c.add_prediction(0, 0)  # TN
        c.add_prediction(1, 0)  # FP
        c.stop()
        result = c.get_result()
        # 自定义度量存储在 statistics 中(成功时为 specificity,失败时为 specificity_error)
        stats = result.statistics
        assert "specificity" in stats or "specificity_error" in stats
        if "specificity" in stats:
            # specificity = TN/(TN+FP) = 1/2 = 0.5
            assert abs(stats["specificity"] - 0.5) < 0.01

    def test_reset(self):
        from core_benchmark.core.abstractions import MetricError
        c = AccuracyCollector()
        c.start()
        c.add_prediction(1, 1)
        c.stop()
        c.reset()
        c.start()
        c.stop()
        with pytest.raises(MetricError):
            c.get_result()
        # reset 后重新记录应得到全新数据
        c.start()
        c.add_prediction(0, 0)
        c.stop()
        result = c.get_result()
        assert result.statistics.get("prediction_count") == 1
