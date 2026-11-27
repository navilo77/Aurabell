"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { format } from "date-fns";
import { Send, Paperclip, Loader2, Check, CheckCheck, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MessageRead, ConversationRead } from "@/lib/types";
import { sendMessage as sendMessageApi, markConversationRead } from "@/lib/community-api";
import { useRealtimeMessages } from "@/hooks/use-realtime";

interface ChatViewProps {
  conversation: ConversationRead;
  currentUserId: string;
  onBack: () => void;
}

export function ChatView({ conversation, currentUserId, onBack }: ChatViewProps) {
  const [messages, setMessages] = useState<MessageRead[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [showLoadMore, setShowLoadMore] = useState(false);
  const [failedMessageIds, setFailedMessageIds] = useState<Set<string>>(new Set());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isLoadingRef = useRef(false);
  const initialLoadDone = useRef(false);

  const otherUser = conversation.other_user;

  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? "smooth" : "auto" });
  }, []);

  const loadMessages = useCallback(
    async (pageNum: number, append = false) => {
      if (isLoadingRef.current) return;
      isLoadingRef.current = true;

      try {
        if (!append) setLoading(true);
        setError(null);

        const result = await sendMessageApi(
          conversation.id,
          { content: "" } // This won't be sent, just for type inference
        );
        // We need to use listMessages instead
      } catch {
        // Ignore - we'll use listMessages directly
      }

      try {
        const { listMessages } = await import("@/lib/community-api");
        const data = await listMessages(conversation.id, pageNum, 20, "v2");

        if (data && typeof data === "object" && "data" in data) {
          const paginated = data as { data: MessageRead[]; meta: { has_next: boolean } };
          const newMessages = paginated.data;

          if (append) {
            setMessages((prev) => {
              const existingIds = new Set(prev.map((m) => m.id));
              const uniqueNew = newMessages.filter((m) => !existingIds.has(m.id));
              return [...uniqueNew, ...prev];
            });
          } else {
            setMessages(newMessages);
            initialLoadDone.current = true;
            setTimeout(() => scrollToBottom(false), 0);
          }
          setHasMore(paginated.meta.has_next);
          setShowLoadMore(paginated.meta.has_next);
        } else if (Array.isArray(data)) {
          if (append) {
            setMessages((prev) => {
              const existingIds = new Set(prev.map((m) => m.id));
              const uniqueNew = data.filter((m) => !existingIds.has(m.id));
              return [...uniqueNew, ...prev];
            });
          } else {
            setMessages(data);
            initialLoadDone.current = true;
            setTimeout(() => scrollToBottom(false), 0);
          }
          setHasMore(data.length === 20);
          setShowLoadMore(data.length === 20);
        }
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load messages";
        setError(errorMessage);
      } finally {
        if (!append) setLoading(false);
        isLoadingRef.current = false;
      }
    },
    [conversation.id, scrollToBottom]
  );

  useEffect(() => {
    loadMessages(1, false);
  }, [conversation.id, loadMessages]);

  useEffect(() => {
    if (initialLoadDone.current && messages.length > 0) {
      markConversationRead(conversation.id).catch(console.error);
    }
  }, [messages.length, conversation.id]);

  const handleRealtimeMessage = useCallback(
    (message: MessageRead) => {
      if (message.conversation_id !== conversation.id) return;

      setMessages((prev) => {
        if (prev.some((m) => m.id === message.id)) return prev;
        return [...prev, message];
      });
    },
    [conversation.id]
  );

  useRealtimeMessages({
    conversationId: conversation.id,
    onNewMessage: handleRealtimeMessage,
    enabled: true,
  });

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const content = newMessage.trim();
    if (!content || sending) return;

    setSending(true);
    setError(null);

    const tempId = `temp-${Date.now()}`;
    const optimisticMessage: MessageRead = {
      id: tempId,
      conversation_id: conversation.id,
      sender_id: currentUserId,
      content,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      deleted_at: null,
    };

    setMessages((prev) => [...prev, optimisticMessage]);
    setNewMessage("");
    setTimeout(() => scrollToBottom(), 0);

    try {
      const sentMessage = await sendMessageApi(conversation.id, { content });
      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? sentMessage : m))
      );
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to send message";
      setError(errorMessage);
      setFailedMessageIds((prev) => new Set(prev).add(tempId));
      setMessages((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m } : m))
      );
    } finally {
      setSending(false);
    }
  };

  const handleLoadMore = async () => {
    if (isLoadingRef.current || !hasMore) return;
    const nextPage = page + 1;
    const container = scrollContainerRef.current;
    const scrollHeightBefore = container?.scrollHeight ?? 0;
    const scrollTopBefore = container?.scrollTop ?? 0;

    await loadMessages(nextPage, true);
    setPage(nextPage);

    if (container) {
      requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight - scrollHeightBefore + scrollTopBefore;
      });
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    if (target.scrollTop === 0 && hasMore && !isLoadingRef.current) {
      handleLoadMore();
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#090b0e]">
        <div className="w-8 h-8 animate-spin rounded-full border-2 border-gold-400 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#090b0e] min-w-0">
      {/* Chat Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-[#0c0e14]/80 backdrop-blur-xl sticky top-0 z-10">
        <button
          onClick={onBack}
          className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors lg:hidden"
          aria-label="Back to conversations"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="w-10 h-10 rounded-full bg-gold-500/20 border border-gold-400/30 flex items-center justify-center overflow-hidden flex-shrink-0">
          {otherUser?.avatar_url ? (
            <img src={otherUser.avatar_url} alt={otherUser.display_name} className="w-full h-full rounded-full object-cover" />
          ) : (
            <span className="text-gold-300 font-medium">
              {otherUser?.display_name
                ?.split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2) ?? "?"}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-white truncate">{otherUser?.display_name ?? "Unknown"}</h3>
          <p className="text-[10px] text-zinc-500">Active now</p>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {showLoadMore && (
          <div ref={loadMoreRef} className="text-center mb-4">
            <button
              onClick={handleLoadMore}
              disabled={isLoadingRef.current}
              className="text-xs text-zinc-500 hover:text-gold-300 transition-colors"
            >
              {isLoadingRef.current ? "Loading..." : "Load earlier messages"}
            </button>
          </div>
        )}

        {messages.map((message, index) => {
          const isOwn = message.sender_id === currentUserId;
          const showTime = index === 0 || (messages[index - 1] && format(new Date(message.created_at), "MMM d") !== format(new Date(messages[index - 1].created_at), "MMM d"));
          const prevMessage = messages[index - 1];
          const showAvatar = isOwn ? false : !prevMessage || prevMessage.sender_id !== message.sender_id;

          return (
            <div
              key={message.id}
              className={cn(
                "flex gap-2",
                isOwn ? "justify-end" : "justify-start"
              )}
            >
              {!isOwn && showAvatar && (
                <div className="w-8 h-8 rounded-full bg-gold-500/20 border border-gold-400/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
                  {otherUser?.avatar_url ? (
                    <img src={otherUser.avatar_url} alt="" className="w-full h-full rounded-full object-cover" />
                  ) : (
                    <span className="text-gold-300 text-xs font-medium">
                      {otherUser?.display_name
                        ?.split(" ")
                        .map((n) => n[0])
                        .join("")
                        .toUpperCase()
                        .slice(0, 2) ?? "?"}
                    </span>
                  )}
                </div>
              )}

              <div className={cn("flex flex-col max-w-[75%]")}>
                {!isOwn && showAvatar && (
                  <span className="text-[10px] text-zinc-500 ml-1 mb-1">{otherUser?.display_name}</span>
                )}

                <div
                  className={cn(
                    "relative rounded-2xl px-4 py-2",
                    isOwn
                      ? "bg-gold-500/20 border border-gold-400/30 text-white rounded-tr-md"
                      : "bg-[#141821] border border-white/10 text-zinc-100 rounded-tl-md"
                  )}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>

                  {failedMessageIds.has(message.id) && (
                    <div className="absolute -bottom-6 right-0 flex items-center gap-1 text-[10px] text-rose-400">
                      <AlertCircle className="w-3 h-3" />
                      Failed to send
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1 mt-1 text-[10px] text-zinc-600">
                  <span>{format(new Date(message.created_at), "HH:mm")}</span>
                  {isOwn && (
                    <span className="flex items-center gap-0.5">
                      {message.id.startsWith("temp-") ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : message.sender_id === currentUserId ? (
                        <CheckCheck className="w-3 h-3 text-gold-400" />
                      ) : (
                        <Check className="w-3 h-3" />
                      )}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-4 mb-3 p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Composer */}
      <form onSubmit={handleSend} className="p-4 border-t border-white/10 bg-[#0c0e14]/80 backdrop-blur-xl">
        <div className="flex items-end gap-2">
          <button
            type="button"
            className="p-2 rounded-full text-zinc-500 hover:text-white hover:bg-white/5 transition-colors flex-shrink-0"
            aria-label="Attach file"
          >
            <Paperclip className="w-5 h-5" />
          </button>

          <div className="flex-1 relative">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Message"
              rows={1}
              className="w-full bg-[#0e1117] border border-white/10 rounded-full px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-gold-400/50 focus:ring-1 focus:ring-gold-400/30 resize-none pr-12"
              disabled={sending}
            />
          </div>

          <button
            type="submit"
            disabled={!newMessage.trim() || sending}
            className="flex-shrink-0 p-2.5 rounded-full bg-gold-gradient text-black hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}