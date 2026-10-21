import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Button, Input, Select, Card, CardHeader, Badge, Table, Pagination, useToast } from '../components/ui';
import type { Evaluation, EvaluationCreate, EvaluationSummary } from '../types/api';

export function EvaluationsPage() {
  const { showToast } = useToast();

  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [agents, setAgents] = useState<Array<{id: number; name: string}>>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ agent_id: '', dataset: '', min_score: '', max_score: '' });

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState<EvaluationCreate>({
    agent_id: 0,
    name: '',
    dataset: '',
    score: 0,
    metrics: {},
    details: '',
  });
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchEvaluations = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 20,
        ...(filters.agent_id && { agent_id: Number(filters.agent_id) }),
        ...(filters.dataset && { dataset: filters.dataset }),
        ...(filters.min_score && { min_score: Number(filters.min_score) }),
        ...(filters.max_score && { max_score: Number(filters.max_score) }),
      };
      const [listRes, summaryRes, agentsRes] = await Promise.all([
        api.listEvaluations(params),
        api.getEvaluationSummary(filters.agent_id ? Number(filters.agent_id) : undefined),
        api.listAgents({ page_size: 100, is_active: true }),
      ]);
      setEvaluations(listRes.items);
      setTotal(listRes.total);
      setTotalPages(listRes.total_pages);
      setSummary(summaryRes);
      setAgents(agentsRes.items.map(a => ({ id: a.id, name: a.name })));
    } catch (error) {
      showToast(`Failed to load evaluations: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluations();
  }, [page, filters]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitLoading(true);
    try {
      await api.createEvaluation(formData);
      showToast('Evaluation created', 'success');
      setShowCreateModal(false);
      setFormData({ agent_id: 0, name: '', dataset: '', score: 0, metrics: {}, details: '' });
      fetchEvaluations();
    } catch (error) {
      showToast(`Failed to create evaluation: ${error}`, 'error');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this evaluation?')) return;
    try {
      await api.deleteEvaluation(id);
      showToast('Evaluation deleted', 'success');
      fetchEvaluations();
    } catch (error) {
      showToast(`Failed to delete: ${error}`, 'error');
    }
  };

  const getScoreBadge = (score: number) => {
    if (score >= 0.8) return <Badge variant="success">{score.toFixed(2)}</Badge>;
    if (score >= 0.6) return <Badge variant="warning">{score.toFixed(2)}</Badge>;
    return <Badge variant="danger">{score.toFixed(2)}</Badge>;
  };

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Evaluations</h1>
          <p className="text-slate-500">Agent evaluation results with LLM explanations (opt-in)</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create Evaluation</Button>
      </div>

      {/* Summary Cards */}
      {summary && total > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <div className="text-3xl font-bold text-slate-900">{summary.total_evaluations}</div>
            <div className="text-sm text-slate-500">Total Evaluations</div>
          </Card>
          <Card>
            <div className="text-3xl font-bold text-blue-600">{summary.average_score.toFixed(2)}</div>
            <div className="text-sm text-slate-500">Average Score</div>
          </Card>
          <Card>
            <div className="text-3xl font-bold text-green-600">{summary.best_score.toFixed(2)}</div>
            <div className="text-sm text-slate-500">Best Score</div>
          </Card>
          <Card>
            <div className="text-3xl font-bold text-red-600">{summary.worst_score.toFixed(2)}</div>
            <div className="text-sm text-slate-500">Worst Score</div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Select
            label="Agent"
            options={[{ value: '', label: 'All Agents' }, ...agents.map(a => ({ value: String(a.id), label: a.name }))]}
            value={filters.agent_id}
            onChange={(e) => setFilters({ ...filters, agent_id: e.target.value })}
          />
          <Input
            label="Dataset"
            placeholder="Filter by dataset"
            value={filters.dataset}
            onChange={(e) => setFilters({ ...filters, dataset: e.target.value })}
          />
          <Input
            label="Min Score"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="0.00"
            value={filters.min_score}
            onChange={(e) => setFilters({ ...filters, min_score: e.target.value })}
          />
          <Input
            label="Max Score"
            type="number"
            step="0.01"
            min="0"
            max="1"
            placeholder="1.00"
            value={filters.max_score}
            onChange={(e) => setFilters({ ...filters, max_score: e.target.value })}
          />
        </div>
      </Card>

      {/* Evaluations Table */}
      <Card>
        <CardHeader title={`Evaluations (${total})`} />
        {loading ? (
          <div className="loading">Loading evaluations...</div>
        ) : (
          <>
            <Table
              columns={[
                { key: 'name', header: 'Name', render: (e) => <span className="font-medium">{e.name}</span> },
                { key: 'dataset', header: 'Dataset', render: (e) => <Badge variant="primary">{e.dataset}</Badge> },
                { key: 'score', header: 'Score', render: (e) => getScoreBadge(e.score) },
                {
                  key: 'metrics',
                  header: 'Metrics',
                  render: (e) => (
                    <div className="flex flex-wrap gap-1 text-xs">
                      {Object.entries(e.metrics).map(([k, v]) => (
                        <Badge key={k} variant="default">{k}: {typeof v === 'number' ? v.toFixed(2) : String(v)}</Badge>
                      ))}
                    </div>
                  ),
                },
                { key: 'created_at', header: 'Created', render: (e) => new Date(e.created_at).toLocaleString() },
                {
                  key: 'llm_explanation',
                  header: 'LLM Explanation',
                  render: (e) => e.llm_explanation ? (
                    <Badge variant="success" className="cursor-help" title={e.llm_explanation}>
                      Available
                    </Badge>
                  ) : (
                    <span className="text-slate-400 text-sm">Not generated</span>
                  ),
                },
                {
                  key: 'actions',
                  header: 'Actions',
                  render: (e) => (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(ev) => { ev.stopPropagation(); handleDelete(e.id); }}
                    >
                      Delete
                    </Button>
                  ),
                },
              ]}
              data={evaluations}
              keyExtractor={(e) => e.id}
              emptyMessage="No evaluations found. Create one to get started."
            />
            <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
          </>
        )}
      </Card>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto" padding="lg">
            <CardHeader
              title="Create Evaluation"
              action={<Button variant="ghost" onClick={() => setShowCreateModal(false)}>Close</Button>}
            />
            <form onSubmit={handleSubmit} className="space-y-4">
              <Select
                label="Agent"
                options={agents.map(a => ({ value: String(a.id), label: a.name }))}
                value={String(formData.agent_id)}
                onChange={(e) => setFormData({ ...formData, agent_id: Number(e.target.value) })}
                required
              />
              <Input
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
              <Input
                label="Dataset"
                value={formData.dataset}
                onChange={(e) => setFormData({ ...formData, dataset: e.target.value })}
                required
              />
              <Input
                label="Score (0.0 - 1.0)"
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={formData.score}
                onChange={(e) => setFormData({ ...formData, score: Number(e.target.value) })}
                required
              />
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Metrics (JSON)</label>
                <textarea
                  className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500 font-mono text-xs"
                  rows={3}
                  value={JSON.stringify(formData.metrics, null, 2)}
                  onChange={(e) => {
                    try {
                      setFormData({ ...formData, metrics: JSON.parse(e.target.value) });
                    } catch {}
                  }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Details (Optional)</label>
                <textarea
                  className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500"
                  rows={3}
                  value={formData.details}
                  onChange={(e) => setFormData({ ...formData, details: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" loading={submitLoading}>
                  Create Evaluation
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}