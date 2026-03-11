"""
Widget Schemas for WhatsApp RAG Assistant
"""
from pydantic import BaseModel
from typing import Optional


class WidgetConfigUpdate(BaseModel):
    position: Optional[str] = None  # 'bottom-right', 'bottom-left', 'top-right', 'top-left'
    color_scheme: Optional[str] = None
    icon_type: Optional[str] = None
    pre_filled_message: Optional[str] = None
    is_enabled: Optional[bool] = None


class WidgetConfigResponse(BaseModel):
    widget_id: str
    position: str
    color_scheme: str
    icon_type: str
    pre_filled_message: str
    is_enabled: bool

    class Config:
        from_attributes = True