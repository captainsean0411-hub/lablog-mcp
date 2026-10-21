# lablog-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 Python FastMCP 的轻量级开源 MCP 服务，自动扫描、解析本地 AI 实验 Markdown 笔记，提取实验改动、评测好坏与采纳原因，并按时间线提供结构化查询工具。

**Architecture:** 采用分层模块化设计。`models.py` 定义 Pydantic 实体；`parser.py` 负责 Markdown 文本启发式切分与元数据抽取；`scanner.py` 负责本地目录递归扫描与时间线过滤排序；`server.py` 封装 FastMCP 接口注册并暴露 `get_experiment_timeline` 与 `get_experiment_detail`。

**Tech Stack:** Python 3.10+, `mcp[cli]>=1.0.0`, `python-frontmatter>=1.1.0`, `pydantic>=2.0.0`, `pytest>=8.0.0`

**Spec:** `C:/Users/msi/.gemini/antigravity/scratch/lablog-mcp/docs/superpowers/specs/2026-10-21-lablog-mcp-design.md`

## Global Constraints

- Python 版本要求：>= 3.10
- 只读约束：所有文件操作必须是严格只读的，禁止修改、重命名或覆写任何 Markdown 笔记
- 依赖最小化：禁止引入外部大型向量库或外部数据库服务
- 框架规范：必须使用官方 `mcp.server.fastmcp.FastMCP` API

## Review Focus

1. **缺失部分标准标题的 Markdown 文件**：笔记没有 `## 结论` 或 `## 改动`，预期提取为空字符串或默认提示，不得抛出异常崩溃。
2. **文件名与 Frontmatter 无有效日期的文件**：预期自动安全回退至文件系统的最后修改时间（`mtime`）。
3. **空目录或不存在的目录路径**：`get_experiment_timeline` 预期返回空列表并在结果中给出友好提示，而不是抛出未捕获的 `FileNotFoundError`。
4. **带有非 UTF-8 编码的异常 Markdown 文件**：读取时预期使用 `errors="replace"` 或容错策略，避免编码解码中断流程。
5. **超大笔记目录扫描（含数百个文件）**：文件检索仅过滤 `.md` 扩展名并忽略常见忽略目录（如 `.git`, `node_modules`, `__pycache__`）。

---

### Task 1: 项目脚手架与数据模型 (Project Scaffolding & Pydantic Models)

**Files:**
- Create: `pyproject.toml`
- Create: `src/lablog_mcp/__init__.py`
- Create: `src/lablog_mcp/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: None
- Produces:
  - `class ExperimentEntry(BaseModel)`: 包含 `file_path: str`, `date: str`, `topic: str`, `delta: str`, `outcome: str`, `decision: str`, `rationale: str`
  - `class TimelineResponse(BaseModel)`: 包含 `total: int`, `entries: list[ExperimentEntry]`

- [ ] **Step 1: Write the failing test for models**

```python
# tests/test_models.py
from lablog_mcp.models import ExperimentEntry, TimelineResponse

def test_experiment_entry_creation():
    entry = ExperimentEntry(
        file_path="notes/2026-10-21-exp1.md",
        date="2026-10-21",
        topic="模型学习率测试",
        delta="将 lr 从 1e-4 改为 5e-5",
        outcome="收敛速度变慢，但验证集 loss 下降 0.05",
        decision="采用",
        rationale="提升了泛化性能"
    )
    assert entry.topic == "模型学习率测试"
    assert entry.decision == "采用"

def test_timeline_response():
    resp = TimelineResponse(total=0, entries=[])
    assert resp.total == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py`
Expected: FAIL (ModuleNotFoundError: No module named 'lablog_mcp')

- [ ] **Step 3: Implement `pyproject.toml`, `src/lablog_mcp/__init__.py`, and `models.py`**

在 `pyproject.toml` 中配置 `hatchling` 或 `setuptools` 打包规范，并在 `src/lablog_mcp/models.py` 中实现 `ExperimentEntry` 和 `TimelineResponse`。

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/lablog_mcp/__init__.py src/lablog_mcp/models.py tests/test_models.py
git commit -m "feat: setup project scaffolding and pydantic models"
```

---

### Task 2: Markdown 启发式解析器 (Markdown Heuristic Parser)

**Files:**
- Create: `src/lablog_mcp/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: `ExperimentEntry` from `src/lablog_mcp/models.py`
- Produces:
  - `parse_markdown_note(file_path: str, content: str = None) -> ExperimentEntry`

- [ ] **Step 1: Write the failing test for parser**

```python
# tests/test_parser.py
from lablog_mcp.parser import parse_markdown_note

def test_parse_standard_note(tmp_path):
    note_content = """---
date: "2026-10-20"
topic: "LoRA 秩对比实验"
---
# 实验日志：LoRA Rank 优化

## 实验改动
将 lora_rank 从 8 提升至 32，batch_size 调为 16。

## 实验结果
训练 loss 下降 12%，显存占用增加 1.2GB。

## 结论与决策
采用。虽然显存微涨，但整体生成质量提升明显。
"""
    note_file = tmp_path / "2026-10-20-lora.md"
    note_file.write_text(note_content, encoding="utf-8")

    entry = parse_markdown_note(str(note_file))
    assert entry.date == "2026-10-20"
    assert entry.topic == "LoRA 秩对比实验"
    assert "lora_rank 从 8 提升至 32" in entry.delta
    assert "训练 loss 下降 12%" in entry.outcome
    assert "采用" in entry.decision

