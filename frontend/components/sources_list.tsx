'use client';

import { Source } from '@/types/research';
import { ExternalLink } from 'lucide-react';

interface SourcesListProps {
  sources: Source[];
}

export default function SourcesList({ sources }: SourcesListProps) {
  const arxivSources = sources.filter(s => s.source_type === 'arxiv');
  const webSources = sources.filter(s => s.source_type === 'web');

  return (
    <div className="mt-6">
      {arxivSources.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
            <span>📚</span>
            Academic Papers (ArXiv)
          </h3>
          <div className="space-y-2">
            {arxivSources.map((source, index) => (
              <div
                key={index}
                className="bg-[#212121] rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h4 className="font-medium text-white mb-1 text-sm">{source.title}</h4>
                    {source.authors && source.authors.length > 0 && (
                      <p className="text-xs text-gray-400">
                        👥 {source.authors.slice(0, 3).join(', ')}
                        {source.authors.length > 3 && ' et al.'}
                      </p>
                    )}
                  </div>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 text-blue-400 hover:text-blue-300 transition-colors"
                    title="View on ArXiv"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {webSources.length > 0 && (
        <div>
          <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
            <span>🌐</span>
            Web Articles
          </h3>
          <div className="space-y-2">
            {webSources.map((source, index) => (
              <div
                key={index}
                className="bg-[#212121] rounded-lg p-4 border border-gray-800 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h4 className="font-medium text-white text-sm">{source.title}</h4>
                  </div>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 text-green-400 hover:text-green-300 transition-colors"
                    title="Visit website"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
