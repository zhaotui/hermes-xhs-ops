---
name: xhs-reply-comment
description: 在小红书笔记详情页回复评论。
---

# XHS Reply Comment

> **依赖 Plugin:** `xhs` (提供 `xhs_reply_comment` 工具)
> **前置:** 必须先通过 `xhs_view_note_detail()` 进入笔记详情页

## 流程

1. 确认已在详情页，且该评论没有你的作者回复
2. **调 `xhs_reply_comment(reply_text="回复内容")`** — 自动找目标评论的"回复"按钮、填文本、发送、验证

## 陷阱

- 必须先调 `xhs_view_note_detail`，不能在通知页回复
- 每个评论都有"回复"按钮，插件自动选最后一个（最新的评论）
- 回复前检查详情页里是否已经有 `作者` 标识的回复

## 输出

```
回帖结果：
用户：【authorName】
评论：【commentText】  
回复：【replyText】
状态：【成功/失败】
```
