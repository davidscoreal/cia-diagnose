"""Pytest configuration for cia-diagnose tests."""
import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "asyncio: async test")
