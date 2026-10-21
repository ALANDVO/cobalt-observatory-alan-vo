/**
 * Type definitions matching backend API responses.
 */

export interface TraceContext {
  uid: string;
  span_id?: string;
}

export interface OCSFEventCreate {
  class_uid: number;
  activity_id: number;
  category_uid: number;
  category_name: string;
  class_name: string;
  time: string;
  severity_id: number;
  severity: string;
  status_id: number;
  status: string;
  trace_context?: TraceContext;
  profiles?: string[];
  event_data?: Record<string, unknown>;
}

export interface OCSFEvent {
  id: number;
  class_uid: number;
  activity_id: number;
  category_uid: number;
  category_name: string;
  class_name: string;
  time: string;
  severity_id: number;
  severity: string;
  status_id: number;
  status: string;
  trace_uid?: string;
  span_uid?: string;
  trace_profile: boolean;
  profiles: string[];
  event_data: Record<string, unknown>;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AgentCreate {
  name: string;
  description?: string;
  model: string;
  provider: string;
  configuration?: Record<string, unknown>;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  model?: string;
  provider?: string;
  configuration?: Record<string, unknown>;
  is_active?: boolean;
}

export interface Agent {
  id: number;
  name: string;
  description?: string;
  model: string;
  provider: string;
  configuration: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EvaluationCreate {
  agent_id: number;
  name: string;
  dataset: string;
  score: number;
  metrics?: Record<string, unknown>;
  details?: string;
  llm_explanation?: string;
}

export interface Evaluation {
  id: number;
  agent_id: number;
  name: string;
  dataset: string;
  score: number;
  metrics: Record<string, unknown>;
  details?: string;
  llm_explanation?: string;
  created_at: string;
}

export interface EvaluationSummary {
  total_evaluations: number;
  average_score: number;
  best_score: number;
  worst_score: number;
  by_dataset: Record<string, {
    count: number;
    average: number;
    best: number;
    worst: number;
  }>;
}

export interface HealthResponse {
  status: string;
  service?: string;
  database?: string;
  error?: string;
}