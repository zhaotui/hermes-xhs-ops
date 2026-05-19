---
name: xhs-read-comments
description: Use Kimi WebBridge to open Xiaohongshu notifications and extract note comments.
---

# XHS Read Comments

Use this skill for reading Xiaohongshu comments and viewing note detail pages.

> **Prerequisite:** Load `kimi-webbridge` skill for WebBridge setup, snippet library, and API reference.
> All code snippets below are defined in kimi-webbridge `## Reusable Snippets`.

## Setup

1. Load `kimi-webbridge`, resolve `$WEBBRIDGE`, health check.
2. Session name: `xhs`.

## Read Comments (Notification Page)

1. Navigate to `https://www.xiaohongshu.com/notification`
2. Run `snippet:switch-comment-tab` (page defaults to "赞和收藏")
3. Wait 2s, run `snippet:parse-comments` to extract comment items
4. Output JSON + Chinese summary

## View Note Detail (Full Context)

Use when you need to see the complete note page with all comments and author replies.

1. Navigate to creator note manager:
   ```
   https://creator.xiaohongshu.com/new/note-manager?source=official
   ```
2. Run `snippet:cover-list` to list all cover images with index and position
3. **Skip "仅自己可见" notes** — they cannot open detail pages
4. Run `snippet:click-cover` with the target `INDEX` (0-indexed)
5. Wait 2s, run `snippet:find-tab-bind` with `URL_PATTERN="www.xiaohongshu.com"`
6. Verify with `evaluate`: `window.location.href` should show `explore/...`

### Check If Already Replied

Look for `作者` badge next to a username — that's your reply. Notification page alone cannot tell.

## Output

```json
[{"authorName":"昵称","timeText":"时间","text":"评论原文"}]
```

```
本次读取到 X 条评论。
```

## Pitfalls

- **仅自己可见的笔记无法打开前端详情页**
- `.container` selector does NOT work — use `snippet:parse-comments`
- Page defaults to "赞和收藏" — always switch to "评论和@"
- React SPAs need `snippet:click-react`, not plain `.click()`
- `snapshot` refs expire after re-render — re-snapshot before clicking
- New tabs need `snippet:find-tab-bind`
- Only "评论了你的笔记", ignore "回复了你的评论" and "赞了你的评论"

## Hard Rules

- Do not open profiles or collect unrelated data
- Stop if WebBridge unreachable
