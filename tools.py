"""XHS plugin tools — registered into the 'xhs' toolset."""

from __future__ import annotations

import json
import os
import time

# 不依赖 Hermes 内置 registry，内联定义
def tool_result(data: dict) -> str:
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)

def tool_error(message: str) -> str:
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)

# 优先相对导入，失败则回退脚本目录
try:
    from .client import _cmd as _bridge_cmd, _eval as _bridge_eval, _find_tab as _bridge_find_tab, _health_check, _navigate as _bridge_navigate
except ImportError:
    import sys
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from client import _cmd as _bridge_cmd, _eval as _bridge_eval, _find_tab as _bridge_find_tab, _health_check, _navigate as _bridge_navigate


DATA_DIR = os.path.expanduser("~/.hermes/data/xhs-ops")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
ACCOUNT_STATES_DIR = os.path.join(DATA_DIR, "account-states")
XHS_STATE_URLS = [
    "https://creator.xiaohongshu.com/new/note-manager?source=official",
    "https://www.xiaohongshu.com/",
]
DEFAULT_ACCOUNT = {
    "key": "default",
    "name": "默认账号",
    "session": "xhs",
    "home_url": "https://creator.xiaohongshu.com/new/note-manager?source=official",
    "nickname": "",
}


def _read_accounts_state() -> dict:
    default_state = {"current": DEFAULT_ACCOUNT["key"], "accounts": [DEFAULT_ACCOUNT.copy()]}
    if not os.path.exists(ACCOUNTS_FILE):
        _write_accounts_state(default_state)
        return default_state
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        _write_accounts_state(default_state)
        return default_state

    accounts = state.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        accounts = [DEFAULT_ACCOUNT.copy()]
    if not any(a.get("key") == DEFAULT_ACCOUNT["key"] for a in accounts):
        accounts.insert(0, DEFAULT_ACCOUNT.copy())
    current = state.get("current") or DEFAULT_ACCOUNT["key"]
    if not any(a.get("key") == current for a in accounts):
        current = DEFAULT_ACCOUNT["key"]
    for account in accounts:
        key = account.get("key")
        legacy_auto_session = f"xhs-{key}"
        if key and account.get("session") == legacy_auto_session:
            account["session"] = DEFAULT_ACCOUNT["session"]
    return {"current": current, "accounts": accounts}


def _write_accounts_state(state: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _normalize_account_key(value: str) -> str:
    key = "".join(ch for ch in value.strip().lower() if ch.isalnum() or ch in ("-", "_"))
    if not key:
        raise ValueError("账号 key 不能为空，只能包含字母、数字、-、_")
    return key


def _session_for_key(key: str) -> str:
    return DEFAULT_ACCOUNT["session"]


def _state_file_for_key(key: str) -> str:
    return os.path.join(ACCOUNT_STATES_DIR, f"{key}.json")


def _current_account() -> dict:
    state = _read_accounts_state()
    for account in state["accounts"]:
        if account.get("key") == state["current"]:
            return account
    return DEFAULT_ACCOUNT.copy()


def _current_session() -> str:
    return _current_account().get("session") or DEFAULT_ACCOUNT["session"]


def _cmd(action: str, args: dict | None = None, session: str | None = None, timeout: int = 15) -> dict:
    return _bridge_cmd(action, args, session=session or _current_session(), timeout=timeout)


def _eval(code: str, session: str | None = None) -> str:
    return _bridge_eval(code, session=session or _current_session())


def _navigate(url: str, session: str | None = None) -> dict:
    return _bridge_navigate(url, session=session or _current_session())


def _find_tab(url_pattern: str, active: bool, session: str | None = None) -> dict:
    return _bridge_find_tab(url_pattern, active, session=session or _current_session())


# ── tool schemas ──────────────────────────────────────────────────────────

XHS_READ_COMMENTS_SCHEMA = {
    "name": "xhs_read_comments",
    "description": "从笔记管理页点击封面打开详情页，提取所有评论。返回评论列表 JSON。",
    "parameters": {
        "type": "object",
        "properties": {
            "note_index": {
                "type": "integer",
                "description": "笔记在列表中的索引（0-based），默认 0",
                "default": 0,
            },
        },
        "required": [],
    },
}

XHS_VIEW_NOTE_DETAIL_SCHEMA = {
    "name": "xhs_view_note_detail",
    "description": "从创作者中心笔记管理页，根据索引点击封面图打开笔记前端详情页（仅已发布笔记可用）。返回页面文本内容。",
    "parameters": {
        "type": "object",
        "properties": {
            "note_index": {
                "type": "integer",
                "description": "笔记在列表中的索引（0-based）",
            },
        },
        "required": ["note_index"],
    },
}

XHS_REPLY_COMMENT_SCHEMA = {
    "name": "xhs_reply_comment",
    "description": "在笔记详情页回复指定评论。必须先调用 xhs_view_note_detail 进入详情页。",
    "parameters": {
        "type": "object",
        "properties": {
            "reply_text": {
                "type": "string",
                "description": "回复内容",
            },
        },
        "required": ["reply_text"],
    },
}

XHS_PUBLISH_POST_SCHEMA = {
    "name": "xhs_publish_post",
    "description": "发布小红书长文帖子。打开创作服务平台发布页，填写标题和正文并发布。",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "帖子标题，30字以内",
            },
            "body": {
                "type": "string",
                "description": "帖子正文",
            },
            "visibility": {
                "type": "string",
                "enum": ["public", "private", "friends", "include", "exclude"],
                "description": "可见范围：public=公开, private=仅自己可见, friends=仅互关好友, include=只给谁看, exclude=不给谁看",
                "default": "private",
            },
            "images": {
                "type": "array",
                "items": {"type": "string"},
                "description": "图片路径列表（Windows 或 WSL 路径均可）",
            },
            "location": {
                "type": "string",
                "description": "发布地点，如'北京'",
            },
            "template": {
                "type": "string",
                "description": "排版模板名称",
            },
            "content_type": {
                "type": "string",
                "description": "内容类型声明",
            },
            "source_type": {
                "type": "string",
                "description": "来源声明",
            },
            "allow_collab": {
                "type": "boolean",
                "description": "允许合拍",
            },
            "allow_copy": {
                "type": "boolean",
                "description": "允许正文复制",
            },
            "original": {
                "type": "boolean",
                "description": "原创声明",
            },
            "visibility_users": {
                "type": "array",
                "items": {"type": "string"},
                "description": "可见用户列表（visibility=include/exclude 时使用）",
            },
            "save_draft": {
                "type": "boolean",
                "description": "仅暂存不发布",
            },
            "click_items": {
                "type": "array",
                "items": {"type": "string"},
                "description": "额外点击的按钮文本列表（如'添加话题'）",
            },
            "preview_tab": {
                "type": "string",
                "description": "预览 tab 名称（如'图片编辑'）",
            },
        },
        "required": ["title", "body"],
    },
}

