"""CIA curated tool registry — best-of-the-best per area, with per-industry overrides.

Source of truth for tools_recommend and the Triple Option OSS/paid options.
YAML-driven: `areas.yaml` holds defaults; `by_industry/<icp>.yaml` overrides an
area for a specific ICP. Refreshed weekly (see TOOLS_REGISTRY.md).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("cia-diagnose.tools_registry")

_DIR = Path(__file__).resolve().parent
_cache: dict[str, dict[str, Any]] = {}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _areas_default() -> dict[str, Any]:
    if "areas" not in _cache:
        _cache["areas"] = _load_yaml(_DIR / "areas.yaml").get("areas", {})
    return _cache["areas"]


def _industry_overrides(icp_id: str) -> dict[str, Any]:
    key = f"icp:{icp_id}"
    if key not in _cache:
        _cache[key] = _load_yaml(_DIR / "by_industry" / f"{icp_id}.yaml").get("areas", {})
    return _cache[key]


def list_areas() -> list[str]:
    return list(_areas_default().keys())


def tools_for(area: str, icp_id: str = "", lang: str = "es") -> list[dict[str, str]]:
    """Return the curated tools for an area, applying an ICP override if present."""
    area = (area or "").lower().strip()
    overrides = _industry_overrides(icp_id) if icp_id else {}
    entries = overrides.get(area) or _areas_default().get(area) or []
    out = []
    for t in entries:
        out.append({
            "name": t.get("name", ""),
            "tier": t.get("tier", "oss"),
            "url": t.get("url", ""),
            "description": t.get(f"desc_{lang}") or t.get("desc_es", ""),
            "why_best": t.get(f"why_best_{lang}") or t.get("why_best_es", ""),
        })
    return out


def best_pick(area: str, tier: str, icp_id: str = "", lang: str = "es") -> dict[str, str] | None:
    """First curated tool in an area matching a tier (free/oss/paid)."""
    for t in tools_for(area, icp_id, lang):
        if t["tier"] == tier:
            return t
    return None


def clear_cache() -> None:
    _cache.clear()
