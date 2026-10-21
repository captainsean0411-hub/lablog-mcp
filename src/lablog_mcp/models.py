"""数据模型定义 (Pydantic Models)."""

from pydantic import BaseModel, Field


class ExperimentEntry(BaseModel):
    """单次实验的结构化核心要素."""

    file_path: str = Field(..., description="实验笔记文件路径")
    date: str = Field(..., description="实验记录日期 (YYYY-MM-DD 或 ISO 格式)")
    topic: str = Field(default="未命名实验", description="实验主题或目标")
    delta: str = Field(default="", description="本次实验所做的具体改动或参数调整")
    outcome: str = Field(default="", description="实验结果评定与指标好坏")
    decision: str = Field(default="待定", description="决策：采用 / 放弃 / 待定")
    rationale: str = Field(default="", description="采纳或放弃的原因与见解")


class TimelineResponse(BaseModel):
    """时间线查询返回结果."""

    total: int = Field(..., description="扫描到的实验总数")
    entries: list[ExperimentEntry] = Field(default_factory=list, description="实验条目列表")
