#!/usr/bin/env python3
"""小红书长文发布脚本，供 Hermes 直接调用。

流程：
1. 打开创作页
2. 切到写长文
3. 新建创作
4. 填写标题和正文
5. 一键排版
6. 下一步
7. 填写描述
8. 发布

每一步都用 evaluate 做 DOM 验证，不依赖 snapshot 字符串，不硬编码 @e ref。
"""

import json
import argparse
import subprocess
import sys
import time


TITLE = ""
BODY = ""
DESCRIPTION = ""
VISIBILITY = "private"
AUTO_PUBLISH = True
SESSION = "xiaohongshu-auto"


WIN_HOST = subprocess.run(
    "ip route | awk '/default/ {print $3; exit}'",
    shell=True,
    capture_output=True,
    text=True,
).stdout.strip()
WB = f"http://{WIN_HOST}:10086/command"


JS_HELPERS = r"""
const visible = el => {
  if (!el) return false;
  if (el.closest('[aria-hidden="true"], [hidden]')) return false;
  const style = getComputedStyle(el);
  return style.display !== 'none' &&
    style.visibility !== 'hidden' &&
    style.opacity !== '0';
};

const textOf = el => (el.innerText || el.textContent || '').trim();

const allTextElements = () => Array.from(
  document.querySelectorAll('button, [role="button"], a, div, span, p')
).filter(visible);

const findByText = (text, options = {}) => {
  const exact = options.exact !== false;
  const items = allTextElements()
    .map(el => {
      const t = textOf(el);
      const interactive = !!el.closest('button, [role="button"], a, .btn, .button, [class*="btn"], [class*="button"]');
      const exactHit = t === text;
      const hit = exact ? exactHit : (exactHit || t.includes(text));
      return { el, t, interactive, exactHit, hit };
    })
    .filter(x => x.hit)
    .sort((a, b) => {
      if (a.exactHit !== b.exactHit) return a.exactHit ? -1 : 1;
      if (a.interactive !== b.interactive) return a.interactive ? -1 : 1;
      return a.t.length - b.t.length;
    });
  return (items[0] && items[0].el) || null;
};

const findNearestClickable = el => {
  let cur = el;
  while (cur && cur !== document.body) {
    if (
      cur.matches('button, [role="button"], a, .btn, .button, [class*="btn"], [class*="button"]') ||
      cur.onclick ||
      cur.getAttribute('tabindex') === '0'
    ) {
      return cur;
    }
    cur = cur.parentElement;
  }
  return el;
};

const findClickableByText = (text, options = {}) => {
  const el = findByText(text, options);
  if (!el) return null;
  return findNearestClickable(el);
};

const clickElement = el => {
  el.scrollIntoView({ block: 'center', inline: 'center' });
  for (const type of ['pointerdown', 'mousedown', 'mouseup', 'pointerup', 'click']) {
    el.dispatchEvent(new MouseEvent(type, {
      bubbles: true,
      cancelable: true,
      view: window
    }));
  }
};

const clickByText = (text, options = {}) => {
  const el = findClickableByText(text, options);
  if (!el) return { ok: false, reason: `未找到：${text}` };
  clickElement(el);
  return { ok: true, text };
};

const scrollDown = () => {
  const containers = Array.from(document.querySelectorAll('body, body *'))
    .filter(el => el.scrollHeight > el.clientHeight + 50)
    .sort((a, b) => (b.clientHeight * b.clientWidth) - (a.clientHeight * a.clientWidth));
  const target = containers[0] || document.scrollingElement || document.documentElement;
  target.scrollTop += Math.round((target.clientHeight || window.innerHeight) * 0.75);
  window.scrollBy(0, Math.round(window.innerHeight * 0.75));
};

const scrollToBottom = () => {
  const containers = Array.from(document.querySelectorAll('body, body *'))
    .filter(el => el.scrollHeight > el.clientHeight + 50)
    .sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));
  for (const el of containers.slice(0, 4)) {
    el.scrollTop = el.scrollHeight;
  }
  window.scrollTo(0, document.body.scrollHeight);
};

const deepQueryAll = (selector, root = document) => {
  const results = [];
  const visit = node => {
    if (!node) return;
    if (node.querySelectorAll) {
      results.push(...node.querySelectorAll(selector));
      for (const el of node.querySelectorAll('*')) {
        if (el.shadowRoot) visit(el.shadowRoot);
      }
    }
  };
  visit(root);
  return results;
};

const setNativeValue = (el, value) => {
  const proto = el instanceof HTMLTextAreaElement
    ? HTMLTextAreaElement.prototype
    : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
  setter.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
};

const fillEditable = (el, value) => {
  el.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, value);
  el.dispatchEvent(new InputEvent('input', {
    bubbles: true,
    inputType: 'insertText',
    data: value
  }));
};
"""


