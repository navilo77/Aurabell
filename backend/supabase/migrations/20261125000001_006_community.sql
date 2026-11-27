-- BE-06: Community / Chat Backend
-- Migration: conversations, conversation_members, messages, message_reads

-- ─── Community Profiles (optional bio/display_name) ───────────────────────────

CREATE TABLE public.user_community_profiles (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    bio VARCHAR(500),
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Conversations ────────────────────────────────────────────────────────────

CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Conversation Members ─────────────────────────────────────────────────────

CREATE TABLE public.conversation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    last_read_at TIMESTAMPTZ,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (conversation_id, user_id)
);

-- Unique index to prevent duplicate direct conversations between same two users
-- Enforced via a pair key (smaller UUID first)
CREATE UNIQUE INDEX uq_conversation_pair
ON public.conversation_members (conversation_id)
WHERE FALSE;  -- placeholder, replaced below

-- Actually, we enforce uniqueness at the application level using a sorted pair.
-- Add a helper column for pair uniqueness.
ALTER TABLE public.conversations ADD COLUMN pair_key VARCHAR(80) UNIQUE;

CREATE INDEX idx_conversation_members_user ON public.conversation_members(user_id);
CREATE INDEX idx_conversation_members_conversation ON public.conversation_members(conversation_id);

-- ─── Messages ─────────────────────────────────────────────────────────────────

CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES public.profiles(id),
    content TEXT NOT NULL CHECK (char_length(content) BETWEEN 1 AND 4000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_messages_conversation_created ON public.messages(conversation_id, created_at ASC);
CREATE INDEX idx_messages_sender ON public.messages(sender_id);

-- ─── RLS Policies ─────────────────────────────────────────────────────────────

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Conversations: user can read if they are a member
CREATE POLICY "conversations_member_read"
ON public.conversations FOR SELECT
USING (
    id IN (
        SELECT conversation_id FROM public.conversation_members
        WHERE user_id = auth.uid()
    )
);

-- Conversation members: user can read their own memberships
CREATE POLICY "conversation_members_own_read"
ON public.conversation_members FOR SELECT
USING (user_id = auth.uid());

-- Conversation members: user can read other members of their conversations
CREATE POLICY "conversation_members_conversation_read"
ON public.conversation_members FOR SELECT
USING (
    conversation_id IN (
        SELECT conversation_id FROM public.conversation_members
        WHERE user_id = auth.uid()
    )
);

-- Messages: user can read messages in conversations they belong to
CREATE POLICY "messages_member_read"
ON public.messages FOR SELECT
USING (
    conversation_id IN (
        SELECT conversation_id FROM public.conversation_members
        WHERE user_id = auth.uid()
    )
);

-- Messages: user can insert only as themselves in conversations they belong to
CREATE POLICY "messages_member_insert"
ON public.messages FOR INSERT
WITH CHECK (
    sender_id = auth.uid()
    AND conversation_id IN (
        SELECT conversation_id FROM public.conversation_members
        WHERE user_id = auth.uid()
    )
);

-- Conversation members: user can update their own last_read_at
CREATE POLICY "conversation_members_own_update"
ON public.conversation_members FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());
