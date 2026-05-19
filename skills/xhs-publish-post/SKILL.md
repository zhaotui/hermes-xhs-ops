---
name: xhs-publish-post
description: 发布小红书长文帖子。实际通过 Kimi WebBridge 浏览器自动化执行。
---

# XHS Publish Post

> 实际发布通过 **Kimi WebBridge** 浏览器自动化完成（`xhs_publish_post` plugin tool 尚未实现）。
> 严格工作流文档：加载 `kimi-webbridge` skill 后读取 `references/xiaohongshu-workflow.md`（已验证端到端可用）。

## 前置条件

- Windows 端 Kimi WebBridge daemon 运行中（`curl http://<WIN_HOST>:10086/status` 返回 `extension_connected: true`）
- 浏览器已登录小红书创作者账号

## 流程概要

```
健康检查 → 打开创作页 → 切换长文 tab → 新建创作 → 
填标题正文 → 一键排版 → 下一步 → 填描述 → 设仅自己可见 → 
最终验证 → 发布
```

## 关键规则

- Session 名：`xiaohongshu-publish`
- 描述字段是 contenteditable div，用 `fill` action 填充
- JS 传参必须用文件 + python3 json.dumps 模式（见 kimi-webbridge `snippet:bash-eval`）
- 最终发布前需用户确认，除非用户明确要求测试且设为"仅自己可见"
- 成功标志：URL 包含 `published=true`

## 固定测试内容

| 字段 | 内容 |
|------|------|
| 标题 | 新人报道，今天开始记录生活 |
| 正文 | 第一次在这里发帖...（61字） |
| 描述 | 新人第一篇，记录日常 |