def test_parse_fallback_when_sections_missing(tmp_path):
    note_file = tmp_path / "2026-10-21-simple.md"
    note_file.write_text("# 简易测试\n随手测试了一下提示词。", encoding="utf-8")

    entry = parse_markdown_note(str(note_file))
    assert entry.date == "2026-10-21"
    assert entry.topic == "简易测试"
    assert entry.delta == ""
    assert entry.outcome == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser.py`
Expected: FAIL (cannot import `parse_markdown_note`)

- [ ] **Step 3: Implement `parse_markdown_note` in `src/lablog_mcp/parser.py`**

使用 `python-frontmatter` 解析头部元数据；通过标题分级正则匹配截取 `## 改动 / 调整`、`## 结果 / 现象`、`## 结论 / 决策` 段落；支持日期正则兜底及文件名提取。

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lablog_mcp/parser.py tests/test_parser.py
git commit -m "feat: implement markdown heuristic parser"
```

---

### Task 3: 本地目录扫描与时间线编排 (Directory Scanner & Timeline Aggregator)

**Files:**
- Create: `src/lablog_mcp/scanner.py`
- Test: `tests/test_scanner.py`

**Interfaces:**
- Consumes: `parse_markdown_note` from `parser.py`, `TimelineResponse` from `models.py`
- Produces:
  - `get_timeline(directory: str, limit: int = 20, topic_filter: str = None, order: str = "desc") -> TimelineResponse`
  - `get_detail(file_path: str) -> dict`

- [ ] **Step 1: Write the failing test for scanner**

```python
# tests/test_scanner.py
from lablog_mcp.scanner import get_timeline, get_detail

def test_get_timeline_sorting(tmp_path):
    # 创建三个不同日期的测试笔记
    (tmp_path / "2026-10-01-expA.md").write_text("# 实验 A\n## 结论\n采用", encoding="utf-8")
    (tmp_path / "2026-10-05-expB.md").write_text("# 实验 B\n## 结论\n放弃", encoding="utf-8")
    (tmp_path / "2026-10-10-expC.md").write_text("# 实验 C\n## 结论\n采用", encoding="utf-8")

    res_desc = get_timeline(str(tmp_path), limit=2, order="desc")
    assert res_desc.total == 3
    assert len(res_desc.entries) == 2
    assert res_desc.entries[0].topic == "实验 C"
    assert res_desc.entries[1].topic == "实验 B"

def test_get_detail_reads_full_content(tmp_path):
    file = tmp_path / "note.md"
    file.write_text("# 实验内容\n详细记录...", encoding="utf-8")
    detail = get_detail(str(file))
    assert detail["content"] == "# 实验内容\n详细记录..."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scanner.py`
Expected: FAIL

- [ ] **Step 3: Implement `get_timeline` and `get_detail` in `src/lablog_mcp/scanner.py`**

使用 `pathlib.Path.rglob("*.md")` 遍历目录，跳过 `.git` 等隐藏文件夹；对所有条目按 `date` 排序；支持 `limit` 和关键词 `topic_filter` 过滤。

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scanner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lablog_mcp/scanner.py tests/test_scanner.py
git commit -m "feat: implement notes directory scanner and timeline aggregator"
```

---

### Task 4: FastMCP 协议接口与服务入口 (FastMCP Server Implementation)

**Files:**
- Create: `src/lablog_mcp/server.py`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: `get_timeline`, `get_detail` from `src/lablog_mcp/scanner.py`
- Produces:
  - FastMCP App 实例与入口函数 `main()`
  - MCP 工具 `get_experiment_timeline`
  - MCP 工具 `get_experiment_detail`

- [ ] **Step 1: Write the failing test for server tools**

```python
# tests/test_server.py
from lablog_mcp.server import get_experiment_timeline, get_experiment_detail

def test_mcp_tools_callable(tmp_path):
    (tmp_path / "2026-10-01-exp.md").write_text("# 测试\n## 结论\n通过", encoding="utf-8")
    
    result = get_experiment_timeline(notes_dir=str(tmp_path))
    assert "测试" in str(result)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_server.py`
Expected: FAIL

- [ ] **Step 3: Implement `server.py` with FastMCP**

使用 `from mcp.server.fastmcp import FastMCP`；注册 `get_experiment_timeline` 与 `get_experiment_detail`；配置环境变量 `LABLOG_NOTES_DIR` 回退逻辑与 `main()` 运行函数。

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lablog_mcp/server.py tests/test_server.py
git commit -m "feat: implement FastMCP server and tool registrations"
```

---

### Task 5: 规范文档、示例与开箱即用验证 (Documentation, Examples & Packaging)

**Files:**
- Create: `examples/notes/2026-10-15-prompt-opt.md`
- Create: `examples/notes/2026-10-18-temperature-tuning.md`
- Create: `README.md`
- Create: `LICENSE`

**Interfaces:**
- 完整打包与客户端集成文档

- [ ] **Step 1: Create example notes in `examples/notes/`**

编写 2 篇生动典型的 AI 实验 Markdown 总结文档作为测试用例和展示资产。

- [ ] **Step 2: Run full test suite across all modules**

Run: `pytest tests/ -v`
Expected: 全量用例通过 (100% PASS)

- [ ] **Step 3: Create README.md and LICENSE**

编写详细的中英文 README，包含项目介绍、痛点说明、一键安装指南（`uvx` 与 `pip`）、Claude Desktop 与 Cursor 的配置 JSON 示例以及开源 MIT LICENSE。

- [ ] **Step 4: Commit**

```bash
git add examples/ README.md LICENSE
git commit -m "docs: add comprehensive documentation, examples, and MIT license"
```
