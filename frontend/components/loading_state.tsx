'use client';

import { useEffect, useState } from 'react';

interface LoadingStateProps {
  status: string;
  details?: string;
}

const STAGE_ORDER = [
  'checking memory',
  'planning',
  'searching',
  'analyzing',
  'writing',
  'critiquing',
  'revising',
  're-critiquing',
  'saving',
  'finalizing',
  'finished'
];

const stageToProgress = (stage: string): number => {
  const normalized = stage.trim().toLowerCase();
  const index = STAGE_ORDER.findIndex((s) => normalized.includes(s));
  if (index === -1) {
    return 8;
  }
  return Math.round(((index + 1) / STAGE_ORDER.length) * 100);
};

export default function LoadingState({ status, details }: LoadingStateProps) {
  const progress = stageToProgress(status);
  const [displayProgress, setDisplayProgress] = useState(progress);

  useEffect(() => {
    setDisplayProgress((prev) => Math.max(prev, progress));
  }, [progress]);

  return (
    <div className="card relative overflow-hidden">
      <div className="scanlines" />
      <div className="grid gap-6 lg:grid-cols-[320px_1fr] items-center">
        <div className="flex justify-center">
          <svg
            viewBox="0 0 200 200"
            className="papersio-loader"
            role="img"
            aria-label="Searching papers"
          >
            <rect x="40" y="20" width="120" height="150" rx="12" className="papersio-loader__sheet" />
            <rect x="55" y="45" width="90" height="8" rx="4" className="papersio-loader__line papersio-loader__line--accent" />
            <rect x="55" y="70" width="95" height="8" rx="4" className="papersio-loader__line" />
            <rect x="55" y="95" width="75" height="8" rx="4" className="papersio-loader__line" />

            <g className="papersio-loader__magnifier">
              <circle cx="135" cy="135" r="22" className="papersio-loader__glass" />
              <rect x="148" y="150" width="10" height="30" rx="5" className="papersio-loader__handle" />
            </g>
          </svg>
        </div>

        <div className="space-y-4">
          <div>
            <div className="text-sm uppercase tracking-[0.28em] text-[color:var(--ink-muted)]">
              Papersio Live Research
            </div>
            <div className="text-2xl font-semibold text-[color:var(--ink)]">{status}</div>
            <div className="text-sm text-[color:var(--ink-muted)] mt-1 max-w-xl">
              {details || 'Synthesizing sources and drafting the report...'}
            </div>
          </div>

          <div className="panel">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.2em] text-[color:var(--ink-muted)]">
              <span>Signal</span>
              <span className="stat-chip">{displayProgress}%</span>
            </div>
            <div className="mt-3 h-2 w-full rounded-full bg-[color:var(--line)] overflow-hidden">
              <div
                className="h-full bg-[color:var(--accent)] transition-[width] duration-500 ease-out"
                style={{ width: `${displayProgress}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
