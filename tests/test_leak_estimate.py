"""Acceptance invariants for _estimate_monthly_leak (cia-diagnose).

Ported from 02-fixes/leak_test_battery.py (handoff 2026-06-05). These are
INVARIANTS, not brittle magic numbers — they pin the behaviour that broke the
demo: $0 leaks, en-dash dropdown values diverging from hyphen ones, ranges
taking the floor instead of the midpoint, and absurd pre-revenue figures.

Reference values were measured at leak_score=70 (post-fix) and kept inline.
"""
import pytest

from cia_diagnose.domain.diagnosis.service import _estimate_monthly_leak

SCORE = 70.0  # weak/critical health → meaningful leak


def leak(rev: str) -> tuple[int, int]:
    return _estimate_monthly_leak({"revenue_range": rev}, SCORE)


def mid(rev: str) -> float:
    lo, hi = leak(rev)
    return (lo + hi) / 2.0


# Bands exercised by the battery, with their post-fix reference ($/mo).
ALL_BANDS = [
    "0-200k",                    # ref 3017-3167  (was $0 — the demo-killer)
    "200k-1m",                   # ref 9050-9500
    "USD 200k – 1M",        # en-dash; MUST equal 200k-1m
    "Menos de USD 50k",          # ref 754-792
    "USD 50k – 200k",       # ref 1885-1979  (midpoint, not floor)
    "pre-ingresos / validando",  # ref 1508-1583  (was ~$15k absurd)
    "$1.2m",                     # ref 18100-19000
    "500000",                    # ref 7542-7917
]


# INV1 — a weak score must NEVER read $0 (self-contradiction on the demo).
@pytest.mark.parametrize("rev", ALL_BANDS)
def test_inv1_never_zero(rev):
    lo, hi = leak(rev)
    assert hi > 0, f"$0 leak for {rev!r}"
    assert lo > 0, f"$0 lower bound for {rev!r}"
    assert lo <= hi


# INV2 — dash-invariance: hyphen and en-dash dropdown values must match.
def test_inv2_dash_invariance():
    assert leak("200k-1m") == leak("USD 200k – 1M")
    # em-dash and minus sign too, for good measure.
    assert leak("200k-1m") == leak("USD 200k — 1M")
    assert leak("200k-1m") == leak("USD 200k − 1M")


# INV3 — monotonic by band: bigger revenue band → bigger leak.
def test_inv3_monotonic_by_band():
    order = ["Menos de USD 50k", "USD 50k – 200k", "200k-1m", "$1.2m"]
    mids = [mid(b) for b in order]
    assert mids == sorted(mids), f"not monotonic across bands -> {mids}"


# INV4 — pre-revenue is bounded & credible (< $3000/mo), not an absurd default.
def test_inv4_pre_revenue_bounded():
    _, hi = leak("pre-ingresos / validando")
    assert hi < 3000, f"pre-revenue leak not credible (>= $3000/mo): {hi}"


# INV5 — two-sided ranges use the midpoint, not the lower bound (floor).
def test_inv5_range_uses_midpoint():
    assert mid("USD 50k – 200k") > mid("Menos de USD 50k")
    # "50k-200k" midpoint is 125k → strictly above the 50k-anchored band.


# Spot-check the post-fix reference values so an accidental formula change is caught.
@pytest.mark.parametrize(
    "rev,expected",
    [
        ("0-200k", (3017, 3167)),
        ("200k-1m", (9050, 9500)),
        ("USD 50k – 200k", (1885, 1979)),
        ("pre-ingresos / validando", (1508, 1583)),
        ("$1.2m", (18100, 19000)),
        ("500000", (7542, 7917)),
    ],
)
def test_reference_values(rev, expected):
    assert leak(rev) == expected
