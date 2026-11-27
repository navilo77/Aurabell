"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface ToastProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  variant?: "default" | "destructive";
}

const TOAST_LIMIT = 5;
const TOAST_REMOVE_DELAY = 5000;

type ToastItem = ToastProps & {
  id: string;
};

const toastListeners = new Set<(toast: ToastItem) => void>();
let toasts: ToastItem[] = [];
let toastId = 0;

function addToast(toast: Omit<ToastItem, "id">) {
  const id = (toastId++).toString();
  const newToast = { ...toast, id };
  toasts = [newToast, ...toasts].slice(0, TOAST_LIMIT);
  toastListeners.forEach((listener) => listener(newToast));
  return id;
}

function dismiss(id: string) {
  toasts = toasts.filter((t) => t.id !== id);
}

export function useToast() {
  const [state, setState] = React.useState<ToastItem[]>([]);

  React.useEffect(() => {
    const listener = (toast: ToastItem) => setState([...toasts]);
    toastListeners.add(listener);
    return () => {
      toastListeners.delete(listener);
    };
  }, []);

  const toast = React.useCallback(
    (props: Omit<ToastItem, "id">) => {
      const id = addToast(props);
      setTimeout(() => dismiss(id), TOAST_REMOVE_DELAY);
      return id;
    },
    []
  );

  const dismissToast = React.useCallback((id: string) => dismiss(id), []);

  return { toast, toasts: state, dismiss: dismissToast };
}

export function Toast({ title, description, action, variant = "default" }: ToastProps) {
  return (
    <div
      className={cn(
        "w-full overflow-hidden border border-border bg-background p-4 text-foreground shadow-lg",
        variant === "destructive" && "border-destructive/50 bg-destructive/5 text-destructive"
      )}
    >
      <div className="flex flex-row items-center gap-3">
        <div className="shrink-0">
          {variant === "destructive" ? (
            <div className="h-5 w-5 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center">
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 001.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
          ) : (
            <div className="h-5 w-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 10a1 1 0 011-1h2.586l-1.293-1.293a1 1 0 111.414-1.414L15 9.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 11-1.414-1.414L13.586 10H8a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          {title && <h4 className="text-sm font-semibold">{title}</h4>}
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
        </div>
        {action && <div className="ml-auto">{action}</div>}
      </div>
    </div>
  );
}

Toast.displayName = "Toast";

export function Toaster() {
  const { toasts, dismiss } = useToast();

  return (
    <div className="fixed top-0 right-0 z-50 p-4 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto w-full max-w-md">
          <Toast
            title={toast.title}
            description={toast.description}
            action={toast.action}
            variant={toast.variant}
          />
          <button
            onClick={() => dismiss(toast.id)}
            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

Toaster.displayName = "Toaster";
