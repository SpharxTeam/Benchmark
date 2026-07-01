# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
"""
core_benchmark.metrics.accuracy — 准确度度量收集器

提供准确度度量收集能力:
    - 支持 mAP、Precision、Recall、F1 度量
    - 支持自定义度量回调
    - 支持二分类和多分类评估
    - 单位: %(百分比)或 ratio(0-1)

使用示例:
    # 方式1: 直接记录准确度值
    collector = AccuracyCollector()
    collector.start()
    for accuracy in [0.95, 0.92, 0.88, 0.96]:
        collector.record(accuracy)
    collector.stop()
    result = collector.get_result()

    # 方式2: 添加预测对,自动计算 Precision/Recall/F1
    collector = AccuracyCollector()
    collector.start()
    collector.add_prediction("cat", "cat")    # TP
    collector.add_prediction("cat", "dog")    # FP
    collector.add_prediction("dog", "dog")    # TP
    collector.add_prediction("dog", "cat")    # FP
    collector.stop()
    result = collector.get_result()  # 含 precision/recall/f1

    # 方式3: 自定义度量回调
    collector = AccuracyCollector()
    collector.register_custom_metric("mae", lambda preds, truth: sum(abs(p-t) for p,t in zip(preds, truth))/len(preds))
    collector.start()
    collector.add_prediction(0.9, 1.0)
    collector.add_prediction(0.8, 0.7)
    collector.stop()
    result = collector.get_result()  # 含 mae
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from core_benchmark.core.abstractions import ErrorCode, MetricError
from core_benchmark.core.interfaces import IMetricCollector
from core_benchmark.core.models import MetricSample, MetricType


class AccuracyCollector(IMetricCollector):
    """
    准确度度量收集器

    支持多种准确度度量:
        - 直接记录准确度值(record())
        - 添加预测对计算 Precision/Recall/F1(add_prediction())
        - 自定义度量回调(register_custom_metric())
    """

    def __init__(self, unit: str = "%") -> None:
        """
        初始化准确度收集器

        Args:
            unit: 度量单位(默认 %,可选 ratio)
        """
        self._unit = unit
        self._samples: List[float] = []
        self._predictions: List[Any] = []
        self._ground_truth: List[Any] = []
        self._custom_metrics: Dict[str, Callable[[List[Any], List[Any]], float]] = {}
        self._started = False

    @property
    def name(self) -> str:
        return "accuracy"

    @property
    def unit(self) -> str:
        return self._unit

    def start(self) -> None:
        """开始收集准确度度量"""
        self._samples = []
        self._predictions = []
        self._ground_truth = []
        self._started = True

    def record(self, value: float) -> None:
        """
        记录一个准确度值

        Args:
            value: 准确度值(0-100 如果单位为 %,0-1 如果单位为 ratio)

        Raises:
            MetricError: 收集器未启动或值无效
        """
        if not self._started:
            raise MetricError(
                code=ErrorCode.METRIC_COLLECTION_FAILED,
                message="准确度收集器未启动,请先调用 start()",
                metric_name=self.name,
            )
        if value < 0:
            raise MetricError(
                code=ErrorCode.METRIC_OUT_OF_RANGE,
                message=f"准确度值不能为负数,实际为 {value}",
                metric_name=self.name,
            )
        self._samples.append(float(value))

    def add_prediction(self, prediction: Any, ground_truth: Any) -> None:
        """
        添加预测/真实值对,用于计算 Precision/Recall/F1

        Args:
            prediction: 预测值
            ground_truth: 真实值

        Raises:
            MetricError: 收集器未启动
        """
        if not self._started:
            raise MetricError(
                code=ErrorCode.METRIC_COLLECTION_FAILED,
                message="准确度收集器未启动,请先调用 start()",
                metric_name=self.name,
            )
        self._predictions.append(prediction)
        self._ground_truth.append(ground_truth)

    def register_custom_metric(
        self,
        name: str,
        callback: Callable[[List[Any], List[Any]], float],
    ) -> None:
        """
        注册自定义度量回调

        Args:
            name: 度量名称
            callback: 计算回调,接受 (predictions, ground_truth) 列表,返回 float
        """
        self._custom_metrics[name] = callback

    def stop(self) -> None:
        """停止收集"""
        self._started = False

    def compute_precision(self, positive_class: Any = True) -> float:
        """
        计算 Precision(精确率)

        Precision = TP / (TP + FP)

        Args:
            positive_class: 正样本类别(默认 True)

        Returns:
            Precision 值(0-1)
        """
        if not self._predictions:
            return 0.0
        tp = sum(1 for p, t in zip(self._predictions, self._ground_truth)
                 if p == positive_class and t == positive_class)
        fp = sum(1 for p, t in zip(self._predictions, self._ground_truth)
                 if p == positive_class and t != positive_class)
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)

    def compute_recall(self, positive_class: Any = True) -> float:
        """
        计算 Recall(召回率)

        Recall = TP / (TP + FN)

        Args:
            positive_class: 正样本类别(默认 True)

        Returns:
            Recall 值(0-1)
        """
        if not self._predictions:
            return 0.0
        tp = sum(1 for p, t in zip(self._predictions, self._ground_truth)
                 if p == positive_class and t == positive_class)
        fn = sum(1 for p, t in zip(self._predictions, self._ground_truth)
                 if p != positive_class and t == positive_class)
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)

    def compute_f1(self, positive_class: Any = True) -> float:
        """
        计算 F1 分数

        F1 = 2 * (Precision * Recall) / (Precision + Recall)

        Args:
            positive_class: 正样本类别(默认 True)

        Returns:
            F1 值(0-1)
        """
        precision = self.compute_precision(positive_class)
        recall = self.compute_recall(positive_class)
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def compute_accuracy(self) -> float:
        """
        计算分类准确率

        Accuracy = (正确预测数) / (总预测数)

        Returns:
            Accuracy 值(0-1)
        """
        if not self._predictions:
            return 0.0
        correct = sum(1 for p, t in zip(self._predictions, self._ground_truth)
                      if p == t)
        return correct / len(self._predictions)

    def get_result(self) -> MetricSample:
        """
        获取准确度度量结果

        Returns:
            MetricSample: 含 mean/precision/recall/f1/accuracy 统计信息

        Raises:
            MetricError: 样本不足
        """
        statistics: Dict[str, float] = {}

        # 如果有直接记录的准确度值,计算统计
        if self._samples:
            n = len(self._samples)
            mean = sum(self._samples) / n
            sorted_samples = sorted(self._samples)
            min_val = sorted_samples[0]
            max_val = sorted_samples[-1]
            variance = sum((x - mean) ** 2 for x in self._samples) / n
            std = math.sqrt(variance)

            statistics.update({
                "count": float(n),
                "mean": mean,
                "min": min_val,
                "max": max_val,
                "std": std,
            })

        # 如果有预测对,计算 Precision/Recall/F1/Accuracy
        if self._predictions:
            statistics["precision"] = self.compute_precision()
            statistics["recall"] = self.compute_recall()
            statistics["f1"] = self.compute_f1()
            statistics["accuracy"] = self.compute_accuracy()
            statistics["prediction_count"] = float(len(self._predictions))

        # 如果没有样本和预测对,报错
        if not self._samples and not self._predictions:
            raise MetricError(
                code=ErrorCode.METRIC_INSUFFICIENT_SAMPLES,
                message="无准确度样本,请先收集数据(record() 或 add_prediction())",
                metric_name=self.name,
            )

        # 计算自定义度量
        for name, callback in self._custom_metrics.items():
            try:
                value = callback(self._predictions, self._ground_truth)
                statistics[name] = float(value)
            except Exception as e:
                statistics[f"{name}_error"] = float("inf")
                # 不抛出异常,继续其他度量

        return MetricSample(
            metric_name=self.name,
            metric_type=MetricType.ACCURACY,
            unit=self._unit,
            samples=list(self._samples),
            statistics=statistics,
            timestamp=datetime.now(),
        )

    def reset(self) -> None:
        """重置收集器"""
        self._samples = []
        self._predictions = []
        self._ground_truth = []
        self._started = False

    def __repr__(self) -> str:
        return (
            f"<AccuracyCollector samples={len(self._samples)} "
            f"predictions={len(self._predictions)} unit={self._unit}>"
        )


__all__ = ["AccuracyCollector"]
