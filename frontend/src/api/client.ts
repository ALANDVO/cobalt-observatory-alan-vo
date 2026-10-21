import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  OCSFEventCreate,
  OCSFEvent,
  PaginatedResponse,
  AgentCreate,
  AgentUpdate,
  Agent,
  EvaluationCreate,
  Evaluation,
  EvaluationSummary,
  HealthResponse,
} from '../types/api';

// Extend ImportMeta for Vite env
declare global {
  interface ImportMetaEnv {
    readonly VITE_API_URL: string;
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<{ detail?: string }>) => {
        const message = error.response?.data?.detail || error.message;
        return Promise.reject(new Error(message));
      }
    );
  }

  // Health
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  async healthDb(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health/db');
    return response.data;
  }

  // OCSF Events
  async createOcsfEvent(event: OCSFEventCreate): Promise<OCSFEvent> {
    const response = await this.client.post<OCSFEvent>('/ocsf/events', event);
    return response.data;
  }

  async listOcsfEvents(params?: {
    page?: number;
    page_size?: number;
    trace_uid?: string;
    class_uid?: number;
    activity_id?: number;
    category_uid?: number;
    severity_id?: number;
    start_time?: string;
    end_time?: string;
    has_trace?: boolean;
  }): Promise<PaginatedResponse<OCSFEvent>> {
    const response = await this.client.get<PaginatedResponse<OCSFEvent>>('/ocsf/events', { params });
    return response.data;
  }

  async getOcsfEvent(id: number): Promise<OCSFEvent> {
    const response = await this.client.get<OCSFEvent>(`/ocsf/events/${id}`);
    return response.data;
  }

  async getEventsByTrace(traceUid: string): Promise<OCSFEvent[]> {
    const response = await this.client.get<OCSFEvent[]>(`/ocsf/events/trace/${traceUid}`);
    return response.data;
  }

  async deleteOcsfEvent(id: number): Promise<void> {
    await this.client.delete(`/ocsf/events/${id}`);
  }

  // Agents
  async createAgent(agent: AgentCreate): Promise<Agent> {
    const response = await this.client.post<Agent>('/agents', agent);
    return response.data;
  }

  async listAgents(params?: {
    page?: number;
    page_size?: number;
    is_active?: boolean;
    provider?: string;
  }): Promise<PaginatedResponse<Agent>> {
    const response = await this.client.get<PaginatedResponse<Agent>>('/agents', { params });
    return response.data;
  }

  async getAgent(id: number): Promise<Agent> {
    const response = await this.client.get<Agent>(`/agents/${id}`);
    return response.data;
  }

  async updateAgent(id: number, agent: AgentUpdate): Promise<Agent> {
    const response = await this.client.patch<Agent>(`/agents/${id}`, agent);
    return response.data;
  }

  async deleteAgent(id: number): Promise<void> {
    await this.client.delete(`/agents/${id}`);
  }

  // Evaluations
  async createEvaluation(evaluation: EvaluationCreate): Promise<Evaluation> {
    const response = await this.client.post<Evaluation>('/evaluations', evaluation);
    return response.data;
  }

  async listEvaluations(params?: {
    page?: number;
    page_size?: number;
    agent_id?: number;
    dataset?: string;
    min_score?: number;
    max_score?: number;
  }): Promise<PaginatedResponse<Evaluation>> {
    const response = await this.client.get<PaginatedResponse<Evaluation>>('/evaluations', { params });
    return response.data;
  }

  async getEvaluationSummary(agentId?: number): Promise<EvaluationSummary> {
    const response = await this.client.get<EvaluationSummary>('/evaluations/summary', {
      params: { agent_id: agentId },
    });
    return response.data;
  }

  async getEvaluation(id: number): Promise<Evaluation> {
    const response = await this.client.get<Evaluation>(`/evaluations/${id}`);
    return response.data;
  }

  async deleteEvaluation(id: number): Promise<void> {
    await this.client.delete(`/evaluations/${id}`);
  }
}

export const api = new ApiClient();
