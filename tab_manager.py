"""Tab lifecycle management for XHS browser sessions.

All tab operations go through this module. Rules live here, not scattered.
"""

from __future__ import annotations

import json
import os
import sys

# Import from local file, not hermes plugin (avoids plugin loader chain)
_local = os.path.dirname(os.path.abspath(__file__))
if _local not in sys.path:
    sys.path.insert(0, _local)

from client import _cmd


def _navigate(url: str, session: str = "xhs") -> dict:
    return _cmd("navigate", {"url": url}, session=session)


def list_all(session: str = "xhs") -> list[dict]:
    """返回 session 中所有 tab 列表。"""
    result = _cmd("list_tabs", {}, session=session)
    return result.get("data", {}).get("tabs", [])


def close_all(session: str = "xhs") -> int:
    """关闭 session 中所有 tab，返回关闭数。"""
    tabs = list_all(session)
    closed = 0
    for t in tabs:
        try:
            _cmd("close_tab", {"tabId": t["tabId"]}, session=session)
            closed += 1
        except Exception:
            pass
    return closed


def close_one(tab_id: int, session: str = "xhs") -> bool:
    """关闭指定 tabId 的 tab。"""
    try:
        result = _cmd("close_tab", {"tabId": tab_id}, session=session)
        return result.get("ok", False)
    except Exception:
        return False


def ensure(url: str, session: str = "xhs") -> dict:
    """确保 session 中有可用 tab 并导航到目标 URL。
    规则：有 tab → navigate(url)；0 tab → navigate(url, newTab=True)。
    不关闭任何已有 tab。"""
    tabs = list_all(session)
    if tabs:
        return _navigate(url, session=session)  # no newTab
    else:
        return _cmd("navigate", {"url": url, "newTab": True}, session=session)
