"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

const Dialog = ({ open, onOpenChange, children }: DialogProps) => {
  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md rounded-lg border border-border bg-card shadow-xl">{children}</div>
      </div>
    </>
  );
};

Dialog.displayName = "Dialog";

interface DialogHeaderProps {}
const DialogHeader = ({ children }: { children: React.ReactNode }) => (
  <div className="flex flex-col space-y-1.5 p-6">{children}</div>
);
DialogHeader.displayName = "DialogHeader";

interface DialogTitleProps {}
const DialogTitle = ({ children }: { children: React.ReactNode }) => (
  <h3 className="text-lg font-semibold leading-none">{children}</h3>
);
DialogTitle.displayName = "DialogTitle";

interface DialogDescriptionProps {}
const DialogDescription = ({ children }: { children: React.ReactNode }) => (
  <p className="text-sm text-muted-foreground">{children}</p>
);
DialogDescription.displayName = "DialogDescription";

interface DialogContentProps {}
const DialogContent = ({ children }: { children: React.ReactNode }) => (
  <div className="p-6 pt-0">{children}</div>
);
DialogContent.displayName = "DialogContent";

interface DialogFooterProps {}
const DialogFooter = ({ children }: { children: React.ReactNode }) => (
  <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 p-6 pt-0">{children}</div>
);
DialogFooter.displayName = "DialogFooter";

interface DialogCloseProps {}
const DialogClose = ({ onOpenChange }: { onOpenChange: (open: boolean) => void }) => (
  <button
    onClick={() => onOpenChange(false)}
    className="rounded-md p-1 text-muted-foreground hover:bg-accent"
  >
    ✕
  </button>
);
DialogClose.displayName = "DialogClose";

export { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogContent, DialogFooter, DialogClose };
