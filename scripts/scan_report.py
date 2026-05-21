#!/usr/bin/env python3
"""小红书评论扫描报告脚本。

独立运行，输出纯文本报告。供 cron --script --no-agent 调用。
报告保存到 ~/.hermes/data/xhs-ops/reports/ 目录。
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

# ── 路径设置 ──────────────────────────────────────────────────────────
# 从 ~/.hermes/scripts/ 运行时需要找到 xhs 项目目录
PROJECT = os.environ.get("XHS_PROJECT", "/mnt/c/Users/yxkj/Desktop/work/xhs")
sys.path.insert(0, PROJECT)
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

from client import _navigate, _eval, _find_tab, _health_check

REPORT_DIR = os.path.expanduser("~/.hermes/data/xhs-ops/reports")
COLLECT_FILE = os.path.expanduser("~/.hermes/data/xhs-ops/records.jsonl")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def main():
    report_lines = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_lines.append(f"# XHS 扫描报告 — {timestamp}")

    # ── 1. 健康检查 ──
    if not _health_check():
        report_lines.append("\n❌ WebBridge 不可用，跳过扫描。")
        return write_report(report_lines)

    report_lines.append("\n## 连接状态")
    report_lines.append("✅ WebBridge 在线")

    # ── 2. 读取评论 ──
    report_lines.append("\n## 评论扫描")
    try:
        _navigate("https://creator.xiaohongshu.com/new/note-manager?source=official")
        time.sleep(4)

        # 列封面
        COVER_LIST = """(() => {
          const imgs = document.querySelectorAll('img.content');
          const results = [];
          imgs.forEach((img, i) => {
            const rect = img.getBoundingClientRect();
            results.push({ i, src: img.src.substring(0, 80), w: Math.round(rect.width), h: Math.round(rect.height), top: Math.round(rect.top) });
          });
          return JSON.stringify(results);
        })()"""
        covers_raw = _eval(COVER_LIST)
        covers = json.loads(covers_raw)

        if not covers:
            report_lines.append("⚠️ 没有笔记。")
            return write_report(report_lines)

        report_lines.append(f"共 {len(covers)} 篇笔记")

        all_comments = []
        for ci in range(min(len(covers), 3)):  # 最多扫 3 篇
            # 记下当前 tab
            before_ids = _get_current_tab_ids()

            # 点击封面
            click_js = f"""(() => {{
              const img = document.querySelectorAll('img.content')[{ci}];
              if (!img) return 'no cover';
              const rect = img.getBoundingClientRect();
              const x = rect.left + rect.width / 2;
              const y = rect.top + rect.height / 2;
              img.dispatchEvent(new PointerEvent('pointerdown', {{ bubbles: true, clientX: x, clientY: y }}));
              img.dispatchEvent(new PointerEvent('pointerup', {{ bubbles: true, clientX: x, clientY: y }}));
              img.dispatchEvent(new MouseEvent('click', {{ bubbles: true, clientX: x, clientY: y, button: 0 }}));
              return 'clicked';
            }})()"""
            _eval(click_js)
            time.sleep(2)

            # 切换到详情 tab
            _find_tab("www.xiaohongshu.com", active=False)
            time.sleep(1)
            _find_tab("www.xiaohongshu.com", active=True)
            time.sleep(3)

            # 校验
            page_check = "window.location.href.includes('xiaohongshu.com/explore/') ? 'ok' : 'not'"
            if _eval(page_check) != "ok":
                # 关掉新 tab
                _close_extra_tabs(before_ids)
                continue

            # 提取标题和评论
            PARSE = r"""(() => {
              const bodyText = document.body.innerText || '';
              // 提取标题：从 document.title（格式："标题 - 小红书"）
              let title = document.title.split(' - 小红书')[0].split(' | 小红书')[0].trim();
              if (title.length > 40) title = title.substring(0, 40) + '...';

              // 提取评论
              const items = [];
              const m = bodyText.match(/共\s*(\d+)\s*条评论/);
              if (!m || parseInt(m[1]) === 0) return JSON.stringify({title, items});
              const idx = bodyText.indexOf(m[0]) + m[0].length;
              const tail = bodyText.substring(idx);
              const endMarkers = ['- THE END -', '说点什么...'];
              let endIdx = tail.length;
              for (const marker of endMarkers) {
                const pos = tail.indexOf(marker);
                if (pos >= 0 && pos < endIdx) endIdx = pos;
              }
              const section = tail.substring(0, endIdx).trim();
              if (!section) return JSON.stringify({title, items});
              const lines = section.split('\n').map(x => x.trim());
              let i = 0;
              while (i < lines.length) {
                if (!lines[i] || lines[i] === '赞' || lines[i] === '回复') { i++; continue; }
                const authorName = lines[i++];
                if (i >= lines.length) break;
                let isAuthor = false;
                if (lines[i] === '作者') { isAuthor = true; i++; }
                if (i >= lines.length) break;
                const commentText = lines[i++];
                if (!commentText || commentText === '赞' || commentText === '回复') continue;
                let meta = '';
                if (i < lines.length && /\d+/.test(lines[i]) && !/\n/.test(lines[i])) { meta = lines[i++]; }
                while (i < lines.length && (lines[i] === '赞' || lines[i] === '回复')) i++;
                items.push({ authorName, text: commentText, isAuthor, meta });
              }
              return JSON.stringify({title, items});
            })()"""
            raw = _eval(PARSE)
            data = json.loads(raw)
            note_title = data.get("title", f"笔记#{ci}")
            comments = data.get("items", [])

            # 关详情 tab
            _close_extra_tabs(before_ids)

            if comments:
                for c in comments:
                    c["note_index"] = ci
                all_comments.extend(comments)
                report_lines.append(
                    f"\n### {note_title}"
                )
                report_lines.append(f"共 {len(comments)} 条评论")
                for c in comments:
                    tag = " [作者]" if c.get("isAuthor") else ""
                    report_lines.append(f"  - {c['authorName']}{tag}: {c['text']}")

        if not all_comments:
            report_lines.append("\n📭 没有新评论。")
            return write_report(report_lines)

        report_lines.append(f"\n总计: {len(all_comments)} 条评论")

        # ── 3. 分类收集 ──
        report_lines.append("\n## 信息收集")
        positive_signals = ["感兴趣", "想了解", "怎么报名", "联系", "微信", "电话", "咨询"]
        negative_signals = ["你好", "你好啊", "哈喽", "hi", "在吗", "表情", "打卡"]
        SIMPLE_GREETINGS = {"你好", "你好啊", "hi", "hello", "在吗", "哈喽"}

        def classify(text: str) -> str:
            t = text.strip()
            for s in negative_signals:
                if s == "单纯问候" and t in SIMPLE_GREETINGS:
                    return "ignore"
            for s in positive_signals:
                if s in t:
                    return "useful"
            return "ignore"

        useful = []
        for c in all_comments:
            c["classification"] = classify(c["text"])
            if c["classification"] != "ignore" and not c.get("isAuthor"):
                useful.append(c)

        if useful:
            ensure_dir(os.path.dirname(COLLECT_FILE))
            existing = set()
            if os.path.exists(COLLECT_FILE):
                with open(COLLECT_FILE) as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            existing.add((rec.get("authorName"), rec.get("sourceText")))
                        except Exception:
                            pass

            new_count = 0
            with open(COLLECT_FILE, "a") as f:
                for r in useful:
                    key = (r["authorName"], r["text"])
                    if key not in existing:
                        rec = {
                            "type": "xhs_collected_info",
                            "platform": "xiaohongshu",
                            "authorName": r["authorName"],
                            "sourceText": r["text"],
                            "classification": r["classification"],
                            "fields": {},
                            "status": "new",
                            "capturedAt": datetime.now(timezone.utc).isoformat(),
                        }
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        new_count += 1

            report_lines.append(f"✅ 收集到 {new_count} 条有效信息")
            for r in useful:
                report_lines.append(f"  - {r['authorName']}: {r['text']} [{r['classification']}]")
        else:
            report_lines.append("📭 没有需要收集的有效信息。")

    except Exception as e:
        report_lines.append(f"\n❌ 扫描出错: {e}")

    return write_report(report_lines)


def _get_current_tab_ids() -> set:
    """获取当前 session 的 tab id 集合。"""
    from client import _cmd
    result = _cmd("list_tabs", {})
    tabs = result.get("data", {}).get("tabs", [])
    return {t["tabId"] for t in tabs}


def _close_extra_tabs(before_ids: set):
    """关闭新增的 tab。"""
    from client import _cmd
    after = _get_current_tab_ids()
    new_ids = after - before_ids
    for tid in new_ids:
        try:
            _cmd("close_tab", {"tabId": tid})
        except Exception:
            pass


def write_report(lines: list[str]):
    ensure_dir(REPORT_DIR)
    content = "\n".join(lines)
    filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)

    # 同时输出到 stdout（供 cron --script --no-agent 获取）
    print(content)

    # 也输出文件路径
    print(f"\n---\n报告已保存: {filepath}")


if __name__ == "__main__":
    main()
