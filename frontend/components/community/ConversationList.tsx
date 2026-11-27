"use client";

import { useState, useEffect, useCallback } from "react";
import { MessageCircle, Search, Loader2, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ConversationRead } from "@/lib/types";
import { listConversations, getPublicProfile as getPublicProfileApi } from "@/lib/community-api";
import { ConversationItem } from "@/components/community/ConversationItem";
import { useRealtimeConversations } from "@/hooks/use-realtime";
import { ProfileCard } from "@/components/community/ProfileCard";

interface ConversationListProps {
  onSelectConversation: (conversation: ConversationRead) => void;
  onNewConversation: () => void;
  currentUserId: string;
  activeConversationId?: string;
}

export function ConversationList({
  onSelectConversation,
  onNewConversation,
  currentUserId,
  activeConversationId,
}: ConversationListProps) {
  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const loadConversations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listConversations();
      setConversations(data);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load conversations";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useRealtimeConversations({
    onConversationUpdate: loadConversations,
    enabled: true,
  });

  const filteredConversations = conversations.filter((conv) =>
    conv.other_user?.display_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full bg-[#090b0e] border-r border-white/5 lg:border-r-0">
      {/* Header */}
      <div className="p-4 border-b border-white/10 bg-[#0c0e14]/80 backdrop-blur-xl sticky top-0 z-10">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-serif text-lg font-bold text-white">Messages</h2>
          <button
            onClick={onNewConversation}
            className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
            aria-label="New conversation"
          >
            <MessageCircle className="w-5 h-5" />
          </button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full bg-[#0e1117] border border-white/10 rounded-full pl-10 pr-4 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-gold-400/50 focus:ring-1 focus:ring-gold-400/30"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="p-4 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-gold-400" />
          </div>
        )}

        {error && (
          <div className="p-4 text-center">
            <p className="text-xs text-rose-400">{error}</p>
            <button
              onClick={loadConversations}
              className="mt-2 text-xs text-gold-400 hover:underline"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && filteredConversations.length === 0 && (
          <div className="p-6 text-center">
            <div className="w-16 h-16 rounded-full bg-gold-500/10 border border-gold-400/20 flex items-center justify-center mx-auto mb-3">
              <MessageCircle className="w-8 h-8 text-gold-400" />
            </div>
            <h3 className="font-medium text-zinc-300">No conversations yet</h3>
            <p className="text-xs text-zinc-500 mt-1 max-w-xs mx-auto">
              Start a conversation with someone from the Aura Bell community.
            </p>
            <button
              onClick={onNewConversation}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 transition-all"
            >
              <MessageCircle className="w-4 h-4" />
              <span>New Conversation</span>
            </button>
          </div>
        )}

        {!loading && filteredConversations.length > 0 && (
          <div className="divide-y divide-white/5">
            {filteredConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === activeConversationId}
                onClick={() => onSelectConversation(conversation)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Community Discovery Footer */}
      <div className="p-4 border-t border-white/10 bg-[#0c0e14]/80 backdrop-blur-xl">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gold-500/10 border border-gold-400/30 text-gold-300 text-sm font-medium hover:bg-gold-500/20 transition-all"
        >
          <Users className="w-4 h-4" />
          <span>Discover Community Members</span>
        </button>
      </div>
    </div>
  );
}