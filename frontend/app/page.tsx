'use client';

import { useState } from 'react';
import SearchBar from '@/components/search_bar';
import LoadingState from '@/components/loading_state';
import ResultsDisplay from '@/components/results_display';
import PapersioLogo from '@/components/papersio_logo';
import { ResearchResponse } from '@/types/research';

export default function Home() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [status, setStatus] = useState("Initializing...");
  const [statusDetails, setStatusDetails] = useState("");

  const handleSubmit = async () => {
    if (!query.trim()) {
      setError('Please enter a research question!');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    setStatus("Starting...");
    setStatusDetails("Connecting to research agents...");

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const wsUrl = backendUrl.replace(/^http/, 'ws') + '/ws';
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({
          query: query.trim(),
          use_search: true,
          mode: 'ultra'
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'status') {
          setStatus(data.stage);
          setStatusDetails(data.details || '');
        } else if (data.type === 'result') {
          setResult({
            query: query.trim(),
            answer: data.answer,
            sources: data.sources || [],
            search_strategy: "Real-time Agent Research"
          });
          setIsLoading(false);
          ws.close();
        } else if (data.type === 'error') {
          setError(data.content);
          setIsLoading(false);
          ws.close();
        }
      };

      ws.onerror = (e) => {
        console.error("WebSocket Error:", e);
        setError("Connection failed. Make sure backend is running.");
        setIsLoading(false);
      };

      ws.onclose = () => {
      };

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setResult(null);
    setError(null);
    setQuery('');
  };

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div className="nav-inner max-w-6xl mx-auto">
          <div className="logo-mark">
            <PapersioLogo className="w-10 h-10" />
            <div>
              <div className="brand-title">Papersio Research Desk</div>
              <div className="brand-meta">Multi-Agent Briefing</div>
            </div>
          </div>
          <div className="report-meta">
            <span className="stat-chip">Live Search</span>
            <span className="text-xs">Evidence-driven reports</span>
          </div>
        </div>
      </header>

      <div className="flex-1 w-full max-w-6xl mx-auto px-6 pb-24">
        {!result && !isLoading && (
          <section className="hero">
            <div>
              <h2 className="hero-title">Turn your queries into research memos.</h2>
            </div>
            <div className="card">
              <div className="section-title">Papersio provides reports with:</div>
              <ul className="text-sm text-[color:var(--ink-muted)] space-y-2">
                <li>• Planning, searching, analyzing, and critiquing in one run.</li>
                <li>• Automatic citations and source vaults.</li>
                <li>• Exportable PDF-ready structure.</li>
              </ul>
            </div>
          </section>
        )}

        <section className="search-panel">
          <SearchBar
            query={query}
            onChange={setQuery}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </section>

        {error && (
          <div className="card mt-6 border border-[#e2b7a9] bg-[#f7e4dd] text-[#9b3b2e]">
            ⚠️ {error}
          </div>
        )}

        {isLoading && (
          <div className="mt-8">
            <LoadingState status={status} details={statusDetails} />
          </div>
        )}

        {!isLoading && result && (
          <div className="mt-10">
            <ResultsDisplay result={result} onClear={handleClear} />
          </div>
        )}
      </div>
    </main>
  );
}
