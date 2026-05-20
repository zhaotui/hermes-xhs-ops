---
name: xhs-delete-post
description: 删除小红书笔记管理页中的帖子（测试后清理）。
---

# XHS Delete Post

> 实际通过 **Kimi WebBridge** 浏览器自动化完成。

## ⚠️ 绝对规则

**只删除"仅自己可见"的帖子。不要批量顺序删所有帖子。**
每次删除前必须用 JS 确认目标帖子带有"仅自己可见"标签。

## 流程

1. 导航到 `https://creator.xiaohongshu.com/new/note-manager?source=official`
2. 确认页面加载，看到笔记列表
3. **先识别"仅自己可见"帖子**，列出它们的索引
4. 只对"仅自己可见"的帖子点击"删除"
5. 确认弹窗 → 点击"确定"
6. 验证删除：页面刷新后笔记数减少

## 识别仅自己可见帖子

```javascript
// 返回仅自己可见帖子的索引列表
(() => {
  // 获取 body 文本，按帖子拆分
  const text = document.body.innerText;
  // 找到笔记列表区域的起始位置
  const start = text.indexOf('全部笔记');
  const section = text.slice(start);
  // 按"权限设置"切分每条帖子
  const posts = section.split('权限设置');
  const selfOnly = [];
  posts.forEach((p, i) => {
    if (p.includes('仅自己可见')) {
      selfOnly.push(i);
    }
  });
  return JSON.stringify({ total: posts.length - 1, selfOnly });
})()
```

## 删帖 JS（只删指定索引）

```javascript
// 点击第 N 个"删除"按钮（0-indexed）
(() => {
  const all = Array.from(document.querySelectorAll('*'));
  const deletes = all.filter(el => (el.innerText || el.textContent || '').trim() === '删除' && el.offsetParent);
  if (!deletes[N]) return JSON.stringify({ ok: false, reason: 'no delete at index ' + N });
  deletes[N].click();
  return JSON.stringify({ ok: true, index: N });
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

## 批量删除（安全版）

```python
# 1. 先识别仅自己可见帖子索引
# 2. 对每个索引：删 → 确认 → wait 2s
# 3. 每轮重新识别（删除后索引会变化）
```

## 陷阱

- 🚨 **绝对不要盲目顺序删所有帖子** — 会误删公开帖
- 删除按钮是 StaticText 无 @e ref → 必须用 evaluate 在 DOM 中查找
- 每次删除后 DOM 索引可能变化 → 删除一个后重新 snapshot 再删下一个
- 删除后页面缓存可能不同步 → 验证用 `navigate` 刷新
- 公开帖（无"仅自己可见"标签）**绝不删除**
