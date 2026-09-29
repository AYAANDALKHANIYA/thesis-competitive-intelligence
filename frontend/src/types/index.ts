// Common
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Companies
export interface Company {
  id: number;
  name: string;
  ticker?: string;
  industry?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Competitor {
  id: number;
  company_id: number;
  competitor_id: number;
  competitor_company?: Company;
}

// Documents
export interface DocumentSummary {
  id: number;
  company_id: number;
  source_id: number;
  title: string;
  url: string;
  document_type: string;
  published_at: string;
  collected_at: string;
  is_processed: boolean;
}

// Analytics - Dashboard
export interface DashboardResponse {
  company?: Company;
  market_activity?: {
    company_id: number;
    metric_date: string;
    index_value: number;
    components: Record<string, number>;
    weights: Record<string, number>;
  };
  sentiment?: {
    company_id: number;
    total_documents: number;
    positive: number;
    neutral: number;
    negative: number;
    average_score: number;
    distribution: Record<string, number>;
  };
  signals?: {
    signal_type: string;
    topic?: string;
    entity?: string;
    current_mentions: number;
    previous_mentions: number;
    growth_rate: number;
    sentiment_shift?: number;
    confidence: number;
    evidence: any[];
    detected_at: string;
  }[];
  top_topics?: {
    id: number;
    topic_key: number;
    name: string;
    description?: string;
    document_count: number;
    created_at: string;
  }[];
  recent_insights?: {
    id: number;
    company_id: number;
    insight_type: string;
    content: any;
    generated_at: string;
  }[];
  automation_status?: {
    last_intelligence_update?: string;
    next_scheduled_collection?: string;
    new_documents: number;
    sources_checked: number;
  };
}

// Analytics - Other
export interface TrendPoint {
  date: string;
  value: number;
}

export interface TopicSummary {
  topic_id: number;
  name: string;
  count: number;
  momentum: number;
}

export interface SentimentSummary {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}

// Predictions
export interface ModelVersion {
  id: number;
  model_name: string;
  version_tag: string;
  is_active: boolean;
  metrics: Record<string, number>;
  created_at: string;
}

export interface Prediction {
  id: number;
  company_id: number;
  model_version_id: number;
  target_metric: string;
  target_date: string;
  predicted_value: number;
  confidence_lower?: number;
  confidence_upper?: number;
  created_at: string;
}

// Insights
export interface InsightResponse {
  id: number;
  company_id: number;
  insight_type: string;
  content: any;
  input_hash: string;
  generated_at: string;
}

// System / Ingestion
export interface IngestionRun {
  id: number;
  source_id: number;
  status: string;
  items_found: number;
  items_new: number;
  items_changed: number;
  items_skipped: number;
  items_failed: number;
  requests_made: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface SourceHealth {
  source_id: number;
  source_name: string;
  source_type: string;
  is_active: boolean;
  is_healthy: boolean;
  consecutive_errors: number;
  last_success?: string;
  last_error?: string;
}
