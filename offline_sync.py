"""Offline cache and sync queue. Caches /me user; queue for future layout sync."""
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional


def _db_path() -> Path:
    base = Path(os.environ.get("OPS_MONITOR_DATA", os.path.expanduser("~/.ops_monitor")))
    base.mkdir(parents=True, exist_ok=True)
    return base / "offline.db"


def _get_conn() -> sqlite3.Connection:
    p = _db_path()
    conn = sqlite3.connect(str(p))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache_user (id INTEGER PRIMARY KEY, data TEXT)"
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            payload TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )"""
    )
    conn.commit()
    return conn


def get_cached_user() -> Optional[dict]:
    """Return cached /me user or None."""
    try:
        conn = _get_conn()
        row = conn.execute("SELECT data FROM cache_user WHERE id = 1").fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def set_cached_user(user: dict) -> None:
    """Store /me response for offline use."""
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO cache_user (id, data) VALUES (1, ?)",
            (json.dumps(user, default=str),),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def push_sync(action: str, payload: Optional[dict] = None) -> None:
    """Add a pending sync action (e.g. 'layout_save', payload)."""
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO sync_queue (action, payload) VALUES (?, ?)",
            (action, json.dumps(payload or {}, default=str)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_pending_sync_count() -> int:
    try:
        conn = _get_conn()
        n = conn.execute("SELECT COUNT(*) FROM sync_queue").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return 0


def clear_sync_queue() -> None:
    """Clear queue after successful sync (or discard)."""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM sync_queue")
        conn.commit()
        conn.close()
    except Exception:
        pass


def clear_cache() -> None:
    """Clear cached user (on logout)."""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM cache_user")
        conn.execute("DELETE FROM sync_queue")
        conn.commit()
        conn.close()
    except Exception:
        pass
