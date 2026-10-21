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
    assert entry.file_path == "notes/2026-10-21-exp1.md"

def test_timeline_response():
    resp = TimelineResponse(total=0, entries=[])
    assert resp.total == 0
    assert len(resp.entries) == 0
