import pytest
from pathlib import Path
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
    assert "生成质量提升明显" in entry.rationale

def test_parse_fallback_when_sections_missing(tmp_path):
    note_file = tmp_path / "2026-10-21-simple.md"
    note_file.write_text("# 简易测试\n随手测试了一下提示词。", encoding="utf-8")

    entry = parse_markdown_note(str(note_file))
    assert entry.date == "2026-10-21"
    assert entry.topic == "简易测试"
    assert entry.delta == ""
    assert entry.outcome == ""
    assert entry.decision == "待定"

def test_parse_date_from_mtime(tmp_path):
    note_file = tmp_path / "nodate_experiment.md"
    note_file.write_text("# 未命名记录\n测试内容", encoding="utf-8")

    entry = parse_markdown_note(str(note_file))
    # Should be valid YYYY-MM-DD
    assert len(entry.date) == 10
    assert entry.date.count("-") == 2
    assert entry.topic == "未命名记录"

def test_parse_alternative_headers(tmp_path):
    note_content = """# 调优笔记

## 方案调整
调整 temperature 为 0.2。

## 评测数据
准确率下降 5%。

## 下一步
放弃当前参数，恢复默认。
"""
    note_file = tmp_path / "2026-10-15-temp.md"
    note_file.write_text(note_content, encoding="utf-8")

    entry = parse_markdown_note(str(note_file))
    assert "temperature 为 0.2" in entry.delta
    assert "准确率下降 5%" in entry.outcome
    assert entry.decision == "放弃"