XHS_COLLECT_INFO_SCHEMA = {
    "name": "xhs_collect_info",
    "description": "根据规则分类评论，收集用户主动提供的信息，保存到本地 JSONL 文件。",
    "parameters": {
        "type": "object",
        "properties": {
            "comments_json": {
                "type": "string",
                "description": "评论列表 JSON 字符串，格式 [{\"authorName\":\"...\",\"timeText\":\"...\",\"text\":\"...\"}]",
            },
            "goal": {
                "type": "string",
                "description": "任务目标",
            },
            "positive_signals": {
                "type": "string",
                "description": "正向信号，逗号分隔，如 '感兴趣,想了解,怎么报名'",
                "default": "感兴趣,想了解,怎么报名",
            },
            "negative_signals": {
                "type": "string",
                "description": "负向信号，逗号分隔，如 '无关闲聊,表情,单纯问候'",
                "default": "无关闲聊,表情,单纯问候",
            },
        },
        "required": ["comments_json", "goal"],
    },
}

XHS_DELETE_POST_SCHEMA = {
    "name": "xhs_delete_post",
    "description": "删除笔记管理页中指定可见范围的帖子（测试后清理）。先识别后删除，绝不误删非目标帖。",
    "parameters": {
        "type": "object",
        "properties": {
            "visibility": {
                "type": "string",
                "enum": ["private", "public", "all"],
                "description": "删除范围：private=仅自己可见，public=公开，all=全部",
                "default": "private",
            },
        },
        "required": [],
    },
}

XHS_ACCOUNT_MANAGER_SCHEMA = {
    "name": "xhs_account_manager",
    "description": "管理并切换小红书账号。配置只保存昵称/切换文本等非敏感信息，登录态由浏览器保存。",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "current", "detect", "add", "save_state", "restore_state", "switch", "clear_local_state", "cleanup_tabs", "remove", "open"],
                "description": "操作：list=列出账号，current=查看当前配置，detect=识别当前页面登录账号，add=新增/更新账号，save_state=保存真实登录状态，restore_state=恢复真实登录状态，switch=恢复指定账号状态，clear_local_state=只清本地小红书登录状态不点退出登录，cleanup_tabs=关闭当前账号 session 多余页面，remove=删除账号，open=打开账号主页",
                "default": "list",
            },
            "key": {
                "type": "string",
                "description": "账号唯一标识，只能包含字母、数字、-、_，如 main、brand-a",
            },
            "name": {
                "type": "string",
                "description": "账号备注名，如 招聘号、品牌号",
            },
            "nickname": {
                "type": "string",
                "description": "小红书页面显示的昵称，用于识别当前登录账号",
            },
            "session": {
                "type": "string",
                "description": "WebBridge session 名称，仅用于浏览器标签分组，不代表登录态。未传时默认使用当前真实浏览器 session：xhs",
            },
            "home_url": {
                "type": "string",
                "description": "账号打开后的默认页面，默认小红书创作者中心笔记管理页",
            },
            "linked_creator": {
                "type": "string",
                "description": "关联的 EHR 职位创建人，用于发布时自动匹配账号。用户手动指定，如 '赵锐'",
            },
            "target_url": {
                "type": "string",
                "description": "恢复状态后打开的目标页面，默认账号 home_url",
            },
            "activate": {
                "type": "boolean",
                "description": "add 后是否立即设为当前账号",
                "default": True,
            },
        },
        "required": [],
    },
}


# ── helpers ───────────────────────────────────────────────────────────────

def _check_webbridge() -> bool:
    return _health_check()


def _get_tab_ids(session: str | None = None) -> set[int]:
    """返回当前 session 所有 tab 的 id 集合。"""
    result = _cmd("list_tabs", {}, session=session)
    tabs = result.get("data", {}).get("tabs", [])
    return {t["tabId"] for t in tabs}


def _close_new_tabs(before: set[int], session: str | None = None) -> int:
    """关闭 before 之后新出现的 tab，返回关闭数。"""
    after = _get_tab_ids(session)
    new_ids = after - before
    closed = 0
    for tid in new_ids:
        try:
            _cmd("close_tab", {"tabId": tid}, session=session)
            closed += 1
        except Exception:
            pass
    return closed



