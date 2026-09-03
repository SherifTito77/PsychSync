import { useState, useEffect, useCallback } from 'react';
import { getOKRSummary, type OKRSummary, type OKRObjective } from '../services/okrService';

const PERIODS = [
  { value: 'q1', label: 'Q1' },
  { value: 'q2', label: 'Q2' },
  { value: 'q3', label: 'Q3' },
  { value: 'q4', label: 'Q4' },
  { value: 'h1', label: 'H1' },
  { value: 'h2', label: 'H2' },
  { value: 'annual', label: 'Annual' },
];

function healthColor(health: string): string {
  if (health === 'green') return '#22c55e';
  if (health === 'yellow') return '#eab308';
  return '#ef4444';
}

function statusBadge(status: string) {
  const colors: Record<string, { bg: string; text: string }> = {
    active: { bg: '#dbeafe', text: '#1d4ed8' },
    completed: { bg: '#dcfce7', text: '#15803d' },
    draft: { bg: '#f3f4f6', text: '#6b7280' },
    cancelled: { bg: '#fee2e2', text: '#b91c1c' },
  };
  const c = colors[status] || colors.draft;
  return (
    <span style={{ background: c.bg, color: c.text, padding: '2px 8px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
      {status.toUpperCase()}
    </span>
  );
}

function KRHealthBar({ summary }: { summary: OKRSummary }) {
  const kr = summary.key_results;
  const total = kr.total || 1;
  const segments = [
    { count: kr.achieved, color: '#22c55e', label: 'Achieved' },
    { count: kr.on_track, color: '#3b82f6', label: 'On Track' },
    { count: kr.at_risk, color: '#eab308', label: 'At Risk' },
    { count: kr.off_track, color: '#ef4444', label: 'Off Track' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', height: 24, borderRadius: 12, overflow: 'hidden', background: '#f3f4f6' }}>
        {segments.map((s) => (
          s.count > 0 && (
            <div
              key={s.label}
              style={{ width: `${(s.count / total) * 100}%`, background: s.color, transition: 'width 0.5s' }}
              title={`${s.label}: ${s.count}`}
            />
          )
        ))}
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 13 }}>
        {segments.map((s) => (
          <span key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: s.color, display: 'inline-block' }} />
            {s.label}: {s.count}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function OKRDashboard() {
  const currentQuarter = `q${Math.ceil((new Date().getMonth() + 1) / 3)}`;
  const [period, setPeriod] = useState(currentQuarter);
  const [year, setYear] = useState(new Date().getFullYear());
  const [summary, setSummary] = useState<OKRSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getOKRSummary(period, year);
      setSummary(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load OKR data');
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, [period, year]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>OKR Dashboard</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            style={{ padding: '6px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}
          >
            {PERIODS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            min={2020}
            max={2030}
            style={{ width: 80, padding: '6px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}
          />
        </div>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 48, color: '#6b7280' }}>Loading OKR data...</div>}
      {error && <div style={{ textAlign: 'center', padding: 48, color: '#ef4444' }}>{error}</div>}

      {summary && !loading && (
        <>
          {/* Health + Stats Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
            <div style={{
              background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e5e7eb',
              display: 'flex', flexDirection: 'column', alignItems: 'center',
            }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%', background: healthColor(summary.overall_health),
                display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 8,
              }}>
                <span style={{ fontSize: 20 }}>
                  {summary.overall_health === 'green' ? '✓' : summary.overall_health === 'yellow' ? '!' : '✕'}
                </span>
              </div>
              <div style={{ fontSize: 13, color: '#6b7280' }}>Overall Health</div>
              <div style={{ fontSize: 16, fontWeight: 700, textTransform: 'capitalize' }}>{summary.overall_health}</div>
            </div>

            <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e5e7eb', textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 700, color: '#3b82f6' }}>{summary.objectives.total}</div>
              <div style={{ fontSize: 13, color: '#6b7280' }}>Objectives</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{summary.objectives.completion_rate}% complete</div>
            </div>

            <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e5e7eb', textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 700, color: '#8b5cf6' }}>{summary.key_results.total}</div>
              <div style={{ fontSize: 13, color: '#6b7280' }}>Key Results</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{summary.key_results.achievement_rate}% achieved</div>
            </div>

            <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e5e7eb', textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 700, color: '#22c55e' }}>{summary.key_results.achieved}</div>
              <div style={{ fontSize: 13, color: '#6b7280' }}>KRs Achieved</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>
                {summary.key_results.at_risk + summary.key_results.off_track} need attention
              </div>
            </div>
          </div>

          {/* KR Health Bar */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e5e7eb', marginBottom: 24 }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: 16, fontWeight: 600 }}>Key Results Health</h3>
            <KRHealthBar summary={summary} />
          </div>

          {/* Objectives List */}
          <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e5e7eb' }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: 16, fontWeight: 600 }}>Objectives</h3>
            {summary.objectives_list.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 32, color: '#6b7280' }}>
                No objectives for this period. Create objectives to start tracking.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {summary.objectives_list.map((obj: OKRObjective) => (
                  <div
                    key={obj.id}
                    style={{
                      padding: 16, borderRadius: 8, border: '1px solid #e5e7eb',
                      display: 'flex', alignItems: 'center', gap: 16,
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, marginBottom: 4 }}>{obj.title}</div>
                      <div style={{ fontSize: 13, color: '#6b7280' }}>
                        {obj.key_results_count} key results
                      </div>
                    </div>
                    <div style={{ width: 160 }}>
                      <div style={{
                        height: 8, borderRadius: 4, background: '#f3f4f6', overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%', borderRadius: 4,
                          width: `${Math.min(obj.progress, 100)}%`,
                          background: obj.progress >= 100 ? '#22c55e' : obj.progress >= 50 ? '#3b82f6' : '#eab308',
                          transition: 'width 0.5s',
                        }} />
                      </div>
                      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4, textAlign: 'right' }}>
                        {obj.progress.toFixed(0)}%
                      </div>
                    </div>
                    {statusBadge(obj.status)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
