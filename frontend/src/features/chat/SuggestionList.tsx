interface SuggestionListProps {
  suggestions: readonly string[];
  onPick: (suggestion: string) => void;
  disabled?: boolean;
}

/** One-click prompts. Picking one sends it. */
export function SuggestionList({ suggestions, onPick, disabled }: SuggestionListProps) {
  return (
    <ul aria-label="Suggestions" className="flex flex-wrap gap-1.5">
      {suggestions.map((suggestion) => (
        <li key={suggestion}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onPick(suggestion)}
            className="rounded-full border border-app-border bg-app-panel px-2.5 py-1 text-xs text-app-muted transition-colors hover:border-app-border-strong hover:text-app-fg disabled:opacity-50"
          >
            {suggestion}
          </button>
        </li>
      ))}
    </ul>
  );
}
