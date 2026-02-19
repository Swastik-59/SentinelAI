"""
SentinelAI — Enterprise Database Layer

Manages all database operations for:
- Audit logs
- Investigation cases & case notes
- Corporate client risk profiles
- Analytics aggregation queries

Uses async SQLite via aiosqlite.
"""

import aiosqlite
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentinel.db")


# ── Initialisation ─────────────────────────────────────────────────────────

async def init_db():
    """Create all tables on startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT    NOT NULL,
                input_type      TEXT    NOT NULL,
                input_hash      TEXT,
                ai_probability  REAL,
                fraud_risk_score REAL,
                risk_level      TEXT,
                result_json     TEXT,
                flagged         INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id                TEXT PRIMARY KEY,
                content_hash      TEXT,
                risk_score        REAL NOT NULL DEFAULT 0.0,
                ai_probability    REAL NOT NULL DEFAULT 0.0,
                fraud_probability REAL NOT NULL DEFAULT 0.0,
                risk_level        TEXT NOT NULL DEFAULT 'LOW',
                status            TEXT NOT NULL DEFAULT 'OPEN',
                assigned_to       TEXT,
                escalation_reason TEXT,
                client_id         TEXT,
                result_json       TEXT,
                created_at        TEXT NOT NULL,
                updated_at        TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS case_notes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id   TEXT NOT NULL,
                author    TEXT NOT NULL,
                note      TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id                  TEXT PRIMARY KEY,
                name                TEXT NOT NULL UNIQUE,
                industry            TEXT,
                contact_email       TEXT,
                total_cases         INTEGER DEFAULT 0,
                open_cases          INTEGER DEFAULT 0,
                avg_risk_score      REAL    DEFAULT 0.0,
                last_incident_date  TEXT,
                created_at          TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                username      TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT 'analyst',
                full_name     TEXT,
                created_at    TEXT NOT NULL
            )
        """)
        await db.commit()


# ── Audit Logs ─────────────────────────────────────────────────────────────

