# WebBridge 实战模式

## JSON 引号转义

中文特殊字符在 bash 单引号中容易炸。用 `python3 -c` 构造 JSON 负载：

```bash
CODE=$(cat /tmp/script.js)
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'xhs'}))" "$CODE")"
```

## 新标签导航

当点击在新标签页打开页面时，不要检查 `window.location.href`（那是当前标签），用 `find_tab` 定位新标签：

**两步绑定模式**：先查找，再激活绑定。

```bash
# Step 1: 查找新标签（不激活）
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d '{"action":"find_tab","args":{"url":"www.xiaohongshu.com","active":false},"session":"xhs"}'

# Step 2: 绑定到新标签（激活，此后 evaluate/snapshot 都操作这个标签）
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d '{"action":"find_tab","args":{"url":"www.xiaohongshu.com","active":true},"session":"xhs"}'
```

**注意区分两种情况**：
- 创作者中心点击封面图 → 打开真实新浏览器标签 → `find_tab` 可以找到并绑定 ✅
- 通知页 `target="_blank"` 链接 → 新标签不在 session group 中 → `find_tab` 找不到 ❌ → 改用提取 href 后 `navigate` 方案

## snapshot ref 生命周期

`snapshot` 返回的 `@eXX` ref 在页面 DOM 变化后立即失效。需要重新快照获取新 ref。

## React 页面点击

React 页面可能不响应简单的 `.click()`，需要 dispatch 完整事件序列：

```javascript
el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y }));
el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y }));
el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, button: 0 }));
```

## 位置排序定位（多实例选择）

当页面有多个同名元素（如多个"回复"按钮），必须按坐标定位目标：

```javascript
(() => {
  const all = document.querySelectorAll('*');
  const targets = [];
  all.forEach(el => {
    if ((el.innerText || '') === '回复' && el.offsetParent) {
      targets.push({el, top: Math.round(el.getBoundingClientRect().top)});
    }
  });
  // 按垂直位置排序，选最后一个（或按需选第 N 个）
  targets.sort((a, b) => a.top - b.top);
  const target = targets[targets.length - 1]; // 最后一个 = 最下方
  // ... dispatch click on target.el
})()
```
