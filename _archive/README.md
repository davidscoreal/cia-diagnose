# _archive/

Orphaned v0.1 files preserved for data mining. These contain valuable
business logic (ICP pain language, objection handling, CLOSER framework,
value ladder pricing, toolstack comparisons) but are NOT wired to v0.2.

## domain_v1/
- icps.py — 7 ICP dataclasses with pain language, vacation pitches, pricing (~400 lines)
- scoring.py — v0.1 ScoreBreakdown (fit_score + revenue_leak_score)
- questions.py — Fixed 7-question bank (REJECTED by David: each user is 99% unique)
- closer.py — CLOSER pre-qualification (C, L, O stages)
- value_ladder.py — Sandwich pricing with 3 tiers
- objections.py — 9 A.A.A. objection responses (self-contained, reusable)
- toolstack.py — 10 tool categories with triple option (~500 lines)
- toolstack_compare.py — Comparison table builder

## Other
- server_v1_backup.py — Old 6-tool server
- renderer.py — Jinja2 report renderer (v0.1 schema, broken for v0.2)
- test_domain.py — v0.1 domain tests
- test_e2e.py — v0.1 end-to-end tests
- PLAN.md — v0.1 implementation plan
- INVESTOR-PITCH-BRIEF.md — Investor pitch (being done in another chat)
