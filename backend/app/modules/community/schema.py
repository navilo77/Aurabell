"""Community module schemas (BE-06)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CommunityProfileRead(BaseModel):
    """Public community profile (safe fields only)."""

    user_id: str
    display_name: str
    avatar_url: str | None = None
    bio: str | None = None
    member_since: datetime | None = None


class CommunityProfileUpdate(BaseModel):
    """Update own community profile."""

    display_name: str | None = Field(None, min_length=1, max_length=100)
    avatar_url: str | None = None
    bio: str | None = Field(None, max_length=500)


class ConversationCreate(BaseModel):
    """Create a direct conversation."""

    recipient_id: str = Field(..., description="Recipient user UUID")


class ConversationRead(BaseModel):
    """Conversation response."""

    id: str
    created_at: datetime
    updated_at: datetime
    other_user: CommunityProfileRead | None = None
    last_message: str | None = None
    unread_count: int = 0


class MessageCreate(BaseModel):
    """Send a message."""

    content: str = Field(..., min_length=1, max_length=4000, description="Message content (1-4000 chars)")


class MessageRead(BaseModel):
    """Message response."""

    id: str
    conversation_id: str
    sender_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ConversationMemberRead(BaseModel):
    """Conversation member info."""

    user_id: str
    last_read_at: datetime | None = None
    joined_at: datetime


class ReadStateUpdate(BaseModel):
    """Mark conversation as read (no body needed, but defined for contract)."""

    pass
