---
name: xhs-read-comments
description: Use Kimi WebBridge to open Xiaohongshu notifications and extract note comments.
---

# XHS Read Comments

Use this skill only for opening Xiaohongshu notifications and reading comments.

## WebBridge

Hermes usually runs in WSL. Use this base URL first:

```bash
WEBBRIDGE_BASE="http://$(ip route | awk '/default/ {print $3; exit}'):10086"
```

Health check:

```bash
curl -s "$WEBBRIDGE_BASE/status"
```

Continue only if `running=true` and `extension_connected=true`.

If it fails, stop and tell the user WebBridge is not reachable. Do not debug networking.

Command format:

```bash
curl -s -X POST "$WEBBRIDGE_BASE/command" \
  -H 'Content-Type: application/json' \
  -d '{"action":"snapshot","args":{},"session":"xhs"}'
```

## Input

```json
{
  "limit": 20
}
```

## Read Comments

Navigate to:

```
https://www.xiaohongshu.com/notification
```

```bash
curl -s -X POST "$WEBBRIDGE_BASE/command" \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://www.xiaohongshu.com/notification"},"session":"xhs"}'
```

Switch to "评论和@" tab (page defaults to "赞和收藏"):

```javascript
(() => {
  const spans = document.querySelectorAll("span");
  for (const s of spans) {
    if (s.innerText === "评论和@" && s.offsetParent !== null) { s.click(); return "clicked"; }
  }
  return "not found";
})()
```

Wait 2s, then extract comments via `document.body.innerText` parsing (`.container` CSS selector does NOT work):

```javascript
(() => {
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
})()
```

## Output

Always output comments as JSON first, then a Chinese summary:

```json
[
  {
    "authorName": "昵称",
    "timeText": "时间",
    "text": "评论原文"
  }
]
```

```text
本次读取到 X 条评论。
```

If none:

```text
本次没有读取到评论。
```

## View Note Detail (Full Context)

The notification page only shows comment text, NOT the full note context or whether the author has already replied. To view the complete note with all comments and replies:

### Navigate from Creator Center

1. Open note manager:
```bash
curl -s -X POST "$WEBBRIDGE_BASE/command" \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://creator.xiaohongshu.com/new/note-manager?source=official"},"session":"xhs"}'
```

2. Wait 3s, find cover images (`img.content`):
```javascript
(() => {
  const imgs = document.querySelectorAll('img.content');
  const results = [];
  imgs.forEach((img, i) => {
    const rect = img.getBoundingClientRect();
    results.push({ i, src: img.src, w: Math.round(rect.width), h: Math.round(rect.height), top: Math.round(rect.top) });
  });
  return JSON.stringify(results);
})()
```

3. Click the target cover image. **Must dispatch synthetic events** — React SPA, plain `.click()` or WebBridge `click` won't navigate:
```javascript
(() => {
  const img = document.querySelectorAll('img.content')[INDEX];
  const rect = img.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  img.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
  img.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
  img.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
  return 'clicked';
})()
```

4. The note opens in a **new tab** (outside session group). Use `find_tab` to locate and bind:
```bash
# Find the new tab
curl -s -X POST "$WEBBRIDGE_BASE/command" \
  -H 'Content-Type: application/json' \
  -d '{"action":"find_tab","args":{"url":"www.xiaohongshu.com","active":false},"session":"xhs"}'

# Bind to it (makes it the active tab for this session)
curl -s -X POST "$WEBBRIDGE_BASE/command" \
  -H 'Content-Type: application/json' \
  -d '{"action":"find_tab","args":{"url":"www.xiaohongshu.com","active":true},"session":"xhs"}'
```

5. Verify you're on the note page, then read content with `evaluate`.

### Check If Already Replied

On the note detail page, look for `作者` badge next to a username — that's your reply. The notification page alone cannot tell you if you've replied.

## Evaluate JS: Bash Escape Pattern

`evaluate` code with Chinese characters, quotes, or special chars will break when passed directly in curl `-d`. Always use this pattern:

```bash
# 1. Write JS to file
cat > /tmp/xhs_eval.js << 'JSEOF'
(() => { return "your code here"; })()
JSEOF

# 2. Read and send via python3 for safe JSON encoding
CODE=$(cat /tmp/xhs_eval.js)
curl -s -X POST "$WEBBRIDGE_BASE/command" \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'xhs'}))" "$CODE")"
```

## Pitfalls

- **仅自己可见的笔记无法打开前端详情页**。只有已发布的笔记（无"仅自己可见"标签）才能点击封面图跳转到 `www.xiaohongshu.com/explore/...`。
- Notification page does NOT show note thumbnails as clickable links — only comment text and user info. To see full context, use the Note Detail flow above.
- `.container` CSS selector does NOT match notification items. Use `document.body.innerText` parsing instead.
- Page defaults to "赞和收藏" — always switch to "评论和@" first.
- WebBridge `click` action often fails on React SPAs. Use `evaluate` with `.click()` or dispatch `PointerEvent` + `MouseEvent` instead.
- `snapshot` `@e` refs become stale after page re-render — always re-snapshot before clicking.
- New tabs opened by clicks are NOT automatically tracked by the session. Use `find_tab` to locate and bind them.
- Only "评论了你的笔记" items are new comments. "回复了你的评论" and "赞了你的评论" are secondary interactions.
- `window.location.href` may not reflect client-side navigation — verify page content, not just URL.
- Do NOT confirm reply status from notification page alone — check the note detail page.

## Hard Rules

- Do not open profiles.
- Do not collect profile bio, followers, likes, or unrelated data.
- Stop when WebBridge is unreachable.
- Only extract items containing "评论了你的笔记", ignore "回复了你的评论" and "赞了你的评论".