async def insert_audit_log(
    input_type: str,
    input_hash: str,
    ai_probability: float,
    fraud_risk_score: float,
    risk_level: str,
    result: dict,
):
    async with aiosqlite.connect(DB_PATH) as db:
        flagged = 1 if risk_level in ("HIGH", "CRITICAL") else 0
        await db.execute(
            """INSERT INTO audit_logs
                (timestamp, input_type, input_hash, ai_probability,
                 fraud_risk_score, risk_level, result_json, flagged)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.utcnow().isoformat(), input_type, input_hash,
             ai_probability, fraud_risk_score, risk_level,
             json.dumps(result), flagged),
        )
        await db.commit()


async def get_audit_logs(
    limit: int = 50, offset: int = 0,
    flagged_only: bool = False, input_type: Optional[str] = None,
):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: list = []
        if flagged_only:
            query += " AND flagged = 1"
        if input_type:
            query += " AND input_type = ?"
            params.append(input_type)
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "input_type": row["input_type"],
                "ai_probability": row["ai_probability"],
                "fraud_risk_score": row["fraud_risk_score"],
                "risk_level": row["risk_level"],
                "result": json.loads(row["result_json"]) if row["result_json"] else {},
                "flagged": bool(row["flagged"]),
            }
            for row in rows
        ]


async def delete_audit_log(log_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM audit_logs WHERE id = ?", (log_id,))
        await db.commit()
        return cursor.rowcount > 0


# ── Users ──────────────────────────────────────────────────────────────────

async def create_user(username: str, password_hash: str, role: str, full_name: str = "") -> str:
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (id, username, password_hash, role, full_name, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, username, password_hash, role, full_name, now),
        )
        await db.commit()
    return user_id


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"], "username": row["username"],
            "password_hash": row["password_hash"], "role": row["role"],
            "full_name": row["full_name"], "created_at": row["created_at"],
        }


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"], "username": row["username"],
            "password_hash": row["password_hash"], "role": row["role"],
            "full_name": row["full_name"], "created_at": row["created_at"],
        }


# ── Cases ──────────────────────────────────────────────────────────────────

async def create_case(
    content_hash: str, risk_score: float, ai_probability: float,
    fraud_probability: float, risk_level: str, status: str = "OPEN",
    escalation_reason: Optional[str] = None, client_id: Optional[str] = None,
    result: Optional[dict] = None,
) -> str:
    case_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO cases
                (id, content_hash, risk_score, ai_probability, fraud_probability,
                 risk_level, status, escalation_reason, client_id, result_json,
                 created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (case_id, content_hash, risk_score, ai_probability,
             fraud_probability, risk_level, status, escalation_reason,
             client_id, json.dumps(result) if result else None, now, now),
        )
        await db.commit()
    if client_id:
        await _update_client_stats(client_id)
    return case_id


async def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        row = await cursor.fetchone()
        return _row_to_case(row) if row else None


async def get_cases(
    limit: int = 50, offset: int = 0,
    status: Optional[str] = None, risk_level: Optional[str] = None,
    client_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM cases WHERE 1=1"
        params: list = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [_row_to_case(row) for row in rows]


async def update_case_status(case_id: str, status: str, assigned_to: Optional[str] = None) -> bool:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        if assigned_to is not None:
            cursor = await db.execute(
                "UPDATE cases SET status=?, assigned_to=?, updated_at=? WHERE id=?",
                (status, assigned_to, now, case_id),
            )
        else:
            cursor = await db.execute(
                "UPDATE cases SET status=?, updated_at=? WHERE id=?",
                (status, now, case_id),
            )
        await db.commit()
        return cursor.rowcount > 0


def _row_to_case(row) -> Dict[str, Any]:
    return {
        "id": row["id"], "content_hash": row["content_hash"],
        "risk_score": row["risk_score"], "ai_probability": row["ai_probability"],
        "fraud_probability": row["fraud_probability"], "risk_level": row["risk_level"],
        "status": row["status"], "assigned_to": row["assigned_to"],
        "escalation_reason": row["escalation_reason"], "client_id": row["client_id"],
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
        "created_at": row["created_at"], "updated_at": row["updated_at"],
    }


# ── Case Notes ─────────────────────────────────────────────────────────────

async def add_case_note(case_id: str, author: str, note: str) -> int:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO case_notes (case_id, author, note, timestamp) VALUES (?,?,?,?)",
            (case_id, author, note, now),
        )
        await db.commit()
        return cursor.lastrowid


async def get_case_notes(case_id: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM case_notes WHERE case_id = ? ORDER BY timestamp ASC", (case_id,),
        )
        rows = await cursor.fetchall()
        return [
            {"id": row["id"], "case_id": row["case_id"], "author": row["author"],
             "note": row["note"], "timestamp": row["timestamp"]}
            for row in rows
        ]


# ── Clients ────────────────────────────────────────────────────────────────

async def create_client(
    name: str, industry: Optional[str] = None, contact_email: Optional[str] = None,
) -> str:
    client_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO clients (id, name, industry, contact_email, created_at) VALUES (?,?,?,?,?)",
            (client_id, name, industry, contact_email, now),
        )
        await db.commit()
    return client_id


async def get_client(client_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = await cursor.fetchone()
        return _row_to_client(row) if row else None


async def get_clients(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM clients ORDER BY name ASC LIMIT ? OFFSET ?", (limit, offset),
        )
        rows = await cursor.fetchall()
        return [_row_to_client(row) for row in rows]


async def get_client_risk_summary(client_id: str) -> Dict[str, Any]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        client = await get_client(client_id)
        if not client:
            return {}
        cursor = await db.execute(
            "SELECT COUNT(*) as total, AVG(risk_score) as avg_risk FROM cases WHERE client_id=?",
            (client_id,),
        )
        stats = await cursor.fetchone()
        cursor = await db.execute(
            "SELECT risk_level, COUNT(*) as cnt FROM cases WHERE client_id=? GROUP BY risk_level",
            (client_id,),
        )
        risk_dist = {r["risk_level"]: r["cnt"] for r in await cursor.fetchall()}
        cursor = await db.execute(
            "SELECT status, COUNT(*) as cnt FROM cases WHERE client_id=? GROUP BY status",
            (client_id,),
        )
        status_dist = {r["status"]: r["cnt"] for r in await cursor.fetchall()}
        cursor = await db.execute(
            "SELECT * FROM cases WHERE client_id=? ORDER BY created_at DESC LIMIT 5",
            (client_id,),
        )
        recent = [_row_to_case(r) for r in await cursor.fetchall()]
        return {
            "client": client, "total_cases": stats["total"] or 0,
            "average_risk_score": round(stats["avg_risk"] or 0, 4),
            "risk_distribution": risk_dist, "status_distribution": status_dist,
            "recent_cases": recent,
        }


async def _update_client_stats(client_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as total, AVG(risk_score) as avg_risk, MAX(created_at) as last_date "
            "FROM cases WHERE client_id=?", (client_id,),
        )
        row = await cursor.fetchone()
        open_cursor = await db.execute(
            "SELECT COUNT(*) FROM cases WHERE client_id=? AND status IN ('OPEN','UNDER_REVIEW','ESCALATED')",
            (client_id,),
        )
        open_row = await open_cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE clients SET total_cases=?, open_cases=?, avg_risk_score=?, last_incident_date=? WHERE id=?",
                (row[0] or 0, open_row[0] if open_row else 0, round(row[1] or 0, 4), row[2], client_id),
            )
            await db.commit()


def _row_to_client(row) -> Dict[str, Any]:
    return {
        "id": row["id"], "name": row["name"],
        "industry": row["industry"], "contact_email": row["contact_email"],
        "total_cases": row["total_cases"], "open_cases": row["open_cases"],
        "avg_risk_score": row["avg_risk_score"],
        "created_at": row["created_at"],
    }


# ── Analytics ──────────────────────────────────────────────────────────────

async def get_analytics_overview(days: int = 30) -> Dict[str, Any]:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        total = (await (await db.execute(
            "SELECT COUNT(*) as cnt FROM audit_logs WHERE timestamp >= ?", (since,)
        )).fetchone())["cnt"]

        flagged = (await (await db.execute(
            "SELECT COUNT(*) as cnt FROM audit_logs WHERE timestamp >= ? AND flagged = 1", (since,)
        )).fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT DATE(timestamp) as day, COUNT(*) as cnt FROM audit_logs "
            "WHERE timestamp >= ? AND flagged = 1 GROUP BY DATE(timestamp) ORDER BY day ASC",
            (since,),
        )
        fraud_per_day = [{"date": r["day"], "count": r["cnt"]} for r in await cursor.fetchall()]

        ai_fraud_count = (await (await db.execute(
            "SELECT COUNT(*) as cnt FROM audit_logs "
            "WHERE timestamp >= ? AND flagged = 1 AND ai_probability > 0.5", (since,)
        )).fetchone())["cnt"]
        ai_fraud_pct = round((ai_fraud_count / flagged * 100) if flagged > 0 else 0, 1)

        cursor = await db.execute(
            "SELECT risk_level, COUNT(*) as cnt FROM audit_logs WHERE timestamp >= ? GROUP BY risk_level",
            (since,),
        )
        risk_breakdown = {r["risk_level"]: r["cnt"] for r in await cursor.fetchall()}

        cursor = await db.execute(
            "SELECT input_type, COUNT(*) as cnt FROM audit_logs WHERE timestamp >= ? GROUP BY input_type",
            (since,),
        )
        type_breakdown = {r["input_type"]: r["cnt"] for r in await cursor.fetchall()}

        total_cases = (await (await db.execute(
            "SELECT COUNT(*) as cnt FROM cases WHERE created_at >= ?", (since,)
        )).fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT status, COUNT(*) as cnt FROM cases WHERE created_at >= ? GROUP BY status",
            (since,),
        )
        case_status = {r["status"]: r["cnt"] for r in await cursor.fetchall()}

        avg_res_row = await (await db.execute(
            "SELECT AVG(julianday(updated_at) - julianday(created_at)) as avg_days "
            "FROM cases WHERE status = 'RESOLVED' AND created_at >= ?", (since,)
        )).fetchone()
        avg_resolution_hours = round((avg_res_row["avg_days"] or 0) * 24, 1)

        cursor = await db.execute(
            "SELECT result_json FROM audit_logs "
            "WHERE timestamp >= ? AND flagged = 1 AND result_json IS NOT NULL", (since,),
        )
        keyword_freq: Dict[str, int] = {}
        async for row in cursor:
            try:
                data = json.loads(row[0])
                signals = data.get("fraud_signals", {})
                for cat in ("urgency", "financial_redirection", "impersonation"):
                    for kw in signals.get(cat, {}).get("keywords", []):
                        keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
            except (json.JSONDecodeError, AttributeError):
                continue
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        total_escalated = (await (await db.execute(
            "SELECT COUNT(*) as cnt FROM cases WHERE status = 'ESCALATED' AND created_at >= ?", (since,)
        )).fetchone())["cnt"]

        return {
            "period_days": days, "total_analyses": total, "flagged_analyses": flagged,
            "fraud_per_day": fraud_per_day, "ai_fraud_percentage": ai_fraud_pct,
            "risk_breakdown": risk_breakdown, "type_breakdown": type_breakdown,
            "total_cases": total_cases, "total_escalated": total_escalated,
            "case_status": case_status,
            "avg_resolution_hours": avg_resolution_hours,
            "top_fraud_keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
        }
