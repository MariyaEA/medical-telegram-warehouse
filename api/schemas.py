"""Pydantic response schemas for analytical API endpoints."""
from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class TopProduct(BaseModel):
    product_term: str
    mention_count: int


class ChannelActivity(BaseModel):
    channel_name: str
    activity_date: date
    post_count: int
    total_views: int
    total_forwards: int


class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_date: date
    message_text: str
    view_count: int
    forward_count: int
    has_image: bool


class VisualContentStats(BaseModel):
    channel_name: str
    total_messages: int
    image_messages: int
    image_share: float = Field(..., description="Share of messages that contain images")
    promotional_posts: Optional[int] = 0
    product_display_posts: Optional[int] = 0
    lifestyle_posts: Optional[int] = 0
    other_posts: Optional[int] = 0
