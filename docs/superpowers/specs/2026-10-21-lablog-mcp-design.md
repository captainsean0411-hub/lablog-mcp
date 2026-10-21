# Design Spec: lablog-mcp (实验日志时间线 MCP 服务)

- **Date**: 2026-10-21
- **Status**: Reviewed & Ready (工程评审通过)
- **Target Audience**: AI 辅助开发/科研人员、大模型调优工程师、实验记录者

---

## 1. 意图与初衷 (Intent & The Why)

### 1.1 业务与个人初衷
1. **建立首个高质量开源资产**：作为项目发起人的第一个 Python 开源项目，具备清晰的解决场景与持续维护价值。
2. **满足开源维护者认证需求**：契合 OpenAI “Codex for Open Source” 官方资助计划的评审偏好（重视开发者工作流工具、代码质量、自动化以及现代 AI/MCP 生态整合）。
3. **解决实际实验痛点**：在利用 AI 进行开发、调参或算法实验时，用户通常会使用 AI 生成一篇篇分散的 Markdown 实验小结。随着实验次数增加，实验记录碎片化严重，开发者难以快速回溯历史演进，极易重复踩坑或混淆最佳参数配置。

### 1.2 核心愿景
用户在 AI 客户端（如 Claude Desktop、Cursor 等）中只需简单输入**“查看实验日志”**，MCP 服务便能自动遍历扫描指定文件夹下的所有 Markdown 笔记，提取每次实验的关键信息，按时间线拼装成结构化演进记录，辅助用户理顺实验思路、进行方案优化与复现。

---

## 2. 目标、非目标与反面目标 (Goals, Non-goals & Anti-goals)

### 2.1 目标 (Goals)
- **核心工具暴露**：基于官方 Python `FastMCP` 提供标准 MCP 工具：
  - `get_experiment_timeline(notes_dir: str = None, limit: int = 20, topic: str = None, order: str = "desc")`：返回结构化实验里程碑摘要（默认降序，最新优先）。
  - `get_experiment_detail(file_path: str)`：获取某次具体实验的完整上下文、参数与复现细节。
- **关键维度提取**：每条实验记录提取 4 大核心要素：
  1. **时间与主题**（Date & Topic）
  2. **实验改动**（What was changed / Delta）
  3. **结果评定**（Outcome / Good or Bad）
  4. **决策与原因**（Decision & Rationale: 采纳/放弃及其精简理由）
- **高兼容性文本解析**：兼容主流 AI 常见生成的 Markdown 格式（基于常见二级标题如 `## 结论`、`## 结果`、`## 改动` 等进行启发式抽取，支持 YAML Frontmatter 元数据及文件名日期识别）。
- **新手友好的工程规范**：配置 `pyproject.toml`，支持 `uvx` / `pip install -e .` 一键运行；包含完整的 `pytest` 自动化测试与中英文专业 README。

### 2.2 非目标 (Non-Goals)
- 不开发独立的前端 GUI 网页（用户直接借助 Claude Desktop、Cursor、Cline 等 AI 宿主界面交互）。
- 不引入重型数据库（如 PostgreSQL/Milvus），坚持纯文件系统驱动，免运维、零配置负担。
- 不强制要求云端同步或多端协作。

### 2.3 反面目标 (Anti-Goals)
- **绝对不修改、重写或损坏用户的原始 Markdown 笔记**（所有操作必须是只读的）。
- **杜绝过度工程化**：避免在 V1.0 中强行引入重量级向量数据库或复杂本地嵌入模型，防止依赖膨胀和跨平台安装报错。

---

## 3. 技术约束与规范 (Constraints)

- **语言环境**：Python 3.10+
- **核心依赖**：
  - `mcp[cli]>=1.0.0`（Anthropic / OpenAI 兼容的标准 MCP Python SDK）
  - `python-frontmatter` 或轻量级正则解析器（用于提取 Markdown 元信息）
  - `pytest`（单元测试框架）
- **目录结构与分层**：
  ```text
  lablog-mcp/
  ├── src/
  │   └── lablog_mcp/
  │       ├── __init__.py
  │       ├── server.py       # FastMCP 工具注册与服务入口
  │       ├── parser.py       # Markdown 实验笔记解析核心逻辑
  │       └── models.py       # 实验数据结构定义 (Pydantic)
  ├── tests/
  │   ├── test_parser.py     # 解析逻辑测试
  │   └── test_server.py     # MCP 服务通信测试
  ├── examples/
  │   └── notes/             # 示例测试实验笔记
  ├── pyproject.toml         # 现代 Python 打包标准
  ├── README.md              # 详尽安装与接入文档 (带接入示例)
  └── LICENSE                # MIT 开源协议
  ```

---

## 4. 用户决策 (Decisions Made)

- **实现方式**：采用官方推荐的 `FastMCP` 接口，保证极简代码量与易读性。
- **用户交互流程**：
  1. 用户启动 AI 客户端并配置 `lablog-mcp`。
  2. 用户在聊天框输入“查看实验日志”或“帮我对比过去一周在模型调参上的改动和结果”。
  3. AI 自动调用 `get_experiment_timeline` 工具获取提取后的关键字段。
  4. AI 在聊天界面组织成直观的时间线表格或总结卡片。

---

## 5. 开发者自主裁量项与工程决策 (Builder's Calls)

1. **默认排序规则**：时间线默认按时间**降序**（`order="desc"`，最新实验优先展示），符合回顾最新实验进展的习惯。
2. **默认笔记路径回退**：`notes_dir` 若未传参，按优先级检查环境变量 `LABLOG_NOTES_DIR` -> 当前进程工作目录 `.`。
3. **启发式关键词词库**：
   - 改动字段：匹配 `## 实验改动`、`## 方案调整`、`## 参数配置`、`## 变量`。
   - 结果字段：匹配 `## 实验结果`、`## 评测数据`、`## 结果`、`## 现象`。
   - 决策字段：匹配 `## 结论`、`## 决策`、`## 是否采纳`、`## 下一步`。
4. **日期容错**：优先解析 Frontmatter `date`，其次正则提取文件名中 `YYYY-MM-DD`，最后回退读取文件修改时间。
