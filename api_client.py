"""API client for OPS Monitor backend. Handles token, 401, refresh."""
import requests
from typing import Any, Optional

from auth_store import load_tokens, save_tokens, clear_tokens


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")


class NotAuthenticatedError(APIError):
    pass


def _base_url(config) -> str:
    url = getattr(config, "api_base_url", None) or "https://opsmonitor-alpha.vercel.app"
    return url.rstrip("/")


def _get_token(config) -> Optional[str]:
    tokens = load_tokens()
    return tokens.get("access_token") or None


def _refresh_token(config) -> bool:
    """Refresh access token using refresh_token. Returns True if new token saved."""
    tokens = load_tokens()
    ref = tokens.get("refresh_token")
    if not ref:
        return False
    base = _base_url(config)
    try:
        r = requests.post(
            f"{base}/auth/refresh",
            json={"refresh_token": ref},
            timeout=10,
        )
        if r.status_code != 200:
            clear_tokens()
            return False
        data = r.json()
        save_tokens(data["access_token"], data.get("refresh_token", ref))
        return True
    except Exception:
        clear_tokens()
        return False


def request(
    config,
    method: str,
    path: str,
    *,
    json: Optional[dict] = None,
    require_auth: bool = True,
) -> dict:
    """
    Call API. path should start with / e.g. /me, /auth/login.
    On 401 if require_auth: tries refresh once, then raises NotAuthenticatedError.
    """
    base = _base_url(config)
    url = f"{base}{path}"
    headers = {}
    if require_auth:
        token = _get_token(config)
        if not token:
            raise NotAuthenticatedError(401, "Ikke innlogget")
        headers["Authorization"] = f"Bearer {token}"

    r = requests.request(method, url, headers=headers, json=json, timeout=15)
    if r.status_code == 401 and require_auth:
        if _refresh_token(config):
            return request(config, method, path, json=json, require_auth=True)
        clear_tokens()
        raise NotAuthenticatedError(401, "Sesjon utløpt – logg inn på nytt")
    if r.status_code >= 400:
        detail = "Ukjent feil"
        try:
            d = r.json()
            detail = d.get("detail", detail)
            if isinstance(detail, list):
                detail = detail[0].get("msg", str(detail))
        except Exception:
            detail = r.text or detail
        raise APIError(r.status_code, detail)
    if r.status_code == 204 or not r.content:
        return {}
    return r.json()


def login(config, email: str, password: str) -> dict:
    """Login and store tokens. Returns /me-style user info."""
    data = request(
        config,
        "POST",
        "/auth/login",
        json={"email": email, "password": password},
        require_auth=False,
    )
    save_tokens(data["access_token"], data["refresh_token"])
    return request(config, "GET", "/me")


def register(config, org_name: str, email: str, password: str) -> dict:
    """Register org + admin user and store tokens. Returns /me-style user info."""
    data = request(
        config,
        "POST",
        "/auth/register",
        json={"org_name": org_name, "email": email, "password": password},
        require_auth=False,
    )
    save_tokens(data["access_token"], data["refresh_token"])
    return request(config, "GET", "/me")


def get_me(config) -> Optional[dict]:
    """Fetch current user. Returns None if not logged in or token invalid."""
    try:
        return request(config, "GET", "/me")
    except NotAuthenticatedError:
        return None
    except Exception:
        return None


def list_users(config) -> list:
    """List users in current org (admin only)."""
    return request(config, "GET", "/users")


def create_user(config, email: str, password: str, role: str = "user") -> dict:
    """Create user in current org (admin only)."""
    return request(config, "POST", "/users", json={"email": email, "password": password, "role": role})


def delete_user(config, user_id: int) -> None:
    """Delete user (admin only)."""
    request(config, "DELETE", f"/users/{user_id}")


def list_layouts(config) -> list[dict]:
    """List layouts stored for the current organization."""
    return request(config, "GET", "/layouts")


def create_layout_remote(config, layout_cfg: dict) -> dict:
    """Create a remote layout entry for current org."""
    name = layout_cfg.get("title") or "Dashboard"
    payload = {
        "name": name,
        "config": layout_cfg,
    }
    return request(config, "POST", "/layouts", json=payload)


def update_layout_remote(config, layout_id: int, layout_cfg: dict) -> dict:
    """Update a remote layout entry."""
    name = layout_cfg.get("title") or "Dashboard"
    payload = {
        "name": name,
        "config": layout_cfg,
    }
    return request(config, "PUT", f"/layouts/{layout_id}", json=payload)


def logout() -> None:
    clear_tokens()
    try:
        from offline_sync import clear_cache
        clear_cache()
    except Exception:
        pass
