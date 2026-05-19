# 小红书低智长文发布流程

This workflow is intentionally rigid. Follow it exactly. Do not invent alternate paths unless this document says to.

This exact path was tested end-to-end with Kimi WebBridge. Final publish succeeded when the publish settings page had:

```text
title = 新人报道，今天开始记录生活
description = 新人第一篇，记录日常
visibility = 仅自己可见
snapshot publish ref = @e14
final URL = https://creator.xiaohongshu.com/publish/publish?source=official&published=true
```

## Absolute Rules

1. Do not click hidden publish buttons.
2. Do not force `display:none`, `disabled=false`, or fake-enable publish buttons.
3. Do not use DOM visibility to reject a publish button returned by `snapshot`.
4. If `snapshot()` returns `button name="发布" ref="@e..."`, that ref is the final publish button.
5. Do not keep trying random click events when a tab does not switch.
6. Final `发布` click requires explicit user confirmation unless the user already explicitly asked to test publishing.
7. If a required state cannot be confirmed, stop and report the exact missing state.

## WebBridge Call Shape

Use one session name throughout:

```text
session = "xiaohongshu-publish"
```

Command body examples:

```json
{"action":"snapshot","args":{},"session":"xiaohongshu-publish"}
```

```json
{"action":"click","args":{"selector":"@e14"},"session":"xiaohongshu-publish"}
```

```json
{"action":"evaluate","args":{"code":"(() => 'ok')()"},"session":"xiaohongshu-publish"}
```

## Fixed Content

```text
标题:
新人报道，今天开始记录生活

长文正文:
第一次在这里发帖，先认真打个招呼。

以后想随手记录一些日常：看到的风景、吃到的好吃的、还有一点点生活里的小心情。

今天就从这篇开始。

发布描述:
新人第一篇，记录日常
```

Do not add hashtags unless the user explicitly asks.

## Tested Deterministic Path

The URL parameter `type=longresource` may still load the video page. Use it only as the entry URL, then switch to the real visible long-form tab with the exact JS below.

### 1. Health Check

From WSL2:

```bash
WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
WEBBRIDGE="http://${WIN_HOST}:10086/command"
curl -s "http://${WIN_HOST}:10086/status"
```

If `/status` does not work, use:

```bash
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d '{"action":"list_tabs","args":{},"session":"xiaohongshu-publish"}'
```

If WebBridge is not connected, stop.

### 2. Open Creator Page

```text
navigate("https://creator.xiaohongshu.com/publish/publish?source=official&type=longresource", newTab=true, session="xiaohongshu-publish")
sleep(3000)
snapshot(session="xiaohongshu-publish")
```

Expected page may still show video upload. That is normal.

### 3. Switch To Long-Form Tab

Do not click `data-hp-kind="creator-tab-写长文"` overlays. They can be invisible instrumentation layers and may not switch the tab.

Run exactly this JS with `evaluate`:

```javascript
(() => {
  const tabs = Array.from(document.querySelectorAll('div.creator-tab'));
  const target = tabs.find(el =>
    (el.innerText || el.textContent || '').trim() === '写长文' &&
    el.getAttribute('aria-hidden') !== 'true' &&
    getComputedStyle(el).display !== 'none' &&
    getComputedStyle(el).visibility !== 'hidden' &&
    el.getBoundingClientRect().width > 0 &&
    el.getBoundingClientRect().height > 0
  );
  if (!target) return JSON.stringify({ ok: false, reason: 'no real visible long-form tab' });
  target.scrollIntoView({ block: 'center', inline: 'center' });
  ['pointerdown', 'mousedown', 'mouseup', 'pointerup', 'click'].forEach(type => {
    target.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
  });
  return JSON.stringify({ ok: true, className: String(target.className) });
})()
```

Then:

```text
sleep(1000)
snapshot()
```

Required:

```text
button name="新的创作"
```

If `新的创作` does not appear, stop. Do not try more tab-click variants.

### 4. Click New Creation

Use snapshot ref only:

```text
find button name="新的创作" ref="@e..."
click("@e...")
sleep(2000)
snapshot()
```

Required editor state:

```text
textbox name="输入标题"
字数：0
button name="一键排版"
```

If editor does not appear, stop.

### 5. Fill Title And Body

Run exactly with `evaluate`:

