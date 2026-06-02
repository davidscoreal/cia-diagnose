#!/usr/bin/env python3
"""Aggregate diagnoses into ANONYMIZED trend data — the foundation for CIA's
own research papers (target: first dataset after a semester / year).

Reads the append-only JSONL written by the lead webhook's vault sink
(CIA_VAULT_LEAD_LOG). Each line is one diagnosis intake. This script:
  - strips ALL PII (company_name, contact_*, ip, session_id) → research-safe,
  - aggregates by industry (icp_id), niche, and per-dimension health,
  - reports distributions and simple time trends (by created_at month),
  - emits CSV/JSON for further analysis (pandas, notebooks, NotebookLM).

It NEVER phones home and NEVER writes PII. Run it where the vault log lives.

Usage:
  python scripts/trends.py --log /path/to/leads.jsonl --out trends.json
  python scripts/trends.py --log leads.jsonl --format csv > trends.csv
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict

# Fields that must NEVER appear in research output.
_PII = {"company_name", "contact_name", "contact_email", "email", "contact",
        "ip_address", "session_id"}


def _iter_records(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _month(ts: str) -> str:
    # created_at like "2026-06-02T..." → "2026-06"
    return (ts or "")[:7] or "unknown"


def aggregate(path: str) -> dict:
    by_industry = defaultdict(int)
    by_niche = defaultdict(int)
    by_month = defaultdict(int)
    health_by_industry = defaultdict(list)
    dim_health = defaultdict(list)        # dimension -> [scores]
    pains = defaultdict(int)              # pain phrase -> count
    total = 0

    for rec in _iter_records(path):
        if rec.get("action") != "diagnose":
            continue
        total += 1
        icp = rec.get("icp_id") or "generic"
        by_industry[icp] += 1
        niche = (rec.get("niche") or "").strip().lower()
        if niche:
            by_niche[niche] += 1
        by_month[_month(rec.get("created_at"))] += 1

        health = rec.get("health_score")
        if health is None:
            health = rec.get("revenue_leak_score")
        if isinstance(health, (int, float)):
            health_by_industry[icp].append(float(health))

        diag = rec.get("diagnosis") or {}
        for d in diag.get("dimensions", []):
            if isinstance(d.get("score"), (int, float)):
                dim_health[d.get("dimension")].append(float(d["score"]))

        for p in rec.get("pain_points", []) or []:
            pains[str(p).strip().lower()] += 1

    def _stats(xs):
        xs = [x for x in xs if isinstance(x, (int, float))]
        if not xs:
            return None
        return {
            "n": len(xs),
            "mean": round(statistics.mean(xs), 1),
            "median": round(statistics.median(xs), 1),
            "min": round(min(xs), 1),
            "max": round(max(xs), 1),
        }

    return {
        "total_diagnoses": total,
        "by_industry": dict(sorted(by_industry.items(), key=lambda x: -x[1])),
        "by_niche": dict(sorted(by_niche.items(), key=lambda x: -x[1])[:50]),
        "by_month": dict(sorted(by_month.items())),
        "health_by_industry": {k: _stats(v) for k, v in health_by_industry.items()},
        "weakest_dimensions": dict(sorted(
            ((dim, round(statistics.mean(v), 1)) for dim, v in dim_health.items() if v),
            key=lambda x: x[1],  # lowest health (biggest opportunity) first
        )),
        "top_pains": dict(sorted(pains.items(), key=lambda x: -x[1])[:25]),
        "_note": "Anonymized aggregate — no PII. Source: CIA diagnosis vault log.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="Path to the vault JSONL log")
    ap.add_argument("--out", default=None, help="Write JSON here (default: stdout)")
    ap.add_argument("--format", choices=["json", "csv"], default="json")
    args = ap.parse_args()

    data = aggregate(args.log)

    if args.format == "csv":
        import csv
        import io
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["industry", "diagnoses", "health_mean", "health_median", "n"])
        hbi = data["health_by_industry"]
        for icp, count in data["by_industry"].items():
            s = hbi.get(icp) or {}
            w.writerow([icp, count, s.get("mean", ""), s.get("median", ""), s.get("n", "")])
        out = buf.getvalue()
    else:
        out = json.dumps(data, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"wrote {args.out} ({data['total_diagnoses']} diagnoses)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
