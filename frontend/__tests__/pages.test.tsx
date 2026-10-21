import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ToastProvider } from '@/components/ui';
import { DashboardPage } from '@/pages/DashboardPage';
import { OCSFEventsPage } from '@/pages/OCSFEventsPage';
import { AgentsPage } from '@/pages/AgentsPage';
import { EvaluationsPage } from '@/pages/EvaluationsPage';
import { api } from '@/api/client';
import { vi } from 'vitest';

// Mock API
vi.mock('@/api/client', () => ({
  api: {
    listOcsfEvents: vi.fn().mockResolvedValue({ total: 10, items: [] }),
    listAgents: vi.fn().mockResolvedValue({ total: 3, items: [] }),
    listEvaluations: vi.fn().mockResolvedValue({ total: 5, items: [] }),
    getEvaluationSummary: vi.fn().mockResolvedValue({
      total_evaluations: 5,
      average_score: 0.75,
      best_score: 0.9,
      worst_score: 0.5,
      by_dataset: {},
    }),
  },
}));

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <ToastProvider>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </ToastProvider>
  );
}

describe('DashboardPage', () => {
  it('renders dashboard with stats', async () => {
    renderWithProviders(<DashboardPage />);
    await screen.findByText(/Cobalt Observatory/i);
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Avg Score/i)).toBeInTheDocument();
  });

  it('shows three workflows', async () => {
    renderWithProviders(<DashboardPage />);
    await screen.findByText(/AI\/ML observability/i);
    expect(screen.getByText(/OCSF Event Ingestion/i)).toBeInTheDocument();
    expect(screen.getByText(/Agent Management/i)).toBeInTheDocument();
    expect(screen.getByText(/Agent Evaluation/i)).toBeInTheDocument();
  });
});

describe('OCSFEventsPage', () => {
  it('renders event list page', async () => {
    renderWithProviders(<OCSFEventsPage />);
    await screen.findByText(/OCSF Events/i);
    expect(screen.getByText(/Trace-correlated security events/i)).toBeInTheDocument();
  });
});

describe('AgentsPage', () => {
  it('renders agents page', async () => {
    renderWithProviders(<AgentsPage />);
    await screen.findByText(/AI agents for evaluation/i);
    expect(screen.getByText(/AI agents for evaluation workflows/i)).toBeInTheDocument();
  });
});

describe('EvaluationsPage', () => {
  it('renders evaluations page', async () => {
    renderWithProviders(<EvaluationsPage />);
    await screen.findByText(/Agent evaluation results/i);
    expect(screen.getByText(/Agent evaluation results/i)).toBeInTheDocument();
  });
});