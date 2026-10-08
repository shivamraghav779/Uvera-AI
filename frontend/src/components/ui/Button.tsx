import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/utils/cn";

/** `accent` is for committing work (apply, save, restore); `primary` for other main actions. */
type Variant = "primary" | "accent" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

const VARIANT: Record<Variant, string> = {
  primary: "bg-app-primary text-app-primary-fg hover:bg-app-primary-hover",
  accent: "bg-app-accent text-app-accent-fg hover:opacity-90",
  secondary: "border border-app-border bg-app-panel text-app-fg hover:bg-app-subtle",
  ghost: "text-app-fg hover:bg-app-subtle",
  danger: "bg-app-danger text-white hover:opacity-90",
};

const SIZE: Record<Size, string> = { sm: "h-7 px-2.5 text-xs", md: "h-8 px-3 text-sm" };

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  busy?: boolean;
  icon?: ReactNode;
}

export function Button({
  variant = "secondary",
  size = "md",
  busy = false,
  icon,
  className,
  children,
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={cn(
        "inline-flex shrink-0 items-center justify-center gap-1.5 rounded-md font-medium whitespace-nowrap",
        "transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        VARIANT[variant],
        SIZE[size],
        className,
      )}
      {...rest}
    >
      {busy ? <Loader2 size={14} aria-hidden className="animate-spin" /> : icon}
      {children}
    </button>
  );
}

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Accessible name; also shown as a tooltip. */
  label: string;
  active?: boolean;
}

export function IconButton({ label, active = false, className, children, type = "button", ...rest }: IconButtonProps) {
  return (
    <button
      type={type}
      aria-label={label}
      title={label}
      aria-pressed={active || undefined}
      className={cn(
        "grid size-8 shrink-0 place-items-center rounded-md text-app-muted transition-colors",
        "hover:bg-app-subtle hover:text-app-fg disabled:cursor-not-allowed disabled:opacity-40",
        active && "bg-app-accent-soft text-app-accent hover:bg-app-accent-soft hover:text-app-accent",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
