"""WebBridge HTTP client for the XHS plugin.

Talks to the Kimi WebBridge daemon running on the Windows host.
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from typing import Any


def _get_webbridge_base() -> str:
    """Resolve Windows host gateway from WSL2."""
    try:
        result = subprocess.run(
            ["ip", "route"], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if line.startswith("default"):
                gateway = line.split()[2]
                return f"http://{gateway}:10086"
    except Exception:
        pass
    # Fallback
    return "http://172.26.240.1:10086"


def _health_check() -> bool:
    """Verify WebBridge is reachable and extension connected."""
    try:
        base = _get_webbridge_base()
        resp = _get(f"{base}/status")
        data = json.loads(resp)
        return data.get("running") and data.get("extension_connected")
    except Exception:
        return False


def _get(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _post(url: str, data: dict, timeout: int = 15) -> str:
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _cmd(action: str, args: dict | None = None, session: str = "xhs", timeout: int = 15) -> dict:
    """Send a command to WebBridge and return parsed response."""
    base = _get_webbridge_base()
    body = {"action": action, "args": args or {}, "session": session}
    result = _post(f"{base}/command", body, timeout=timeout)
    return json.loads(result)


def _eval(code: str, session: str = "xhs") -> str:
    """Run JavaScript in the browser and return the string result."""
    resp = _cmd("evaluate", {"code": code}, session=session)
    if resp.get("ok"):
        return resp.get("data", {}).get("value", "")
    raise RuntimeError(f"evaluate failed: {resp.get('error', {}).get('message', resp)}")


def _navigate(url: str, session: str = "xhs") -> dict:
    return _cmd("navigate", {"url": url}, session=session)


def _find_tab(url_pattern: str, active: bool, session: str = "xhs") -> dict:
    return _cmd("find_tab", {"url": url_pattern, "active": active}, session=session)


def close_all_tabs(session: str = "xhs") -> int:
    """关闭指定 session 中的所有 tab，返回关闭数量。"""
    result = _cmd("list_tabs", {}, session=session)
    tabs = result.get("data", {}).get("tabs", [])
    closed = 0
    for t in tabs:
        try:
            _cmd("close_tab", {"tabId": t["tabId"]}, session=session)
            closed += 1
        except Exception:
            pass
    return closed
