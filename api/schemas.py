from datetime import date
from typing import Optional

from pydantic import BaseModel


class TopProduct(BaseModel):
    token: str
    mentions: int


class ChannelActivityPoint(BaseModel):
    date: date
    message_count: int
    avg_views: Optional[float] = None


class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: str
    message_date: date
    view_count: int
    forward_count: int


class VisualContentStats(BaseModel):
    channel_name: str
    total_messages: int
    image_messages: int
    image_rate: Optional[float] = None
    promotional: int = 0
    product_display: int = 0
    lifestyle: int = 0
    other: int = 0


