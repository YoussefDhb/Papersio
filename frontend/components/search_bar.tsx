'use client';

import { Send, Sparkles } from 'lucide-react';

interface SearchBarProps {
  query: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export default function SearchBar({ query, onChange, onSubmit, isLoading }: SearchBarProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isLoading && query.trim()) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="w-full space-y-3">
      <div className="input-shell">
        <Sparkles className="w-4 h-4 text-[color:var(--accent)]" />
        <textarea
          value={query}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Draft a research question, add scope, constraints, or preferred sources..."
          className="input-field min-h-[72px] resize-none"
          disabled={isLoading}
        />
        <button
          onClick={onSubmit}
          disabled={isLoading || !query.trim()}
          className="btn-primary flex items-center gap-2"
        >
          {isLoading ? (
            <span className="w-4 h-4 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          Research
        </button>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-xs text-[color:var(--ink-muted)]">
        <span>Tip: press Enter to run, Shift + Enter for a new line.</span>
      </div>
    </div>
  );
}
