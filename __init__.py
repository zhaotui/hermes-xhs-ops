"""Xiaohongshu (小红书) operations plugin.

Registers 7 tools into the ``xhs`` toolset:
- xhs_account_manager — 管理账号工作区并切换当前账号
- xhs_read_comments   — 从笔记管理页打开详情页读取评论
- xhs_view_note_detail — 打开笔记前端详情页
- xhs_reply_comment    — 回复评论
- xhs_publish_post     — 发布帖子
- xhs_collect_info     — 分类收集信息
- xhs_delete_post      — 删除仅自己可见帖

Requires Kimi WebBridge running on Windows host.
"""

from __future__ import annotations

import os
import sys

# 优先用相对导入（兼容任意安装路径），失败则回退绝对导入
try:
    from .tools import TOOLS, _check_webbridge
except ImportError:
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from tools import TOOLS, _check_webbridge


def register(ctx) -> None:
    """Register all XHS tools. Called once by the plugin loader."""
    for name, schema, handler, emoji in TOOLS:
        ctx.register_tool(
            name=name,
            toolset="xhs",
            schema=schema,
            handler=handler,
            check_fn=_check_webbridge,
            emoji=emoji,
        )
