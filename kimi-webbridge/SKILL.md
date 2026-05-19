---
name: kimi-webbridge
description: |
  Kimi WebBridge lets an AI running in WSL2 control the user's real Windows browser through the local WebBridge daemon. Use it for browser navigation, clicking, filling forms, reading page structure, screenshots, uploads, and web tasks that need the user's real login session.
---

# Kimi WebBridge For WSL2

Kimi WebBridge controls the user's real browser through a Windows daemon and browser extension. In this setup Hermes runs in WSL2, while the daemon runs on Windows.

## Important Mental Model

- The browser session is real and may already be logged in.
- WebBridge actions are sent by HTTP POST to the Windows host daemon.
- Prefer semantic page snapshots over screenshots or CSS class guessing.
- Public or irreversible actions, such as posting, deleting, paying, or submitting forms, require explicit user confirmation before the final click.

## Resolve The Daemon URL

From WSL2, `127.0.0.1` usually means WSL itself, not Windows. Resolve the Windows host gateway dynamically:

```bash
WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
WEBBRIDGE="http://${WIN_HOST}:10086/command"
```

If dynamic resolution is unavailable and the user has confirmed a fixed gateway, use that fixed address. Do not hard-code `172.26.240.1` unless it is known to be correct for this machine.

## Health Check

Always do a cheap health check before browser work:

```bash
WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
curl -s "http://${WIN_HOST}:10086/status"
```

Healthy means the daemon is running and the extension is connected. If the status endpoint is unavailable, try a harmless command such as `list_tabs`. If the daemon or extension is not connected, stop and ask the user to start or reconnect Kimi WebBridge.

Do not change Hermes approval or sandbox settings from inside the skill. If curl is blocked by the agent runtime, report the block and ask the user to allow WebBridge calls.

## Command Format

All commands are POST requests to `/command`:

```bash
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://example.com","newTab":true},"session":"example"}'
```

Use a stable `session` name per task, for example `xiaohongshu-publish`. Reuse the same session for later `snapshot`, `click`, `fill`, and `evaluate` calls.

## Tools

| Action | Args | Use |
|---|---|---|
| `navigate` | `url`, `newTab`, `group_title` | Open a URL. Use `newTab:true` for the first navigation in a task. |
| `find_tab` | `url`, `active` | Reuse an already open tab. Use when the user says to operate on the current/open page. |
| `snapshot` | none | Read accessibility tree: roles, names, values, and `@e` refs. Primary way to understand pages. |
| `click` | `selector` | Click an `@e` ref or CSS selector. Text alone is not a valid selector. |
| `fill` | `selector`, `value` | Fill input, textarea, or contenteditable elements. |
| `evaluate` | `code` | Run JS in the top page. Use for DOM inspection or events when snapshot/fill/click are not enough. |
| `upload` | `selector`, `files` | Upload files using WSL-visible paths. |
| `screenshot` | `format`, `quality`, `selector` | Avoid direct API for full page screenshots; use helper script. |
| `save_as_pdf` | print args | Save current page as PDF. |
| `list_tabs` | none | Inspect browser tabs. |
| `close_tab` | none | Close current tab for this session. |
| `close_session` | none | Close tabs created for this session when the user wants cleanup. |

## Snapshot First Workflow

Use this pattern for most tasks:

```text
1. navigate or find_tab
2. snapshot
3. find the target by role/name/value
4. click or fill the returned @e ref
5. snapshot again to verify page state
6. use evaluate only if refs are missing or page needs custom JS
```

Example:

```text
snapshot returns: button name="发布" ref="@e14"
click selector: @e14
```

Do not use screenshots as the main control path. Screenshots are for visual confirmation when semantic structure is insufficient.

## Evaluate Rules

- Wrap JS in an IIFE to avoid redeclaring `const` or `let` across calls.
- Return compact strings, preferably `JSON.stringify(data)` without pretty printing.
- When searching DOM, filter for visible and enabled elements before clicking.
- Do not force hidden or disabled controls to submit business actions. Hidden/disabled usually means validation is failing or the real control is elsewhere.

