"""Xiaohongshu (小红书) operations plugin.

Registers 6 tools into the ``xhs`` toolset:
- xhs_read_comments   — 读取通知页评论
- xhs_view_note_detail — 打开笔记前端详情页
- xhs_reply_comment    — 回复评论
- xhs_publish_post     — 发布帖子
- xhs_collect_info     — 分类收集信息
- xhs_delete_post      — 删除仅自己可见帖

Requires Kimi WebBridge running on Windows host.
"""

from __future__ import annotations

from plugins.xhs.tools import TOOLS, _check_webbridge


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
