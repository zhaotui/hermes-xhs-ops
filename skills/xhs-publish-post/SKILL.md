---
name: xhs-publish-post
description: 发布小红书长文帖子。
---

# XHS Publish Post

> **依赖 Plugin:** `xhs` (提供 `xhs_publish_post` 工具，⚠️ 尚未实现)

## 输入

```json
{
  "goal": "任务目标",
  "visibility": "private",
  "autoPublish": true
}
```

## 流程

1. 根据任务目标生成标题（30字以内）和正文
2. **调 `xhs_publish_post(title=..., body=..., visibility=...)`**

## 输出

```
发帖结果：
标题：【title】
可见范围：【public/private】
状态：【成功/失败】
```
