---
name: xhs-publish-post
description: Use Kimi WebBridge to publish a Xiaohongshu long-form post from a user goal.
---

# XHS Publish Post

Use this skill only for creating and publishing a Xiaohongshu long-form post.

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
  "goal": "任务目标",
  "visibility": "private",
  "autoPublish": true
}
```

## Publish Post

1. Generate natural Chinese content from the user's goal:

```json
{
  "xhsTitle": "30字以内标题",
  "longBody": "正文",
  "publishDescription": "20字以内描述"
}
```

2. Open creator publish page:

```text
https://creator.xiaohongshu.com/publish/publish?source=official
```

3. Switch to `写长文` with JS:

```javascript
(() => {
  const tabs = Array.from(document.querySelectorAll('div.creator-tab'));
  const target = tabs.find(el =>
    (el.innerText || el.textContent || '').trim() === '写长文' &&
    getComputedStyle(el).display !== 'none' &&
    getComputedStyle(el).visibility !== 'hidden' &&
    el.getBoundingClientRect().width > 0
  );
  if (!target) return JSON.stringify({ ok: false });
  target.click();
  return JSON.stringify({ ok: true });
})()
```

4. Click `新的创作`.
5. Fill title and body.
6. Click `一键排版`.
7. Click `下一步`.
8. Fill `publishDescription`.
9. If `visibility=private`, click `仅自己可见`.
10. If `autoPublish=true`, click snapshot button `发布`.
11. Success when URL contains `published=true`.

If any key button cannot be found, stop and report the current page state.

## Output

End with:

```text
发帖结果：
标题：
可见范围：
状态：
当前页面：
```

## Hard Rules

- Do not bypass captcha.
- Do not invent publish success.
- Stop when WebBridge is unreachable.
