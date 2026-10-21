import json
import pytest
from lablog_mcp.server import get_experiment_timeline, get_experiment_detail, mcp

def test_mcp_tools_registered():
    tools = mcp._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_experiment_timeline" in tool_names
    assert "get_experiment_detail" in tool_names

def test_get_experiment_timeline_tool(tmp_path, monkeypatch):
    (tmp_path / "2026-10-21-exp.md").write_text(
        "# 测试实验\n## 实验改动\n更新代码\n## 结果\n效果良好\n## 结论\n采用",
        encoding="utf-8"
    )
    # 模拟环境变量
    monkeypatch.setenv("LABLOG_NOTES_DIR", str(tmp_path))

    res_str = get_experiment_timeline()
    data = json.loads(res_str)
    assert data["total"] == 1
    assert data["entries"][0]["topic"] == "测试实验"
    assert data["entries"][0]["decision"] == "采用"

def test_get_experiment_detail_tool(tmp_path):
    note = tmp_path / "2026-10-21-exp.md"
    note.write_text("# 详情内容\n详细记录...", encoding="utf-8")

    res_str = get_experiment_detail(str(note))
    data = json.loads(res_str)
    assert data["file_path"] == str(note.as_posix())
    assert "详细记录" in data["content"]
