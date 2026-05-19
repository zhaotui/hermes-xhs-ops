---
name: xhs-reply-comment
description: Use Kimi WebBridge to reply to Xiaohongshu comments on note detail page.
---

# XHS Reply Comment

Use this skill for replying to Xiaohongshu comments on the note detail page (NOT the notification page).

> **Prerequisite:** Load `kimi-webbridge` skill for WebBridge setup and snippet library.
> All snippets referenced below are defined in kimi-webbridge `## Reusable Snippets`.

## Input

```json
{
  "authorName": "昵称",
  "commentText": "评论原文",
  "replyText": "回复内容"
}
```

## Reply Flow

> **Must be on the note detail page** (`www.xiaohongshu.com/explore/...`).
> If not, follow `xhs-read-comments` "View Note Detail" to get there first.

1. **Click the target comment's "回复" button** — run `snippet:position-click`:
   - `TARGET_TEXT` = `"回复"`
   - `POSITION` = `targets.length - 1` (bottommost = last commenter's button)
   - **Why last:** each comment has its own "回复", the bottommost matches the last visible commenter

2. **Fill reply text** — run `snippet:fill-paragraph`:
   - `REPLY_TEXT` = the reply content from input

3. **Click send** — run `snippet:click-send`

4. **Verify** — wait 2s, check page content. Reply should appear as `momo 作者\n回复内容\n刚刚` immediately below the target comment.

## Before Replying: Check Note Detail

Notification page does NOT show whether you already replied. Always:
1. Follow `xhs-read-comments` "View Note Detail" to open note detail
2. Look for your username with `作者` badge in comment list
3. Only reply if no author reply exists for that commenter

## Output

```text
回帖结果：
用户：【authorName】
评论：【commentText】
回复：【replyText】
状态：【成功/失败】
```

## Pitfalls

- **Wrong "回复" button**: Each comment has one. Use `snippet:position-click` with bottommost position.
- **Input is P.content-input**: Use `el.innerText` not `el.value`.
- **Reply from detail page only**: Notification page doesn't support replying.
- Always verify the reply landed on the correct commenter.

## Hard Rules

- Do not reply to ignored comments or mass-message strangers
- Do not bypass captcha
- Stop if WebBridge unreachable
- Always check detail page to confirm not already replied
