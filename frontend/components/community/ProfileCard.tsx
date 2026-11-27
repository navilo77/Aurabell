"use client";

import Image from "next/image";
import { MessageCircle, UserCircle, Calendar } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import type { CommunityProfileRead } from "@/lib/types";

interface ProfileCardProps {
  profile: CommunityProfileRead;
  currentUserId?: string;
  onMessageClick?: (userId: string) => void;
  compact?: boolean;
}

export function ProfileCard({
  profile,
  currentUserId,
  onMessageClick,
  compact = false,
}: ProfileCardProps) {
  const isCurrentUser = currentUserId && profile.user_id === currentUserId;

  const initials = profile.display_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  if (compact) {
    return (
      <Link
        href={`/community/users/${profile.user_id}`}
        className="flex items-center gap-3 p-3 rounded-xl bg-[#0e1117]/50 border border-white/5 hover:border-gold-500/30 hover:bg-white/3 transition-all"
      >
        <div className="w-10 h-10 rounded-full bg-gold-500/20 border border-gold-400/30 flex items-center justify-center text-gold-300 font-medium text-sm">
          {profile.avatar_url ? (
            <Image src={profile.avatar_url} alt="" fill className="rounded-full" />
          ) : (
            initials
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-zinc-100 truncate">{profile.display_name}</p>
          {profile.bio && (
            <p className="text-xs text-zinc-500 truncate">{profile.bio}</p>
          )}
        </div>
        {!isCurrentUser && onMessageClick && (
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onMessageClick(profile.user_id);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-gold-300 bg-gold-500/15 border border-gold-400/30 hover:bg-gold-500/25 transition-all"
          >
            <MessageCircle className="w-3.5 h-3.5" />
            <span>Message</span>
          </button>
        )}
      </Link>
    );
  }

  return (
    <div className="rounded-2xl border border-gold-500/20 bg-[#0e1117]/60 p-5 shadow-xl glass-card-hover">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-gold-500/15 border border-gold-400/30 flex items-center justify-center overflow-hidden flex-shrink-0">
          {profile.avatar_url ? (
            <Image
              src={profile.avatar_url}
              alt={profile.display_name}
              fill
              className="rounded-2xl object-cover"
            />
          ) : (
            <span className="text-2xl sm:text-3xl font-bold text-gold-300">{initials}</span>
          )}
        </div>

        <div className="flex-1 min-w-0 text-center sm:text-left">
          <div className="flex items-center justify-center sm:justify-start gap-2 mb-2">
            <h3 className="font-serif text-lg sm:text-xl font-bold text-white">
              {profile.display_name}
            </h3>
            {isCurrentUser && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gold-500/20 border border-gold-400/40 text-gold-300">
                You
              </span>
            )}
          </div>

          {profile.bio && (
            <p className="text-sm text-zinc-400 line-clamp-2 mb-2">{profile.bio}</p>
          )}

          <div className="flex items-center justify-center sm:justify-start gap-4 text-xs text-zinc-500">
            {profile.member_since && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                Member since {new Date(profile.member_since).getFullYear()}
              </span>
            )}
          </div>
        </div>

        {!isCurrentUser && onMessageClick && (
          <button
            onClick={() => onMessageClick(profile.user_id)}
            className="flex-shrink-0 mt-2 sm:mt-0 px-5 py-2.5 rounded-full bg-gold-gradient text-black font-extrabold text-xs uppercase tracking-wider shadow-gold hover:opacity-95 transition-all group"
          >
            <MessageCircle className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span className="ml-1">Message</span>
          </button>
        )}
      </div>
    </div>
  );
}