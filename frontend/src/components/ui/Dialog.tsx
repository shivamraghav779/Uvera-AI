import * as RadixDialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  /** Wide dialogs suit lists such as a version comparison. */
  size?: "sm" | "md";
  children?: ReactNode;
  footer?: ReactNode;
}

/** The application's modal dialog: focus-trapped, labelled, closes on Escape. */
export function Dialog({ open, onOpenChange, title, description, size = "sm", children, footer }: DialogProps) {
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-app-overlay" />
        <RadixDialog.Content
          aria-describedby={description ? undefined : undefined}
          className={cn(
            "fixed top-1/2 left-1/2 z-50 flex max-h-[85vh] w-[92vw] -translate-x-1/2 -translate-y-1/2 flex-col",
            "rounded-xl border border-app-border bg-app-raised text-app-fg shadow-app-modal",
            size === "sm" ? "max-w-md" : "max-w-xl",
          )}
        >
          <header className="flex items-start justify-between gap-4 px-5 pt-5">
            <div>
              <RadixDialog.Title className="text-base font-semibold">{title}</RadixDialog.Title>
              {description ? (
                <RadixDialog.Description className="mt-1 text-sm text-app-muted">
                  {description}
                </RadixDialog.Description>
              ) : (
                <RadixDialog.Description className="sr-only">{title}</RadixDialog.Description>
              )}
            </div>
            <RadixDialog.Close
              aria-label="Close"
              className="rounded-md p-1 text-app-muted hover:bg-app-subtle hover:text-app-fg"
            >
              <X size={16} />
            </RadixDialog.Close>
          </header>
          {children && <div className="overflow-auto px-5 py-4">{children}</div>}
          {footer && <footer className="flex justify-end gap-2 px-5 pb-5">{footer}</footer>}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}
