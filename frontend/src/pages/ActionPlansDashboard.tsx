import { useState, useEffect } from 'react';

interface ActionPlan {
  id: string;
  title: string;
  category: string;
  status: string;
  priority: string;
  due_date: string | null;
  owner_id: string;
  source: string;
}

interface DashboardData {
  total: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  overdue: number;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  proposed: { bg: '#f3f4f6', text: '#6b7280' },
  accepted: { bg: '#dbeafe', text: '#1d4ed8' },
  in_progress: { bg: '#fef3c7', text: '#92400e' },
  completed: { bg: '#dcfce7', text: '#15803d' },
  skipped: { bg: '#fee2e2', text: '#991b1b' },
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

function ActionPlansDashboard() {
  const [plans, setPlans] = useState<ActionPlan[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    // Placeholder — will wire to API
    setLoading(false);
    setDashboard({
      total: 0,
      by_status: { proposed: 0, accepted: 0, in_progress: 0, completed: 0, skipped: 0 },
      by_category: {},
      overdue: 0,
    });
  }, []);

  const filtered = filter === 'all' ? plans : plans.filter(p => p.status === filter);

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Action Plans</h1>
      <p style={{ color: '#6b7280', marginBottom: 24 }}>
        Track interventions from Pulse warnings, Manager Intelligence, and manual creation.
      </p>

      {/* Status summary cards */}
      {dashboard && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 24 }}>
          {Object.entries(dashboard.by_status).map(([status, count]) => {
            const c = STATUS_COLORS[status] || STATUS_COLORS.proposed;
            return (
              <div
                key={status}
                onClick={() => setFilter(filter === status ? 'all' : status)}
                style={{
                  background: c.bg,
                  color: c.text,
                  padding: 16,
                  borderRadius: 12,
                  cursor: 'pointer',
                  border: filter === status ? `2px solid ${c.text}` : '2px solid transparent',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: 28, fontWeight: 700 }}>{count}</div>
                <div style={{ fontSize: 13, textTransform: 'capitalize' }}>{status.replace('_', ' ')}</div>
              </div>
            );
          })}
          <div style={{ background: '#fef2f2', color: '#991b1b', padding: 16, borderRadius: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{dashboard.overdue}</div>
            <div style={{ fontSize: 13 }}>Overdue</div>
          </div>
        </div>
      )}

      {/* Plans list */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#9ca3af' }}>Loading...</div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#9ca3af', background: '#f9fafb', borderRadius: 12 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📋</div>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: '#374151' }}>No action plans yet</h3>
          <p style={{ fontSize: 14 }}>Action plans are auto-created from Pulse warnings and Manager Intelligence insights.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(plan => {
            const sc = STATUS_COLORS[plan.status] || STATUS_COLORS.proposed;
            return (
              <div key={plan.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 4, height: 40, borderRadius: 2, background: PRIORITY_COLORS[plan.priority] || '#9ca3af' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{plan.title}</div>
                  <div style={{ fontSize: 12, color: '#6b7280' }}>{plan.category} &middot; {plan.source}</div>
                </div>
                <span style={{ background: sc.bg, color: sc.text, padding: '4px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
                  {plan.status.replace('_', ' ').toUpperCase()}
                </span>
                {plan.due_date && (
                  <span style={{ fontSize: 12, color: '#6b7280' }}>Due {plan.due_date}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ActionPlansDashboard;
