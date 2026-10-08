import { ArrowUp, ChevronDown, ChevronUp, MousePointerClick, X } from "lucide-react";
import { useEffect, useRef, type KeyboardEvent } from "react";

import { IconButton } from "@/components/ui/Button";
import { cn } from "@/utils/cn";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder: string;
  disabled: boolean;
  busy: boolean;
  /** Id of the selected component, sent as context so "this" is unambiguous. */
  selectedId: string | null;
  onClearSelection: () => void;
  expanded: boolean;
  onToggleExpanded: () => void;
  /** Changes when something asks the input to take focus. */
  focusToken: number;
}

const MAX_HEIGHT_PX = 140;

/** The command line of the workspace. Enter sends, Shift+Enter adds a line. */
export function ChatInput({
  value,
  onChange,
  onSubmit,
  placeholder,
  disabled,
  busy,
  selectedId,
  onClearSelection,
  expanded,
  onToggleExpanded,
  focusToken,
}: ChatInputProps) {
  const textarea = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (focusToken > 0) textarea.current?.focus();
  }, [focusToken]);

  useEffect(() => {
    const element = textarea.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, [value]);

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      onSubmit();
    }
  };

  const canSend = value.trim().length > 0 && !disabled && !busy;
  return (
    <div
      className={cn(
        "flex items-end gap-2 rounded-xl border border-app-border bg-app-panel p-1.5 pl-3",
        "focus-within:border-app-accent",
      )}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-1 py-1">
        {selectedId && (
          <span className="inline-flex w-fit items-center gap-1 rounded bg-app-accent-soft py-0.5 pr-0.5 pl-1.5 text-xs font-medium text-app-accent">
            <MousePointerClick size={12} aria-hidden />
            <span>
              About <code className="font-mono">{selectedId}</code>
            </span>
            <button
              type="button"
              aria-label="Stop referring to the selected component"
              onClick={onClearSelection}
              className="rounded p-0.5 hover:bg-black/10"
            >
              <X size={11} />
            </button>
          </span>
        )}
        <textarea
          ref={textarea}
          rows={1}
          value={value}
          aria-label="Describe a change"
          placeholder={placeholder}
          disabled={disabled}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={onKeyDown}
          className="w-full resize-none bg-transparent text-sm outline-none placeholder:text-app-muted disabled:cursor-not-allowed"
        />
      </div>
      <IconButton
        label={expanded ? "Hide conversation" : "Show conversation"}
        onClick={onToggleExpanded}
        aria-expanded={expanded}
      >
        {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
      </IconButton>
      <button
        type="button"
        aria-label="Send"
        disabled={!canSend}
        onClick={onSubmit}
        className="grid size-8 shrink-0 place-items-center rounded-lg bg-app-accent text-app-accent-fg transition-opacity disabled:opacity-35"
      >
        <ArrowUp size={16} />
      </button>
    </div>
  );
}
