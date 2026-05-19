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

Open:

```text
https://www.xiaohongshu.com/notification
```

Use `评论和@`.

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
    "index": 0,
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

## Hard Rules

- Do not open profiles.
- Do not collect profile bio, followers, likes, or unrelated data.
- Stop when WebBridge is unreachable.
