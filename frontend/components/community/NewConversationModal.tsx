"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { X, Search, Loader2, MessageCircle, UserCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CommunityProfileRead } from "@/lib/types";
import { getPublicProfile as getPublicProfileApi, createConversation } from "@/lib/community-api";
import { useToast } from "@/components/ui/toast";
import { ProfileCard } from "@/components/community/ProfileCard";

interface NewConversationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentUserId: string;
  onConversationCreated: (conversationId: string) => void;
}

export function NewConversationModal({
  open,
  onOpenChange,
  currentUserId,
  onConversationCreated,
}: NewConversationModalProps) {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");
  const [users, setUsers] = useState<CommunityProfileRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (open) {
      setSearchQuery("");
      setUsers([]);
      setSelectedUserId(null);
      setError(null);
    }
  }, [open]);

  const searchUsers = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setUsers([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const profile = await getPublicProfileApi(query.trim());
      if (profile && profile.user_id !== currentUserId) {
        setUsers([profile]);
      } else {
        setUsers([]);
      }
    } catch {
      setUsers([]);
      setError("User not found");
    } finally {
      setLoading(false);
    }
  }, [currentUserId]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      searchUsers(searchQuery);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, searchUsers]);

  const handleCreateConversation = async (userId: string) => {
    setLoading(true);
    try {
      const conversation = await createConversation({ recipient_id: userId });
      onConversationCreated(conversation.id);
      onOpenChange(false);
      toast({
        title: "Conversation started",
        description: "You can now send messages.",
      });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create conversation";
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      <div className="relative w-full max-w-md rounded-2xl border border-gold-500/30 bg-[#0e1117] shadow-2xl overflow-hidden animate-in slide-in-from-bottom duration-300">
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <h3 className="font-serif text-lg font-bold text-white">New Conversation</h3>
          <button
            onClick={() => onOpenChange(false)}
            className="p-1 rounded-full text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4">
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by user ID or display name..."
              className="w-full bg-[#090b0e] border border-white/10 rounded-full pl-10 pr-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-gold-400/50 focus:ring-1 focus:ring-gold-400/30"
              autoFocus
            />
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gold-400" />
            </div>
          ) : users.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {users.map((user) => (
                <ProfileCard
                  key={user.user_id}
                  profile={user}
                  currentUserId={currentUserId}
                  compact
                  onMessageClick={handleCreateConversation}
                />
              ))}
            </div>
          ) : searchQuery.length >= 2 ? (
            <div className="text-center py-8 text-zinc-500">
              <UserCheck className="w-10 h-10 mx-auto text-zinc-600 mb-2" />
              <p className="text-sm">No user found</p>
              <p className="text-xs mt-1">Try searching by user ID</p>
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-500">
              <MessageCircle className="w-10 h-10 mx-auto text-zinc-600 mb-2" />
              <p className="text-sm">Search for a community member</p>
              <p className="text-xs mt-1">Enter at least 2 characters</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}