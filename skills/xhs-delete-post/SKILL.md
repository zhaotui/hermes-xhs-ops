---
name: xhs-delete-post
description: 删除小红书笔记管理页中的帖子（测试后清理）。
---

# XHS Delete Post

> 实际通过 **Kimi WebBridge** 浏览器自动化完成。

## 流程

1. 导航到 `https://creator.xiaohongshu.com/new/note-manager?source=official`
2. 确认页面加载，看到笔记列表
3. 用 evaluate JS 找到"删除"元素并点击（DOM 中无 ref，只有 StaticText）
4. 确认弹窗出现 → 点击"确定"
5. 验证删除：页面刷新后笔记数减少

## 删帖 JS

```javascript
// 点击第 N 个"删除"（0-indexed）
(() => {
  const all = Array.from(document.querySelectorAll('*'));
  const deletes = all.filter(el => (el.innerText || el.textContent || '').trim() === '删除' && el.offsetParent);
  if (deletes.length === 0) return JSON.stringify({ ok: false });
  deletes[N].click();
  return JSON.stringify({ ok: true });
})()
```

## 确认弹窗

```javascript
(() => {
  const all = document.querySelectorAll('button, span, div');
  for (const el of all) {
    if ((el.innerText || el.textContent || '').trim() === '确定' && el.offsetParent) {
      el.click();
      return JSON.stringify({ ok: true });
    }
  }
  return JSON.stringify({ ok: false });
})()
```

## 批量删除

用 Python 脚本循环：删 → 确认 → wait 2s → 重复。每轮需重新 snapshot 或 depend on DOM state。

## 陷阱

- 删除按钮是 StaticText 无 @e ref → 必须用 evaluate 在 DOM 中查找
- 每次删除后弹窗可能残留 → 确保点击确认后等页面刷新再继续
- 公开帖不要误删 → 先检查是否有"仅自己可见"标签
- 删除后页面缓存可能不同步 → 验证用 `navigate` 刷新
