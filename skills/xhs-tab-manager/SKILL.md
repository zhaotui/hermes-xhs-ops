---
name: xhs-tab-manager
description: 小红书浏览器 tab 感知与管理——开始任何 xhs 操作前先加载此 skill，了解当前 tab 状态，通过 tab_manager 模块统一管理。
---

# XHS Tab Manager

> **tab 管理脚本：`scripts/tab_manager.py`**。所有 tab 操作统一入口，规则集中管理。

## 何时加载

- 任何涉及 xhs 浏览器的操作之前（发布、读评论、删帖、回复等）
- 不确定当前浏览器状态时
- 需要清理残留 tab 时

## 核心 API

```python
import sys; sys.path.insert(0, "/mnt/c/Users/yxkj/Desktop/work/xhs/scripts")
from tab_manager import list_all, close_all, close_one, ensure

# 查看当前 session 所有 tab
tabs = list_all()                     # session="xhs"
tabs = list_all("xiaohongshu-auto")   # 其他 session

# 关闭 tab
close_all()                           # 关 xhs session 全部
close_all("xiaohongshu-auto")         # 关其他 session 全部
close_one(tab_id)                     # 关指定 tab

# 确保有可用 tab 并导航
ensure("https://creator.xiaohongshu.com/new/note-manager")  # 有 tab → navigate；0 tab → newTab
```

## 操作规则

1. **复用优先**：`ensure(url)` — 有 tab → navigate；0 tab → newTab
2. **统一 session**：所有操作用 `session="xhs"`
3. **关闭**：`close_all()` / `close_all("other-session")` — 需要时直接调
4. **规则在 tab_manager.py**：以后规则变了只改这一个文件
