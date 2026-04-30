"""YAML benchmark loader for ICP-specific diagnosis.

Add an industry = add a YAML file. No code changes.
Each YAML defines dimension weights, signals, defaults, and findings
for one ICP.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("univercity-mcp.benchmarks")

_BENCHMARKS_DIR = Path(__file__).parent / "benchmarks"
_cache: dict[str, dict[str, Any]] = {}


def load_benchmark(icp_id: str) -> dict[str, Any]:
    """Load a benchmark YAML by ICP id. Falls back to 'generic'."""
    if icp_id in _cache:
        return _cache[icp_id]

    path = _BENCHMARKS_DIR / f"{icp_id}.yaml"
    if not path.exists():
        logger.warning("No benchmark for ICP '%s', falling back to generic", icp_id)
        path = _BENCHMARKS_DIR / "generic.yaml"

    if not path.exists():
        logger.error("Generic benchmark not found at %s", path)
        return _default_benchmark()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _cache[icp_id] = data
    return data


def list_available_icps() -> list[dict[str, str]]:
    """List all available ICP benchmarks."""
    result = []
    for path in sorted(_BENCHMARKS_DIR.glob("*.yaml")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            result.append({
                "id": data.get("id", path.stem),
                "name_es": data.get("name_es", path.stem),
                "name_en": data.get("name_en", path.stem),
                "tier": data.get("tier", 2),
            })
        except Exception as e:
            logger.warning("Failed to read benchmark %s: %s", path, e)
    return result


def get_dimension_config(benchmark: dict[str, Any], dimension: str) -> dict[str, Any]:
    """Get configuration for a specific dimension from a benchmark."""
    dims = benchmark.get("dimensions", {})
    return dims.get(dimension, {})


def _default_benchmark() -> dict[str, Any]:
    """Fallback benchmark if no YAML files exist at all."""
    return {
        "id": "generic",
        "name_es": "General",
        "name_en": "General",
        "tier": 2,
        "dimensions": {
            dim: {"weight": 0.125, "defaults": {"base_score": 50}, "findings": {}}
            for dim in [
                "digital", "operations", "supply_chain", "talent",
                "financial", "leadership", "market", "regulatory",
            ]
        },
    }


def clear_cache():
    """Clear the benchmark cache (for testing)."""
    _cache.clear()
