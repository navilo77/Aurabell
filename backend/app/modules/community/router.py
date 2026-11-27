"""Community router (BE-06)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, get_current_user
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.modules.community.schema import (
    CommunityProfileRead,
    CommunityProfileUpdate,
    ConversationCreate,
    ConversationRead,
    MessageCreate,
    MessageRead,
    ReadStateUpdate,
)
from app.modules.community.service import CommunityError, CommunityService

router = APIRouter(prefix="/community", tags=["Community"])


def get_community_service(db: AsyncSession = Depends(get_db)):
    return CommunityService(db)


# ─── Community Profile ──────────────────────────────────────────────────────────


@router.get(
    "/users/{user_id}/profile",
    response_model=CommunityProfileRead,
    summary="Get public community profile",
)
async def get_public_profile(
    user_id: str = Path(..., description="User UUID"),
    service: CommunityService = Depends(get_community_service),
):
    """Get public community profile for a user."""
    try:
        data = await service.get_public_profile(user_id)
        return CommunityProfileRead(**data)
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.get(
    "/profile/me",
    response_model=CommunityProfileRead,
    summary="Get own community profile",
)
async def get_own_profile(
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Get own community profile."""
    try:
        data = await service.get_public_profile(str(user.id))
        return CommunityProfileRead(**data)
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.patch(
    "/profile/me",
    response_model=CommunityProfileRead,
    summary="Update own community profile",
)
async def update_own_profile(
    data: CommunityProfileUpdate,
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Update own community profile."""
    try:
        update_data = data.model_dump(exclude_unset=True)
        result = await service.update_own_profile(str(user.id), update_data)
        return CommunityProfileRead(**result)
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


# ─── Conversations ──────────────────────────────────────────────────────────────


@router.get(
    "/conversations",
    summary="List conversations",
)
async def list_conversations(
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """List all conversations for the authenticated user."""
    try:
        convs = await service.list_conversations(str(user.id))
        return convs
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or get direct conversation",
)
async def create_conversation(
    data: ConversationCreate,
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Create or return existing direct conversation with a recipient."""
    try:
        conv = await service.create_conversation(str(user.id), data.recipient_id)
        return ConversationRead(**conv)
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
    summary="Get conversation details",
)
async def get_conversation(
    conversation_id: str = Path(..., description="Conversation UUID"),
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Get conversation details."""
    try:
        conv = await service._get_conversation(conversation_id, str(user.id))
        return ConversationRead(**conv)
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


# ─── Messages ───────────────────────────────────────────────────────────────────


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="List messages in conversation",
)
async def list_messages(
    conversation_id: str = Path(..., description="Conversation UUID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    format: str | None = Query(None, description="Response format: 'v2' for paginated {data, meta}"),
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """List messages in a conversation with pagination."""
    try:
        return await service.list_messages(conversation_id, str(user.id), page=page, per_page=per_page, format_param=format)
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
)
async def send_message(
    conversation_id: str = Path(..., description="Conversation UUID"),
    data: MessageCreate = ...,
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Send a message to a conversation."""
    try:
        msg = await service.send_message(conversation_id, str(user.id), data.content)
        return MessageRead(**msg)
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


# ─── Read State ─────────────────────────────────────────────────────────────────


@router.post(
    "/conversations/{conversation_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark conversation as read",
)
async def mark_read(
    conversation_id: str = Path(..., description="Conversation UUID"),
    user: User = Depends(get_current_user),
    service: CommunityService = Depends(get_community_service),
):
    """Mark a conversation as read for the authenticated user."""
    try:
        await service.mark_read(conversation_id, str(user.id))
    except CommunityError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e
