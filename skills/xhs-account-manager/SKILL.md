---
name: xhs-account-manager
description: 小红书账号真实状态保存和切换。通过 xhs_account_manager 保存/恢复 cookies、localStorage、sessionStorage，让后续 xhs 工具使用指定账号状态。
---

# XHS Account Manager

> 通过 `xhs_account_manager` plugin tool 完成。账号元数据保存在 `accounts.json`，真实状态快照保存在 `account-states/`。

## 何时使用

- 用户要求切换小红书账号
- 用户要新增、查看、删除账号工作区
- 用户要关联账号到 EHR 职位创建人（如"main 关联赵锐"）
- 发布、读评论、回复前需要确认当前操作账号

## 常用操作

```python
# 识别当前页面登录账号候选信息
xhs_account_manager(action="detect")

# 新增账号（key 不传，默认用昵称）
xhs_account_manager(action="add", nickname="小红薯68761C00")
xhs_account_manager(action="save_state")

# 新增账号并保存当前浏览器里的真实登录状态
xhs_account_manager(action="add", key="main", nickname="小红书页面昵称")
xhs_account_manager(action="save_state", key="main")

# 切换当前账号：恢复保存过的 cookies/localStorage/sessionStorage
xhs_account_manager(action="switch", key="main")
xhs_account_manager(action="restore_state", key="main")

# 不点退出登录，只清本地小红书状态，方便用户手动登录另一个号
xhs_account_manager(action="clear_local_state")

# 清理当前账号 session 的多余页面
xhs_account_manager(action="cleanup_tabs")

# 打开当前账号的小红书创作者中心
xhs_account_manager(action="open")

# 关联账号到 EHR 职位创建人（用于发布时自动匹配）
xhs_account_manager(action="add", key="main", linked_creator="赵锐")

# 查看账号列表
xhs_account_manager(action="list")
```

## 规则

1. 账号 `key` 默认为昵称，不传 key 时自动取 `nickname`。也支持手动指定短 key（如 `main`）。
2. 默认账号为 `default`，session 是 `xhs`。
3. 未指定 session 时统一使用当前真实浏览器 session：`xhs`。
4. 只有用户明确要求多个 WebBridge session 时，才传 `session` 参数。
5. 新环境如果没有 `accounts.json`，工具会自动创建默认模板。
6. 后续 `xhs_publish_post`、`xhs_read_comments`、`xhs_view_note_detail`、`xhs_reply_comment`、`xhs_delete_post` 自动使用当前账号 session。
7. `save_state` 保存小红书相关 cookies、localStorage、sessionStorage。
8. `switch` 等价于恢复指定账号状态，并把当前账号指针切到该账号。
9. 登录另一个账号前，优先用 `clear_local_state`，不要点网页“退出登录”。
10. 状态保存、恢复、清理会复用同一个 tab，避免打开过多页面。
11. 如果历史操作已经留下过多页面，用 `cleanup_tabs` 清理。
12. 如果某账号状态过期，先 `open`，让用户登录，再重新 `save_state`。
