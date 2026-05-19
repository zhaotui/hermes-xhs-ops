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

## Reply Flow (Note Detail Page)

This flow assumes you are already on the note detail page (`www.xiaohongshu.com/explore/...`). If not, follow `xhs-read-comments` "View Note Detail" flow first.

### 1. Find the Commenter's Reply Button

"回复" text appears for EVERY comment. Must click the correct one — use position matching:

```javascript
(() => {
  const all = document.querySelectorAll('*');
  const replyEls = [];
  all.forEach(el => {
    if ((el.innerText || '') === '回复' && el.offsetParent) {
      replyEls.push({el, top: Math.round(el.getBoundingClientRect().top)});
    }
  });
  // Sort by vertical position, take the LAST one (bottom-most = target commenter)
  replyEls.sort((a, b) => a.top - b.top);
  const target = replyEls[replyEls.length - 1];
  const rect = target.el.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  target.el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
  target.el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
  target.el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
  return 'clicked reply at top=' + target.top;
})()
```

### 2. Fill Reply Text

The reply input is a `P.content-input` (paragraph, not textarea). Use native setters:

```javascript
(() => {
  const el = document.querySelector('P.content-input');
  if (!el) return 'input not found';
  el.focus();
  el.innerText = '回复内容';
  el.dispatchEvent(new InputEvent('input', { bubbles: true }));
  return 'filled';
})()
```

### 3. Click Send

The "发送" button appears after the input. Click the last one on the page:

```javascript
(() => {
  const all = document.querySelectorAll('*');
  for (const el of all) {
    if ((el.innerText || '').trim() === '发送' && el.offsetParent && el.tagName === 'BUTTON') {
      el.click();
      return 'clicked';
    }
  }
  return 'not found';
})()
```

### 4. Verify

Wait 2s, check page content for your reply text next to the target commenter's name.

## Pitfalls

- **Clicking the wrong "回复"**: Each comment has a "回复" text. The bottom-most one corresponds to the last commenter. Always sort by vertical position and pick the last one.
- **Input is a paragraph, not textarea**: Use `el.innerText = '...'` not `el.value`.
- **Reply appears as nested**: A successful reply shows as `momo 作者\n回复内容\n刚刚` immediately below the target comment.
- Do NOT reply from the notification page — it doesn't show whether you already replied.
- Always verify the reply landed on the correct commenter.

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
