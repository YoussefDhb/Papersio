'use client';

import ReactMarkdown from 'react-markdown';
import { ResearchResponse } from '@/types/research';
import { BookOpen, FileText, Globe, X } from 'lucide-react';
import PDFExportButton from '@/components/pdf_export_button';
import WorkflowStages from '@/components/workflow_stages';


interface ResultsDisplayProps {
  result: ResearchResponse;
  onClear: () => void;
}

export default function ResultsDisplay({ result, onClear }: ResultsDisplayProps) {
  const arxivSources = result.sources?.filter(s => s.source_type === 'arxiv') || [];
  const webSources = result.sources?.filter(s => s.source_type === 'web') || [];
  const totalSources = arxivSources.length + webSources.length;

  return (
    <div className="report-layout">
      <section className="space-y-6">
        <div className="card">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="report-meta">
                <span className="stat-chip">
                  <FileText className="w-3 h-3" /> Report Draft
                </span>
                {result.search_strategy && <span>{result.search_strategy}</span>}
                <span>{totalSources} sources cited</span>
              </div>
              <h2 className="section-title mt-3">Research Report</h2>
            </div>
            <div className="flex items-center gap-2">
              <PDFExportButton result={result} />
              <button
                onClick={onClear}
                className="btn-ghost flex items-center gap-2"
                title="New research"
              >
                <X className="w-4 h-4" /> New Query
              </button>
            </div>
          </div>
        </div>

        {result.workflow_stages && result.workflow_stages.length > 0 && (
          <div className="panel">
            <WorkflowStages stages={result.workflow_stages} />
          </div>
        )}

        <div className="card">
          <div className="markdown-content">
            <ReactMarkdown>{result.answer}</ReactMarkdown>
          </div>
        </div>
      </section>

      <aside className="space-y-4">
        <div className="panel">
          <div className="section-title flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-[color:var(--accent)]" /> Evidence Vault
          </div>
          <div className="text-sm text-[color:var(--ink-muted)]">
            Curated sources used to build the report.
          </div>
          <div className="mt-4 space-y-4">
            {totalSources === 0 && (
              <div className="text-sm text-[color:var(--ink-muted)]">
                No external sources were attached to this report.
              </div>
            )}
            {arxivSources.length > 0 && (
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--ink)] mb-2">
                  <BookOpen className="w-4 h-4" /> Academic Papers
                </div>
                <div className="space-y-2">
                  {arxivSources.map((source, index) => (
                    <a
                      key={index}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-lg border border-[color:var(--line)] bg-white/80 p-3 transition hover:border-[color:var(--accent)]"
                    >
                      <h4 className="text-sm font-medium text-[color:var(--ink)] line-clamp-2">
                        {source.title}
                      </h4>
                      {source.authors && source.authors.length > 0 && (
                        <p className="text-xs text-[color:var(--ink-muted)] line-clamp-1">
                          {source.authors.slice(0, 2).join(', ')}
                          {source.authors.length > 2 && ' et al.'}
                        </p>
                      )}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {webSources.length > 0 && (
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--ink)] mb-2">
                  <Globe className="w-4 h-4" /> Web Articles
                </div>
                <div className="space-y-2">
                  {webSources.map((source, index) => (
                    <a
                      key={index}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-lg border border-[color:var(--line)] bg-white/80 p-3 transition hover:border-[color:var(--signal)]"
                    >
                      <h4 className="text-sm font-medium text-[color:var(--ink)] line-clamp-2">
                        {source.title}
                      </h4>
                      <p className="text-xs text-[color:var(--ink-muted)] line-clamp-1">
                        {new URL(source.url).hostname}
                      </p>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
