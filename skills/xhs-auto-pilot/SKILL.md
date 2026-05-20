---
name: xhs-auto-pilot
description: 小红书自驱动运营——cron 链式调度，自动发帖/扫评论/回帖/收集信息，24 小时无人值守。
---

# XHS Auto Pilot

> 基于 Hermes cron 的小红书自循环运营系统。
> 每次 cron 触发执行本轮工作，完成后根据结果调度下一次。

## 前置条件

- Windows 不锁屏不休眠
- Kimi WebBridge daemon 运行中
- 浏览器已登录小红书
- Hermes cron scheduler 运行中（`hermes cron status`）

## 依赖 Skills

| Skill | 用途 |
|-------|------|
| `xhs-publish-post` | 发布笔记（或 `scripts/publish_auto.py`） |
| `xhs-read-comments` | 扫通知页提取评论 |
| `xhs-collect-info` | 分类收集评论信息 |
| `xhs-reply-comment` | 自动回复评论 |
| `xhs-delete-post` | 清理测试帖 |

## 调度架构

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ scan_cron   │────▶│ 扫评论 + 回帖 │────▶│ 更新下次 cron │
│ 每 2 小时    │     │ 收集信息      │     │              │
└─────────────┘     └──────────────┘     └──────────────┘

┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ post_cron   │────▶│ 生成内容+发帖 │────▶│ 更新下次 cron │
│ 每天 1 次    │     │              │     │              │
└─────────────┘     └──────────────┘     └──────────────┘
```

## 使用方式

当用户提出小红书运营需求时：

### Phase 1：策略讨论（与用户确认）

1. **发帖策略**
   - 频率：每天几篇？
   - 主题方向：生活/职场/美妆/教育/…
   - 标题风格：亲和/专业/种草
   - 可见性：公开 or 自己可见过渡

2. **回帖策略**
   - 回什么：positive（感兴趣/想了解）→ 回；问候/表情 → 忽略
   - 回复风格：礼貌引导 or 直接回答
   - 频率限制：每帖回几条？同用户回几次？

3. **收集策略**
   - positive_signals：感兴趣,想了解,怎么报名,联系,微信
   - negative_signals：你好,哈喽,表情,打卡,单纯问候

### Phase 2：Cron 自循环搭建

```bash
# 1. 扫评论任务（每 2 小时）
hermes cron create "0 */2 * * *" \
  --prompt "加载 xhs-read-comments 和 xhs-collect-info。扫通知页评论，分类收集。如有 positive 评论需回复，加载 xhs-reply-comment 处理。"

# 2. 发帖任务（每天上午 10 点）
hermes cron create "0 10 * * *" \
  --prompt "加载 xhs-publish-post。生成一篇{主题}帖子，设置{可见性}，通过 scripts/publish_auto.py 发布。"

# 3. 清理任务（每周清理测试帖）
hermes cron create "0 3 * * 0" \
  --prompt "加载 xhs-delete-post。识别并删除所有仅自己可见的测试帖。"

# 查看状态
hermes cron list
```

### Phase 3：监控

```bash
# 查看最近执行
hermes cron list --all

# 查看某次执行的 session
hermes sessions list --limit 10

# 手动触发测试
hermes cron run <job_id>
```

## Prompt 模板

### scan + reply prompt

```
你是小红书运营助手。加载 xhs-read-comments 和 xhs-collect-info。
1. 导航到通知页，用 snippet:parse-comments 提取"评论了你的笔记"
2. 调用 collect-info 分类保存
3. 对 positive 评论（{positive_signals}），加载 xhs-reply-comment，回复：{reply_style}
4. 忽略 greeting/emoji/无关评论
5. 输出本次处理汇总
```

### post prompt

```
你是小红书运营助手。加载 xhs-publish-post。
生成一篇关于{主题}的小红书长文，标题{标题风格}，内容自然不AI感。
调用 scripts/publish_auto.py 发布，visibility={可见性}。
发布后汇报标题和链接。
```

## 陷阱

- cron 之间不要冲突：扫评论和发帖错开时间
- WebBridge session 名统一：推荐 `xhs-ops`
- 每次 cron 结束用独立的 session，不要复用
- cron 失败不会重试：关键任务可以设两个间隔短的 cron 互为备份
- 电脑休眠/锁屏会导致 WebBridge 失效 → 确保电源设置"永不"
