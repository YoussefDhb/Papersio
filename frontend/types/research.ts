export interface Source {
  title: string;
  url: string;
  source_type: 'arxiv' | 'web';
  authors?: string[];
}

export interface WorkflowStage {
  stage: string;
  status: 'complete' | 'failed' | 'pending';
  details: any;
}

export interface QualityAssessment {
  quality_score: number;
  approved: boolean;
  strengths?: string[];
  improvements?: string[];
  [key: string]: any;
}

export interface ResearchResponse {
  query: string;
  answer: string;
  sources: Source[];
  workflow_stages?: WorkflowStage[];
  quality_assessment?: QualityAssessment;
  search_strategy?: string;
  framework?: string;
  has_past_context?: boolean;
  papers_extracted?: number;
  tables_found?: number;
  revisions_made?: number;
  saved_to_database?: boolean;
  processing_time?: number;
  errors?: string[];
}

export interface ResearchRequest {
  query: string;
  use_search?: boolean;
  use_planning?: boolean;
}
