---
name: xhs-tab-manager
description: 小红书浏览器 tab 感知与管理——开始任何 xhs 操作前先加载此 skill，了解当前 tab 状态，复用已有页面而非盲目新开。
---

# XHS Tab Manager

> **规则：开始任何 xhs 操作前，先了解当前有哪些浏览器 tab，能复用就复用，不乱开新 tab。**

## 何时加载

- 任何涉及 xhs 浏览器的操作之前（发布、读评论、删帖、回复等）
- 不确定当前浏览器状态时
- 操作结束后确认 tab 清理情况

## Tab 检查

通过 `client.py` 的 `_cmd` 函数列出各 session 的 tab：

```python
from client import _cmd
for session in ["xhs"]:
    r = _cmd("list_tabs", {}, session=session)
    tabs = r.get("data", {}).get("tabs", [])
```

## 已知 Session

| Session | 用途 | 说明 |
|---------|------|------|
| `xhs` | **主 session** | 所有正式操作统一用这个 |
| `xiaohongshu-auto` | publish_auto.py 默认 | 旧脚本默认，已统一改为 `xhs` |
| `xhs-image-test` | 旧测试残留 | 不再使用 |

## 操作规则

1. **复用优先**：如果 session 中有 tab（任何页面），直接 navigate 到目标 URL，不关不新建
2. **统一 session**：所有操作都用 `session="xhs"`
3. **只有 0 tab 才 newTab**：`list_tabs` 为空时才 `newTab=True`
4. **换个 URL 就行**：同一个 tab 可以 navigate 到不同页面，不需要为每个页面开新 tab

## 常见页面 URL

| 页面 | URL |
|------|-----|
| 笔记管理 | `https://creator.xiaohongshu.com/new/note-manager?source=official` |
| 发布页 | `https://creator.xiaohongshu.com/publish/publish?source=official&from=menu&target=article` |
| 通知页 | `https://www.xiaohongshu.com/notification` |
| 详情页 | `https://www.xiaohongshu.com/explore/{note_id}` |

## 陷阱

- `_find_tab` 只搜非活跃 tab，当前 active tab 不会被 match
- `close_tab` 超时通常是 tab 有未关闭的弹窗，先处理弹窗再关
- 不同 session 的 tab 互不可见，确保始终用 `session="xhs"`
