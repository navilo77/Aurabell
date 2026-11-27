"""Community service (BE-06)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.pagination import compute_pagination_meta


class CommunityError(AuthError):
    """Community domain error."""

    pass


class CommunityService:
    """Community chat: conversations, messages, read state."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Community Profile ───────────────────────────────────────────────────

    async def get_public_profile(self, user_id: str) -> dict:
        """Get public community profile for a user."""
        result = await self.db.execute(
            text(
                "SELECT id, full_name, avatar_url, created_at FROM profiles WHERE id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.mappings().first()
        if not row:
            raise CommunityError(message="User not found", code="USER_NOT_FOUND", status_code=404)

        # Get bio from a community profile table if it exists, otherwise use full_name
        bio = None
        try:
            bio_result = await self.db.execute(
                text("SELECT bio, display_name FROM user_community_profiles WHERE user_id = :uid"),
                {"uid": user_id},
            )
            bio_row = bio_result.mappings().first()
            if bio_row:
                bio = bio_row["bio"]
        except Exception:
            pass

        display_name = row["full_name"] or "User"
        try:
            bio_result = await self.db.execute(
                text("SELECT display_name FROM user_community_profiles WHERE user_id = :uid"),
                {"uid": user_id},
            )
            bio_row = bio_result.mappings().first()
            if bio_row and bio_row["display_name"]:
                display_name = bio_row["display_name"]
        except Exception:
            pass

        return {
            "user_id": str(row["id"]),
            "display_name": display_name,
            "avatar_url": row["avatar_url"] if "avatar_url" in row else None,
            "bio": bio,
            "member_since": str(row["created_at"]) if row["created_at"] else None,
        }

    async def update_own_profile(self, user_id: str, data: dict) -> dict:
        """Update own community profile."""
        # Upsert into user_community_profiles
        await self.db.execute(
            text(
                """
                INSERT INTO user_community_profiles (user_id, display_name, bio, avatar_url, updated_at)
                VALUES (:uid, :display_name, :bio, :avatar_url, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    display_name = COALESCE(:display_name, user_community_profiles.display_name),
                    bio = COALESCE(:bio, user_community_profiles.bio),
                    avatar_url = COALESCE(:avatar_url, user_community_profiles.avatar_url),
                    updated_at = NOW()
                """
            ),
            {
                "uid": user_id,
                "display_name": data.get("display_name"),
                "bio": data.get("bio"),
                "avatar_url": data.get("avatar_url"),
            },
        )
        await self.db.commit()
        return await self.get_public_profile(user_id)

    # ─── Conversations ───────────────────────────────────────────────────────

    async def create_conversation(self, user_id: str, recipient_id: str) -> dict:
        """Create or return existing direct conversation between two users."""
        if user_id == recipient_id:
            raise CommunityError(message="Cannot create conversation with yourself", code="SELF_CONVERSATION", status_code=400)

        # Verify recipient exists
        recipient = await self.db.execute(
            text("SELECT id FROM profiles WHERE id = :rid"),
            {"rid": recipient_id},
        )
        if not recipient.scalar_one_or_none():
            raise CommunityError(message="Recipient not found", code="RECIPIENT_NOT_FOUND", status_code=404)

        # Check for existing conversation (sorted pair key)
        pair_key = ":".join(sorted([user_id, recipient_id]))
        existing = await self.db.execute(
            text("SELECT id FROM conversations WHERE pair_key = :pk"),
            {"pk": pair_key},
        )
        existing_row = existing.mappings().first()
        if existing_row:
            return await self._get_conversation(str(existing_row["id"]), user_id)

        # Create new conversation
        async with self.db.begin():
            conv_result = await self.db.execute(
                text(
                    "INSERT INTO conversations (pair_key, created_at, updated_at) "
                    "VALUES (:pk, NOW(), NOW()) RETURNING id, created_at, updated_at"
                ),
                {"pk": pair_key},
            )
            conv_row = conv_result.mappings().first()
            conv_id = str(conv_row["id"])

            # Add both members
            await self.db.execute(
                text(
                    "INSERT INTO conversation_members (conversation_id, user_id, joined_at) "
                    "VALUES (:cid, :uid, NOW())"
                ),
                {"cid": conv_id, "uid": user_id},
            )
            await self.db.execute(
                text(
                    "INSERT INTO conversation_members (conversation_id, user_id, joined_at) "
                    "VALUES (:cid, :uid, NOW())"
                ),
                {"cid": conv_id, "uid": recipient_id},
            )

        return await self._get_conversation(conv_id, user_id)

    async def _get_conversation(self, conversation_id: str, user_id: str) -> dict:
        """Get conversation details with membership check."""
        # Verify membership
        member_check = await self.db.execute(
            text(
                "SELECT 1 FROM conversation_members WHERE conversation_id = :cid AND user_id = :uid"
            ),
            {"cid": conversation_id, "uid": user_id},
        )
        if not member_check.scalar_one_or_none():
            raise CommunityError(message="Conversation not found", code="NOT_FOUND", status_code=404)

        result = await self.db.execute(
            text(
                "SELECT id, created_at, updated_at FROM conversations WHERE id = :cid"
            ),
            {"cid": conversation_id},
        )
        row = result.mappings().first()
        if not row:
            raise CommunityError(message="Conversation not found", code="NOT_FOUND", status_code=404)

        # Get other user's profile
        other_member = await self.db.execute(
            text(
                "SELECT user_id FROM conversation_members WHERE conversation_id = :cid AND user_id != :uid"
            ),
            {"cid": conversation_id, "uid": user_id},
        )
        other_row = other_member.mappings().first()
        other_profile = None
        if other_row:
            other_profile = await self.get_public_profile(str(other_row["user_id"]))

        # Get last message
        last_msg = await self.db.execute(
            text(
                "SELECT content FROM messages WHERE conversation_id = :cid AND deleted_at IS NULL "
                "ORDER BY created_at DESC LIMIT 1"
            ),
            {"cid": conversation_id},
        )
        last_msg_row = last_msg.mappings().first()

        # Get unread count
        unread = await self._get_unread_count(conversation_id, user_id)

        return {
            "id": str(row["id"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "other_user": other_profile,
            "last_message": last_msg_row["content"] if last_msg_row else None,
            "unread_count": unread,
        }

    async def list_conversations(self, user_id: str) -> list[dict]:
        """List all conversations for a user."""
        result = await self.db.execute(
            text(
                "SELECT conversation_id FROM conversation_members WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        conv_ids = [str(row["conversation_id"]) for row in result.mappings().all()]

        conversations = []
        for cid in conv_ids:
            try:
                conv = await self._get_conversation(cid, user_id)
                conversations.append(conv)
            except CommunityError:
                pass

        # Sort by updated_at desc
        conversations.sort(key=lambda c: str(c["updated_at"]), reverse=True)
        return conversations

    # ─── Messages ────────────────────────────────────────────────────────────

    async def send_message(self, conversation_id: str, sender_id: str, content: str) -> dict:
        """Send a message to a conversation."""
        # Verify membership
        member_check = await self.db.execute(
            text(
                "SELECT 1 FROM conversation_members WHERE conversation_id = :cid AND user_id = :uid"
            ),
            {"cid": conversation_id, "uid": sender_id},
        )
        if not member_check.scalar_one_or_none():
            raise CommunityError(message="Conversation not found", code="NOT_FOUND", status_code=404)

        # Validate content
        content = content.strip()
        if not content:
            raise CommunityError(message="Message content cannot be empty", code="EMPTY_CONTENT", status_code=400)
        if len(content) > 4000:
            raise CommunityError(message="Message too long (max 4000 chars)", code="CONTENT_TOO_LONG", status_code=400)

        async with self.db.begin():
            result = await self.db.execute(
                text(
                    "INSERT INTO messages (conversation_id, sender_id, content, created_at, updated_at) "
                    "VALUES (:cid, :sid, :content, NOW(), NOW()) RETURNING id, conversation_id, sender_id, content, created_at, updated_at"
                ),
                {"cid": conversation_id, "sid": sender_id, "content": content},
            )
            row = result.mappings().first()

            # Update conversation updated_at
            await self.db.execute(
                text("UPDATE conversations SET updated_at = NOW() WHERE id = :cid"),
                {"cid": conversation_id},
            )

        return {
            "id": str(row["id"]),
            "conversation_id": str(row["conversation_id"]),
            "sender_id": str(row["sender_id"]),
            "content": row["content"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "deleted_at": None,
        }

    async def list_messages(
        self,
        conversation_id: str,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        format_param: str | None = None,
    ) -> list | dict:
        """List messages in a conversation with pagination."""
        # Verify membership
        member_check = await self.db.execute(
            text(
                "SELECT 1 FROM conversation_members WHERE conversation_id = :cid AND user_id = :uid"
            ),
            {"cid": conversation_id, "uid": user_id},
        )
        if not member_check.scalar_one_or_none():
            raise CommunityError(message="Conversation not found", code="NOT_FOUND", status_code=404)

        # Count total
        count_result = await self.db.execute(
            text(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = :cid AND deleted_at IS NULL"
            ),
            {"cid": conversation_id},
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * per_page
        result = await self.db.execute(
            text(
                "SELECT id, conversation_id, sender_id, content, created_at, updated_at, deleted_at "
                "FROM messages WHERE conversation_id = :cid AND deleted_at IS NULL "
                "ORDER BY created_at ASC LIMIT :limit OFFSET :offset"
            ),
            {"cid": conversation_id, "limit": per_page, "offset": offset},
        )
        rows = result.mappings().all()
        messages = [
            {
                "id": str(row["id"]),
                "conversation_id": str(row["conversation_id"]),
                "sender_id": str(row["sender_id"]),
                "content": row["content"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "deleted_at": row["deleted_at"],
            }
            for row in rows
        ]

        from app.core.pagination import paginate
        return paginate(messages, total, page, per_page, format_param)

    # ─── Read State ──────────────────────────────────────────────────────────

    async def mark_read(self, conversation_id: str, user_id: str) -> None:
        """Mark conversation as read for the user."""
        member_check = await self.db.execute(
            text(
                "SELECT 1 FROM conversation_members WHERE conversation_id = :cid AND user_id = :uid"
            ),
            {"cid": conversation_id, "uid": user_id},
        )
        if not member_check.scalar_one_or_none():
            raise CommunityError(message="Conversation not found", code="NOT_FOUND", status_code=404)

        await self.db.execute(
            text(
                "UPDATE conversation_members SET last_read_at = NOW() "
                "WHERE conversation_id = :cid AND user_id = :uid"
            ),
            {"cid": conversation_id, "uid": user_id},
        )
        await self.db.commit()

    async def _get_unread_count(self, conversation_id: str, user_id: str) -> int:
        """Get unread message count for a user in a conversation."""
        result = await self.db.execute(
            text(
                "SELECT COUNT(*) FROM messages m "
                "JOIN conversation_members cm ON cm.conversation_id = m.conversation_id "
                "WHERE m.conversation_id = :cid AND m.sender_id != :uid "
                "AND m.deleted_at IS NULL "
                "AND (cm.last_read_at IS NULL OR m.created_at > cm.last_read_at) "
                "AND cm.user_id = :uid"
            ),
            {"cid": conversation_id, "uid": user_id},
        )
        return result.scalar() or 0
