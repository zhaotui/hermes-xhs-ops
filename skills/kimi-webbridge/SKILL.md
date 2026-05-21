     1|     1|---
     2|     2|name: kimi-webbridge
     3|     3|description: |
     4|     4|  Kimi WebBridge lets an AI running in WSL2 control the user's real Windows browser through the local WebBridge daemon. Use it for browser navigation, clicking, filling forms, reading page structure, screenshots, uploads, and web tasks that need the user's real login session.
     5|     5|---
     6|     6|
     7|     7|# Kimi WebBridge For WSL2
     8|     8|
     9|     9|Kimi WebBridge controls the user's real browser through a Windows daemon and browser extension. In this setup Hermes runs in WSL2, while the daemon runs on Windows.
    10|    10|
    11|    11|## Important Mental Model
    12|    12|
    13|    13|- The browser session is real and may already be logged in.
    14|    14|- WebBridge actions are sent by HTTP POST to the Windows host daemon.
    15|    15|- Prefer semantic page snapshots over screenshots or CSS class guessing.
    16|    16|- Public or irreversible actions, such as posting, deleting, paying, or submitting forms, require explicit user confirmation before the final click.
    17|    17|
    18|    18|## Resolve The Daemon URL
    19|    19|
    20|    20|From WSL2, `127.0.0.1` usually means WSL itself, not Windows. Resolve the Windows host gateway dynamically:
    21|    21|
    22|    22|```bash
    23|    23|WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
    24|    24|WEBBRIDGE="http://${WIN_HOST}:10086/command"
    25|    25|```
    26|    26|
    27|    27|If dynamic resolution is unavailable and the user has confirmed a fixed gateway, use that fixed address. Do not hard-code `172.26.240.1` unless it is known to be correct for this machine.
    28|    28|
    29|    29|## Health Check
    30|    30|
    31|    31|Always do a cheap health check before browser work:
    32|    32|
    33|    33|```bash
    34|    34|WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
    35|    35|curl -s "http://${WIN_HOST}:10086/status"
    36|    36|```
    37|    37|
    38|    38|Healthy means the daemon is running and the extension is connected. If the status endpoint is unavailable, try a harmless command such as `list_tabs`. If the daemon or extension is not connected, stop and ask the user to start or reconnect Kimi WebBridge.
    39|    39|
    40|    40|Do not change Hermes approval or sandbox settings from inside the skill. If curl is blocked by the agent runtime, report the block and ask the user to allow WebBridge calls.
    41|    41|
    42|    42|## Command Format
    43|    43|
    44|    44|All commands are POST requests to `/command`:
    45|    45|
    46|    46|```bash
    47|    47|curl -s -X POST "$WEBBRIDGE" \
    48|    48|  -H 'Content-Type: application/json' \
    49|    49|  -d '{"action":"navigate","args":{"url":"https://example.com","newTab":true},"session":"example"}'
    50|    50|```
    51|    51|
    52|    52|Use a stable `session` name per task, for example `xiaohongshu-publish`. Reuse the same session for later `snapshot`, `click`, `fill`, and `evaluate` calls.
    53|    53|
    54|    54|## Tools
    55|    55|
    56|    56|| Action | Args | Use |
    57|    57||---|---|---|
    58|    58|| `navigate` | `url`, `newTab`, `group_title` | Open a URL. Use `newTab:true` for the first navigation in a task. |
    59|    59|| `find_tab` | `url`, `active` | Reuse an already open tab. Use when the user says to operate on the current/open page. |
    60|    60|| `snapshot` | none | Read accessibility tree: roles, names, values, and `@e` refs. Primary way to understand pages. |
    61|    61|| `click` | `selector` | Click an `@e` ref or CSS selector. Text alone is not a valid selector. |
    62|    62|| `fill` | `selector`, `value` | Fill input, textarea, or contenteditable elements. |
    63|    63|| `evaluate` | `code` | Run JS in the top page. Use for DOM inspection or events when snapshot/fill/click are not enough. |
    64|    64|| `upload` | `selector`, `files` | Upload files using WSL-visible paths. |
    65|    65|| `screenshot` | `format`, `quality`, `selector` | Avoid direct API for full page screenshots; use helper script. |
    66|    66|| `save_as_pdf` | print args | Save current page as PDF. |
    67|    67|| `list_tabs` | none | Inspect browser tabs. |
    68|    68|| `close_tab` | none | Close current tab for this session. |
    69|    69|| `close_session` | none | Close tabs created for this session when the user wants cleanup. |
    70|    70|
    71|    71|## Snapshot First Workflow
    72|    72|
    73|    73|Use this pattern for most tasks:
    74|    74|
    75|    75|```text
    76|    76|1. navigate or find_tab
    77|    77|2. snapshot
    78|    78|3. find the target by role/name/value
    79|    79|4. click or fill the returned @e ref
    80|    80|5. snapshot again to verify page state
    81|    81|6. use evaluate only if refs are missing or page needs custom JS
    82|    82|```
    83|    83|
    84|    84|Example:
    85|    85|
    86|    86|```text
    87|    87|snapshot returns: button name="发布" ref="@e14"
    88|    88|click selector: @e14
    89|    89|```
    90|    90|
    91|    91|Do not use screenshots as the main control path. Screenshots are for visual confirmation when semantic structure is insufficient.
    92|    92|
    93|    93|## Evaluate Rules
    94|    94|
    95|    95|- Wrap JS in an IIFE to avoid redeclaring `const` or `let` across calls.
    96|    96|- Return compact strings, preferably `JSON.stringify(data)` without pretty printing.
    97|    97|- When searching DOM, filter for visible and enabled elements before clicking.
    98|    98|- Do not force hidden or disabled controls to submit business actions. Hidden/disabled usually means validation is failing or the real control is elsewhere.
    99|    99|
   100|   100|### Bash 传参（中文/特殊字符）
   101|   101|
   102|   102|JS 代码包含中文、单引号等特殊字符时，直接写在 curl `-d` 里会炸。必须用文件+python3 方案传参。详见 `references/evaluate-bash-escape.md`。
   103|   103|
   104|   104|Visible/enabled helper:
   105|   105|
   106|   106|```javascript
   107|   107|(() => {
   108|   108|  const isVisible = (el) => {
   109|   109|    const s = getComputedStyle(el);
   110|   110|    const r = el.getBoundingClientRect();
   111|   111|    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
   112|   112|  };
   113|   113|  return JSON.stringify(Array.from(document.querySelectorAll('button,a,[role=button],input,textarea,[contenteditable=true]')).map((el, i) => ({
   114|   114|    i,
   115|   115|    tag: el.tagName,
   116|   116|    role: el.getAttribute('role'),
   117|   117|    text: (el.innerText || el.textContent || '').trim(),
   118|   118|    value: el.value || '',
   119|   119|    placeholder: el.getAttribute('placeholder'),
   120|   120|    disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
   121|   121|    visible: isVisible(el)
   122|   122|  })));
   123|   123|})()
   124|   124|```
   125|   125|
   126|   126|## Filling Text
   127|   127|
   128|   128|Prefer `fill` first. If it fails on a framework-controlled textarea or editor, use native setters and input events.
   129|   129|
   130|   130|Textarea/input:
   131|   131|
   132|   132|```javascript
   133|   133|(() => {
   134|   134|  const el = document.querySelector('textarea[placeholder="输入标题"], input[placeholder="输入标题"]');
   135|   135|  const value = '标题内容';
   136|   136|  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
   137|   137|  Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
   138|   138|  el.dispatchEvent(new Event('input', { bubbles: true }));
   139|   139|  el.dispatchEvent(new Event('change', { bubbles: true }));
   140|   140|  return 'ok';
   141|   141|})()
   142|   142|```
   143|   143|
   144|   144|Contenteditable:
   145|   145|
   146|   146|```javascript
   147|   147|(() => {
   148|   148|  const editor = document.querySelector('.ProseMirror[contenteditable="true"], [contenteditable="true"]');
   149|   149|  const text = '正文内容';
   150|   150|  editor.focus();
   151|   151|  document.execCommand('selectAll', false, null);
   152|   152|  document.execCommand('insertText', false, text);
   153|   153|  editor.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
   154|   154|  return 'ok';
   155|   155|})()
   156|   156|```
   157|   157|
   158|   158|## Screenshots
   159|   159|
   160|   160|Do not call the screenshot API directly for full pages because it returns large base64 data. Use the helper script:
   161|   161|
   162|   162|```bash
   163|   163|bash ~/.hermes/skills/xhs/kimi-webbridge/scripts/screenshot.sh -s SESSION_NAME
   164|   164|```
   165|   165|
   166|   166|The helper script requires `jq`. If `jq` is not installed, fall back to a selector screenshot of the relevant area:
   167|   167|
   168|   168|```json
   169|   169|{"action":"screenshot","args":{"format":"png","quality":40,"selector":"body"},"session":"SESSION_NAME"}
   170|   170|```
   171|   171|
   172|   172|Prefer small `selector` scopes (e.g. `#app`, `.main-content`) to keep response size manageable.
   173|   173|
   174|   174|## File Uploads From WSL2
   175|   175|
   176|   176|`upload` needs paths visible from the daemon/extension flow. Prefer WSL paths under `/mnt/<drive>/...` for Windows files or copy assets to a known WSL path and verify the tool can access them. If an upload fails with path errors, ask the user for a WSL-accessible path.
   177|   177|
   178|   178|## Known Limitations
   179|   179|
   180|   180|- Sites that require trusted user events, captchas, or banking-grade protections may reject synthetic `click`/`fill`.
   181|   181|- Cross-origin iframes are not controlled from the top frame; navigate directly to the iframe URL if appropriate.
   182|   182|- `click` requires an `@e` ref or CSS selector, not plain visible text.
   183|   183|- A successful WebBridge click only means the DOM click ran; always verify the resulting page state.
   184|   184|- If a button is hidden or disabled, do not force it visible for final actions. Fix the form state first.
   185|   185|
   186|   186|### `target="_blank"` Links
   187|   187|
   188|   188|When clicking links with `target="_blank"` (common on 小红书 notification page for usernames and note thumbnails), the new tab opens **outside** the session's tab group. `list_tabs` and `find_tab` will NOT see it. The page URL won't change either.
   189|   189|
   190|   190|**Fix:** Instead of clicking, use `evaluate` to extract the `href`, then `navigate` to it directly within the session:
   191|   191|
   192|   192|```bash
   193|   193|# Get the href
   194|   194|CODE="(() => { const el = document.querySelector('your-selector'); return el ? el.href : 'not found'; })()"
   195|   195|curl ... -d '{"action":"evaluate","args":{"code":"'"$CODE"'"},"session":"xhs"}'
   196|   196|
   197|   197|# Then navigate
   198|   198|curl ... -d '{"action":"navigate","args":{"url":"<extracted_href>"},"session":"xhs"}'
   199|   199|```
   200|   200|
   201|   201|## Passing JavaScript via curl
   202|   202|
   203|   203|Single quotes, Chinese characters, and special characters in JS code cause bash escaping hell when inlined in `curl -d` JSON. Use the **file-based pattern** for any non-trivial JS:
   204|   204|
   205|   205|```bash
   206|   206|# 1. Write JS to a temp file (no escaping needed)
   207|   207|cat > /tmp/script.js << 'JSEOF'
   208|   208|(() => {
   209|   209|  // any JavaScript, even with 'quotes', Chinese 中文, regex /.../
   210|   210|  return JSON.stringify({ result: "ok" });
   211|   211|})()
   212|   212|JSEOF
   213|   213|
   214|   214|# 2. Read and pass via python3 json.dumps (handles all escaping)
   215|   215|CODE=$(cat /tmp/script.js)
   216|   216|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   217|   217|  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'xhs'}))" "$CODE")"
   218|   218|```
   219|   219|
   220|   220|This pattern handles any JS content without escape issues. Prefer it over inline `-d` when the code contains single quotes, Chinese, regex literals, or spans more than one line.
   221|   221|
   222|   222|## Site Notes
   223|   223|
   224|   224|For 小红书 long-form publishing, read `references/xiaohongshu-workflow.md` before acting. It includes the current stable flow and validation checks.
   225|   225|
   226|   226|## WebBridge 实战模式
   227|   227|
   228|   228|Common pitfalls and proven patterns: `references/webbridge-patterns.md`. Covers JSON quoting workarounds, new-tab navigation via `find_tab`, snapshot ref lifecycle, and React page click dispatching.
   229|   229|
   230|   230|## Reusable Snippets
   231|   231|
   232|   232|These are pre-verified code fragments shared by business skills (xhs-*, etc.). Use them by name — do NOT rewrite inline.
   233|   233|
   234|   234|### bash-eval
   235|   235|
   236|   236|Pass JS to `evaluate` safely (handles Chinese, quotes, regex). Write JS to temp file, then send via python3 JSON encoding.
   237|   237|
   238|   238|```bash
   239|   239|cat > /tmp/eval.js << 'JSEOF'
   240|   240|(() => { /* your JS here */ })()
   241|   241|JSEOF
   242|   242|CODE=$(cat /tmp/eval.js)
   243|   243|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   244|   244|  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'SESSION_NAME'}))" "$CODE")"
   245|   245|```
   246|   246|
   247|   247|### snippet:click-react
   248|   248|
   249|   249|Click an element on a React SPA page. Plain `.click()` won't work — must dispatch full pointer event sequence.
   250|   250|
   251|   251|```javascript
   252|   252|(() => {
   253|   253|  const el = /* get your element */;
   254|   254|  const rect = el.getBoundingClientRect();
   255|   255|  const x = rect.left + rect.width / 2;
   256|   256|  const y = rect.top + rect.height / 2;
   257|   257|  el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
   258|   258|  el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
   259|   259|  el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
   260|   260|  return 'clicked';
   261|   261|})()
   262|   262|```
   263|   263|
   264|   264|### snippet:cover-list
   265|   265|
   266|   266|List cover images on 小红书 creator note manager page. Returns `{i, src, w, h, top}` for each.
   267|   267|
   268|   268|```javascript
   269|   269|(() => {
   270|   270|  const imgs = document.querySelectorAll('img.content');
   271|   271|  const results = [];
   272|   272|  imgs.forEach((img, i) => {
   273|   273|    const rect = img.getBoundingClientRect();
   274|   274|    results.push({ i, src: img.src, w: Math.round(rect.width), h: Math.round(rect.height), top: Math.round(rect.top) });
   275|   275|  });
   276|   276|  return JSON.stringify(results);
   277|   277|})()
   278|   278|```
   279|   279|
   280|   280|### snippet:click-cover
   281|   281|
   282|   282|Click the N-th cover image (0-indexed) on 小红书 creator note manager. Opens note detail in new tab.
   283|   283|
   284|   284|```javascript
   285|   285|(() => {
   286|   286|  const img = document.querySelectorAll('img.content')[INDEX];
   287|   287|  const rect = img.getBoundingClientRect();
   288|   288|  const x = rect.left + rect.width / 2;
   289|   289|  const y = rect.top + rect.height / 2;
   290|   290|  img.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
   291|   291|  img.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
   292|   292|  img.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
   293|   293|  return 'clicked cover[' + INDEX + ']';
   294|   294|})()
   295|   295|```
   296|   296|
   297|   297|### snippet:find-tab-bind
   298|   298|
   299|   299|After clicking opens a new tab, locate and bind it to the session. Two-step: find first, then activate.
   300|   300|
   301|   301|```bash
   302|   302|# Step 1: find the new tab
   303|   303|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   304|   304|  -d '{"action":"find_tab","args":{"url":"URL_PATTERN","active":false},"session":"SESSION_NAME"}'
   305|   305|
   306|   306|# Step 2: bind (activate)
   307|   307|curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
   308|   308|  -d '{"action":"find_tab","args":{"url":"URL_PATTERN","active":true},"session":"SESSION_NAME"}'
   309|   309|```
   310|   310|
   311|   311|### snippet:position-click
   312|   312|
   313|   313|When multiple elements share the same text (e.g. multiple "回复" buttons), click the one at a specific vertical position.
   314|   314|
   315|   315|```javascript
   316|   316|(() => {
   317|   317|  const all = document.querySelectorAll('*');
   318|   318|  const targets = [];
   319|   319|  all.forEach(el => {
   320|   320|    if ((el.innerText || '') === 'TARGET_TEXT' && el.offsetParent) {
   321|   321|      targets.push({ el, top: Math.round(el.getBoundingClientRect().top) });
   322|   322|    }
   323|   323|  });
   324|   324|  targets.sort((a, b) => a.top - b.top);
   325|   325|  const target = targets[POSITION]; // 0 = topmost, last = bottommost
   326|   326|  const rect = target.el.getBoundingClientRect();
   327|   327|  const x = rect.left + rect.width / 2;
   328|   328|  const y = rect.top + rect.height / 2;
   329|   329|  target.el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
   330|   330|  target.el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
   331|   331|  target.el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
   332|   332|  return 'clicked ' + TARGET_TEXT + ' at top=' + target.top;
   333|   333|})()
   334|   334|```
   335|   335|
   336|   336|### snippet:fill-paragraph
   337|   337|
   338|   338|Fill a `P.content-input` (小红书 comment reply box). This is a paragraph element, NOT a textarea.
   339|   339|
   340|   340|```javascript
   341|   341|(() => {
   342|   342|  const el = document.querySelector('P.content-input');
   343|   343|  if (!el) return 'input not found';
   344|   344|  el.focus();
   345|   345|  el.innerText = 'REPLY_TEXT';
   346|   346|  el.dispatchEvent(new InputEvent('input', { bubbles: true }));
   347|   347|  return 'filled';
   348|   348|})()
   349|   349|```
   350|   350|
   351|   351|### snippet:click-send
   352|   352|
   353|   353|Click the "发送" button on 小红书 comment reply form. Uses the last matching button on the page.
   354|   354|
   355|   355|```javascript
   356|   356|(() => {
   357|   357|  const all = document.querySelectorAll('*');
   358|   358|  for (const el of all) {
   359|   359|    if ((el.innerText || '').trim() === '发送' && el.offsetParent && el.tagName === 'BUTTON') {
   360|   360|      el.click();
   361|   361|      return 'clicked';
   362|   362|    }
   363|   363|  }
   364|   364|  return 'not found';
   365|   365|})()
   366|   366|```
   367|   367|
   368|   368|