# lablog-mcp 🧪

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Protocol%202.x-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **A lightweight, zero-dependency Model Context Protocol (MCP) server that transforms fragmented Markdown experiment notes into an interactive, chronological timeline for AI.**

[English](#features) | [中文说明](#中文介绍)

---

## 中文介绍

在进行 AI 调优、提示词工程（Prompt Engineering）、模型微调或算法开发时，很多开发者习惯用 AI 随手生成一篇篇 Markdown 实验记录。但随着实验积累：
- 历史记录碎片化，极难横向对比；
- 容易忘记“上次为什么放弃了这个参数”；
- 重新复现最佳结果时缺乏连贯的演进脉络。

**`lablog-mcp`** 是一个专为解决该痛点打造的轻量 MCP 插件服务。它让 AI 客户端（如 Claude Desktop、Cursor、Cline 等）拥有自动扫描并理解你本地 Markdown 笔记的能力。

只需对 AI 说一句：
> **“查看实验日志，帮我对比过去一周在提示词上的改动和最终采用结果。”**

AI 即可自动调用该服务，提取关键维度：
1. **时间与主题**（Date & Topic）
2. **实验改动**（What was changed / Delta）
3. **结果好坏评定**（Outcome / Eval metrics）
4. **决策理由**（Decision & Rationale: 采纳还是放弃，以及核心原因）

---

## Features

- ⚡ **Zero Hassle**: Pure file-system driven. No heavy databases or external embedding servers required.
- 🔍 **Smart Heuristics**: Automatically detects section headings like `## 改动`, `## 结果`, `## 结论` or `## Changes`, `## Results`, `## Conclusion`.
- 🛡️ **Strictly Read-Only**: Guarantees zero writes or modifications to your original notes.
- 🕒 **Three-Tier Date Fallback**: Frontmatter `date` → Filename `YYYY-MM-DD` → File system timestamp (`mtime`).
- 🤖 **Universal MCP Support**: Compatible with Claude Desktop, Cursor, Cline, and any MCP 1.x/2.x host.

---

## Installation & Setup

### 1. Run with `uvx` (Recommended)

No manual clone needed:
```bash
uvx lablog-mcp
```

### 2. Install via `pip`

```bash
git clone https://github.com/your-username/lablog-mcp.git
cd lablog-mcp
pip install -e .
```

---

## Client Configuration

### Claude Desktop
Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lablog": {
      "command": "python",
      "args": ["-m", "lablog_mcp.server"],
      "env": {
        "LABLOG_NOTES_DIR": "C:/path/to/your/experiment/notes"
      }
    }
  }
}
```

### Cursor
In Cursor Settings -> Features -> MCP Servers -> Add New MCP Server:
- **Name**: `lablog`
- **Type**: `command`
- **Command**: `python -m lablog_mcp.server`
- **Environment Variables**: `LABLOG_NOTES_DIR=C:/path/to/your/experiment/notes`

---

## Provided MCP Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `get_experiment_timeline` | `notes_dir`, `limit`, `topic`, `order` | Returns a chronological timeline of all scanned experiments with their deltas, outcomes, and decisions. |
| `get_experiment_detail` | `file_path` | Retrieves the full markdown text and parsed metadata of a specific experiment. |

---

## Note Writing Tips (Optional)

`lablog-mcp` is designed to be highly forgiving. Your notes can be as simple as:

```markdown
# 实验：Temperature 调优

## 实验改动
将 temperature 从 0.7 降为 0.2。

## 实验结果
数学逻辑题推导正确率提升 15%。

## 结论
采用。低温极大降低了计算过程中的随机计算失误。
```

---

## Testing & Quality

Run the automated test suite:

```bash
pytest tests/ -v
```

All contributions, issue reports, and PRs are welcome!

## License

[MIT](LICENSE) © 2026 Developer
