import { useEffect, useId, useRef, useState, type ReactNode } from "react";

import { cn } from "@/utils/cn";

interface PopoverProps {
  /** Renders the button that opens the popover. */
  trigger: (props: { onClick: () => void; "aria-expanded": boolean; "aria-controls": string }) => ReactNode;
  align?: "start" | "end";
  className?: string;
  children: ReactNode | ((close: () => void) => ReactNode);
}

/** A small anchored panel that closes on outside click and Escape. */
export function Popover({ trigger, align = "end", className, children }: PopoverProps) {
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const id = useId();

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const close = () => setOpen(false);
  return (
    <div ref={container} className="relative">
      {trigger({ onClick: () => setOpen((value) => !value), "aria-expanded": open, "aria-controls": id })}
      {open && (
        <div
          id={id}
          role="dialog"
          className={cn(
            "absolute top-full z-40 mt-1.5 rounded-lg border border-app-border bg-app-raised p-3 shadow-app-float",
            align === "end" ? "right-0" : "left-0",
            className,
          )}
        >
          {typeof children === "function" ? children(close) : children}
        </div>
      )}
    </div>
  );
}