```javascript
(() => {
  const title = '新人报道，今天开始记录生活';
  const body = '第一次在这里发帖，先认真打个招呼。\n\n以后想随手记录一些日常：看到的风景、吃到的好吃的、还有一点点生活里的小心情。\n\n今天就从这篇开始。';

  const titleEl = document.querySelector('textarea[placeholder="输入标题"], input[placeholder="输入标题"]');
  if (!titleEl) return JSON.stringify({ ok: false, step: 'title' });
  const proto = titleEl instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, 'value').set.call(titleEl, title);
  titleEl.dispatchEvent(new Event('input', { bubbles: true }));
  titleEl.dispatchEvent(new Event('change', { bubbles: true }));

  const editor = document.querySelector('.ProseMirror[contenteditable="true"], .ProseMirror, [contenteditable="true"]');
  if (!editor) return JSON.stringify({ ok: false, step: 'editor' });
  editor.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, body);
  editor.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: body }));

  return JSON.stringify({ ok: true });
})()
```

Then:

```text
snapshot()
```

Must contain:

```text
新人报道，今天开始记录生活
第一次在这里发帖
字数：61
```

If not, stop.

### 6. One-Click Layout

Use snapshot ref:

```text
click(button name="一键排版" ref)
sleep(3000)
snapshot()
```

Required:

```text
button name="下一步"
```

If snapshot says `笔记图片生成中，请稍后`, wait 2 seconds and snapshot again. Repeat up to 10 times. If still generating, stop.

### 7. Next Step

Use snapshot ref:

```text
click(button name="下一步" ref)
sleep(3000)
snapshot()
```

Required publish settings page:

```text
textbox name="填写标题会有更多赞哦"
textbox for description
公开可见
button name="发布" ref="@e..."
```

If not present, stop.

### 8. Fill Description

Prefer snapshot `textbox` ref whose placeholder/value area is the description editor. In the tested run it was `@e2`.

```text
fill(description_ref, "新人第一篇，记录日常")
sleep(1000)
snapshot()
```

Required:

```text
新人第一篇，记录日常
10/1000
```

If not present, stop.

### 9. Set Only Me Visible

Do not rely on opening the dropdown first. The option nodes already exist in DOM. Click the actual option directly with `evaluate`:

```javascript
(() => {
  const options = Array.from(document.querySelectorAll('.custom-option'));
  const target = options.find(el => (el.innerText || el.textContent || '').trim() === '仅自己可见');
  if (!target) return JSON.stringify({ ok: false, reason: 'no option' });
  target.click();
  return JSON.stringify({ ok: true, className: String(target.className), text: (target.innerText || target.textContent || '').trim() });
})()
```

Then:

```text
sleep(1000)
snapshot()
```

Required:

```text
仅自己可见
```

If snapshot still shows `公开可见`, stop. Do not publish.

### 10. Final Validation

Run snapshot.

Required:

```text
title contains 新人报道，今天开始记录生活
description contains 新人第一篇，记录日常
snapshot contains 仅自己可见
snapshot contains button name="发布" ref="@e..."
no text like 笔记图片生成中
no over-limit counter like 31 / 20
```

Important:

```text
If snapshot contains button name="发布" ref="@e14", keep @e14.
Do not run DOM hidden checks on @e14.
Do not restart.
Do not click a DOM node with class btnDisabled/post.
```

### 11. Ask User Unless Already Authorized

If the user did not explicitly authorize final publish, say:

```text
草稿已准备好，并设置为仅自己可见。回复“发布”后我再点击最终发布按钮。
```

Wait.

If the user already said to test publishing because it is `仅自己可见`, continue to final click.

### 12. Final Click

Only click the snapshot publish ref, for example `@e14`:

```text
click(snapshot_publish_ref)
sleep(5000)
snapshot()
```

The tested successful WebBridge click response looked like:

```json
{"success":true,"tag":"BUTTON","text":"发布"}
```

Success:

```text
current URL contains published=true
```

Tested successful URL:

```text
https://creator.xiaohongshu.com/publish/publish?source=official&published=true
```

If not, report visible error text. Do not retry by force-clicking hidden DOM nodes.

## Ref Lifecycle Rule

Refs (`@e1`, `@e2`, ...) are snapshot-specific. They change after every page state transition — clicking a button, navigating, or waiting for async render all invalidate previous refs. Always re-snapshot and re-query refs after each step. Never reuse a ref from a previous snapshot, even if the button name is the same.

If a `click(@eN)` returns `"text":""` (empty text) but the button name you expected is non-empty, the ref is stale. The click landed on a different element that now occupies that ref slot. Re-snapshot and find the correct ref.

## What Not To Do

Never do these:

```javascript
btn.style.display = '';
btn.disabled = false;
btn.click();
```

Never use this target for the long-form tab:

```text
data-hp-kind="creator-tab-写长文"
```

Correct tab target:

```text
div.creator-tab where text == 写长文 and aria-hidden != true
```

Never do this:

```text
snapshot found 发布 ref, but DOM says hidden, so restart
```

Correct behavior:

```text
snapshot found 发布 ref -> validate fields -> ask user or use prior authorization -> click(ref)
```
