"use client";

import Link from "next/link";

interface SidebarItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

interface SidebarProps {
  items: SidebarItem[];
  currentPath: string;
}

export function Sidebar({ items, currentPath }: SidebarProps) {
  return (
    <aside className="hidden lg:flex lg:w-64 flex-col border-r bg-background">
      <div className="flex items-center justify-between px-4 py-6 border-b">
        <span className="font-bold text-xl tracking-tight text-primary">Aura Bell</span>
      </div>
      <nav className="flex-1 px-4 py-6 space-y-2">
        {items.map((item) => {
          const isActive = currentPath === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-primary"
              }`}
            >
              <span className="h-5 w-5 shrink-0">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
