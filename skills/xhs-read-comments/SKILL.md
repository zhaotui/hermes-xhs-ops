---
name: xhs-read-comments
description: 从笔记管理页点击封面打开详情页，提取评论。通过 xhs_read_comments plugin tool 自动化。
---

# XHS Read Comments

> 实际通过 **xhs plugin tool `xhs_read_comments`** 完成。
> 路径：笔记管理页 → 点击封面 → `_find_tab` 切换 → 详情页 → 提取评论。

## 流程

1. 调用 `xhs_read_comments` tool（可选传 `note_index`，默认 0）
2. Tool 自动：导航到笔记管理页 → 列封面 → 点击封面 → find_tab 切换到详情页
3. 用 `PARSE_DETAIL_COMMENTS` JS 从详情页 bodyText 提取评论 JSON
4. 返回 `{comments, count, message}`

## 陷阱

- 详情页评论包含**作者自己的回复**（带 `isAuthor: true`），AI 分析时注意区分
- "仅自己可见"笔记打不开前端详情页 → tool 会报错
- 审核中/未发布笔记也无法打开详情页
- `_find_tab` 切换后需等待 3s 让页面完全加载再提取
