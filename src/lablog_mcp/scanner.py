"""目录扫描与时间线编排器."""

from pathlib import Path
from typing import Optional

from lablog_mcp.models import ExperimentEntry, TimelineResponse
from lablog_mcp.parser import parse_markdown_note

IGNORED_DIRS = {
    ".git",
    ".svn",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    ".superpowers",
}


def _should_ignore(path: Path) -> bool:
    """检查路径中是否包含应忽略的目录."""
    for part in path.parts:
        if part in IGNORED_DIRS or part.startswith("."):
            return True
    return False


def get_timeline(
    directory: str = ".",
    limit: Optional[int] = 20,
    topic_filter: Optional[str] = None,
    order: Optional[str] = "desc",
) -> TimelineResponse:
    """扫描指定目录下的 Markdown 笔记并生成时间线."""
    target_dir = Path(directory)
    if not target_dir.exists():
        return TimelineResponse(
            total=0,
            entries=[],
            message=f"指定的笔记目录不存在: {directory}，请检查路径配置或环境变量 LABLOG_NOTES_DIR",
        )
    if not target_dir.is_dir():
        return TimelineResponse(
            total=0,
            entries=[],
            message=f"指定的路径不是有效文件夹: {directory}",
        )

    all_entries: list[ExperimentEntry] = []

    for file_path in target_dir.rglob("*.md"):
        try:
            rel_path = file_path.relative_to(target_dir)
            if _should_ignore(rel_path):
                continue
        except ValueError:
            if _should_ignore(file_path):
                continue

        try:
            entry = parse_markdown_note(str(file_path))
            if topic_filter:
                filter_lower = topic_filter.lower()
                matched = (
                    filter_lower in entry.topic.lower()
                    or filter_lower in entry.delta.lower()
                    or filter_lower in entry.outcome.lower()
                )
                if not matched:
                    continue
            all_entries.append(entry)
        except Exception:
            continue

    order_str = (order or "desc").lower()
    is_descending = order_str == "desc"
    all_entries.sort(key=lambda x: (x.date, x.file_path), reverse=is_descending)

    total_count = len(all_entries)
    effective_limit = 20 if limit is None else limit
    sliced_entries = all_entries[: max(0, effective_limit)] if effective_limit > 0 else all_entries

    msg = None
    if total_count == 0:
        msg = f"在目录 '{directory}' 中未找到匹配的 Markdown 实验笔记"

    return TimelineResponse(total=total_count, entries=sliced_entries, message=msg)


def get_detail(file_path: str) -> dict:
    """获取单篇实验笔记的完整原文与结构化数据."""
    path = Path(file_path)
    # 安全边界检查：仅允许访问 Markdown 格式文件，防止读取敏感系统文件
    if path.suffix.lower() not in {".md", ".markdown"}:
        return {"error": f"安全限制：仅允许读取 Markdown 实验笔记 (.md, .markdown)，拒绝访问: {file_path}"}

    if not path.exists() or not path.is_file():
        return {"error": f"未找到实验笔记文件: {file_path}"}

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        entry = parse_markdown_note(str(path), raw_content=content)
        return {
            "file_path": str(path.as_posix()),
            "content": content,
            "entry": entry.model_dump(),
        }
    except Exception as e:
        return {"error": f"读取实验笔记失败: {str(e)}"}