### Bash 传参（中文/特殊字符）

JS 代码包含中文、单引号等特殊字符时，直接写在 curl `-d` 里会炸。必须用文件+python3 方案传参。详见 `references/evaluate-bash-escape.md`。

Visible/enabled helper:

```javascript
(() => {
  const isVisible = (el) => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
  };
  return JSON.stringify(Array.from(document.querySelectorAll('button,a,[role=button],input,textarea,[contenteditable=true]')).map((el, i) => ({
    i,
    tag: el.tagName,
    role: el.getAttribute('role'),
    text: (el.innerText || el.textContent || '').trim(),
    value: el.value || '',
    placeholder: el.getAttribute('placeholder'),
    disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
    visible: isVisible(el)
  })));
})()
```

## Filling Text

Prefer `fill` first. If it fails on a framework-controlled textarea or editor, use native setters and input events.

Textarea/input:

```javascript
(() => {
  const el = document.querySelector('textarea[placeholder="输入标题"], input[placeholder="输入标题"]');
  const value = '标题内容';
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return 'ok';
})()
```

Contenteditable:

```javascript
(() => {
  const editor = document.querySelector('.ProseMirror[contenteditable="true"], [contenteditable="true"]');
  const text = '正文内容';
  editor.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, text);
  editor.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
  return 'ok';
})()
```

## Screenshots

Do not call the screenshot API directly for full pages because it returns large base64 data. Use the helper script:

```bash
bash /root/.hermes/skills/browser/kimi-webbridge/scripts/screenshot.sh -s SESSION_NAME
```

The helper script requires `jq`. If `jq` is not installed, fall back to a selector screenshot of the relevant area:

```json
{"action":"screenshot","args":{"format":"png","quality":40,"selector":"body"},"session":"SESSION_NAME"}
```

Prefer small `selector` scopes (e.g. `#app`, `.main-content`) to keep response size manageable.

## File Uploads From WSL2

`upload` needs paths visible from the daemon/extension flow. Prefer WSL paths under `/mnt/<drive>/...` for Windows files or copy assets to a known WSL path and verify the tool can access them. If an upload fails with path errors, ask the user for a WSL-accessible path.

## Known Limitations

- Sites that require trusted user events, captchas, or banking-grade protections may reject synthetic `click`/`fill`.
- Cross-origin iframes are not controlled from the top frame; navigate directly to the iframe URL if appropriate.
- `click` requires an `@e` ref or CSS selector, not plain visible text.
- A successful WebBridge click only means the DOM click ran; always verify the resulting page state.
- If a button is hidden or disabled, do not force it visible for final actions. Fix the form state first.

### `target="_blank"` Links

When clicking links with `target="_blank"` (common on 小红书 notification page for usernames and note thumbnails), the new tab opens **outside** the session's tab group. `list_tabs` and `find_tab` will NOT see it. The page URL won't change either.

**Fix:** Instead of clicking, use `evaluate` to extract the `href`, then `navigate` to it directly within the session:

```bash
# Get the href
CODE="(() => { const el = document.querySelector('your-selector'); return el ? el.href : 'not found'; })()"
curl ... -d '{"action":"evaluate","args":{"code":"'"$CODE"'"},"session":"xhs"}'

# Then navigate
curl ... -d '{"action":"navigate","args":{"url":"<extracted_href>"},"session":"xhs"}'
```

## Passing JavaScript via curl

Single quotes, Chinese characters, and special characters in JS code cause bash escaping hell when inlined in `curl -d` JSON. Use the **file-based pattern** for any non-trivial JS:

```bash
# 1. Write JS to a temp file (no escaping needed)
cat > /tmp/script.js << 'JSEOF'
(() => {
  // any JavaScript, even with 'quotes', Chinese 中文, regex /.../
  return JSON.stringify({ result: "ok" });
})()
JSEOF

# 2. Read and pass via python3 json.dumps (handles all escaping)
CODE=$(cat /tmp/script.js)
curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'xhs'}))" "$CODE")"
```

