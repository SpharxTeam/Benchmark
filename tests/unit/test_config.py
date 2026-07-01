# Copyright (c) 2026 SPHARX. All Rights Reserved.
"""test_config — 配置加载器测试"""

import os
import tempfile

import pytest

from core_benchmark.config import (
    Config,
    BenchmarkConfig,
    MetricsConfig,
    ReportingConfig,
    LoggingConfig,
    load_config,
    get_default_config,
    DEFAULT_CONFIG_PATH,
)
from core_benchmark.core.abstractions import ConfigurationError, ErrorCode


# =============================================================================
# 默认配置测试
# =============================================================================

class TestDefaultConfig:
    """默认配置测试"""

    def test_default_path_exists(self):
        assert DEFAULT_CONFIG_PATH.exists()

    def test_load_default(self):
        config = load_config()
        assert config.benchmark.iterations == 100
        assert config.benchmark.warmup == 5
        assert config.benchmark.parallel is False
        assert config.benchmark.max_workers is None

    def test_get_default_config(self):
        config = get_default_config()
        assert isinstance(config, Config)
        assert config.benchmark.iterations == 100

    def test_default_metrics(self):
        config = load_config()
        assert config.metrics.latency.unit == "ns"
        assert config.metrics.throughput.window_size == 100
        assert config.metrics.memory.enabled is True
        assert config.metrics.accuracy.enabled is False

    def test_default_reporting(self):
        config = load_config()
        assert config.reporting.output_dir == "./produce/reports"
        assert config.reporting.default_format == "json"
        assert config.reporting.include_metadata is True

    def test_default_logging(self):
        config = load_config()
        assert config.logging.level == "INFO"


# =============================================================================
# 用户配置覆盖测试
# =============================================================================

class TestUserOverride:
    """用户配置覆盖(深度合并)测试"""

    def test_partial_override(self):
        user_yaml = """
benchmark:
  iterations: 500
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(user_yaml)
            path = f.name
        try:
            config = load_config(path)
            assert config.benchmark.iterations == 500
            # 未覆盖的字段保留默认值
            assert config.benchmark.warmup == 5
            assert config.benchmark.parallel is False
        finally:
            os.unlink(path)

    def test_deep_merge_preserves_defaults(self):
        user_yaml = """
benchmark:
  iterations: 200
  parallel: true
reporting:
  default_format: markdown
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(user_yaml)
            path = f.name
        try:
            config = load_config(path)
            # 覆盖的值
            assert config.benchmark.iterations == 200
            assert config.benchmark.parallel is True
            assert config.reporting.default_format == "markdown"
            # 未覆盖的值保留默认
            assert config.benchmark.warmup == 5
            assert config.metrics.latency.unit == "ns"
            assert config.logging.level == "INFO"
        finally:
            os.unlink(path)

    def test_empty_file_returns_default(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            path = f.name
        try:
            config = load_config(path)
            assert config.benchmark.iterations == 100
        finally:
            os.unlink(path)

    def test_override_max_workers(self):
        user_yaml = """
benchmark:
  max_workers: 8
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(user_yaml)
            path = f.name
        try:
            config = load_config(path)
            assert config.benchmark.max_workers == 8
        finally:
            os.unlink(path)


# =============================================================================
# 错误处理测试
# =============================================================================

class TestConfigErrors:
    """配置错误处理测试"""

    def test_file_not_found(self):
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("./nonexistent_config.yaml")
        assert exc_info.value.code == ErrorCode.CONFIG_FILE_NOT_FOUND

    def test_invalid_format_value(self):
        user_yaml = """
reporting:
  default_format: xml
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(user_yaml)
            path = f.name
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_config(path)
            assert exc_info.value.code == ErrorCode.CONFIG_VALIDATION_ERROR
        finally:
            os.unlink(path)

    def test_invalid_log_level(self):
        user_yaml = """
logging:
  level: VERBOSE
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(user_yaml)
            path = f.name
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_config(path)
            assert exc_info.value.code == ErrorCode.CONFIG_VALIDATION_ERROR
        finally:
            os.unlink(path)

    def test_invalid_latency_unit(self):
        user_yaml = """
metrics:
  latency:
    unit: GHz
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(user_yaml)
            path = f.name
        try:
            with pytest.raises(ConfigurationError):
                load_config(path)
        finally:
            os.unlink(path)

    def test_invalid_iterations(self):
        user_yaml = """
benchmark:
  iterations: 0
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(user_yaml)
            path = f.name
        try:
            with pytest.raises(ConfigurationError):
                load_config(path)
        finally:
            os.unlink(path)


# =============================================================================
# 配置模型测试
# =============================================================================

class TestConfigModels:
    """配置模型测试"""

    def test_config_is_pydantic_model(self):
        config = Config()
        assert hasattr(config, "model_dump")

    def test_benchmark_config_defaults(self):
        bc = BenchmarkConfig()
        assert bc.iterations == 100
        assert bc.warmup == 5
        assert bc.parallel is False

    def test_reporting_config_defaults(self):
        rc = ReportingConfig()
        assert rc.default_format == "json"

    def test_logging_config_defaults(self):
        lc = LoggingConfig()
        assert lc.level == "INFO"

    def test_metrics_config_defaults(self):
        mc = MetricsConfig()
        assert mc.latency.unit == "ns"
        assert mc.throughput.window_size == 100
