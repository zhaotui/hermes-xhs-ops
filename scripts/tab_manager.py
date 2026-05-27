"""Tab lifecycle management for XHS browser sessions.

All tab operations go through this module. Rules live here, not scattered.
"""

from __future__ import annotations

import json
import os
import sys

# Import client.py from parent directory
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from client import _cmd

DATA_DIR = os.path.expanduser("~/.hermes/data/xhs-ops")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
DEFAULT_SESSION = "xhs"
DEFAULT_ACCOUNT = {
    "key": "default",
    "name": "默认账号",
    "session": DEFAULT_SESSION,
    "home_url": "https://creator.xiaohongshu.com/new/note-manager?source=official",
    "nickname": "",
}


def ensure_accounts_file() -> dict:
    """确保账号配置文件存在，返回配置。"""
    default_state = {"current": DEFAULT_ACCOUNT["key"], "accounts": [DEFAULT_ACCOUNT.copy()]}
    if not os.path.exists(ACCOUNTS_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_state, f, ensure_ascii=False, indent=2)
        return default_state
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_state, f, ensure_ascii=False, indent=2)
        return default_state


def current_session() -> str:
    """返回当前小红书账号对应的 WebBridge session。"""
    try:
        state = ensure_accounts_file()
        current = state.get("current")
        for account in state.get("accounts", []):
            if account.get("key") == current:
                session = account.get("session") or DEFAULT_SESSION
                if account.get("key") and session == f"xhs-{account.get('key')}":
                    return DEFAULT_SESSION
                return session
    except Exception:
        pass
    return DEFAULT_SESSION


def _resolve_session(session: str | None = None) -> str:
    return session or current_session()


def _navigate(url: str, session: str | None = None) -> dict:
    return _cmd("navigate", {"url": url}, session=_resolve_session(session))


def list_all(session: str | None = None) -> list[dict]:
    """返回 session 中所有 tab 列表。"""
    result = _cmd("list_tabs", {}, session=_resolve_session(session))
    return result.get("data", {}).get("tabs", [])


def close_all(session: str | None = None) -> int:
    """关闭 session 中所有 tab，返回关闭数。"""
    resolved = _resolve_session(session)
    tabs = list_all(resolved)
    closed = 0
    for t in tabs:
        try:
            _cmd("close_tab", {"tabId": t["tabId"]}, session=resolved)
            closed += 1
        except Exception:
            pass
    return closed


def close_one(tab_id: int, session: str | None = None) -> bool:
    """关闭指定 tabId 的 tab。"""
    try:
        result = _cmd("close_tab", {"tabId": tab_id}, session=_resolve_session(session))
        return result.get("ok", False)
    except Exception:
        return False


def ensure(url: str, session: str | None = None) -> dict:
    """确保 session 中有可用 tab 并导航到目标 URL。
    规则：有 tab → navigate(url)；0 tab → navigate(url, newTab=True)。
    不关闭任何已有 tab。"""
    resolved = _resolve_session(session)
    tabs = list_all(resolved)
    if tabs:
        return _navigate(url, session=resolved)  # no newTab
    else:
        return _cmd("navigate", {"url": url, "newTab": True}, session=resolved)
