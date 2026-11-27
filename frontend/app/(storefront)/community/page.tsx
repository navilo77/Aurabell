"use client";

import { useState, useCallback } from "react";
import { Header } from "@/components/header";
import { MobileBottomBar } from "@/components/mobile-bottom-bar";
import { ConversationList } from "@/components/community/ConversationList";
import { ChatView } from "@/components/community/ChatView";
import { NewConversationModal } from "@/components/community/NewConversationModal";
import { useAuth } from "@/lib/auth-context";
import type { ConversationRead } from "@/lib/types";

export default function CommunityPage() {
  const { user, isLoading } = useAuth();
  const [activeConversation, setActiveConversation] = useState<ConversationRead | null>(null);
  const [showNewConversationModal, setShowNewConversationModal] = useState(false);
  const [mobileView, setMobileView] = useState<"list" | "chat">("list");

  const handleSelectConversation = useCallback((conversation: ConversationRead) => {
    setActiveConversation(conversation);
    setMobileView("chat");
  }, []);

  const handleNewConversation = useCallback(() => {
    setShowNewConversationModal(true);
  }, []);

  const handleConversationCreated = useCallback((conversationId: string) => {
    // The realtime subscription will update the conversation list
    setActiveConversation(null);
  }, []);

  const handleBack = useCallback(() => {
    setActiveConversation(null);
    setMobileView("list");
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#090b0e] flex items-center justify-center">
        <div className="w-8 h-8 animate-spin rounded-full border-2 border-gold-400 border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-[#090b0e] flex items-center justify-center px-4">
        <div className="text-center max-w-md mx-auto py-12">
          <div className="w-20 h-20 rounded-full bg-gold-500/15 border border-gold-400/30 flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="font-serif text-2xl font-bold text-white mb-2">Join the Community</h2>
          <p className="text-zinc-400 mb-6">
            Sign in to connect with other Aura Bell customers, start conversations, and share experiences.
          </p>
          <a
            href="/login"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gold-gradient text-black font-extrabold text-sm uppercase tracking-wider shadow-gold hover:opacity-95 transition-all"
          >
            <span>Sign In</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#090b0e] pb-20 md:pb-0">
      <Header activeTab="home" />

      <div className="pt-20 lg:pt-24">
        <div className="lg:grid lg:grid-cols-4 lg:h-[calc(100vh-6rem)]">
          {/* Conversation List - 1/4 on desktop, full on mobile */}
          <aside className="lg:col-span-1 hidden lg:block border-r border-white/5">
            <ConversationList
              onSelectConversation={handleSelectConversation}
              onNewConversation={handleNewConversation}
              currentUserId={user.id}
              activeConversationId={activeConversation?.id}
            />
          </aside>

          {/* Mobile Conversation List */}
          <div className="lg:hidden">
            {mobileView === "list" && (
              <ConversationList
                onSelectConversation={handleSelectConversation}
                onNewConversation={handleNewConversation}
                currentUserId={user.id}
                activeConversationId={activeConversation?.id}
              />
            )}
          </div>

          {/* Chat View - 3/4 on desktop, full on mobile */}
          <main className="lg:col-span-3 flex flex-col min-w-0">
            {activeConversation ? (
              <ChatView
                conversation={activeConversation}
                currentUserId={user.id}
                onBack={handleBack}
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[#090b0e]">
                <div className="w-24 h-24 rounded-full bg-gold-500/10 border border-gold-400/20 flex items-center justify-center mx-auto mb-6">
                  <svg className="w-12 h-12 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h3 className="font-serif text-xl font-bold text-white mb-2">Select a conversation</h3>
                <p className="text-zinc-400 max-w-sm">
                  Choose a conversation from the sidebar or start a new one to begin messaging.
                </p>
                <button
                  onClick={handleNewConversation}
                  className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gold-gradient text-black font-extrabold text-sm uppercase tracking-wider shadow-gold hover:opacity-95 transition-all"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7z" />
                  </svg>
                  <span>New Conversation</span>
                </button>
              </div>
            )}
          </main>
        </div>
      </div>

      <MobileBottomBar />

      <NewConversationModal
        open={showNewConversationModal}
        onOpenChange={setShowNewConversationModal}
        currentUserId={user.id}
        onConversationCreated={handleConversationCreated}
      />
    </div>
  );
}