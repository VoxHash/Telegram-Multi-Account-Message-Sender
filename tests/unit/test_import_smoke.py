"""
Import smoke tests: package-level and submodule imports must not circular-fail.
"""

import importlib


class TestCoreImportSmoke:
    def test_spintax_submodule_import(self):
        mod = importlib.import_module("app.core.spintax")
        assert hasattr(mod, "SpintaxProcessor")
        processor = mod.SpintaxProcessor(seed=1)
        result = processor.process("Hi {a|b}")
        assert result.text in {"Hi a", "Hi b"}

    def test_throttler_submodule_import(self):
        mod = importlib.import_module("app.core.throttler")
        assert hasattr(mod, "Throttler")
        assert hasattr(mod, "RateLimiter")

    def test_native_accel_submodule_import(self):
        mod = importlib.import_module("app.core.native_accel")
        status = mod.native_status()
        assert "backend" in status

    def test_core_package_lazy_export(self):
        core = importlib.import_module("app.core")
        # Trigger lazy __getattr__ without loading telethon/engine first via submodule.
        SpintaxProcessor = core.SpintaxProcessor
        assert SpintaxProcessor is not None
        assert SpintaxProcessor(seed=7).process("x").text == "x"

    def test_plugin_exports_without_engine(self):
        from app.core.plugin import MessageFilterPlugin, PluginType

        assert PluginType.FILTER.value == "filter"
        assert MessageFilterPlugin is not None


class TestServicesImportSmoke:
    def test_settings_import(self):
        from app.services.settings import Settings, get_settings

        assert get_settings() is not None
        assert Settings is not None

    def test_logger_import(self):
        from app.services.logger import get_logger

        logger = get_logger()
        assert logger is not None

    def test_services_package_lazy_settings(self):
        services = importlib.import_module("app.services")
        settings = services.get_settings()
        assert settings.app_name
