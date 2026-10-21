import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Button, Input, Select, Card, CardHeader, Badge, Table, Pagination, useToast } from '../components/ui';
import type { OCSFEvent, OCSFEventCreate, TraceContext } from '../types/api';

const SEVERITY_OPTIONS = [
  { value: '1', label: 'Informational (1)' },
  { value: '2', label: 'Low (2)' },
  { value: '3', label: 'Medium (3)' },
  { value: '4', label: 'High (4)' },
  { value: '5', label: 'Critical (5)' },
];

const STATUS_OPTIONS = [
  { value: '1', label: 'Success (1)' },
  { value: '2', label: 'Failure (2)' },
  { value: '3', label: 'Unknown (3)' },
];


export function OCSFEventsPage() {
  const { showToast } = useToast();

  // List state
  const [events, setEvents] = useState<OCSFEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    trace_uid: '',
    has_trace: '',
    class_uid: '',
    severity_id: '',
  });

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<OCSFEventCreate>({
    class_uid: 4001,
    activity_id: 1,
    category_uid: 4,
    category_name: 'Network Activity',
    class_name: 'Network Connection',
    time: new Date().toISOString(),
    severity_id: 1,
    severity: 'Informational',
    status_id: 1,
    status: 'Success',
    profiles: [],
    event_data: {},
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [traceUidInput, setTraceUidInput] = useState('');
  const [spanIdInput, setSpanIdInput] = useState('');

  // Fetch events
  const fetchEvents = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 20,
        ...(filters.trace_uid && { trace_uid: filters.trace_uid }),
        ...(filters.has_trace && { has_trace: filters.has_trace === 'true' }),
        ...(filters.class_uid && { class_uid: Number(filters.class_uid) }),
        ...(filters.severity_id && { severity_id: Number(filters.severity_id) }),
      };
      const response = await api.listOcsfEvents(params);
      setEvents(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (error) {
      showToast(`Failed to load events: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [page, filters]);

  // Handle create
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      const traceContext: TraceContext | undefined = traceUidInput
        ? { uid: traceUidInput, span_id: spanIdInput || undefined }
        : undefined;

      const eventData: OCSFEventCreate = {
        ...createForm,
        trace_context: traceContext,
      };

      await api.createOcsfEvent(eventData);
      showToast('Event created successfully', 'success');
      setShowCreateModal(false);
      setTraceUidInput('');
      setSpanIdInput('');
      fetchEvents();
    } catch (error) {
      showToast(`Failed to create event: ${error}`, 'error');
    } finally {
      setCreateLoading(false);
    }
  };

  // Handle delete
  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this event?')) return;
    try {
      await api.deleteOcsfEvent(id);
      showToast('Event deleted', 'success');
      fetchEvents();
    } catch (error) {
      showToast(`Failed to delete: ${error}`, 'error');
    }
  };

  // Format timestamp
  const formatTime = (iso: string) => {
    const date = new Date(iso);
    return date.toLocaleString();
  };

  return (
    <div className="container py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">OCSF Events</h1>
          <p className="text-slate-500">Trace-correlated security events (OCSF 1.8 Trace Profile)</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create Event</Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Input
            label="Trace UID"
            placeholder="Filter by trace UID (32 hex chars)"
            value={filters.trace_uid}
            onChange={(e) => setFilters({ ...filters, trace_uid: e.target.value })}
          />
          <Select
            label="Has Trace"
            options={[
              { value: '', label: 'All' },
              { value: 'true', label: 'Has Trace' },
              { value: 'false', label: 'No Trace' },
            ]}
            value={filters.has_trace}
            onChange={(e) => setFilters({ ...filters, has_trace: e.target.value })}
          />
          <Input
            label="Class UID"
            type="number"
            placeholder="e.g. 4001"
            value={filters.class_uid}
            onChange={(e) => setFilters({ ...filters, class_uid: e.target.value })}
          />
          <Select
            label="Severity"
            options={[{ value: '', label: 'All' }, ...SEVERITY_OPTIONS]}
            value={filters.severity_id}
            onChange={(e) => setFilters({ ...filters, severity_id: e.target.value })}
          />
        </div>
      </Card>

      {/* Events Table */}
      <Card>
        <CardHeader title={`Events (${total})`} />
        {loading ? (
          <div className="loading">Loading events...</div>
        ) : (
          <>
            <Table
              columns={[
                { key: 'time', header: 'Time', render: (e) => formatTime(e.time) },
                {
                  key: 'class_name',
                  header: 'Class / Activity',
                  render: (e) => (
                    <div>
                      <span className="font-medium">{e.class_name}</span>
                      <div className="text-xs text-slate-500">UID: {e.class_uid} / Act: {e.activity_id}</div>
                    </div>
                  ),
                },
                {
                  key: 'severity',
                  header: 'Severity',
                  render: (e) => (
                    <Badge
                      variant={
                        e.severity_id >= 4 ? 'danger' : e.severity_id >= 3 ? 'warning' : 'default'
                      }
                    >
                      {e.severity}
                    </Badge>
                  ),
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (e) => (
                    <Badge variant={e.status_id === 1 ? 'success' : 'danger'}>
                      {e.status}
                    </Badge>
                  ),
                },
                {
                  key: 'trace',
                  header: 'Trace Correlation',
                  render: (e) => (
                    <div className="font-mono text-xs">
                      {e.trace_uid ? (
                        <>
                          <span className="text-blue-600">{e.trace_uid.slice(0, 16)}…</span>
                          {e.span_uid && (
                            <span className="ml-2 text-slate-500">span: {e.span_uid}</span>
                          )}
                          <Badge variant="primary" className="ml-2">Trace Profile</Badge>
                        </>
                      ) : (
                        <span className="text-slate-400">No trace</span>
                      )}
                    </div>
                  ),
                },
                {
                  key: 'profiles',
                  header: 'Profiles',
                  render: (e) => (
                    <div className="flex flex-wrap gap-1">
                      {e.profiles.map((p) => (
                        <Badge key={p} variant="default" className="text-xs">{p}</Badge>
                      ))}
                    </div>
                  ),
                },
                {
                  key: 'actions',
                  header: 'Actions',
                  render: (e) => (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        handleDelete(e.id);
                      }}
                    >
                      Delete
                    </Button>
                  ),
                },
              ]}
              data={events}
              keyExtractor={(e) => e.id}
              emptyMessage="No events found. Create one or adjust filters."
            />
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </>
        )}
      </Card>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto" padding="lg">
            <CardHeader
              title="Create OCSF Event"
              action={<Button variant="ghost" onClick={() => setShowCreateModal(false)}>Close</Button>}
            />
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Class UID"
                  type="number"
                  value={createForm.class_uid}
                  onChange={(e) => setCreateForm({ ...createForm, class_uid: Number(e.target.value) })}
                  required
                />
                <Input
                  label="Activity ID"
                  type="number"
                  value={createForm.activity_id}
                  onChange={(e) => setCreateForm({ ...createForm, activity_id: Number(e.target.value) })}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Category UID"
                  type="number"
                  value={createForm.category_uid}
                  onChange={(e) => setCreateForm({ ...createForm, category_uid: Number(e.target.value) })}
                  required
                />
                <Select
                  label="Severity"
                  options={SEVERITY_OPTIONS}
                  value={String(createForm.severity_id)}
                  onChange={(e) => setCreateForm({ ...createForm, severity_id: Number(e.target.value), severity: SEVERITY_OPTIONS.find(o => o.value === e.target.value)?.label.split(' ')[0] || 'Informational' })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Category Name"
                  value={createForm.category_name}
                  onChange={(e) => setCreateForm({ ...createForm, category_name: e.target.value })}
                  required
                />
                <Select
                  label="Status"
                  options={STATUS_OPTIONS}
                  value={String(createForm.status_id)}
                  onChange={(e) => setCreateForm({ ...createForm, status_id: Number(e.target.value), status: STATUS_OPTIONS.find(o => o.value === e.target.value)?.label.split(' ')[0] || 'Success' })}
                />
              </div>
              <Input
                label="Class Name"
                value={createForm.class_name}
                onChange={(e) => setCreateForm({ ...createForm, class_name: e.target.value })}
                required
              />
              <Input
                label="Time (ISO 8601)"
                type="datetime-local"
                value={createForm.time.slice(0, 16)}
                onChange={(e) => setCreateForm({ ...createForm, time: new Date(e.target.value).toISOString() })}
              />

              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">Trace Correlation (Optional)</h4>
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Trace UID (32 hex chars)"
                    placeholder="0af7651916cd43dd8448eb211c80319c"
                    value={traceUidInput}
                    onChange={(e) => setTraceUidInput(e.target.value)}
                    pattern="^[0-9a-f]{32}$"
                  />
                  <Input
                    label="Span ID (16 hex chars, optional)"
                    placeholder="1234567890abcdef"
                    value={spanIdInput}
                    onChange={(e) => setSpanIdInput(e.target.value)}
                    pattern="^[0-9a-f]{16}$"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  When provided, adds <code>trace.uid</code> and <code>trace</code> profile per OCSF 1.8 Trace Profile.
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" loading={createLoading}>
                  Create Event
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
