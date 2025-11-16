from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TargetWindowConfigModel(BaseModel):
    title_contains: Optional[str] = Field(default=None, description="窗口标题包含的关键字")
    process_name: Optional[str] = Field(default=None, description="可选进程名")
    hwnd: Optional[int] = Field(default=None, description="指定窗口句柄")


class RectModel(BaseModel):
    x: float
    y: float
    width: float
    height: float
    type: str = "relative"


class TemplateClickPaddingModel(BaseModel):
    left: float = 0
    right: float = 0
    top: float = 0
    bottom: float = 0


class TemplateClickModel(BaseModel):
    mode: str = "center"
    padding: TemplateClickPaddingModel = Field(default_factory=TemplateClickPaddingModel)


class TemplateMatchModel(BaseModel):
    threshold: float = 0.85
    method: str = "TM_CCOEFF_NORMED"


class TemplateDefinitionModel(BaseModel):
    key: str
    file: str
    description: str = ""
    match: TemplateMatchModel = Field(default_factory=TemplateMatchModel)
    search_region: Optional[RectModel] = None
    click: TemplateClickModel = Field(default_factory=TemplateClickModel)
    type: str = "click"


class SaveTemplateRequest(BaseModel):
    task_id: Optional[str] = Field(default=None, description="所属任务，用于按任务分目录存放模板图")
    base_image_path: str
    template_rect: RectModel
    search_region: Optional[RectModel] = None
    key: str
    description: str = ""
    threshold: float = 0.85
    click_mode: str = "center"
    padding: TemplateClickPaddingModel = Field(default_factory=TemplateClickPaddingModel)
    match_method: str = "TM_CCOEFF_NORMED"


class TemplateTestRequest(BaseModel):
    key: str
    base_image_path: str


class TaskDefinitionModel(BaseModel):
    id: str
    name: str
    script: str = "main.py"
    entry: str = "MainTask"
    path: Optional[str] = None
    templates_path: Optional[str] = None
    script_content: Optional[str] = None
    target_window: Optional[TargetWindowConfigModel] = None


class LogRecordModel(BaseModel):
    level: str
    message: str
    task_id: Optional[str] = None
    created_at: float


class TaskListResponse(BaseModel):
    tasks: List[TaskDefinitionModel]
