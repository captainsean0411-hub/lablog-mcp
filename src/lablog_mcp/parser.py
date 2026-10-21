"""Markdown 实验笔记启发式解析器."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional
import frontmatter

from lablog_mcp.models import ExperimentEntry

# 启发式关键词配置
DELTA_KEYWORDS = ["改动", "调整", "变量", "参数", "方案", "change", "delta", "setup", "config"]
OUTCOME_KEYWORDS = ["结果", "评测", "现象", "指标", "表现", "outcome", "result", "metric", "eval"]
DECISION_KEYWORDS = ["结论", "决策", "采纳", "下一步", "总结", "decision", "conclusion", "summary"]

RE_NEGATIVE = re.compile(
    r"(放弃|不采用|不采纳|未采纳|未采用|未通过|不通过|不保留|弃用|淘汰|失败|fail|reject|discard|drop|not\s+pass)",
    re.IGNORECASE,
)
RE_POSITIVE = re.compile(
    r"(采用|采纳|通过|保留|adopt|keep|pass)",
    re.IGNORECASE,
)


def _extract_date(post_metadata: dict, file_path: Path) -> str:
    """提取日期，依次尝试：Frontmatter -> 文件名正则 -> 文件修改时间."""
    # 1. Frontmatter
    if "date" in post_metadata and post_metadata["date"]:
        d = str(post_metadata["date"]).strip().split(" ")[0].split("T")[0]
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            return d

    # 2. 文件名正则匹配 YYYY-MM-DD
    match = re.search(r"(\d{4}-\d{2}-\d{2})", file_path.name)
    if match:
        return match.group(1)

    # 3. 文件修改时间
    try:
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def _extract_topic(post_metadata: dict, content: str, file_path: Path) -> str:
    """提取实验主题."""
    if "topic" in post_metadata and post_metadata["topic"]:
        return str(post_metadata["topic"]).strip()
    if "title" in post_metadata and post_metadata["title"]:
        return str(post_metadata["title"]).strip()

    # 从首个 # 一级或二级标题中提取
    title_match = re.search(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
    if title_match:
        raw_title = title_match.group(1).strip()
        # 清除显式日志前缀如 "实验日志："、"实验记录：" 等
        cleaned = re.sub(
            r"^(实验日志|实验记录|实验总结|Experiment\s*Log|Experiment\s*Notes)[:：\s]+",
            "",
            raw_title,
            flags=re.IGNORECASE,
        )
        if cleaned:
            return cleaned

    # 回退到文件名
    stem = file_path.stem
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}[-_]?", "", stem)
    return stem or "未命名实验"


def _split_into_sections(content: str) -> dict[str, str]:
    """将 Markdown 内容按二级/三级标题拆分为 {标题名: 内容}，自动忽略代码块内的注释."""
    sections = {}
    lines = content.splitlines()
    current_header = "__intro__"
    current_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            current_lines.append(line)
            continue

        if not in_code_block:
            header_match = re.match(r"^#{2,3}\s+(.+)$", stripped)
            if header_match:
                if current_lines:
                    sections[current_header] = "\n".join(current_lines).strip()
                    current_lines = []
                current_header = header_match.group(1).strip()
                continue

        current_lines.append(line)

    if current_lines:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def _match_section_content(sections: dict[str, str], keywords: list[str]) -> str:
    """根据关键词在各个标题中寻找对应段落内容."""
    for header, body in sections.items():
        header_lower = header.lower()
        if any(kw in header_lower for kw in keywords):
            return body
    return ""


def _determine_decision(text: str) -> tuple[str, str]:
    """判定采纳还是放弃，并提取简要说明."""
    if not text:
        return "待定", ""

    # 优先检测否定词（避免“未通过”命中“通过”）
    if RE_NEGATIVE.search(text):
        return "放弃", text.strip()
    if RE_POSITIVE.search(text):
        return "采用", text.strip()

    return "待定", text.strip()


def parse_markdown_note(file_path: str, raw_content: Optional[str] = None) -> ExperimentEntry:
    """解析单篇 Markdown 实验笔记."""
    path = Path(file_path)

    if raw_content is None:
        raw_content = path.read_text(encoding="utf-8", errors="replace")

    metadata = {}
    content = raw_content

    # 增强 Frontmatter 解析容错，防止非标准 YAML 导致崩溃
    try:
        post = frontmatter.loads(raw_content)
        if isinstance(post.metadata, dict):
            metadata = post.metadata
        content = post.content
    except Exception:
        metadata = {}
        content = raw_content

    date_str = _extract_date(metadata, path)
    topic_str = _extract_topic(metadata, content, path)
    sections = _split_into_sections(content)

    delta_text = _match_section_content(sections, DELTA_KEYWORDS)
    outcome_text = _match_section_content(sections, OUTCOME_KEYWORDS)
    decision_section_text = _match_section_content(sections, DECISION_KEYWORDS)

    decision, rationale = _determine_decision(decision_section_text)

    return ExperimentEntry(
        file_path=str(path.as_posix()),
        date=date_str,
        topic=topic_str,
        delta=delta_text,
        outcome=outcome_text,
        decision=decision,
        rationale=rationale,
    )
