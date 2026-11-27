import { apiFetch, apiFetchOptional } from "@/lib/api";
import type {
  CommunityProfileRead,
  CommunityProfileUpdate,
  ConversationRead,
  ConversationCreate,
  MessageRead,
  MessageCreate,
  PaginatedResponse,
} from "@/lib/types";

// ─── Community Profile ────────────────────────────────────────────────────────

export async function getPublicProfile(userId: string): Promise<CommunityProfileRead> {
  return apiFetch<CommunityProfileRead>(`/community/users/${userId}/profile`);
}

export async function getOwnProfile(): Promise<CommunityProfileRead> {
  return apiFetch<CommunityProfileRead>("/community/profile/me");
}

export async function updateOwnProfile(data: CommunityProfileUpdate): Promise<CommunityProfileRead> {
  return apiFetch<CommunityProfileRead>("/community/profile/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ─── Conversations ────────────────────────────────────────────────────────────

export async function listConversations(): Promise<ConversationRead[]> {
  return apiFetch<ConversationRead[]>("/community/conversations");
}

export async function createConversation(data: ConversationCreate): Promise<ConversationRead> {
  return apiFetch<ConversationRead>("/community/conversations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getConversation(conversationId: string): Promise<ConversationRead> {
  return apiFetch<ConversationRead>(`/community/conversations/${conversationId}`);
}

// ─── Messages ──────────────────────────────────────────────────────────────────

export async function listMessages(
  conversationId: string,
  page: number = 1,
  perPage: number = 20,
  format: "v2" | null = "v2"
): Promise<PaginatedResponse<MessageRead> | MessageRead[]> {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString(),
  });
  if (format) params.set("format", format);
  return apiFetch<PaginatedResponse<MessageRead> | MessageRead[]>(
    `/community/conversations/${conversationId}/messages?${params.toString()}`
  );
}

export async function sendMessage(
  conversationId: string,
  data: MessageCreate
): Promise<MessageRead> {
  return apiFetch<MessageRead>(`/community/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ─── Read State ────────────────────────────────────────────────────────────────

export async function markConversationRead(conversationId: string): Promise<void> {
  return apiFetch<void>(`/community/conversations/${conversationId}/read`, {
    method: "POST",
  });
}

// ─── Optional (for unauthenticated access) ────────────────────────────────────

export async function getPublicProfileOptional(
  userId: string
): Promise<CommunityProfileRead | null> {
  return apiFetchOptional<CommunityProfileRead>(`/community/users/${userId}/profile`);
}