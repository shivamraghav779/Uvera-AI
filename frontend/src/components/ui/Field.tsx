import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";

import { cn } from "@/utils/cn";

const CONTROL = cn(
  "w-full rounded-md border border-app-border bg-app-panel px-2.5 text-sm text-app-fg",
  "placeholder:text-app-muted focus-visible:border-app-accent",
);

export function TextInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(CONTROL, "h-8", className)} {...rest} />;
}

export function TextArea({ className, ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(CONTROL, "py-1.5", className)} {...rest} />;
}

export function SelectInput({ className, children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cn(CONTROL, "h-8", className)} {...rest}>
      {children}
    </select>
  );
}

/** A labelled control. `children` receives the id to put on the control. */
export function Field({ label, children }: { label: string; children: (id: string) => ReactNode }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs font-medium text-app-muted">
        {label}
      </label>
      {children(id)}
    </div>
  );
}
