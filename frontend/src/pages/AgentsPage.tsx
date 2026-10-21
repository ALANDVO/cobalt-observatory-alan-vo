import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Button, Input, Select, Card, CardHeader, Badge, Table, Pagination, useToast } from '../components/ui';
import type { Agent, AgentCreate } from '../types/api';

const PROVIDER_OPTIONS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'ollama', label: 'Ollama' },
  { value: 'litellm', label: 'LiteLLM' },
  { value: 'openrouter', label: 'OpenRouter' },
];

export function AgentsPage() {
  const { showToast } = useToast();

  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ provider: '', is_active: '' });

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [formData, setFormData] = useState<AgentCreate>({
    name: '',
    description: '',
    model: '',
    provider: 'openai',
    configuration: {},
  });
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 20,
        ...(filters.provider && { provider: filters.provider }),
        ...(filters.is_active && { is_active: filters.is_active === 'true' }),
      };
      const response = await api.listAgents(params);
      setAgents(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (error) {
      showToast(`Failed to load agents: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, [page, filters]);

  const resetForm = () => {
    setFormData({ name: '', description: '', model: '', provider: 'openai', configuration: {} });
    setEditingAgent(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitLoading(true);
    try {
      if (editingAgent) {
        await api.updateAgent(editingAgent.id, formData);
        showToast('Agent updated', 'success');
      } else {
        await api.createAgent(formData);
        showToast('Agent created', 'success');
      }
      setShowCreateModal(false);
      resetForm();
      fetchAgents();
    } catch (error) {
      showToast(`Failed to save agent: ${error}`, 'error');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleEdit = (agent: Agent) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      description: agent.description || '',
      model: agent.model,
      provider: agent.provider,
      configuration: agent.configuration,
    });
    setShowCreateModal(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this agent?')) return;
    try {
      await api.deleteAgent(id);
      showToast('Agent deleted', 'success');
      fetchAgents();
    } catch (error) {
      showToast(`Failed to delete: ${error}`, 'error');
    }
  };

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Agents</h1>
          <p className="text-slate-500">AI agents for evaluation workflows</p>
        </div>
        <Button onClick={() => { resetForm(); setShowCreateModal(true); }}>Add Agent</Button>
      </div>

      <Card className="mb-6">
        <div className="flex gap-4">
          <Select
            label="Provider"
            options={[{ value: '', label: 'All' }, ...PROVIDER_OPTIONS]}
            value={filters.provider}
            onChange={(e) => setFilters({ ...filters, provider: e.target.value })}
            className="w-48"
          />
          <Select
            label="Status"
            options={[{ value: '', label: 'All' }, { value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive' }]}
            value={filters.is_active}
            onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
            className="w-40"
          />
        </div>
      </Card>

      <Card>
        <CardHeader title={`Agents (${total})`} />
        {loading ? (
          <div className="loading">Loading agents...</div>
        ) : (
          <>
            <Table
              columns={[
                { key: 'name', header: 'Name', render: (a) => <span className="font-medium">{a.name}</span> },
                { key: 'provider', header: 'Provider', render: (a) => <Badge variant="primary">{a.provider}</Badge> },
                { key: 'model', header: 'Model' },
                {
                  key: 'status',
                  header: 'Status',
                  render: (a) => <Badge variant={a.is_active ? 'success' : 'default'}>
                    {a.is_active ? 'Active' : 'Inactive'}
                  </Badge>,
                },
                { key: 'created_at', header: 'Created', render: (a) => new Date(a.created_at).toLocaleDateString() },
                {
                  key: 'actions',
                  header: 'Actions',
                  render: (a) => (
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleEdit(a); }}>
                        Edit
                      </Button>
                      <Button variant="danger" size="sm" onClick={(e) => { e.stopPropagation(); handleDelete(a.id); }}>
                        Delete
                      </Button>
                    </div>
                  ),
                },
              ]}
              data={agents}
              keyExtractor={(a) => a.id}
              emptyMessage="No agents found. Create one to get started."
            />
            <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
          </>
        )}
      </Card>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto" padding="lg">
            <CardHeader
              title={editingAgent ? 'Edit Agent' : 'Create Agent'}
              action={<Button variant="ghost" onClick={() => { setShowCreateModal(false); resetForm(); }}>Close</Button>}
            />
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
              <Input
                label="Model"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                required
              />
              <Select
                label="Provider"
                options={PROVIDER_OPTIONS}
                value={formData.provider}
                onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
              />
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
                <textarea
                  className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Configuration (JSON)</label>
                <textarea
                  className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-500 font-mono text-xs"
                  rows={4}
                  value={JSON.stringify(formData.configuration, null, 2)}
                  onChange={(e) => {
                    try {
                      setFormData({ ...formData, configuration: JSON.parse(e.target.value) });
                    } catch {
                      // Ignore invalid JSON while typing
                    }
                  }}
                />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="secondary" type="button" onClick={() => { setShowCreateModal(false); resetForm(); }}>
                  Cancel
                </Button>
                <Button type="submit" loading={submitLoading}>
                  {editingAgent ? 'Update' : 'Create'} Agent
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}