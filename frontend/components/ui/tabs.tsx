"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsProps {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
  children: React.ReactNode;
}

interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {}
interface TabsTriggerProps extends React.HTMLAttributes<HTMLButtonElement> {
  value?: string;
  selected?: boolean;
}
interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string;
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(({ value, onValueChange, className, children }, ref) => (
  <div ref={ref} className={cn("relative w-full", className)} data-tabs={value}>
    {React.Children.map(children, (child) => {
      if (React.isValidElement(child) && child.type && (child.type as any).displayName === "TabsTrigger") {
        return React.cloneElement(child as any, {
          onClick: () => onValueChange((child.props as any).value),
          selected: (child.props as any).value === value,
        });
      }
      return child;
    })}
  </div>
));

Tabs.displayName = "Tabs";

const TabsList = React.forwardRef<HTMLDivElement, TabsListProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("inline-flex h-10 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground", className)} {...props} />
));

TabsList.displayName = "TabsList";

const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(({ className, selected, children, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      selected ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground hover:bg-accent"
    )}
    {...props}
  >
    {children}
  </button>
));

TabsTrigger.displayName = "TabsTrigger";

const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("mt-2", className)} {...props} />
));

TabsContent.displayName = "TabsContent";

export { Tabs, TabsList, TabsTrigger, TabsContent };