COVER_LIST = """(() => {
  const imgs = document.querySelectorAll('img.content');
  const results = [];
  imgs.forEach((img, i) => {
    const rect = img.getBoundingClientRect();
    results.push({ i, src: img.src, w: Math.round(rect.width), h: Math.round(rect.height), top: Math.round(rect.top) });
  });
  return JSON.stringify(results);
})()"""


def _click_cover_js(index: int) -> str:
    return f"""(() => {{
  const img = document.querySelectorAll('img.content')[{index}];
  if (!img) return 'no cover at index {index}';
  const rect = img.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  img.dispatchEvent(new PointerEvent('pointerdown', {{ bubbles: true, clientX: x, clientY: y }}));
  img.dispatchEvent(new PointerEvent('pointerup', {{ bubbles: true, clientX: x, clientY: y }}));
  img.dispatchEvent(new MouseEvent('click', {{ bubbles: true, clientX: x, clientY: y, button: 0 }}));
  return 'clicked cover[' + {index} + ']';
}})()"""


CLICK_REPLY = """(() => {
  const all = document.querySelectorAll('*');
  const targets = [];
  all.forEach(el => {
    if ((el.innerText || '') === '回复' && el.offsetParent) {
      targets.push({ el, top: Math.round(el.getBoundingClientRect().top) });
    }
  });
  if (targets.length === 0) return 'no reply buttons';
  targets.sort((a, b) => a.top - b.top);
  const target = targets[targets.length - 1];
  const rect = target.el.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  target.el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
  target.el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
  target.el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
  return 'clicked reply at top=' + target.top;
})()"""


def _fill_reply_js(text: str) -> str:
    safe = text.replace("'", "\\'")
    return f"""(() => {{
  const el = document.querySelector('P.content-input');
  if (!el) return 'input not found';
  el.focus();
  el.innerText = '{safe}';
  el.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
  return 'filled';
}})()"""


CLICK_SEND = """(() => {
  const all = document.querySelectorAll('*');
  for (const el of all) {
    if ((el.innerText || '').trim() === '发送' && el.offsetParent && el.tagName === 'BUTTON') {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
})()"""


PARSE_DETAIL_COMMENTS = r"""(() => {
  const items = [];
  const bodyText = document.body.innerText || '';

  // Locate comment section
  const m = bodyText.match(/共\s*(\d+)\s*条评论/);
  if (!m) return JSON.stringify(items);
  if (parseInt(m[1]) === 0) return JSON.stringify(items);

  const idx = bodyText.indexOf(m[0]) + m[0].length;
  const tail = bodyText.substring(idx);

  // Find end of comment section
  const endMarkers = ['- THE END -', '说点什么...'];
  let endIdx = tail.length;
  for (const marker of endMarkers) {
    const pos = tail.indexOf(marker);
    if (pos >= 0 && pos < endIdx) endIdx = pos;
  }
  const section = tail.substring(0, endIdx).trim();
  if (!section) return JSON.stringify(items);

  // Parse comments: each starts with authorName on its own line
  // Pattern: authorName \n [作者\n] commentText \n meta \n 赞 \n 回复
  const lines = section.split('\n').map(x => x.trim());
  let i = 0;
  while (i < lines.length) {
    // Skip action buttons / empty
    if (!lines[i] || lines[i] === '赞' || lines[i] === '回复') { i++; continue; }
    const authorName = lines[i++];
    if (i >= lines.length) break;
    let isAuthor = false;
    if (lines[i] === '作者') { isAuthor = true; i++; }
    if (i >= lines.length) break;
    const commentText = lines[i++];
    if (!commentText || commentText === '赞' || commentText === '回复') continue;
    // Meta line (time + location)
    let meta = '';
    if (i < lines.length && /\d+/.test(lines[i]) && !/\n/.test(lines[i])) {
      meta = lines[i++];
    }
    // Skip 赞 / 回复
    while (i < lines.length && (lines[i] === '赞' || lines[i] === '回复')) i++;
    items.push({ authorName, text: commentText, isAuthor, meta });
  }

  return JSON.stringify(items);
})()"""

PAGE_TEXT = "(() => { const t = document.body.innerText || ''; return t.substring(0, 2000); })()"


# ── handlers ──────────────────────────────────────────────────────────────

def _handle_xhs_read_comments(args: dict, **kwargs) -> str:
    """从笔记管理页打开详情页，提取评论。"""
    note_index = args.get("note_index", 0)
    try:
        # 1. 打开笔记管理页
        _navigate("https://creator.xiaohongshu.com/new/note-manager?source=official")
        time.sleep(4)

        # 2. 列封面，确认索引有效
        covers_raw = _eval(COVER_LIST)
        covers = json.loads(covers_raw)
        if note_index >= len(covers):
            return tool_error(f"笔记索引 {note_index} 超出范围（共 {len(covers)} 篇）")

        # 2.5. 记下当前 tab，点击封面后小会自动开新 tab
        tab_ids_before = _get_tab_ids()

        # 3. 点击封面打开详情页
        _eval(_click_cover_js(note_index))
        time.sleep(2)

        # 4. 切换到新开的详情页 tab
        _find_tab("www.xiaohongshu.com", active=False)
        time.sleep(1)
        _find_tab("www.xiaohongshu.com", active=True)
        time.sleep(3)

        # 5. 校验是否在详情页
        page_check = """(() => {
          return window.location.href.includes('xiaohongshu.com/explore/') ? 'ok' : 'not_detail';
        })()"""
        if _eval(page_check) != "ok":
            _close_new_tabs(tab_ids_before)
            text = _eval(PAGE_TEXT)
            if "笔记管理" in text:
                return tool_error("无法打开笔记详情，帖子可能处于审核中或未发布状态。")
            return tool_error("未成功进入详情页")

        # 6. 提取评论
        result = _eval(PARSE_DETAIL_COMMENTS)
        comments = json.loads(result)

        # 7. 关掉详情页 tab，回到笔记管理页
        _close_new_tabs(tab_ids_before)

        if not comments:
            return tool_result({"comments": [], "count": 0, "message": "该笔记暂无评论。"})
        return tool_result({"comments": comments, "count": len(comments),
                           "message": f"读取到 {len(comments)} 条评论。"})
    except Exception as e:
        return tool_error(f"读取评论失败: {e}")


