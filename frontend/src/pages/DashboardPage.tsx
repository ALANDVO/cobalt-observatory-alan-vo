import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Card, CardHeader, Badge, useToast } from '../components/ui';

export function DashboardPage() {
  const { showToast } = useToast();
  const [stats, setStats] = useState<{
    events: number;
    agents: number;
    evaluations: number;
    avgScore: number;
  }>({ events: 0, agents: 0, evaluations: 0, avgScore: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [eventsRes, agentsRes, evalsRes] = await Promise.all([
          api.listOcsfEvents({ page_size: 1 }),
          api.listAgents({ page_size: 1 }),
          api.listEvaluations({ page_size: 1 }),
        ]);
        const summaryRes = await api.getEvaluationSummary();
        setStats({
          events: eventsRes.total,
          agents: agentsRes.total,
          evaluations: evalsRes.total,
          avgScore: summaryRes.average_score,
        });
      } catch (error) {
        showToast(`Failed to load dashboard: ${error}`, 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [showToast]);

  const statCards = [
    { label: 'OCSF Events', value: stats.events, icon: '📊', color: 'blue' },
    { label: 'Agents', value: stats.agents, icon: '🤖', color: 'green' },
    { label: 'Evaluations', value: stats.evaluations, icon: '📈', color: 'purple' },
    { label: 'Avg Score', value: stats.avgScore.toFixed(2), icon: '🎯', color: 'orange' },
  ];

  if (loading) {
    return (
      <div className="container py-12">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="container py-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Dashboard</h1>
      <p className="text-slate-500 mb-8">Cobalt Observatory — AI/ML Agent Trace Correlation & Evaluation</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => (
          <Card key={stat.label} className="transition-shadow hover:shadow-md">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl bg-${stat.color}-100 text-${stat.color}-600 text-2xl`}>
                {stat.icon}
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
                <div className="text-sm text-slate-500">{stat.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Workflows" description="Three core workflows for AI/ML observability" />
          <div className="space-y-4">
            <div className="p-4 border border-slate-200 rounded-lg">
              <h4 className="font-medium text-slate-900">1. OCSF Event Ingestion</h4>
              <p className="text-sm text-slate-500 mt-1">Ingest security events with trace_id/span_id correlation per OCSF 1.8 Trace Profile.</p>
              <div className="flex gap-2 mt-3">
                <Badge variant="primary">Network Activity</Badge>
                <Badge variant="primary">Process Activity</Badge>
                <Badge variant="primary">API Activity</Badge>
                <Badge variant="primary">Trace Profile</Badge>
              </div>
            </div>
            <div className="p-4 border border-slate-200 rounded-lg">
              <h4 className="font-medium text-slate-900">2. Agent Management</h4>
              <p className="text-sm text-slate-500 mt-1">Register and configure AI agents for evaluation pipelines.</p>
              <div className="flex gap-2 mt-3">
                <Badge variant="success">OpenAI</Badge>
                <Badge variant="success">Anthropic</Badge>
                <Badge variant="success">Gemini</Badge>
                <Badge variant="success">Ollama</Badge>
              </div>
            </div>
            <div className="p-4 border border-slate-200 rounded-lg">
              <h4 className="font-medium text-slate-900">3. Agent Evaluation</h4>
              <p className="text-sm text-slate-500 mt-1">Score agents on datasets with deterministic metrics and opt-in LLM explanations.</p>
              <div className="flex gap-2 mt-3">
                <Badge variant="warning">Accuracy</Badge>
                <Badge variant="warning">F1 Score</Badge>
                <Badge variant="warning">Custom Metrics</Badge>
                <Badge variant="warning">Advisory LLM</Badge>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Quick Actions" />
          <div className="grid grid-cols-2 gap-3">
            <a href="/ocsf" className="block p-4 border border-slate-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
              <div className="font-medium text-slate-900">View OCSF Events</div>
              <div className="text-sm text-slate-500 mt-1">Browse, filter, create events</div>
            </a>
            <a href="/agents" className="block p-4 border border-slate-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors">
              <div className="font-medium text-slate-900">Manage Agents</div>
              <div className="text-sm text-slate-500 mt-1">Add, edit, configure agents</div>
            </a>
            <a href="/evaluations" className="block p-4 border border-slate-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors">
              <div className="font-medium text-slate-900">Run Evaluations</div>
              <div className="text-sm text-slate-500 mt-1">Create, compare, analyze scores</div>
            </a>
            <a href="/ocsf?has_trace=true" className="block p-4 border border-slate-200 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors">
              <div className="font-medium text-slate-900">Trace Correlated</div>
              <div className="text-sm text-slate-500 mt-1">Events with trace context</div>
            </a>
          </div>
        </Card>
      </div>
    </div>
  );
}