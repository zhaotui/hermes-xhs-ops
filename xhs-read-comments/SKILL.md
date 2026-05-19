---
name: xhs-read-comments
description: 读取小红书通知页评论，需要时进入笔记详情页查看完整上下文。
---

# XHS Read Comments

> **依赖 Plugin:** `xhs` (提供 `xhs_read_comments`, `xhs_view_note_detail` 工具)

## 流程

1. **调 `xhs_read_comments()`** — 自动打开通知页、切"评论和@"、提取评论，返回 JSON
2. 输出评论列表给用户
3. **如需看完整上下文**（是否已回复、查看所有评论）：
   - 调 `xhs_view_note_detail(note_index=N)` 打开详情页
   - 仅已发布笔记可用，**跳过"仅自己可见"**

## 陷阱

- 通知页不显示你是否已回复 → 用 `xhs_view_note_detail` 进详情确认
- "仅自己可见"笔记打不开前端详情页
- 只关注"评论了你的笔记"，忽略"回复了你的评论"和"赞了你的评论"
