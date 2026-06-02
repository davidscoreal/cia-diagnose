#!/usr/bin/env python3
"""Weekly refresh of the CIA curated tool registry (the "best of the best").

PROCESS (run weekly — cron or manual):
  1. For each area (and key industries), research the current top free/OSS/paid
     tools: GitHub stars/activity, recent releases, real CIA implementation wins,
     pricing changes, deprecations.
  2. Update src/cia_diagnose/tools_registry/areas.yaml and
     by_industry/<icp>.yaml — add winners, drop stale entries, refresh `why_best`
     and bump `last_reviewed`.
  3. Commit with a dated message so changes are auditable.

This script is a SCAFFOLD: it validates the registry and reports entries whose
`last_reviewed` is older than the cadence, so a human (or an LLM agent with
WebSearch) knows what to refresh. It does NOT auto-edit picks — curation stays
human-reviewed on purpose (that's what makes it "best of the best", not "most
popular").

Usage:
  python scripts/refresh_tools.py --stale-days 7
"""
from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path

import yaml

REG = Path(__file__).resolve().parent.parent / "src" / "cia_diagnose" / "tools_registry"


def _load(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=7)
    ap.add_argument("--today", default=None, help="YYYY-MM-DD (default: file mtime won't be used)")
    args = ap.parse_args()

    today = _dt.date.fromisoformat(args.today) if args.today else None
    files = [REG / "areas.yaml", *sorted((REG / "by_industry").glob("*.yaml"))]
    problems, stale = [], []
    total_tools = 0

    for f in files:
        data = _load(f)
        areas = data.get("areas", {})
        for area, tools in areas.items():
            for t in tools:
                total_tools += 1
                for req in ("name", "tier", "url"):
                    if not t.get(req):
                        problems.append(f"{f.name}:{area}: missing {req} -> {t}")
                if t.get("tier") not in ("free", "oss", "paid"):
                    problems.append(f"{f.name}:{area}: bad tier {t.get('tier')} -> {t.get('name')}")
        lr = (data.get("meta") or {}).get("last_reviewed")
        if today and lr:
            age = (today - _dt.date.fromisoformat(lr)).days
            if age > args.stale_days:
                stale.append(f"{f.name}: last_reviewed {lr} ({age}d old) — needs refresh")

    print(f"registry files: {len(files)} · tools: {total_tools}")
    if problems:
        print("\nPROBLEMS:")
        print("\n".join(problems))
    if stale:
        print("\nSTALE (refresh these):")
        print("\n".join(stale))
    if not problems and not stale:
        print("OK — registry valid and fresh.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
