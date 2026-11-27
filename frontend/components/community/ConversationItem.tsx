"use client";

import { formatDistanceToNow } from "date-fns";
import { MessageCircle, CheckCheck, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ConversationRead } from "@/lib/types";

interface ConversationItemProps {
  conversation: ConversationRead;
  isActive: boolean;
  onClick: () => void;
}

export function ConversationItem({ conversation, isActive, onClick }: ConversationItemProps) {
  const otherUser = conversation.other_user;
  const hasUnread = conversation.unread_count > 0;
  const lastMessageTime = conversation.updated_at
    ? formatDistanceToNow(new Date(conversation.updated_at), { addSuffix: true })
    : "";

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-3 rounded-xl transition-all",
        isActive
          ? "bg-gold-500/15 border border-gold-400/40"
          : "hover:bg-white/3 hover:border-white/10 border border-transparent"
      )}
    >
      <div className="flex items-start gap-3">
        <div className="relative w-11 h-11 rounded-full bg-gold-500/20 border border-gold-400/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
          {otherUser?.avatar_url ? (
            <img
              src={otherUser.avatar_url}
              alt={otherUser.display_name}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span className="text-gold-300 font-medium text-sm">
              {otherUser?.display_name
                ?.split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2) ?? "?"}
            </span>
          )}
          {hasUnread && (
            <span className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-gold-500 text-black text-[10px] font-black flex items-center justify-center">
              {conversation.unread_count > 9 ? "9+" : conversation.unread_count}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h4 className="font-medium text-zinc-100 truncate pr-2">
              {otherUser?.display_name ?? "Unknown User"}
            </h4>
            <span className="text-[10px] text-zinc-500 font-mono whitespace-nowrap flex-shrink-0">
              {lastMessageTime}
            </span>
          </div>

          <div className="flex items-center justify-between gap-2 mt-1">
            <p className="text-xs text-zinc-400 truncate flex-1 pr-2">
              {conversation.last_message ?? "No messages yet"}
            </p>
            {conversation.last_message && (
              <span className="flex items-center gap-1 text-[10px] text-zinc-500 flex-shrink-0">
                <Check className="w-3 h-3" />
              </span>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}