---
name: xhs-read-comments
description: 读取小红书通知页评论，通过 Kimi WebBridge 浏览器自动化提取。
---

# XHS Read Comments

> 实际通过 **Kimi WebBridge** 浏览器自动化完成。
> 提取评论用 `kimi-webbridge` skill 的 `snippet:parse-comments`。

## 流程

1. 加载 `kimi-webbridge` skill
2. 导航到 `https://www.xiaohongshu.com/notification`
3. 默认在"评论和@"tab；如不在用 `snippet:switch-comment-tab`
4. 用 `snippet:parse-comments` evaluate 提取评论 JSON
5. 输出评论列表给用户
6. 如需看完整上下文：提取笔记链接 → navigate 到详情页

## 陷阱

- 通知页不显示你是否已回复 → 进详情页确认
- "仅自己可见"笔记打不开前端详情页 → 跳过
- 只关注"评论了你的笔记"，忽略"回复了你的评论"和"赞了你的评论"
- 通知页用户名/封面是 `target="_blank"` 链接 → 用 evaluate 提取 href 后 navigate
- **不要从创作者笔记管理页点帖子看评论** — SPA 路由拦截，WebBridge session 内不会导航。直接跳通知页。
