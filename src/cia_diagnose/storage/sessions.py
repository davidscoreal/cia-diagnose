"""SQLite session storage for audit sessions.

Summit-ready: aiosqlite for v0.1, PostgreSQL post-Summit.
Each session tracks: user info, ICP, answers, scores, status.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import aiosqlite


class SessionStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    SCORED = "scored"
    REPORTED = "reported"
    BOOKED = "booked"
    SHARED = "shared"


@dataclass
class Session:
    """An audit session with all its data."""
    id: str
    created_at: str
    updated_at: str
    status: SessionStatus

    # User info
    company_name: str = ""
    contact_name: str = ""
    contact_email: str = ""
    industry_hint: str = ""

    # ICP detection
    icp_id: str = "generic"

    # Answers: question_id → answer value
    answers: dict[str, Any] = field(default_factory=dict)

    # Current question index
    current_question: int = 0

    # Scores (populated after all questions answered)
    revenue_leak_score: float | None = None
    fit_score: float | None = None
    score_breakdown: dict | None = None

    # Value ladder (populated after scoring)
    value_ladder: dict | None = None

    # Closer output
    closer: dict | None = None

    # Tool comparison
    tool_comparison: dict | None = None

    # Report
    report_path: str | None = None
    report_shared: bool = False

    # Rate limiting
    ip_address: str = ""

    # Language
    lang: str = "es"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "industry_hint": self.industry_hint,
            "icp_id": self.icp_id,
            "answers": self.answers,
            "current_question": self.current_question,
            "revenue_leak_score": self.revenue_leak_score,
            "fit_score": self.fit_score,
            "lang": self.lang,
        }


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'started',
    company_name TEXT DEFAULT '',
    contact_name TEXT DEFAULT '',
    contact_email TEXT DEFAULT '',
    industry_hint TEXT DEFAULT '',
    icp_id TEXT DEFAULT 'generic',
    answers TEXT DEFAULT '{}',
    current_question INTEGER DEFAULT 0,
    revenue_leak_score REAL,
    fit_score REAL,
    score_breakdown TEXT,
    value_ladder TEXT,
    closer TEXT,
    tool_comparison TEXT,
    report_path TEXT,
    report_shared INTEGER DEFAULT 0,
    ip_address TEXT DEFAULT '',
    lang TEXT DEFAULT 'es'
);

CREATE INDEX IF NOT EXISTS idx_sessions_ip ON sessions(ip_address);
CREATE INDEX IF NOT EXISTS idx_sessions_email ON sessions(contact_email);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

CREATE TABLE IF NOT EXISTS rate_limits (
    ip_address TEXT NOT NULL,
    date TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (ip_address, date)
);
"""


class SessionStore:
    """Async SQLite session store."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Create tables if needed. Idempotent — safe to call from both the MCP
        server lifespan and standalone HTTP custom routes (which don't share the
        MCP per-session lifespan)."""
        if self._db is not None:
            return
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def create_session(
        self,
        company_name: str = "",
        contact_name: str = "",
        contact_email: str = "",
        industry_hint: str = "",
        ip_address: str = "",
        lang: str = "es",
    ) -> Session:
        """Create a new audit session."""
        now = datetime.now(timezone.utc).isoformat()
        session = Session(
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            status=SessionStatus.STARTED,
            company_name=company_name,
            contact_name=contact_name,
            contact_email=contact_email,
            industry_hint=industry_hint,
            ip_address=ip_address,
            lang=lang,
        )

        assert self._db is not None
        await self._db.execute(
            """INSERT INTO sessions
               (id, created_at, updated_at, status, company_name, contact_name,
                contact_email, industry_hint, ip_address, lang)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session.id, now, now, session.status.value,
             company_name, contact_name, contact_email,
             industry_hint, ip_address, lang),
        )
        await self._db.commit()
        return session

    async def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_session(row)

    async def update_session(self, session: Session) -> None:
        """Persist session state back to DB."""
        assert self._db is not None
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """UPDATE sessions SET
                updated_at = ?,
                status = ?,
                company_name = ?,
                contact_name = ?,
                contact_email = ?,
                industry_hint = ?,
                icp_id = ?,
                answers = ?,
                current_question = ?,
                revenue_leak_score = ?,
                fit_score = ?,
                score_breakdown = ?,
                value_ladder = ?,
                closer = ?,
                tool_comparison = ?,
                report_path = ?,
                report_shared = ?,
                lang = ?
               WHERE id = ?""",
            (now, session.status.value,
             session.company_name, session.contact_name,
             session.contact_email, session.industry_hint,
             session.icp_id,
             json.dumps(session.answers),
             session.current_question,
             session.revenue_leak_score, session.fit_score,
             json.dumps(session.score_breakdown) if session.score_breakdown else None,
             json.dumps(session.value_ladder) if session.value_ladder else None,
             json.dumps(session.closer) if session.closer else None,
             json.dumps(session.tool_comparison) if session.tool_comparison else None,
             session.report_path,
             1 if session.report_shared else 0,
             session.lang,
             session.id),
        )
        await self._db.commit()

    async def check_rate_limit(self, ip_address: str, limit: int) -> bool:
        """Check if IP is within rate limit for today. Returns True if allowed."""
        assert self._db is not None
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = await self._db.execute(
            "SELECT count FROM rate_limits WHERE ip_address = ? AND date = ?",
            (ip_address, today),
        )
        row = await cursor.fetchone()
        if not row:
            return True
        return row["count"] < limit

    async def increment_rate_limit(self, ip_address: str) -> None:
        """Increment rate limit counter for today."""
        assert self._db is not None
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        await self._db.execute(
            """INSERT INTO rate_limits (ip_address, date, count)
               VALUES (?, ?, 1)
               ON CONFLICT (ip_address, date)
               DO UPDATE SET count = count + 1""",
            (ip_address, today),
        )
        await self._db.commit()

    async def count_sessions_today(self, ip_address: str) -> int:
        """Count sessions created today by this IP."""
        assert self._db is not None
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = await self._db.execute(
            "SELECT COUNT(*) as cnt FROM sessions WHERE ip_address = ? AND created_at LIKE ?",
            (ip_address, f"{today}%"),
        )
        row = await cursor.fetchone()
        return row["cnt"] if row else 0

    def _row_to_session(self, row: aiosqlite.Row) -> Session:
        """Convert a DB row to a Session object."""
        return Session(
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=SessionStatus(row["status"]),
            company_name=row["company_name"] or "",
            contact_name=row["contact_name"] or "",
            contact_email=row["contact_email"] or "",
            industry_hint=row["industry_hint"] or "",
            icp_id=row["icp_id"] or "generic",
            answers=json.loads(row["answers"]) if row["answers"] else {},
            current_question=row["current_question"] or 0,
            revenue_leak_score=row["revenue_leak_score"],
            fit_score=row["fit_score"],
            score_breakdown=json.loads(row["score_breakdown"]) if row["score_breakdown"] else None,
            value_ladder=json.loads(row["value_ladder"]) if row["value_ladder"] else None,
            closer=json.loads(row["closer"]) if row["closer"] else None,
            tool_comparison=json.loads(row["tool_comparison"]) if row["tool_comparison"] else None,
            report_path=row["report_path"],
            report_shared=bool(row["report_shared"]),
            ip_address=row["ip_address"] or "",
            lang=row["lang"] or "es",
        )