def _handle_xhs_view_note_detail(args: dict, **kwargs) -> str:
    """Open note detail from creator note manager."""
    note_index = args.get("note_index", 0)
    try:
        _navigate("https://creator.xiaohongshu.com/new/note-manager?source=official")
        time.sleep(3)

        # List covers
        covers_raw = _eval(COVER_LIST)
        covers = json.loads(covers_raw)
        if note_index >= len(covers):
            return tool_error(f"笔记索引 {note_index} 超出范围（共 {len(covers)} 篇）")

        # 记下当前 tab，点击封面后小会自动开新 tab
        tab_ids_before = _get_tab_ids()

        # Click cover
        _eval(_click_cover_js(note_index))
        time.sleep(2)

        # Find and bind new tab
        _find_tab("www.xiaohongshu.com", active=False)
        time.sleep(1)
        _find_tab("www.xiaohongshu.com", active=True)
        time.sleep(2)

        # Read page text
        text = _eval(PAGE_TEXT)

        # 校验是否真正打开了详情页（审核中帖子无法打开）
        if "笔记管理" in text and "全部笔记" in text:
            _close_new_tabs(tab_ids_before)
            return tool_error(
                f"无法打开笔记详情（索引 {note_index}）。"
                "帖子可能处于审核中或未发布状态，请稍后再试。"
            )

        # 提取评论
        comments_raw = _eval(PARSE_DETAIL_COMMENTS)
        comments = json.loads(comments_raw)

        return tool_result({
            "content": text,
            "note_index": note_index,
            "comments": comments,
            "comment_count": len(comments),
        })
    except Exception as e:
        return tool_error(f"查看笔记详情失败: {e}")


def _handle_xhs_reply_comment(args: dict, **kwargs) -> str:
    """Reply to a comment on the note detail page."""
    reply_text = args.get("reply_text", "")
    if not reply_text:
        return tool_error("回复内容不能为空")
    try:
        # 校验是否在笔记详情页
        check_js = """(() => {
          const url = window.location.href;
          const isCreator = url.includes('creator.xiaohongshu.com');
          const isNotification = url.includes('notification');
          if (isCreator || isNotification) return 'not_detail';
          return 'ok';
        })()"""
        page_check = _eval(check_js)
        if page_check != "ok":
            return tool_error("当前不在笔记详情页，请先调用 xhs_view_note_detail 打开笔记")

        # Click last "回复" button
        _eval(CLICK_REPLY)
        time.sleep(1)

        # Fill reply
        _eval(_fill_reply_js(reply_text))
        time.sleep(0.5)

        # Send
        _eval(CLICK_SEND)
        time.sleep(2)

        # Verify
        text = _eval(PAGE_TEXT)

        # 回完关掉详情页 tab（除第一个外全关，留笔记管理页）
        all_tabs = list(_get_tab_ids())
        if len(all_tabs) > 1:
            for tid in all_tabs[1:]:
                try:
                    _cmd("close_tab", {"tabId": tid})
                except Exception:
                    pass

        if reply_text in text:
            return tool_result({"success": True, "reply_text": reply_text})
        return tool_result({"success": True, "reply_text": reply_text, "warning": "回复可能未显示，请手动确认"})
    except Exception as e:
        return tool_error(f"回复失败: {e}")


def _handle_xhs_publish_post(args: dict, **kwargs) -> str:
    """发布小红书长文，调用已验证的 publish_auto.py 脚本。"""
    import os
    import subprocess

    title = args.get("title", "")
    body = args.get("body", "")

    payload = {
        "title": title,
        "body": body,
        "description": title,
        "visibility": args.get("visibility", "private"),
        "autoPublish": not args.get("save_draft", False),
        "saveDraft": args.get("save_draft", False),
        "session": _current_session(),
    }

    # 透传可选字段
    field_map = {
        "template": "template",
        "content_type": "contentType",
        "source_type": "sourceType",
        "location": "location",
        "allow_collab": "allowCollab",
        "allow_copy": "allowCopy",
        "original": "original",
        "images": "images",
        "visibility_users": "visibilityUsers",
        "click_items": "clickItems",
        "preview_tab": "previewTab",
    }
    for src, dst in field_map.items():
        val = args.get(src)
        if val is not None:
            payload[dst] = val

    script = os.path.join(os.path.dirname(__file__), "scripts", "publish_auto.py")

    try:
        result = subprocess.run(
            ["python3", script, "--stdin-json"],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=360,
        )
        if result.returncode == 0:
            return tool_result({
                "success": True,
                "title": title,
                "visibility": args.get("visibility", "private"),
                "stdout": result.stdout.strip().split("\n")[-3:],
            })
        return tool_error(f"发布失败 (exit={result.returncode}):\n{result.stderr or result.stdout}")
    except subprocess.TimeoutExpired:
        return tool_error("发布超时（超过6分钟）")
    except Exception as e:
        return tool_error(f"发布异常: {e}")


