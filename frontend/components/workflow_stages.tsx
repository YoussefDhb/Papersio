'use client';

import { WorkflowStage } from '@/types/research';

interface WorkflowStagesProps {
  stages: WorkflowStage[];
}

export default function WorkflowStages({ stages }: WorkflowStagesProps) {
  const getStageIcon = (stageName: string) => {
    const icons: Record<string, string> = {
      'Memory': '🧠',
      'Planning': '🎯',
      'Search': '🔍',
      'Analysis': '📊',
      'Writing': '✍️',
      'Critique': '🎓',
      'Database': '💾',
      'Analyze': '📊',
      'Write': '✍️',
    };
    return icons[stageName] || '✨';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'bg-[color:var(--accent-soft)] text-[color:var(--accent)] border-[color:var(--accent)]/30';
      case 'failed':
        return 'bg-[#f7e4dd] text-[#9b3b2e] border-[#e2b7a9]';
      default:
        return 'bg-white text-[color:var(--ink-muted)] border-[color:var(--line)]';
    }
  };

  return (
    <div>
      <h3 className="section-title">Workflow Stages</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {stages.map((stage, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg border ${getStatusColor(stage.status)} transition-colors`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-base">{getStageIcon(stage.stage)}</span>
                <span className="font-medium text-sm text-[color:var(--ink)]">{stage.stage}</span>
              </div>
              <span className="text-xs uppercase font-semibold opacity-75">{stage.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