def wb(action, args=None):
    body = {"action": action, "args": args or {}, "session": SESSION}
    r = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            WB,
            "-H",
            "Content-Type: application/json",
            "-d",
            json.dumps(body, ensure_ascii=False),
        ],
        capture_output=True,
        text=True,
        timeout=75,
    )
    return json.loads(r.stdout)


def ev(code):
    return wb("evaluate", {"code": code})


def js(body):
    return f"""
(() => {{
{JS_HELPERS}
{body}
}})()
"""


def value(result):
    data = result.get("data", {})
    v = data.get("value", "")
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v).strip('"')


def wait_until(name, verify, timeout=18, interval=1.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = verify()
        if state is True:
            return True
        if state != "wait":
            time.sleep(interval)
            continue
        print(f"{name}处理中...", flush=True)
        time.sleep(interval)
    return False


def page_excerpt():
    r = ev(js("return document.body.innerText.slice(0, 500);"))
    return value(r)[:300]


def step(name, action, verify, timeout=18):
    print(f"{name}...", flush=True)
    result = action()
    result_value = value(result)
    if result_value:
        print(result_value[:300], flush=True)
    time.sleep(1.2)
    if not wait_until(name, verify, timeout=timeout):
        print(f"{name}失败", flush=True)
        print(f"当前页面：{page_excerpt()}", flush=True)
        sys.exit(1)
    print(f"{name}完成", flush=True)


def load_payload():
    parser = argparse.ArgumentParser(description="小红书长文发布")
    parser.add_argument("--title", default="")
    parser.add_argument("--body", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--visibility", default="")
    parser.add_argument("--session", default="")
    parser.add_argument("--auto-publish", default="")
    parser.add_argument("--json", default="")
    parser.add_argument("--stdin-json", action="store_true")
    args = parser.parse_args()

    payload = {}
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            payload.update(json.load(f))
    if args.stdin_json:
        payload.update(json.load(sys.stdin))

    if args.title:
        payload["title"] = args.title
    if args.body:
        payload["body"] = args.body
    if args.description:
        payload["description"] = args.description
    if args.visibility:
        payload["visibility"] = args.visibility
    if args.session:
        payload["session"] = args.session
    if args.auto_publish:
        payload["autoPublish"] = args.auto_publish.lower() in ("1", "true", "yes", "y")

    return payload


def parse_bool(value, default):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y")
    return bool(value)


def apply_payload(payload):
    global TITLE, BODY, DESCRIPTION, VISIBILITY, AUTO_PUBLISH, SESSION

    TITLE = str(payload.get("title") or payload.get("xhsTitle") or "").strip()
    BODY = str(payload.get("body") or payload.get("longBody") or "").strip()
    DESCRIPTION = str(
        payload.get("description") or payload.get("publishDescription") or ""
    ).strip()
    VISIBILITY = str(payload.get("visibility") or VISIBILITY).strip()
    AUTO_PUBLISH = parse_bool(payload.get("autoPublish"), AUTO_PUBLISH)
    SESSION = str(payload.get("session") or SESSION).strip()

    missing = []
    if not TITLE:
        missing.append("title")
    if not BODY:
        missing.append("body")
    if not DESCRIPTION:
        missing.append("description")
    if missing:
        print(f"缺少参数：{', '.join(missing)}", flush=True)
        sys.exit(2)


def is_longform_home():
    r = ev(js("""
const ok = !!findByText('新的创作', { exact: false });
return ok ? '1' : '0';
"""))
    return value(r) == "1"


def is_editor():
    r = ev(js("""
const title = document.querySelector(
  'textarea[placeholder="输入标题"], input[placeholder="输入标题"]'
);
const format = !!findByText('一键排版', { exact: false });
return title && format ? '1' : '0';
"""))
    return value(r) == "1"


def has_content():
    r = ev(js(f"""
const expectedTitle = {json.dumps(TITLE, ensure_ascii=False)};
const expectedBody = {json.dumps(BODY.splitlines()[0], ensure_ascii=False)};
const title = document.querySelector(
  'textarea[placeholder="输入标题"], input[placeholder="输入标题"]'
);
const editor = document.querySelector('.ProseMirror, [contenteditable="true"]');
const titleOk = title && (title.value || '').includes(expectedTitle);
const bodyOk = editor && textOf(editor).includes(expectedBody);
return titleOk && bodyOk ? '1' : '0';
"""))
    return value(r) == "1"


def is_template_step():
    r = ev(js("""
if (document.body.innerText.includes('图片生成中')) return 'wait';
const next = !!findByText('下一步', { exact: true });
const templateText = document.body.innerText.includes('选择模板') ||
  document.body.innerText.includes('封面设置') ||
  document.body.innerText.includes('灵感备忘');
return next && templateText ? '1' : '0';
"""))
    v = value(r)
    if v == "wait":
        return "wait"
    return v == "1"


def is_publish_page():
    r = ev(js("""
const text = document.body.innerText;
const hasPublish = !!findByText('发布', { exact: true }) || !!findByText('定时发布', { exact: false });
const hasVisibility = text.includes('公开可见') || text.includes('仅自己可见');
const hasDesc = text.includes('输入正文描述') || text.includes('正文描述');
const hasPublishEditor = text.includes('图片编辑') &&
  text.includes('内容设置') &&
  (text.includes('/1000') || text.includes('话题'));
return (hasPublish && (hasVisibility || hasDesc || hasPublishEditor)) || hasPublishEditor ? '1' : '0';
"""))
    return value(r) == "1"


def set_visibility():
    if VISIBILITY not in ("private", "public"):
        return ev(js("""
return JSON.stringify({ ok: true, skipped: true });
"""))
    if VISIBILITY == "public":
        return ev(js("""
return JSON.stringify({ ok: true, visibility: 'public' });
"""))
    return ev(f"""
(async () => {{
{JS_HELPERS}
  for (let i = 0; i < 10; i++) {{
    const privateOption = findClickableByText('仅自己可见', {{ exact: false }});
    if (privateOption) {{
      clickElement(privateOption);
      return JSON.stringify({{ ok: true, visibility: 'private' }});
    }}
    const publicOption = findClickableByText('公开可见', {{ exact: false }});
    if (publicOption) {{
      clickElement(publicOption);
      await new Promise(resolve => setTimeout(resolve, 500));
      const openedPrivateOption = findClickableByText('仅自己可见', {{ exact: false }}) ||
        findClickableByText('私密', {{ exact: false }});
      if (openedPrivateOption) {{
        clickElement(openedPrivateOption);
        return JSON.stringify({{ ok: true, visibility: 'private' }});
      }}
    }}
    scrollDown();
    await new Promise(resolve => setTimeout(resolve, 300));
  }}
  return JSON.stringify({{ ok: false, reason: '未找到：仅自己可见' }});
}})()
""")


def has_visibility():
    if VISIBILITY != "private":
        return True
    r = ev(f"""
(async () => {{
{JS_HELPERS}
  for (let i = 0; i < 4; i++) {{
    const text = document.body.innerText;
    if (text.includes('仅自己可见') || text.includes('私密')) return '1';
    scrollDown();
    await new Promise(resolve => setTimeout(resolve, 200));
  }}
  return '0';
}})()
""")
    return value(r) == "1"


def reset_scroll_top():
    return ev(js("""
window.scrollTo(0, 0);
return JSON.stringify({ ok: true });
"""))


def has_scroll_top():
    r = ev(js("""
return window.scrollY < 10 ? '1' : '0';
"""))
    return value(r) == "1"


def has_description():
    r = ev(js(f"""
const desc = {json.dumps(DESCRIPTION, ensure_ascii=False)};
const ok = Array.from(document.querySelectorAll('[contenteditable="true"]'))
  .some(el => ((el.innerText || el.textContent || '')).includes(desc));
return ok ? '1' : '0';
"""))
    return value(r) == "1"


def is_published():
    r = ev(js("""
return window.location.href.includes('published=true') ? '1' : '0';
"""))
    return value(r) == "1"


def switch_longform():
    return ev(js("""
const tab = Array.from(document.querySelectorAll('div.creator-tab, [role="tab"]'))
  .filter(visible)
  .find(el => textOf(el) === '写长文') ||
  Array.from(document.querySelectorAll('div, span'))
    .filter(visible)
    .find(el => textOf(el) === '写长文' && !el.closest('[aria-hidden="true"]'));
if (!tab) return JSON.stringify({ ok: false, reason: '未找到写长文' });
clickElement(tab);
return JSON.stringify({ ok: true });
"""))


def click_new_creation():
    return ev(js("""
return JSON.stringify(clickByText('新的创作', { exact: true }));
"""))


def fill_content():
    return ev(js(f"""
const titleText = {json.dumps(TITLE, ensure_ascii=False)};
const bodyText = {json.dumps(BODY, ensure_ascii=False)};
const title = document.querySelector(
  'textarea[placeholder="输入标题"], input[placeholder="输入标题"]'
);
if (!title) return JSON.stringify({{ ok: false, reason: '未找到标题输入框' }});
setNativeValue(title, titleText);

const editor = document.querySelector('.ProseMirror[contenteditable="true"], .ProseMirror, [contenteditable="true"]');
if (!editor) return JSON.stringify({{ ok: false, reason: '未找到正文编辑器' }});
fillEditable(editor, bodyText);
return JSON.stringify({{ ok: true }});
"""))


def click_format():
    return ev(js("""
return JSON.stringify(clickByText('一键排版', { exact: false }));
"""))


def click_next():
    return ev(js("""
return JSON.stringify(clickByText('下一步', { exact: true }));
"""))


def fill_description():
    return ev(js(f"""
const desc = {json.dumps(DESCRIPTION, ensure_ascii=False)};
const fields = Array.from(document.querySelectorAll('[contenteditable="true"]'))
  .filter(visible);

let target = fields.find(el => {{
  const boxText = textOf(el.closest('div') || el);
  return boxText.includes('输入正文描述') ||
    boxText.includes('正文描述') ||
    boxText.includes('/1000');
}});

if (!target) {{
  target = fields.find(el =>
    el.matches('.ProseMirror, .tiptap') ||
    el.className.toString().includes('ProseMirror') ||
    el.className.toString().includes('tiptap')
  );
}}
if (!target) return JSON.stringify({{ ok: false, reason: '未找到描述输入框' }});

fillEditable(target, desc);
return JSON.stringify({{ ok: true }});
"""))


def publish():
    if not AUTO_PUBLISH:
        return ev(js("""
return JSON.stringify({ ok: true, skipped: true, reason: 'autoPublish=false' });
"""))
    last = ""
    for _ in range(240):
        r = ev(js("""
const text = document.body.innerText;
if (text.includes('笔记图片生成中') || text.includes('图片生成中')) {
  return JSON.stringify({ ok: false, wait: true, reason: '图片生成中' });
}
scrollToBottom();

const publishRoots = deepQueryAll('xhs-publish-btn');
for (const root of publishRoots) {
  if (root.getAttribute('submit-disabled') === 'true') {
    return JSON.stringify({ ok: false, wait: true, reason: '发布按钮禁用' });
  }
  if (typeof root._onPublish === 'function') {
    root._onPublish();
    return JSON.stringify({ ok: true, mode: 'xhs-publish-btn._onPublish' });
  }
  const scope = root.shadowRoot || root;
  const items = Array.from(scope.querySelectorAll('button, [role="button"], div, span'))
    .filter(visible)
    .map(el => ({ el, text: textOf(el) }))
    .filter(x => x.text === '发布');
  if (items.length) {
    clickElement(findNearestClickable(items[0].el));
    return JSON.stringify({ ok: true, mode: 'xhs-publish-btn-shadow' });
  }
  if (root.getAttribute('submit-text') === '发布' || textOf(root).includes('发布')) {
    clickElement(root);
    return JSON.stringify({ ok: true, mode: 'xhs-publish-btn-root' });
  }
}

const fallback = Array.from(document.querySelectorAll('button, [role="button"], div, span'))
  .filter(visible)
  .map(el => ({ el, text: textOf(el), cls: String(el.className || '') }))
  .filter(x =>
    x.text === '发布' &&
    !x.el.closest('.menu-container, .d-new-menu, .publish-video') &&
    !x.text.includes('发布笔记')
  )
  .sort((a, b) => {
    const ap = /submit|publish|button|btn/.test(a.cls) ? 0 : 1;
    const bp = /submit|publish|button|btn/.test(b.cls) ? 0 : 1;
    if (ap !== bp) return ap - bp;
    return a.text.length - b.text.length;
  });
if (!fallback.length) {
  return JSON.stringify({ ok: false, wait: true, reason: '未找到发布按钮' });
}
clickElement(findNearestClickable(fallback[0].el));
return JSON.stringify({ ok: true, mode: 'fallback' });
"""))
        last = value(r)
        if '"ok":true' in last or '"ok": true' in last:
            return r
        time.sleep(1)
    return {"data": {"value": last or '{"ok":false,"reason":"发布超时"}'}}


def is_publish_done():
    if not AUTO_PUBLISH:
        return True
    return is_published()


def open_publish_page():
    print("打开创作页...", flush=True)
    result = wb(
        "navigate",
        {
            "url": "https://creator.xiaohongshu.com/publish/publish?source=official&type=longresource",
            "newTab": True,
        },
    )
    if not result.get("ok", False):
        print(f"打开创作页失败：{json.dumps(result, ensure_ascii=False)}", flush=True)
        sys.exit(1)
    wait_until("打开创作页", is_publish_home_loaded, timeout=45)
    print("打开创作页完成", flush=True)


def is_publish_home_loaded():
    r = ev(js("""
const text = document.body.innerText;
const ok = text.includes('写长文') ||
  text.includes('上传图文') ||
  text.includes('创作服务平台') ||
  text.includes('新的创作');
return ok ? '1' : '0';
"""))
    return value(r) == "1"


if __name__ == "__main__":
    apply_payload(load_payload())
    open_publish_page()
    step("切换长文", switch_longform, is_longform_home)
    step("新建创作", click_new_creation, is_editor)
    step("填写内容", fill_content, has_content)
    step("一键排版", click_format, is_template_step, timeout=35)
    step("下一步", click_next, is_publish_page)
    step("填写描述", fill_description, has_description)
    step("设置可见范围", set_visibility, has_visibility)
    step("发布", publish, is_publish_done, timeout=300)
    if AUTO_PUBLISH:
        print("发布成功", flush=True)
    else:
        print("已停在发布前", flush=True)
