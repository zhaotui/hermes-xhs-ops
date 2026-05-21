#!/usr/bin/env python3
"""通用报告工具 — 统一格式、统一存储。

其他脚本导入 write_report() 即可生成标准化报告。
"""

import os
from datetime import datetime


REPORT_DIR = os.path.expanduser("~/.hermes/data/xhs-ops/reports")


def write_report(title: str, sections: list[tuple[str, list[str]]]) -> str:
    """生成并保存报告。

    Args:
        title: 报告标题（不含时间戳，会自动追加）
        sections: [(节标题, [内容行]), ...]

    Returns: 报告文件路径
    """
    os.makedirs(REPORT_DIR, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    filename = f"report_{now.strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(REPORT_DIR, filename)

    lines = [f"# {title} — {timestamp}", ""]
    for section_title, section_lines in sections:
        lines.append(f"## {section_title}")
        lines.extend(section_lines)
        lines.append("")

    content = "\n".join(lines)
    with open(filepath, "w") as f:
        f.write(content)

    print(content)
    print(f"\n---\n报告已保存: {filepath}")
    return filepath
