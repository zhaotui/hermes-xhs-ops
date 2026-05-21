     1|---
     2|name: kimi-webbridge
     3|description: |
     4|  Kimi WebBridge lets an AI running in WSL2 control the user's real Windows browser through the local WebBridge daemon. Use it for browser navigation, clicking, filling forms, reading page structure, screenshots, uploads, and web tasks that need the user's real login session.
     5|---
     6|
     7|# Kimi WebBridge For WSL2
     8|
     9|Kimi WebBridge controls the user's real browser through a Windows daemon and browser extension. In this setup Hermes runs in WSL2, while the daemon runs on Windows.
    10|
    11|## Important Mental Model
    12|
    13|- The browser session is real and may already be logged in.
    14|- WebBridge actions are sent by HTTP POST to the Windows host daemon.
    15|- Prefer semantic page snapshots over screenshots or CSS class guessing.
    16|- Public or irreversible actions, such as posting, deleting, paying, or submitting forms, require explicit user confirmation before the final click.
    17|
    18|## Resolve The Daemon URL
    19|
    20|From WSL2, `127.0.0.1` usually means WSL itself, not Windows. Resolve the Windows host gateway dynamically:
    21|
    22|```bash
    23|WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
    24|WEBBRIDGE="http://${WIN_HOST}:10086/command"
    25|```
    26|
    27|If dynamic resolution is unavailable and the user has confirmed a fixed gateway, use that fixed address. Do not hard-code `172.26.240.1` unless it is known to be correct for this machine.
    28|
    29|## Health Check
    30|
    31|Always do a cheap health check before browser work:
    32|
    33|```bash
    34|WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
    35|curl -s "http://${WIN_HOST}:10086/status"
    36|```
    37|
    38|Healthy means the daemon is running and the extension is connected. If the status endpoint is unavailable, try a harmless command such as `list_tabs`. If the daemon or extension is not connected, stop and ask the user to start or reconnect Kimi WebBridge.
    39|
    40|Do not change Hermes approval or sandbox settings from inside the skill. If curl is blocked by the agent runtime, report the block and ask the user to allow WebBridge calls.
    41|
    42|## Command Format
    43|
    44|All commands are POST requests to `/command`:
    45|
    46|```bash
    47|curl -s -X POST "$WEBBRIDGE" \
    48|  -H 'Content-Type: application/json' \
    49|  -d '{"action":"navigate","args":{"url":"https://example.com","newTab":true},"session":"example"}'
    50|```
    51|
    52|Use a stable `session` name per task, for example `xiaohongshu-publish`. Reuse the same session for later `snapshot`, `click`, `fill`, and `evaluate` calls.
    53|
    54|## Tools
    55|
    56|| Action | Args | Use |
    57||---|---|---|
    58|| `navigate` | `url`, `newTab`, `group_title` | Open a URL. Use `newTab:true` for the first navigation in a task. |
    59|| `find_tab` | `url`, `active` | Reuse an already open tab. Use when the user says to operate on the current/open page. |
    60|| `snapshot` | none | Read accessibility tree: roles, names, values, and `@e` refs. Primary way to understand pages. |
    61|| `click` | `selector` | Click an `@e` ref or CSS selector. Text alone is not a valid selector. |
    62|| `fill` | `selector`, `value` | Fill input, textarea, or contenteditable elements. |
    63|| `evaluate` | `code` | Run JS in the top page. Use for DOM inspection or events when snapshot/fill/click are not enough. |
    64|| `upload` | `selector`, `files` | Upload files using WSL-visible paths. |
    65|| `screenshot` | `format`, `quality`, `selector` | Avoid direct API for full page screenshots; use helper script. |
    66|| `save_as_pdf` | print args | Save current page as PDF. |
    67|| `list_tabs` | none | Inspect browser tabs. |
    68|| `close_tab` | none | Close current tab for this session. |
    69|| `close_session` | none | Close tabs created for this session when the user wants cleanup. |
    70|
    71|## Snapshot First Workflow
    72|
    73|Use this pattern for most tasks:
    74|
    75|```text
    76|1. navigate or find_tab
    77|2. snapshot
    78|3. find the target by role/name/value
    79|4. click or fill the returned @e ref
    80|5. snapshot again to verify page state
    81|6. use evaluate only if refs are missing or page needs custom JS
    82|```
    83|
    84|Example:
    85|
    86|```text
    87|snapshot returns: button name="发布" ref="@e14"
    88|click selector: @e14
    89|```
    90|
    91|Do not use screenshots as the main control path. Screenshots are for visual confirmation when semantic structure is insufficient.
    92|
    93|## Evaluate Rules
    94|
    95|- Wrap JS in an IIFE to avoid redeclaring `const` or `let` across calls.
    96|- Return compact strings, preferably `JSON.stringify(data)` without pretty printing.
    97|- When searching DOM, filter for visible and enabled elements before clicking.
    98|- Do not force hidden or disabled controls to submit business actions. Hidden/disabled usually means validation is failing or the real control is elsewhere.
    99|
   100|### Bash 传参（中文/特殊字符）
   101|
   102|JS 代码包含中文、单引号等特殊字符时，直接写在 curl `-d` 里会炸。必须用文件+python3 方案传参。详见 `references/evaluate-bash-escape.md`。
   103|
   104|Visible/enabled helper:
   105|
   106|```javascript
   107|(() => {
   108|  const isVisible = (el) => {
   109|    const s = getComputedStyle(el);
   110|    const r = el.getBoundingClientRect();
   111|    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
   112|  };
   113|  return JSON.stringify(Array.from(document.querySelectorAll('button,a,[role=button],input,textarea,[contenteditable=true]')).map((el, i) => ({
   114|    i,
   115|    tag: el.tagName,
   116|    role: el.getAttribute('role'),
   117|    text: (el.innerText || el.textContent || '').trim(),
   118|    value: el.value || '',
   119|    placeholder: el.getAttribute('placeholder'),
   120|    disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
   121|    visible: isVisible(el)
   122|  })));
   123|})()
   124|```
   125|
   126|## Filling Text
   127|
   128|Prefer `fill` first. If it fails on a framework-controlled textarea or editor, use native setters and input events.
   129|
   130|Textarea/input:
   131|
   132|```javascript
   133|(() => {
   134|  const el = document.querySelector('textarea[placeholder="输入标题"], input[placeholder="输入标题"]');
   135|  const value = '标题内容';
   136|  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
   137|  Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
   138|  el.dispatchEvent(new Event('input', { bubbles: true }));
   139|  el.dispatchEvent(new Event('change', { bubbles: true }));
   140|  return 'ok';
   141|})()
   142|```
   143|
   144|Contenteditable:
   145|
   146|```javascript
   147|(() => {
   148|  const editor = document.querySelector('.ProseMirror[contenteditable="true"], [contenteditable="true"]');
   149|  const text = '正文内容';
   150|  editor.focus();
   151|  document.execCommand('selectAll', false, null);
   152|  document.execCommand('insertText', false, text);
   153|  editor.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
   154|  return 'ok';
   155|})()
   156|```
   157|
   158|## Screenshots
   159|
   160|Do not call the screenshot API directly for full pages because it returns large base64 data. Use the helper script:
   161|
   162|```bash
   163|bash ~/.hermes/skills/xhs/kimi-webbridge/scripts/screenshot.sh -s SESSION_NAME
   164|```
   165|
   166|The helper script requires `jq`. If `jq` is not installed, fall back to a selector screenshot of the relevant area:
   167|
   168|```json
   169|{"action":"screenshot","args":{"format":"png","quality":40,"selector":"body"},"session":"SESSION_NAME"}
   170|```
   171|
   172|Prefer small `selector` scopes (e.g. `#app`, `.main-content`) to keep response size manageable.
   173|
   174|## File Uploads From WSL2
   175|
   176|`upload` needs paths visible from the daemon/extension flow. Prefer WSL paths under `/mnt/<drive>/...` for Windows files or copy assets to a known WSL path and verify the tool can access them. If an upload fails with path errors, ask the user for a WSL-accessible path.
   177|
   178|## Known Limitations
   179|
   180|- Sites that require trusted user events, captchas, or banking-grade protections may reject synthetic `click`/`fill`.
   181|- Cross-origin iframes are not controlled from the top frame; navigate directly to the iframe URL if appropriate.
   182|- `click` requires an `@e` ref or CSS selector, not plain visible text.
   183|- A successful WebBridge click only means the DOM click ran; always verify the resulting page state.
   184|- If a button is hidden or disabled, do not force it visible for final actions. Fix the form state first.
   185|
   186|### `target="_blank"` Links
   187|
   188|When clicking links with `target="_blank"` (common on 小红书 notification page for usernames and note thumbnails), the new tab opens **outside** the session's tab group. `list_tabs` and `find_tab` will NOT see it. The page URL won't change either.
   189|
   190|**Fix:** Instead of clicking, use `evaluate` to extract the `href`, then `navigate` to it directly within the session:
   191|
   192|```bash
   193|# Get the href
   194|CODE="(() => { const el = document.querySelector('your-selector'); return el ? el.href : 'not found'; })()"
   195|curl ... -d '{"action":"evaluate","args":{"code":"'"$CODE"'"},"session":"xhs"}'
   196|
   197|# Then navigate
   198|curl ... -d '{"action":"navigate","args":{"url":"<extracted_href>"},"session":"xhs"}'
   199|```
   200|
   201|## Passing JavaScript via curl
   202|
   203|Single quotes, Chinese characters, and special characters in JS code cause bash escaping hell when inlined in `curl -d` JSON. Use the **file-based pattern** for any non-trivial JS:
   204|
   205|```bash
   206|# 1. Write JS to a temp file (no escaping needed)
   207|cat > /tmp/script.js << 'JSEOF'
   208|(() => {
   209|  // any JavaScript, even with 'quotes', Chinese 中文, regex /.../
   210|  return JSON.stringify({ result: "ok" });
   211|})()
   212|JSEOF
   213|
   214|# 2. Read and pass via python3 json.dumps (handles all escaping)
   215|CODE=$(cat /tmp/script.js)
   216|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   217|  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'xhs'}))" "$CODE")"
   218|```
   219|
   220|This pattern handles any JS content without escape issues. Prefer it over inline `-d` when the code contains single quotes, Chinese, regex literals, or spans more than one line.
   221|
   222|## Site Notes
   223|
   224|For 小红书 long-form publishing, read `references/xiaohongshu-workflow.md` before acting. It includes the current stable flow and validation checks.
   225|
   226|## WebBridge 实战模式
   227|
   228|Common pitfalls and proven patterns: `references/webbridge-patterns.md`. Covers JSON quoting workarounds, new-tab navigation via `find_tab`, snapshot ref lifecycle, and React page click dispatching.
   229|
   230|## Reusable Snippets
   231|
   232|These are pre-verified code fragments shared by business skills (xhs-*, etc.). Use them by name — do NOT rewrite inline.
   233|
   234|### bash-eval
   235|
   236|Pass JS to `evaluate` safely (handles Chinese, quotes, regex). Write JS to temp file, then send via python3 JSON encoding.
   237|
   238|```bash
   239|cat > /tmp/eval.js << 'JSEOF'
   240|(() => { /* your JS here */ })()
   241|JSEOF
   242|CODE=$(cat /tmp/eval.js)
   243|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   244|  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'SESSION_NAME'}))" "$CODE")"
   245|```
   246|
   247|### snippet:click-react
   248|
   249|Click an element on a React SPA page. Plain `.click()` won't work — must dispatch full pointer event sequence.
   250|
   251|```javascript
   252|(() => {
   253|  const el = /* get your element */;
   254|  const rect = el.getBoundingClientRect();
   255|  const x = rect.left + rect.width / 2;
   256|  const y = rect.top + rect.height / 2;
   257|  el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
   258|  el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
   259|  el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
   260|  return 'clicked';
   261|})()
   262|```
   263|
   264|### snippet:cover-list
   265|
   266|List cover images on 小红书 creator note manager page. Returns `{i, src, w, h, top}` for each.
   267|
   268|```javascript
   269|(() => {
   270|  const imgs = document.querySelectorAll('img.content');
   271|  const results = [];
   272|  imgs.forEach((img, i) => {
   273|    const rect = img.getBoundingClientRect();
   274|    results.push({ i, src: img.src, w: Math.round(rect.width), h: Math.round(rect.height), top: Math.round(rect.top) });
   275|  });
   276|  return JSON.stringify(results);
   277|})()
   278|```
   279|
   280|### snippet:click-cover
   281|
   282|Click the N-th cover image (0-indexed) on 小红书 creator note manager. Opens note detail in new tab.
   283|
   284|```javascript
   285|(() => {
   286|  const img = document.querySelectorAll('img.content')[INDEX];
   287|  const rect = img.getBoundingClientRect();
   288|  const x = rect.left + rect.width / 2;
   289|  const y = rect.top + rect.height / 2;
   290|  img.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
   291|  img.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
   292|  img.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
   293|  return 'clicked cover[' + INDEX + ']';
   294|})()
   295|```
   296|
   297|### snippet:find-tab-bind
   298|
   299|After clicking opens a new tab, locate and bind it to the session. Two-step: find first, then activate.
   300|
   301|```bash
   302|# Step 1: find the new tab
   303|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   304|  -d '{"action":"find_tab","args":{"url":"URL_PATTERN","active":false},"session":"SESSION_NAME"}'
   305|
   306|# Step 2: bind (activate)
   307|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   308|  -d '{"action":"find_tab","args":{"url":"URL_PATTERN","active":true},"session":"SESSION_NAME"}'
   309|```
   310|
   311|### snippet:position-click
   312|
   313|When multiple elements share the same text (e.g. multiple "回复" buttons), click the one at a specific vertical position.
   314|
   315|```javascript
   316|(() => {
   317|  const all = document.querySelectorAll('*');
   318|  const targets = [];
   319|  all.forEach(el => {
   320|    if ((el.innerText || '') === 'TARGET_TEXT' && el.offsetParent) {
   321|      targets.push({ el, top: Math.round(el.getBoundingClientRect().top) });
   322|    }
   323|  });
   324|  targets.sort((a, b) => a.top - b.top);
   325|  const target = targets[POSITION]; // 0 = topmost, last = bottommost
   326|  const rect = target.el.getBoundingClientRect();
   327|  const x = rect.left + rect.width / 2;
   328|  const y = rect.top + rect.height / 2;
   329|  target.el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
   330|  target.el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
   331|  target.el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
   332|  return 'clicked ' + TARGET_TEXT + ' at top=' + target.top;
   333|})()
   334|```
   335|
   336|### snippet:fill-paragraph
   337|
   338|Fill a `P.content-input` (小红书 comment reply box). This is a paragraph element, NOT a textarea.
   339|
   340|```javascript
   341|(() => {
   342|  const el = document.querySelector('P.content-input');
   343|  if (!el) return 'input not found';
   344|  el.focus();
   345|  el.innerText = 'REPLY_TEXT';
   346|  el.dispatchEvent(new InputEvent('input', { bubbles: true }));
   347|  return 'filled';
   348|})()
   349|```
   350|
   351|### snippet:click-send
   352|
   353|Click the "发送" button on 小红书 comment reply form. Uses the last matching button on the page.
   354|
   355|```javascript
   356|(() => {
   357|  const all = document.querySelectorAll('*');
   358|  for (const el of all) {
   359|    if ((el.innerText || '').trim() === '发送' && el.offsetParent && el.tagName === 'BUTTON') {
   360|      el.click();
   361|      return 'clicked';
   362|    }
   363|  }
   364|  return 'not found';
   365|})()
   366|```
   367|
   368|### snippet:switch-comment-tab
   369|
   370|Switch 小红书 notification page from "赞和收藏" to "评论和@" tab.
   371|
   372|```javascript
   373|(() => {
   374|  const spans = document.querySelectorAll("span");
   375|  for (const s of spans) {
   376|    if (s.innerText === "评论和@" && s.offsetParent !== null) { s.click(); return "clicked"; }
   377|  }
   378|  return "not found";
   379|})()
   380|```
   381|
   382|### snippet:parse-comments
   383|
   384|Extract "评论了你的笔记" items from 小红书 notification page via body text parsing (`.container` selector is unreliable).
   385|
   386|```javascript
   387|(() => {
   388|  const items = [];
   389|  const allText = document.body.innerText;
   390|  const sections = allText.split(/\n(?=\S+\n评论了你的笔记)/);
   391|  for (const section of sections) {
   392|    if (!section.includes("评论了你的笔记")) continue;
   393|    const lines = section.split("\n").map(x => x.trim()).filter(Boolean);
   394|    const authorName = lines[0] || "";
   395|    const actionIdx = lines.findIndex(x => x.startsWith("评论了你的笔记"));
   396|    if (actionIdx < 0) continue;
   397|    const timeText = lines[actionIdx].replace("评论了你的笔记", "").trim();
   398|    const commentText = lines[actionIdx + 1] || "";
   399|    if (!authorName || !commentText || commentText === "回复") continue;
   400|    items.push({ authorName, timeText, text: commentText });
   401|  }
   402|  return JSON.stringify(items);
   403|})()
   404|```
   405|