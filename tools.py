"""XHS plugin tools — registered into the 'xhs' toolset."""

from __future__ import annotations

import json
import time
from tools.registry import tool_error, tool_result

# 优先相对导入，失败则回退脚本目录
try:
    from .client import _cmd, _eval, _find_tab, _health_check, _navigate
except ImportError:
    import os, sys
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from client import _cmd, _eval, _find_tab, _health_check, _navigate


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


# ── helpers ───────────────────────────────────────────────────────────────

def _check_webbridge() -> bool:
    return _health_check()


def _get_tab_ids(session: str = "xhs") -> set[int]:
    """返回当前 session 所有 tab 的 id 集合。"""
    result = _cmd("list_tabs", {}, session=session)
    tabs = result.get("data", {}).get("tabs", [])
    return {t["tabId"] for t in tabs}


def _close_new_tabs(before: set[int], session: str = "xhs") -> int:
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
        "session": "xhs",
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


# ── required exports ──────────────────────────────────────────────────────

TOOLS = (
    ("xhs_read_comments",  XHS_READ_COMMENTS_SCHEMA,  _handle_xhs_read_comments,  "📖"),
    ("xhs_view_note_detail", XHS_VIEW_NOTE_DETAIL_SCHEMA, _handle_xhs_view_note_detail, "🔍"),
    ("xhs_reply_comment",  XHS_REPLY_COMMENT_SCHEMA,  _handle_xhs_reply_comment,  "💬"),
    ("xhs_publish_post",   XHS_PUBLISH_POST_SCHEMA,   _handle_xhs_publish_post,   "📝"),
    ("xhs_collect_info",   XHS_COLLECT_INFO_SCHEMA,   _handle_xhs_collect_info,   "📊"),
    ("xhs_delete_post",    XHS_DELETE_POST_SCHEMA,    _handle_xhs_delete_post,    "🗑️"),
)
