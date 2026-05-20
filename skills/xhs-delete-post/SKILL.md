---
name: xhs-delete-post
description: 删除小红书笔记管理页中的帖子（测试后清理），仅安全删除"仅自己可见"帖。
---

# XHS Delete Post

> 实际通过 **Kimi WebBridge** 浏览器自动化完成。

## ⚠️ 绝对规则

**只删除"仅自己可见"的帖子。先识别再删，绝不盲删。**

## 流程

1. 导航到笔记管理页
2. 识别所有"仅自己可见"帖子
3. 逐个删除：点"删除" → 确认 → 刷新验证

## 识别仅自己可见帖子（已验证）

小红书笔记管理页 body text 结构：
```
仅自己可见           ← 仅自己可见标签
{标题}
发布于 2026年XX月XX日 XX:XX
0  0  0  0  0         ← 互动数据
权限设置
置顶
编辑
删除
```

识别 JS（正则匹配 `仅自己可见\n{标题}\n发布于 2026年` 模式）：

```javascript
(() => {
  const text = document.body.innerText;
  const re = /仅自己可见\n(.+?)\n发布于 \d{4}年/g;
  const posts = [];
  let match;
  while ((match = re.exec(text)) !== null) {
    posts.push({ title: match[1] });
  }
  return JSON.stringify({ count: posts.length, posts });
})()
```

## 删帖（已识别后）

```javascript
// "删除"按钮顺序与帖子顺序一致
(() => {
  const all = Array.from(document.querySelectorAll('*'));
  const deletes = all.filter(el =>
    (el.innerText || el.textContent || '').trim() === '删除' && el.offsetParent
  );
  // deletes[N] 对应第 N 篇"仅自己可见"帖
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

## 陷阱

- 🚨 **绝不盲删**：必须先 identify → 验证只有"仅自己可见"帖 → 再删
- 公开帖无"仅自己可见"标签，正则自动跳过
- "发布于 \d{4}年"确保不会匹配到过滤栏的"仅自己可见"