def _handle_xhs_collect_info(args: dict, **kwargs) -> str:
    """Classify comments and save to local JSONL."""
    import os
    from datetime import datetime, timezone

    try:
        comments = json.loads(args["comments_json"])
    except Exception:
        return tool_error("comments_json 格式无效")

    goal = args.get("goal", "")
    positive = [s.strip() for s in args.get("positive_signals", "感兴趣,想了解,怎么报名").split(",") if s.strip()]
    negative = [s.strip() for s in args.get("negative_signals", "无关闲聊,表情,单纯问候").split(",") if s.strip()]
    output_file = os.path.expanduser("~/.hermes/data/xhs-ops/records.jsonl")

    SIMPLE_GREETINGS = {"你好", "你好啊", "hi", "hello", "在吗", "哈喽"}

    def classify(text: str) -> str:
        t = text.strip()
        # Negative first
        for s in negative:
            if s == "单纯问候" and t in SIMPLE_GREETINGS:
                return "ignore"
        for s in positive:
            if s in t:
                return "useful"
        return "ignore"

    results = []
    for c in comments:
        results.append({**c, "classification": classify(c["text"])})

    useful = [r for r in results if r["classification"] != "ignore"]

    if useful:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        existing = set()
        if os.path.exists(output_file):
            with open(output_file) as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        existing.add((rec.get("goal"), rec.get("authorName"), rec.get("sourceText")))
                    except Exception:
                        pass

        new_count = 0
        with open(output_file, "a") as f:
            for r in useful:
                key = (goal, r["authorName"], r["text"])
                if key not in existing:
                    rec = {
                        "type": "xhs_collected_info",
                        "goal": goal,
                        "platform": "xiaohongshu",
                        "sourceType": "comment",
                        "authorName": r["authorName"],
                        "sourceText": r["text"],
                        "classification": r["classification"],
                        "fields": {},
                        "status": "new",
                        "capturedAt": datetime.now(timezone.utc).isoformat(),
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    new_count += 1

        return tool_result({
            "collected": new_count,
            "total": len(useful),
            "output_file": output_file,
            "details": [{k: r[k] for k in ["authorName", "text", "classification"]} for r in useful],
        })

    return tool_result({"collected": 0, "total": 0, "message": "本次没有收集到新的有效信息。"})


def _handle_xhs_delete_post(args: dict, **kwargs) -> str:
    """删除笔记管理页中指定可见范围的帖子。先识别后删除。"""
    visibility = args.get("visibility", "private")
    try:
        _navigate("https://creator.xiaohongshu.com/new/note-manager?source=official")
        time.sleep(3)

        # 1. 识别目标帖子（按 visibility 不同策略）
        if visibility == "private":
            identify_js = """(() => {
              const text = document.body.innerText;
              const re = /仅自己可见\\n(.+?)\\n发布于 \\d{4}年/g;
              const posts = [];
              let match;
              while ((match = re.exec(text)) !== null) {
                posts.push({ title: match[1] });
              }
              return JSON.stringify({ count: posts.length, posts });
            })()"""
        elif visibility == "public":
            identify_js = """(() => {
              const text = document.body.innerText;
              // 匹配所有 "title\\n发布于"，但排除前面是 "仅自己可见" 的
              const allRe = /(.+?)\\n发布于 \\d{4}年/g;
              const posts = [];
              let match;
              while ((match = allRe.exec(text)) !== null) {
                const title = match[1];
                // 检查前面一行是不是 "仅自己可见"
                const before = text.substring(Math.max(0, match.index - 10), match.index);
                if (!before.includes("仅自己可见")) {
                  posts.push({ title });
                }
              }
              return JSON.stringify({ count: posts.length, posts });
            })()"""
        else:  # all
            identify_js = """(() => {
              const text = document.body.innerText;
              const re = /(.+?)\\n发布于 \\d{4}年/g;
              const posts = [];
              let match;
              while ((match = re.exec(text)) !== null) {
                posts.push({ title: match[1] });
              }
              return JSON.stringify({ count: posts.length, posts });
            })()"""

        result = _eval(identify_js)
        data = json.loads(result)

        count = data.get("count", 0)
        label = {"private": "仅自己可见", "public": "公开", "all": "全部"}[visibility]
        if count == 0:
            return tool_result({"deleted": 0, "message": f"没有{label}的帖子"})

        posts = data.get("posts", [])
        deleted = []
        failed = []

        for i in range(count):
            # 2. 点删除按钮
            delete_js = f"""(() => {{
              const all = Array.from(document.querySelectorAll('*'));
              const btns = all.filter(el =>
                (el.innerText || el.textContent || '').trim() === '删除' && el.offsetParent
              );
              if (!btns[{i}]) return JSON.stringify({{ ok: false, reason: 'no delete btn at ' + {i} }});
              btns[{i}].click();
              return JSON.stringify({{ ok: true }});
            }})()"""
            _eval(delete_js)
            time.sleep(1.5)

            # 3. 点确认弹窗
            confirm_js = """(() => {
              const all = document.querySelectorAll('button, span, div');
              for (const el of all) {
                if ((el.innerText || el.textContent || '').trim() === '确定' && el.offsetParent) {
                  el.click();
                  return JSON.stringify({ ok: true });
                }
              }
              return JSON.stringify({ ok: false });
            })()"""
            confirm_raw = _eval(confirm_js)
            confirm_data = json.loads(confirm_raw)

            title = posts[i]["title"] if i < len(posts) else f"#{i}"
            if confirm_data.get("ok"):
                deleted.append(title)
            else:
                failed.append(title)
            time.sleep(2)

        return tool_result({
            "deleted": len(deleted),
            "failed": len(failed),
            "total": count,
            "visibility": visibility,
            "posts": deleted,
            "message": f"删除了 {len(deleted)} 篇{label}帖"
                       + (f"，{len(failed)} 篇失败" if failed else ""),
        })
    except Exception as e:
        return tool_error(f"删除失败: {e}")


DETECT_XHS_ACCOUNT_JS = """(() => {
  const visible = el => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const textOf = el => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim();
  const candidates = [];
  document.querySelectorAll('button,a,span,div,[role="button"],[class*="user"],[class*="account"],[class*="avatar"],[class*="name"]').forEach(el => {
    if (!visible(el)) return;
    const text = textOf(el);
    const cls = String(el.className || '');
    if (!text || text.length > 40) return;
    if (/账号|切换|个人|主页|创作|昵称|user|account|avatar|name/i.test(text + ' ' + cls)) {
      candidates.push({ text, tag: el.tagName, className: cls.slice(0, 120) });
    }
  });
  return JSON.stringify({
    url: location.href,
    title: document.title,
    candidates: candidates.slice(0, 30),
    bodyHead: document.body.innerText.slice(0, 600),
  });
})()"""


def _detect_xhs_account(session: str | None = None) -> dict:
    raw = _eval(DETECT_XHS_ACCOUNT_JS, session=session)
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def _storage_snapshot_js() -> str:
    return """(() => {
  const dump = storage => {
    const data = {};
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      data[key] = storage.getItem(key);
    }
    return data;
  };
  return JSON.stringify({
    origin: location.origin,
    url: location.href,
    localStorage: dump(localStorage),
    sessionStorage: dump(sessionStorage),
  });
})()"""


def _restore_storage_js(local_storage: dict, session_storage: dict) -> str:
    return f"""(() => {{
  const localData = {json.dumps(local_storage, ensure_ascii=False)};
  const sessionData = {json.dumps(session_storage, ensure_ascii=False)};
  localStorage.clear();
  sessionStorage.clear();
  for (const [key, value] of Object.entries(localData)) {{
    localStorage.setItem(key, value);
  }}
  for (const [key, value] of Object.entries(sessionData)) {{
    sessionStorage.setItem(key, value);
  }}
  return JSON.stringify({{
    ok: true,
    origin: location.origin,
    localStorage: Object.keys(localData).length,
    sessionStorage: Object.keys(sessionData).length,
  }});
}})()"""


CLEAR_STORAGE_JS = """(() => {
  localStorage.clear();
  sessionStorage.clear();
  return JSON.stringify({ ok: true, origin: location.origin });
})()"""


def _is_xhs_cookie(cookie: dict) -> bool:
    domain = cookie.get("domain", "").lstrip(".")
    return domain == "xiaohongshu.com" or domain.endswith(".xiaohongshu.com")


def _cookie_for_set(cookie: dict) -> dict:
    allowed = {
        "name", "value", "domain", "path", "secure", "httpOnly", "sameSite",
        "expires", "priority", "sameParty", "sourceScheme", "sourcePort",
        "partitionKey",
    }
    item = {k: v for k, v in cookie.items() if k in allowed and v is not None}
    if item.get("expires", 0) <= 0:
        item.pop("expires", None)
    item.setdefault("path", "/")
    return item


def _delete_xhs_cookies(session: str) -> int:
    data = _cmd("cdp", {"method": "Network.getAllCookies", "params": {}}, session=session)
    cookies = data.get("data", {}).get("cookies", [])
    deleted = 0
    for cookie in cookies:
        if not _is_xhs_cookie(cookie):
            continue
        params = {
            "name": cookie.get("name"),
            "domain": cookie.get("domain"),
            "path": cookie.get("path") or "/",
        }
        try:
            _cmd("cdp", {"method": "Network.deleteCookies", "params": params}, session=session)
            deleted += 1
        except Exception:
            pass
    return deleted


def _ensure_xhs_tab(session: str, url: str | None = None, group_title: str | None = None) -> dict:
    target = url or DEFAULT_ACCOUNT["home_url"]
    tabs_result = _cmd("list_tabs", {}, session=session)
    tabs = tabs_result.get("data", {}).get("tabs", [])
    if tabs:
        return _cmd("navigate", {"url": target}, session=session)
    return _cmd("navigate", {"url": target, "newTab": True, "group_title": group_title or "小红书"}, session=session)


def _save_xhs_state(account: dict) -> dict:
    session = account.get("session") or _session_for_key(account.get("key", ""))
    os.makedirs(ACCOUNT_STATES_DIR, exist_ok=True)
    _ensure_xhs_tab(session, account.get("home_url") or DEFAULT_ACCOUNT["home_url"], account.get("name"))

    cookie_result = _cmd("cdp", {"method": "Network.getAllCookies", "params": {}}, session=session)
    cookies = [
        _cookie_for_set(cookie)
        for cookie in cookie_result.get("data", {}).get("cookies", [])
        if _is_xhs_cookie(cookie)
    ]

    storages = {}
    for url in XHS_STATE_URLS:
        _cmd("navigate", {"url": url}, session=session)
        time.sleep(2)
        raw = _eval(_storage_snapshot_js(), session=session)
        data = json.loads(raw)
        storages[data["origin"]] = {
            "url": data["url"],
            "localStorage": data["localStorage"],
            "sessionStorage": data["sessionStorage"],
        }

    _cmd("navigate", {"url": account.get("home_url") or DEFAULT_ACCOUNT["home_url"]}, session=session)
    state = {
        "key": account.get("key"),
        "name": account.get("name"),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cookies": cookies,
        "storages": storages,
    }
    state_file = _state_file_for_key(account.get("key"))
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return {
        "state_file": state_file,
        "cookies": len(cookies),
        "origins": list(storages.keys()),
    }


def _restore_xhs_state(account: dict, target_url: str | None = None) -> dict:
    session = account.get("session") or _session_for_key(account.get("key", ""))
    state_file = _state_file_for_key(account.get("key"))
    if not os.path.exists(state_file):
        raise RuntimeError(f"账号状态不存在，请先 save_state: {state_file}")

    with open(state_file, "r", encoding="utf-8") as f:
        state = json.load(f)

    _ensure_xhs_tab(session, target_url or account.get("home_url") or DEFAULT_ACCOUNT["home_url"], account.get("name"))
    deleted = _delete_xhs_cookies(session)
    cookies = [_cookie_for_set(cookie) for cookie in state.get("cookies", [])]
    if cookies:
        _cmd("cdp", {"method": "Network.setCookies", "params": {"cookies": cookies}}, session=session)

    restored = []
    for origin, storage in state.get("storages", {}).items():
        url = storage.get("url") or origin
        _cmd("navigate", {"url": url}, session=session)
        time.sleep(1)
        raw = _eval(
            _restore_storage_js(storage.get("localStorage", {}), storage.get("sessionStorage", {})),
            session=session,
        )
        try:
            restored.append(json.loads(raw))
        except Exception:
            restored.append({"origin": origin, "raw": raw})

    final_url = target_url or account.get("home_url") or DEFAULT_ACCOUNT["home_url"]
    nav = _cmd("navigate", {"url": final_url}, session=session)
    time.sleep(2)
    return {
        "state_file": state_file,
        "deleted_cookies": deleted,
        "restored_cookies": len(cookies),
        "restored_storages": restored,
        "navigate": nav,
        "detected": _detect_xhs_account(session),
    }


def _clear_xhs_local_state(session: str, target_url: str | None = None) -> dict:
    _ensure_xhs_tab(session, target_url or DEFAULT_ACCOUNT["home_url"], "清理小红书状态")
    deleted = _delete_xhs_cookies(session)
    cleared = []
    for url in XHS_STATE_URLS:
        _cmd("navigate", {"url": url}, session=session)
        time.sleep(1)
        raw = _eval(CLEAR_STORAGE_JS, session=session)
        try:
            cleared.append(json.loads(raw))
        except Exception:
            cleared.append({"url": url, "raw": raw})

    final_url = target_url or DEFAULT_ACCOUNT["home_url"]
    nav = _cmd("navigate", {"url": final_url}, session=session)
    return {
        "deleted_cookies": deleted,
        "cleared_storages": cleared,
        "navigate": nav,
    }


def _cleanup_extra_tabs(session: str, keep_url: str | None = None) -> dict:
    tabs_result = _cmd("list_tabs", {}, session=session)
    tabs = tabs_result.get("data", {}).get("tabs", [])
    if not tabs:
        nav = _cmd("navigate", {"url": keep_url or DEFAULT_ACCOUNT["home_url"], "newTab": True, "group_title": "小红书"}, session=session)
        return {"closed": 0, "kept": None, "navigate": nav}

    active = next((tab for tab in tabs if tab.get("active")), None)
    kept = active or tabs[-1]
    kept_id = kept.get("tabId")
    closed = 0
    for tab in tabs:
        tab_id = tab.get("tabId")
        if tab_id == kept_id:
            continue
        try:
            result = _cmd("close_tab", {"tabId": tab_id}, session=session)
            if result.get("ok"):
                closed += 1
        except Exception:
            pass

    nav = None
    if keep_url:
        nav = _cmd("navigate", {"url": keep_url}, session=session)
    return {"closed": closed, "kept": kept_id, "navigate": nav}


def _handle_xhs_account_manager(args: dict, **kwargs) -> str:
    """管理小红书账号与当前 WebBridge session。"""
    action = args.get("action", "list")
    state = _read_accounts_state()
    accounts = state["accounts"]

    def public_account(account: dict) -> dict:
        return {
            "key": account.get("key"),
            "name": account.get("name") or account.get("key"),
            "nickname": account.get("nickname") or "",
            "linked_creator": account.get("linked_creator") or "",
            "session": account.get("session") or _session_for_key(account.get("key", "")),
            "home_url": account.get("home_url") or DEFAULT_ACCOUNT["home_url"],
            "state_file": _state_file_for_key(account.get("key", "")),
            "has_state": os.path.exists(_state_file_for_key(account.get("key", ""))),
            "current": account.get("key") == state["current"],
        }

    try:
        if action == "list":
            return tool_result({
                "current": state["current"],
                "accounts": [public_account(a) for a in accounts],
                "accounts_file": ACCOUNTS_FILE,
            })

        if action == "current":
            account = _current_account()
            detected = _detect_xhs_account(account.get("session") or _current_session())
            return tool_result({"account": public_account(account), "detected": detected})

        if action == "detect":
            key = args.get("key")
            session = None
            if key:
                normalized = _normalize_account_key(key)
                account = next((a for a in accounts if a.get("key") == normalized), None)
                if not account:
                    return tool_error(f"账号不存在: {normalized}")
                session = account.get("session")
            return tool_result({"detected": _detect_xhs_account(session)})

        if action == "add":
            key = _normalize_account_key(args.get("key") or "")
            name = (args.get("name") or key).strip()
            nickname = (args.get("nickname") or "").strip()
            linked_creator = (args.get("linked_creator") or "").strip()
            session = (args.get("session") or _session_for_key(key)).strip()
            home_url = (args.get("home_url") or DEFAULT_ACCOUNT["home_url"]).strip()
            account = {
                "key": key,
                "name": name,
                "nickname": nickname,
                "linked_creator": linked_creator,
                "session": session,
                "home_url": home_url,
            }

            replaced = False
            for index, item in enumerate(accounts):
                if item.get("key") == key:
                    accounts[index] = account
                    replaced = True
                    break
            if not replaced:
                accounts.append(account)
            if args.get("activate", True):
                state["current"] = key
            state["accounts"] = accounts
            _write_accounts_state(state)
            return tool_result({
                "success": True,
                "action": "updated" if replaced else "added",
                "account": public_account(account),
            })

        if action == "switch":
            key = _normalize_account_key(args.get("key") or "")
            account = next((a for a in accounts if a.get("key") == key), None)
            if not account:
                return tool_error(f"账号不存在: {key}，请先用 action=add 新增")
            switch_result = _restore_xhs_state(account, args.get("target_url"))
            state["current"] = key
            _write_accounts_state(state)
            return tool_result({"success": True, "account": public_account(account), "switch": switch_result})

        if action == "save_state":
            key = _normalize_account_key(args.get("key") or state["current"])
            account = next((a for a in accounts if a.get("key") == key), None)
            if not account:
                return tool_error(f"账号不存在: {key}，请先用 action=add 新增")
            saved = _save_xhs_state(account)
            return tool_result({"success": True, "account": public_account(account), "saved": saved})

        if action == "restore_state":
            key = _normalize_account_key(args.get("key") or state["current"])
            account = next((a for a in accounts if a.get("key") == key), None)
            if not account:
                return tool_error(f"账号不存在: {key}，请先用 action=add 新增")
            restored = _restore_xhs_state(account, args.get("target_url"))
            state["current"] = key
            _write_accounts_state(state)
            return tool_result({"success": True, "account": public_account(account), "restored": restored})

        if action == "clear_local_state":
            key = args.get("key")
            session = _current_session()
            if key:
                normalized = _normalize_account_key(key)
                account = next((a for a in accounts if a.get("key") == normalized), None)
                if not account:
                    return tool_error(f"账号不存在: {normalized}")
                session = account.get("session") or _session_for_key(normalized)
            cleared = _clear_xhs_local_state(session, args.get("target_url"))
            return tool_result({"success": True, "session": session, "cleared": cleared})

        if action == "cleanup_tabs":
            key = args.get("key")
            session = _current_session()
            home_url = args.get("target_url")
            if key:
                normalized = _normalize_account_key(key)
                account = next((a for a in accounts if a.get("key") == normalized), None)
                if not account:
                    return tool_error(f"账号不存在: {normalized}")
                session = account.get("session") or _session_for_key(normalized)
                home_url = home_url or account.get("home_url")
            cleaned = _cleanup_extra_tabs(session, home_url)
            return tool_result({"success": True, "session": session, "cleanup": cleaned})

        if action == "remove":
            key = _normalize_account_key(args.get("key") or "")
            if key == DEFAULT_ACCOUNT["key"]:
                return tool_error("默认账号不能删除")
            next_accounts = [a for a in accounts if a.get("key") != key]
            if len(next_accounts) == len(accounts):
                return tool_error(f"账号不存在: {key}")
            state["accounts"] = next_accounts
            if state["current"] == key:
                state["current"] = DEFAULT_ACCOUNT["key"]
            _write_accounts_state(state)
            return tool_result({"success": True, "removed": key, "current": state["current"]})

        if action == "open":
            key = args.get("key")
            account = _current_account()
            if key:
                normalized = _normalize_account_key(key)
                account = next((a for a in accounts if a.get("key") == normalized), None)
                if not account:
                    return tool_error(f"账号不存在: {normalized}")
                state["current"] = normalized
                _write_accounts_state(state)
            url = account.get("home_url") or DEFAULT_ACCOUNT["home_url"]
            session = account.get("session") or _session_for_key(account.get("key", ""))
            result = _cmd("navigate", {"url": url, "newTab": True, "group_title": account.get("name")}, session=session)
            detected = _detect_xhs_account(session)
            return tool_result({"success": True, "account": public_account(account), "navigate": result, "detected": detected})

        return tool_error(f"未知 action: {action}")
    except Exception as e:
        return tool_error(f"账号管理失败: {e}")


# ── required exports ──────────────────────────────────────────────────────

TOOLS = (
    ("xhs_account_manager", XHS_ACCOUNT_MANAGER_SCHEMA, _handle_xhs_account_manager, "👤"),
    ("xhs_read_comments",  XHS_READ_COMMENTS_SCHEMA,  _handle_xhs_read_comments,  "📖"),
    ("xhs_view_note_detail", XHS_VIEW_NOTE_DETAIL_SCHEMA, _handle_xhs_view_note_detail, "🔍"),
    ("xhs_reply_comment",  XHS_REPLY_COMMENT_SCHEMA,  _handle_xhs_reply_comment,  "💬"),
    ("xhs_publish_post",   XHS_PUBLISH_POST_SCHEMA,   _handle_xhs_publish_post,   "📝"),
    ("xhs_collect_info",   XHS_COLLECT_INFO_SCHEMA,   _handle_xhs_collect_info,   "📊"),
    ("xhs_delete_post",    XHS_DELETE_POST_SCHEMA,    _handle_xhs_delete_post,    "🗑️"),
)
