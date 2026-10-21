import pytest
from pathlib import Path
from lablog_mcp.scanner import get_timeline, get_detail

def test_get_timeline_sorting_and_limit(tmp_path):
    (tmp_path / "2026-10-01-expA.md").write_text("# 实验 A\n## 结论\n采用", encoding="utf-8")
    (tmp_path / "2026-10-05-expB.md").write_text("# 实验 B\n## 结论\n放弃", encoding="utf-8")
    (tmp_path / "2026-10-10-expC.md").write_text("# 实验 C\n## 结论\n采用", encoding="utf-8")

    # 降序，最新优先
    res_desc = get_timeline(str(tmp_path), limit=2, order="desc")
    assert res_desc.total == 3
    assert len(res_desc.entries) == 2
    assert res_desc.entries[0].topic == "实验 C"
    assert res_desc.entries[1].topic == "实验 B"

    # 升序
    res_asc = get_timeline(str(tmp_path), limit=3, order="asc")
    assert res_asc.entries[0].topic == "实验 A"
    assert res_asc.entries[2].topic == "实验 C"

def test_get_timeline_topic_filter(tmp_path):
    (tmp_path / "2026-10-01-model_lora.md").write_text("# 模型 LoRA 实验\n## 结论\n采用", encoding="utf-8")
    (tmp_path / "2026-10-02-data_clean.md").write_text("# 数据清洗实验\n## 结论\n采用", encoding="utf-8")

    filtered = get_timeline(str(tmp_path), topic_filter="LoRA")
    assert filtered.total == 1
    assert filtered.entries[0].topic == "模型 LoRA 实验"

def test_get_timeline_nonexistent_directory():
    res = get_timeline("nonexistent_path_xyz_123")
    assert res.total == 0
    assert len(res.entries) == 0

def test_get_timeline_ignores_hidden_dirs(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "2026-10-01-git-commit.md").write_text("# Git 内部忽略文件", encoding="utf-8")
    (tmp_path / "2026-10-01-valid.md").write_text("# 有效实验", encoding="utf-8")

    res = get_timeline(str(tmp_path))
    assert res.total == 1
    assert res.entries[0].topic == "有效实验"

def test_get_detail_success(tmp_path):
    note = tmp_path / "2026-10-21-detail.md"
    content = "# 深度实验详情\n\n- 环境: CUDA 12.4\n- 状态: 完成"
    note.write_text(content, encoding="utf-8")

    detail = get_detail(str(note))
    assert detail["file_path"] == str(note.as_posix())
    assert detail["content"] == content
    assert detail["entry"]["topic"] == "深度实验详情"

def test_get_detail_not_found():
    detail = get_detail("not_existing.md")
    assert "error" in detail


def test_get_timeline_friendly_message():
    res = get_timeline("nonexistent_path_xyz_123")
    assert res.total == 0
    assert res.message is not None
    assert "不存在" in res.message

def test_get_detail_security_extension(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=123456", encoding="utf-8")

    detail = get_detail(str(env_file))
    assert "error" in detail
    assert "安全限制" in detail["error"]
