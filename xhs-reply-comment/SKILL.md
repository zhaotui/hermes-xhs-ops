---
name: xhs-reply-comment
description: Use Kimi WebBridge to reply to Xiaohongshu notification comments.
---

# XHS Reply Comment

Use this skill only for replying to Xiaohongshu comments.

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
  "authorName": "昵称",
  "commentText": "评论原文",
  "replyText": "回复内容"
}
```

## Reply

Open:

```text
https://www.xiaohongshu.com/notification
```

Use `评论和@`.

Reply path:

1. Find `.container` containing `authorName`, `commentText`, and `评论了你的笔记`.
2. Click `.action-reply` inside it.
3. Wait 500ms.
4. Fill `textarea.comment-input`.
5. Click `button.submit` in the same `.comment-wrapper`.
6. Success when textarea disappears and no `失败/错误/频繁/稍后再试` appears.

## Default Reply Text

If enough information was collected:

```text
收到，我先记录下来了～
```

If useful but missing fields:

```text
收到，可以再补充一下{缺失字段}，我好记录完整～
```

## Output

End with:

```text
回帖结果：
用户：
评论：
回复：
状态：
```

## Evaluate JS: Bash Escape Pattern

`evaluate` code with Chinese characters or special chars will break in curl `-d`. Use this pattern:

```bash
cat > /tmp/xhs_eval.js << 'JSEOF'
(() => { return "your code"; })()
JSEOF
CODE=$(cat /tmp/xhs_eval.js)
curl -s -X POST "$WEBBRIDGE_BASE/command" \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'xhs'}))" "$CODE")"
```

## Before Replying: Check Note Detail

The notification page does NOT show whether you already replied. To avoid double-replying:

1. Follow the `xhs-read-comments` "View Note Detail" flow to open the note detail page.
2. Look for your own username with `作者` badge in the comment list.
3. Only reply if no author reply exists for that commenter.

## Hard Rules

- Do not reply to ignored comments.
- Do not mass-message strangers.
- Do not bypass captcha.
- Stop when WebBridge is unreachable.
- Always check the note detail page to confirm you haven't already replied.
