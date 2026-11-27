"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { supabase, type SupabaseClient } from "@/lib/supabase";
import { useAuth } from "@/lib/auth-context";
import type { MessageRead } from "@/lib/types";

interface UseRealtimeMessagesOptions {
  conversationId: string | null;
  onNewMessage: (message: MessageRead) => void;
  enabled?: boolean;
}

export function useRealtimeMessages({
  conversationId,
  onNewMessage,
  enabled = true,
}: UseRealtimeMessagesOptions) {
  const { user } = useAuth();
  const channelRef = useRef<ReturnType<SupabaseClient["channel"]> | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const processedMessageIds = useRef<Set<string>>(new Set());

  const handleNewMessage = useCallback(
    (payload: { new: MessageRead }) => {
      const message = payload.new;
      if (!message) return;

      if (processedMessageIds.current.has(message.id)) {
        return;
      }
      processedMessageIds.current.add(message.id);

      onNewMessage(message);
    },
    [onNewMessage]
  );

  useEffect(() => {
    if (!enabled || !conversationId || !user || !supabase) {
      if (channelRef.current) {
        supabase?.removeChannel(channelRef.current);
        channelRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    const channelName = `messages:conversation:${conversationId}`;

    channelRef.current = supabase
      .channel(channelName, {
        config: {
          broadcast: { self: false },
          presence: { key: user.id },
        },
      })
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
          filter: `conversation_id=eq.${conversationId}`,
        },
        handleNewMessage
      )
      .subscribe((status) => {
        if (status === "SUBSCRIBED") {
          setIsConnected(true);
          setError(null);
        } else if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
          setIsConnected(false);
          setError("Realtime connection failed");
        } else if (status === "CLOSED") {
          setIsConnected(false);
        }
      });

    return () => {
      if (channelRef.current) {
        supabase?.removeChannel(channelRef.current);
        channelRef.current = null;
        setIsConnected(false);
      }
    };
  }, [conversationId, user, enabled, handleNewMessage]);

  return { isConnected, error };
}

// ─── Conversation List Realtime ──────────────────────────────────────────────

interface UseRealtimeConversationsOptions {
  onConversationUpdate: () => void;
  enabled?: boolean;
}

export function useRealtimeConversations({
  onConversationUpdate,
  enabled = true,
}: UseRealtimeConversationsOptions) {
  const { user } = useAuth();
  const channelRef = useRef<ReturnType<SupabaseClient["channel"]> | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!enabled || !user || !supabase) {
      if (channelRef.current) {
        supabase?.removeChannel(channelRef.current);
        channelRef.current = null;
        setIsConnected(false);
      }
      return;
    }

    const channelName = `conversations:user:${user.id}`;

    channelRef.current = supabase
      .channel(channelName, {
        config: {
          broadcast: { self: false },
        },
      })
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "conversation_members",
          filter: `user_id=eq.${user.id}`,
        },
        () => {
          onConversationUpdate();
        }
      )
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
        },
        (payload) => {
          onConversationUpdate();
        }
      )
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "conversation_members",
          filter: `user_id=eq.${user.id}`,
        },
        () => {
          onConversationUpdate();
        }
      )
      .subscribe((status) => {
        if (status === "SUBSCRIBED") {
          setIsConnected(true);
        } else if (status === "CLOSED" || status === "CHANNEL_ERROR") {
          setIsConnected(false);
        }
      });

    return () => {
      if (channelRef.current) {
        supabase?.removeChannel(channelRef.current);
        channelRef.current = null;
        setIsConnected(false);
      }
    };
  }, [user, enabled, onConversationUpdate]);

  return { isConnected };
}