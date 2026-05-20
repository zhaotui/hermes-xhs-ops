---
name: xhs-publish-post
description: 发布小红书长文帖子。通过 xhs_publish_post plugin tool 调用 publish_auto.py 脚本自动化。
---

# XHS Publish Post

> 通过 **xhs plugin tool `xhs_publish_post`** 完成。
> 实际执行 `scripts/publish_auto.py` 子进程，step-by-step 浏览器自动化。

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | ✅ | 标题，30字以内 |
| body | string | ✅ | 正文 |
| visibility | enum | ❌ | private/public/friends/include/exclude，默认 private |
| images | string[] | ❌ | 图片路径列表（Windows/WSL 路径均可） |
| location | string | ❌ | 发布地点 |
| template | string | ❌ | 排版模板名称 |
| content_type | string | ❌ | 内容类型声明 |
| source_type | string | ❌ | 来源声明 |
| allow_collab | boolean | ❌ | 允许合拍 |
| allow_copy | boolean | ❌ | 允许正文复制 |
| original | boolean | ❌ | 原创声明 |
| visibility_users | string[] | ❌ | 可见用户（include/exclude 时） |
| save_draft | boolean | ❌ | 仅暂存不发布 |

## 流程概要

```
健康检查 → 打开发布页 → 切换长文(如需要) → 新建创作 →
填标题正文 → 一键排版 → 选择模板 → 下一步 →
填描述 → 可选设置 → 内容类型声明 → 来源声明 →
上传图片 → 设置地点 → [暂存离开 或] 设可见范围 → 发布
```

## 关键规则

- 脚本 6 分钟超时
- `save_draft=true` 时跳过发布步骤，仅暂存
- 图片路径自动从 Windows 转 WSL（`C:\... → /mnt/c/...`）
- 成功标志：发布后 URL 含 `published=true`
