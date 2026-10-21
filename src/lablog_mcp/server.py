"""FastMCP / MCPServer 服务入口与工具定义."""

import json
import os
from typing import Optional

try:
    # mcp 2.x+ 引入并推荐使用 MCPServer
    from mcp.server import MCPServer as FastMCP
except ImportError:  # pragma: no cover
    # mcp 1.x 回退兼容
    from mcp.server.fastmcp import FastMCP

from lablog_mcp.scanner import get_detail, get_timeline

# 初始化 MCP 应用
mcp = FastMCP("lablog-mcp")


@mcp.tool()
def get_experiment_timeline(
    notes_dir: Optional[str] = None,
    limit: int = 20,
    topic: Optional[str] = None,
    order: str = "desc",
) -> str:
    """扫描指定目录下的 Markdown 实验笔记，提取改动、好坏评定与采纳决策，生成按时间排序的实验时间线.

    参数:
        notes_dir: 存放实验笔记的目录路径。若不提供，优先读取环境变量 LABLOG_NOTES_DIR 或当前工作目录。
        limit: 最多返回的实验条目数，默认 20。
        topic: 可选的关键词过滤（如 'LoRA', 'prompt', 'temperature'）。
        order: 时间排序方式，'desc' (最新实验优先) 或 'asc' (最早实验优先)。
    """
    target_dir = notes_dir or os.getenv("LABLOG_NOTES_DIR", ".")
    res = get_timeline(directory=target_dir, limit=limit, topic_filter=topic, order=order)
    return res.model_dump_json(indent=2)


@mcp.tool()
def get_experiment_detail(file_path: str) -> str:
    """获取单篇实验笔记的完整原文、环境配置与结构化详情.

    参数:
        file_path: 实验笔记的具体文件路径。
    """
    detail = get_detail(file_path)
    return json.dumps(detail, ensure_ascii=False, indent=2)


def main():
    """CLI 入口函数，启动标准输入输出 (stdio) MCP 服务."""
    mcp.run()


if __name__ == "__main__":
    main()
