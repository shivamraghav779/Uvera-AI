import { Check, ChevronDown, Loader2 } from "lucide-react";

import { cn } from "@/utils/cn";

import { BUTTON_BASE, BUTTON_VARIANT_CLASS } from "../../patterns/shared";
import type {
  ButtonViewProps,
  CheckboxViewProps,
  FormViewProps,
  InputViewProps,
  SelectViewProps,
} from "../types";

import { SURFACE } from "./layout";

const CONTROL = cn(
  "w-full rounded-g border border-g-border bg-g-surface px-3 text-g-fg",
  "placeholder:text-g-muted-fg focus-visible:border-g-primary",
);
const LABEL = "text-[0.9em] font-medium";

function RequiredMark({ required }: { required: boolean }) {
  return required ? (
    <span aria-hidden className="ml-0.5 text-g-destructive">
      *
    </span>
  ) : null;
}

export function Form({ title, submitLabel, submitting, onSubmit, children }: FormViewProps) {
  return (
    <form
      className={cn(SURFACE, "flex h-full flex-col gap-[var(--g-gap)] p-[var(--g-pad)]")}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      {title && <h3 className="font-semibold">{title}</h3>}
      {children}
      <div>
        <Button label={submitLabel} variant="primary" disabled={false} busy={submitting} onClick={() => {}} submit />
      </div>
    </form>
  );
}

export function Input({ id, name, label, inputType, placeholder, value, required, onChange }: InputViewProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className={LABEL}>
        {label}
        <RequiredMark required={required} />
      </label>
      {inputType === "textarea" ? (
        <textarea
          id={id}
          name={name}
          rows={3}
          value={value}
          required={required}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          className={cn(CONTROL, "py-2")}
        />
      ) : (
        <input
          id={id}
          name={name}
          type={inputType}
          value={value}
          required={required}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          className={cn(CONTROL, "h-[var(--g-control-h)]")}
        />
      )}
    </div>
  );
}

export function Select({ id, name, label, options, value, required, onChange }: SelectViewProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className={LABEL}>
        {label}
        <RequiredMark required={required} />
      </label>
      <div className="relative">
        <select
          id={id}
          name={name}
          value={value}
          required={required}
          onChange={(event) => onChange(event.target.value)}
          className={cn(CONTROL, "h-[var(--g-control-h)] appearance-none pr-9")}
        >
          <option value="">All</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown
          size={16}
          aria-hidden
          className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-g-muted-fg"
        />
      </div>
    </div>
  );
}

export function Checkbox({ id, name, label, checked, onChange }: CheckboxViewProps) {
  return (
    <label htmlFor={id} className="flex w-fit cursor-pointer items-center gap-2.5">
      <span className="relative grid size-[18px] place-items-center">
        <input
          id={id}
          name={name}
          type="checkbox"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          className={cn(
            "peer size-[18px] appearance-none rounded-[5px] border border-g-border bg-g-surface",
            "checked:border-g-primary checked:bg-g-primary",
          )}
        />
        <Check
          size={13}
          strokeWidth={3}
          aria-hidden
          className="pointer-events-none absolute hidden text-g-primary-fg peer-checked:block"
        />
      </span>
      <span>{label}</span>
    </label>
  );
}


export function Button({
  label,
  variant,
  disabled,
  busy,
  onClick,
  submit = false,
}: ButtonViewProps & { submit?: boolean }) {
  return (
    <button
      type={submit ? "submit" : "button"}
      disabled={disabled || busy}
      aria-busy={busy}
      onClick={submit ? undefined : onClick}
      className={cn(BUTTON_BASE, BUTTON_VARIANT_CLASS[variant])}
    >
      {busy && <Loader2 size={15} aria-hidden className="animate-spin" />}
      {label}
    </button>
  );
}
