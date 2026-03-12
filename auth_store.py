"""Secure storage of auth tokens. Uses app data dir (not project dir)."""
import json
import os
from pathlib import Path


def _auth_dir() -> Path:
    base = Path(os.environ.get("OPS_MONITOR_DATA", os.path.expanduser("~/.ops_monitor")))
    base.mkdir(parents=True, exist_ok=True)
    return base


def _token_path() -> Path:
    return _auth_dir() / "auth_token.json"


def load_tokens() -> dict:
    """Returns {} or { 'access_token': str, 'refresh_token': str }."""
    p = _token_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
        }
    except Exception:
        return {}


def save_tokens(access_token: str, refresh_token: str) -> None:
    p = _token_path()
    p.write_text(
        json.dumps({"access_token": access_token, "refresh_token": refresh_token}, indent=0),
        encoding="utf-8",
    )
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def clear_tokens() -> None:
    p = _token_path()
    if p.exists():
        p.unlink()
