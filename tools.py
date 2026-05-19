"""XHS plugin tools — registered into the 'xhs' toolset."""

from __future__ import annotations

import json
import time
from tools.registry import tool_error, tool_result

from plugins.xhs.client import (
    _cmd,
    _eval,
    _find_tab,
    _health_check,
    _navigate,
)


# ── tool schemas ──────────────────────────────────────────────────────────

XHS_READ_COMMENTS_SCHEMA = {
    "name": "xhs_read_comments",
    "description": "打开小红书通知页，切换到'评论和@'标签，提取所有'评论了你的笔记'的评论。返回评论列表 JSON。",
    "parameters": {
        "type": "object",
        "properties": {},
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
                "enum": ["public", "private"],
                "description": "可见范围，默认 private（仅自己可见）",
                "default": "private",
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


# ── helpers ───────────────────────────────────────────────────────────────

def _check_webbridge() -> bool:
    return _health_check()


SWITCH_COMMENT_TAB = """(() => {
  const spans = document.querySelectorAll("span");
  for (const s of spans) {
    if (s.innerText === "评论和@" && s.offsetParent !== null) { s.click(); return "clicked"; }
  }
  return "not found";
})()"""


PARSE_COMMENTS = r"""(() => {
  const items = [];
  const allText = document.body.innerText;
  const sections = allText.split(/\n(?=\S+\n评论了你的笔记)/);
  for (const section of sections) {
    if (!section.includes("评论了你的笔记")) continue;
    const lines = section.split("\n").map(x => x.trim()).filter(Boolean);
    const authorName = lines[0] || "";
    const actionIdx = lines.findIndex(x => x.startsWith("评论了你的笔记"));
    if (actionIdx < 0) continue;
    const timeText = lines[actionIdx].replace("评论了你的笔记", "").trim();
    const commentText = lines[actionIdx + 1] || "";
    if (!authorName || !commentText || commentText === "回复") continue;
    items.push({ authorName, timeText, text: commentText });
  }
  return JSON.stringify(items);
})()"""


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


PAGE_TEXT = "(() => { const t = document.body.innerText || ''; return t.substring(0, 2000); })()"


# ── handlers ──────────────────────────────────────────────────────────────

def _handle_xhs_read_comments(args: dict, **kwargs) -> str:
    """Read comments from 小红书 notification page."""
    try:
        _navigate("https://www.xiaohongshu.com/notification")
        time.sleep(3)
        _eval(SWITCH_COMMENT_TAB)
        time.sleep(2)
        result = _eval(PARSE_COMMENTS)
        comments = json.loads(result)
        if not comments:
            return tool_result({"comments": [], "count": 0, "message": "本次没有读取到评论。"})
        return tool_result({"comments": comments, "count": len(comments),
                           "message": f"本次读取到 {len(comments)} 条评论。"})
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

        # Click cover
        _eval(_click_cover_js(note_index))
        time.sleep(2)

        # Find and bind new tab
        _find_tab("www.xiaohongshu.com", active=False)
        time.sleep(1)
        _find_tab("www.xiaohongshu.com", active=True)
        time.sleep(2)

        # Read page
        text = _eval(PAGE_TEXT)
        return tool_result({"content": text, "note_index": note_index})
    except Exception as e:
        return tool_error(f"查看笔记详情失败: {e}")


def _handle_xhs_reply_comment(args: dict, **kwargs) -> str:
    """Reply to a comment on the note detail page."""
    reply_text = args.get("reply_text", "")
    if not reply_text:
        return tool_error("回复内容不能为空")
    try:
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
        if reply_text in text:
            return tool_result({"success": True, "reply_text": reply_text})
        return tool_result({"success": True, "reply_text": reply_text, "warning": "回复可能未显示，请手动确认"})
    except Exception as e:
        return tool_error(f"回复失败: {e}")


def _handle_xhs_publish_post(args: dict, **kwargs) -> str:
    """Placeholder — not yet implemented."""
    return tool_error("xhs_publish_post: 尚未实现，敬请期待")


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
    output_file = "/root/.hermes/data/xhs-ops/records.jsonl"

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


# ── required exports ──────────────────────────────────────────────────────

TOOLS = (
    ("xhs_read_comments",  XHS_READ_COMMENTS_SCHEMA,  _handle_xhs_read_comments,  "📖"),
    ("xhs_view_note_detail", XHS_VIEW_NOTE_DETAIL_SCHEMA, _handle_xhs_view_note_detail, "🔍"),
    ("xhs_reply_comment",  XHS_REPLY_COMMENT_SCHEMA,  _handle_xhs_reply_comment,  "💬"),
    ("xhs_publish_post",   XHS_PUBLISH_POST_SCHEMA,   _handle_xhs_publish_post,   "📝"),
    ("xhs_collect_info",   XHS_COLLECT_INFO_SCHEMA,   _handle_xhs_collect_info,   "📊"),
)