This pattern handles any JS content without escape issues. Prefer it over inline `-d` when the code contains single quotes, Chinese, regex literals, or spans more than one line.

## Site Notes

For 小红书 long-form publishing, read `references/xiaohongshu-workflow.md` before acting. It includes the current stable flow and validation checks.

## WebBridge 实战模式

Common pitfalls and proven patterns: `references/webbridge-patterns.md`. Covers JSON quoting workarounds, new-tab navigation via `find_tab`, snapshot ref lifecycle, and React page click dispatching.

## Reusable Snippets

These are pre-verified code fragments shared by business skills (xhs-*, etc.). Use them by name — do NOT rewrite inline.

### bash-eval

Pass JS to `evaluate` safely (handles Chinese, quotes, regex). Write JS to temp file, then send via python3 JSON encoding.

```bash
cat > /tmp/eval.js << 'JSEOF'
(() => { /* your JS here */ })()
JSEOF
CODE=$(cat /tmp/eval.js)
curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'SESSION_NAME'}))" "$CODE")"
```

### snippet:click-react

Click an element on a React SPA page. Plain `.click()` won't work — must dispatch full pointer event sequence.

```javascript
(() => {
  const el = /* get your element */;
  const rect = el.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
  el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
  el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
  return 'clicked';
})()
```

### snippet:cover-list

List cover images on 小红书 creator note manager page. Returns `{i, src, w, h, top}` for each.

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

### snippet:click-cover

Click the N-th cover image (0-indexed) on 小红书 creator note manager. Opens note detail in new tab.

```javascript
(() => {
  const img = document.querySelectorAll('img.content')[INDEX];
  const rect = img.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  img.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
  img.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
  img.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
  return 'clicked cover[' + INDEX + ']';
})()
```

### snippet:find-tab-bind

After clicking opens a new tab, locate and bind it to the session. Two-step: find first, then activate.

```bash
# Step 1: find the new tab
curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
  -d '{"action":"find_tab","args":{"url":"URL_PATTERN","active":false},"session":"SESSION_NAME"}'

# Step 2: bind (activate)
curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
  -d '{"action":"find_tab","args":{"url":"URL_PATTERN","active":true},"session":"SESSION_NAME"}'
```

### snippet:position-click

When multiple elements share the same text (e.g. multiple "回复" buttons), click the one at a specific vertical position.

```javascript
(() => {
  const all = document.querySelectorAll('*');
  const targets = [];
  all.forEach(el => {
    if ((el.innerText || '') === 'TARGET_TEXT' && el.offsetParent) {
      targets.push({ el, top: Math.round(el.getBoundingClientRect().top) });
    }
  });
  targets.sort((a, b) => a.top - b.top);
  const target = targets[POSITION]; // 0 = topmost, last = bottommost
  const rect = target.el.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  target.el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
  target.el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
  target.el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
  return 'clicked ' + TARGET_TEXT + ' at top=' + target.top;
})()
```

### snippet:fill-paragraph

Fill a `P.content-input` (小红书 comment reply box). This is a paragraph element, NOT a textarea.

```javascript
(() => {
  const el = document.querySelector('P.content-input');
  if (!el) return 'input not found';
  el.focus();
  el.innerText = 'REPLY_TEXT';
  el.dispatchEvent(new InputEvent('input', { bubbles: true }));
  return 'filled';
})()
```

### snippet:click-send

Click the "发送" button on 小红书 comment reply form. Uses the last matching button on the page.

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

### snippet:switch-comment-tab

Switch 小红书 notification page from "赞和收藏" to "评论和@" tab.

```javascript
(() => {
  const spans = document.querySelectorAll("span");
  for (const s of spans) {
    if (s.innerText === "评论和@" && s.offsetParent !== null) { s.click(); return "clicked"; }
  }
  return "not found";
})()
```

### snippet:parse-comments

Extract "评论了你的笔记" items from 小红书 notification page via body text parsing (`.container` selector is unreliable).

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
