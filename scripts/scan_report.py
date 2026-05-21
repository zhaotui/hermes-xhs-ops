#!/usr/bin/env python3
"""报告任务调度脚本。

用法: python3 scan_report.py [任务名] [参数...]
- 无参数 = 执行默认任务（评论扫描）
- 任务名 = 执行指定任务

新增任务：在下方加一个 task_xxx() 函数即可。
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

# ── 路径 ──
# 需要通过 XHS_PROJECT 环境变量或默认路径找到项目
PROJECT = os.environ.get("XHS_PROJECT")
if not PROJECT:
    # 从 scripts/ 目录反推
    _d = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(_d, "..", "client.py")):
        PROJECT = os.path.abspath(os.path.join(_d, ".."))
    else:
        sys.exit("请设置 XHS_PROJECT 环境变量指向项目目录")
sys.path.insert(0, PROJECT)
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

from client import _navigate, _eval, _find_tab, _health_check
from tab_manager import list_all as _list_tabs, close_one as _close_tab
from reporter import write_report


# ═══════════════════════════════════════════════════════════════════════
# 任务注册
# ═══════════════════════════════════════════════════════════════════════

TASKS = {}


def task(name: str):
    """装饰器：注册任务。"""
    def deco(fn):
        TASKS[name] = fn
        return fn
    return deco


# ═══════════════════════════════════════════════════════════════════════
# 任务实现
# ═══════════════════════════════════════════════════════════════════════

@task("comments")
def task_scan_comments():
    """扫评论：笔记管理页 → 点封面 → 详情页 → 提取评论 + 分类收集。"""
    if not _health_check():
        return [("连接状态", ["❌ WebBridge 不可用"])]

    sections = [("连接状态", ["✅ WebBridge 在线"])]

    try:
        _navigate("https://creator.xiaohongshu.com/new/note-manager?source=official")
        time.sleep(4)

        covers_raw = _eval("""(() => {
          const imgs = document.querySelectorAll('img.content');
          const results = [];
          imgs.forEach((img, i) => {
            const rect = img.getBoundingClientRect();
            results.push({ i, src: img.src.substring(0, 80), w: Math.round(rect.width), h: Math.round(rect.height), top: Math.round(rect.top) });
          });
          return JSON.stringify(results);
        })()""")
        covers = json.loads(covers_raw)

        if not covers:
            sections.append(("评论扫描", ["⚠️ 没有笔记"]))
            return sections

        all_comments = []
        lines = [f"共 {len(covers)} 篇笔记"]

        for ci in range(min(len(covers), 3)):
            before_ids = {t["tabId"] for t in _list_tabs()}

            _eval(f"""(() => {{
              const img = document.querySelectorAll('img.content')[{ci}];
              if (!img) return 'no cover';
              const rect = img.getBoundingClientRect();
              const x = rect.left + rect.width/2, y = rect.top + rect.height/2;
              img.dispatchEvent(new PointerEvent('pointerdown', {{bubbles:true,clientX:x,clientY:y}}));
              img.dispatchEvent(new PointerEvent('pointerup', {{bubbles:true,clientX:x,clientY:y}}));
              img.dispatchEvent(new MouseEvent('click', {{bubbles:true,clientX:x,clientY:y,button:0}}));
              return 'clicked';
            }})()""")
            time.sleep(2)

            _find_tab("www.xiaohongshu.com", active=False)
            time.sleep(1)
            _find_tab("www.xiaohongshu.com", active=True)
            time.sleep(3)

            if _eval("window.location.href.includes('xiaohongshu.com/explore/')?'ok':'not'") != "ok":
                _close_extra(before_ids)
                continue

            raw = _eval(r"""(() => {
              const bodyText = document.body.innerText || '';
              let title = document.title.split(' - 小红书')[0].split(' | 小红书')[0].trim();
              if (title.length > 40) title = title.substring(0, 40) + '...';
              const items = [];
              const m = bodyText.match(/共\s*(\d+)\s*条评论/);
              if (!m || parseInt(m[1]) === 0) return JSON.stringify({title, items});
              const idx = bodyText.indexOf(m[0]) + m[0].length;
              const tail = bodyText.substring(idx);
              let endIdx = tail.length;
              for (const mk of ['- THE END -', '说点什么...']) {
                const p = tail.indexOf(mk); if (p >= 0 && p < endIdx) endIdx = p;
              }
              const section = tail.substring(0, endIdx).trim();
              if (!section) return JSON.stringify({title, items});
              const lines = section.split('\n').map(x => x.trim());
              let i = 0;
              while (i < lines.length) {
                if (!lines[i] || lines[i]==='赞' || lines[i]==='回复') { i++; continue; }
                const authorName = lines[i++];
                if (i >= lines.length) break;
                let isAuthor = false;
                if (lines[i]==='作者') { isAuthor = true; i++; }
                if (i >= lines.length) break;
                const commentText = lines[i++];
                if (!commentText || commentText==='赞' || commentText==='回复') continue;
                let meta = '';
                if (i < lines.length && /\d+/.test(lines[i]) && !/\n/.test(lines[i])) meta = lines[i++];
                while (i < lines.length && (lines[i]==='赞' || lines[i]==='回复')) i++;
                items.push({ authorName, text: commentText, isAuthor, meta });
              }
              return JSON.stringify({title, items});
            })()""")
            data = json.loads(raw)
            title = data.get("title", f"笔记#{ci}")
            comments = data.get("items", [])

            _close_extra(before_ids)

            if comments:
                for c in comments:
                    c["note_index"] = ci
                all_comments.extend(comments)
                lines.append(f"\n### {title}")
                lines.append(f"共 {len(comments)} 条评论")
                for c in comments:
                    tag = " [作者]" if c.get("isAuthor") else ""
                    lines.append(f"  - {c['authorName']}{tag}: {c['text']}")

        if not all_comments:
            lines.append("📭 没有新评论")
            sections.append(("评论扫描", lines))
            return sections

        lines.append(f"\n总计: {len(all_comments)} 条评论")
        sections.append(("评论扫描", lines))

        # 分类收集
        positive_signals = ["感兴趣", "想了解", "怎么报名", "联系", "微信", "电话", "咨询"]
        SIMPLE_GREETINGS = {"你好", "你好啊", "hi", "hello", "在吗", "哈喽"}
        useful = []
        for c in all_comments:
            if c.get("isAuthor"):
                continue
            t = c["text"].strip()
            cls = "ignore"
            for s in positive_signals:
                if s in t:
                    cls = "useful"
                    break
            if cls == "useful":
                useful.append({**c, "classification": cls})

        collect_lines = []
        if useful:
            collect_file = os.path.expanduser("~/.hermes/data/xhs-ops/records.jsonl")
            os.makedirs(os.path.dirname(collect_file), exist_ok=True)
            existing = set()
            if os.path.exists(collect_file):
                with open(collect_file) as f:
                    for line in f:
                        try:
                            r = json.loads(line)
                            existing.add((r.get("authorName"), r.get("sourceText")))
                        except Exception:
                            pass
            new = 0
            with open(collect_file, "a") as f:
                for r in useful:
                    if (r["authorName"], r["text"]) not in existing:
                        rec = {"type":"xhs_collected_info","platform":"xiaohongshu",
                               "authorName":r["authorName"],"sourceText":r["text"],
                               "classification":"useful","fields":{},"status":"new",
                               "capturedAt":datetime.now(timezone.utc).isoformat()}
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        new += 1
            collect_lines.append(f"✅ 收集 {new} 条")
            for r in useful:
                collect_lines.append(f"  - {r['authorName']}: {r['text']}")
        else:
            collect_lines.append("📭 无有效信息")
        sections.append(("信息收集", collect_lines))

    except Exception as e:
        sections.append(("错误", [f"❌ {e}"]))

    return sections


# ═══════════════════════════════════════════════════════════════════════
# 辅助
# ═══════════════════════════════════════════════════════════════════════

def _close_extra(before_ids: set):
    after = {t["tabId"] for t in _list_tabs()}
    for tid in (after - before_ids):
        try:
            _close_tab(tid)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    task_name = sys.argv[1] if len(sys.argv) > 1 else "comments"
    fn = TASKS.get(task_name)
    if not fn:
        print(f"未知任务: {task_name}。可用: {', '.join(TASKS.keys())}")
        sys.exit(1)
    sections = fn()
    write_report(f"XHS {task_name} 报告", sections)
