import { useState, useEffect } from 'react';
import axios from '../api/axios';

function scoreColor(s: number) { return s >= 70 ? '#ef4444' : s >= 45 ? '#f97316' : s >= 25 ? '#eab308' : '#22c55e'; }
function riskColor(l: string) { return l === 'Critical' ? '#ef4444' : l === 'Elevated' ? '#f97316' : l === 'Monitor' ? '#eab308' : l === 'Healthy' ? '#22c55e' : '#6b7280'; }
function formatHour(h: number) { return h === 0 ? '12a' : h < 12 ? `${h}a` : h === 12 ? '12p' : `${h-12}p`; }

function ScoreGauge({ label, score, subtitle }: { label: string; score: number; subtitle: string }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#6b7280', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 42, fontWeight: 700, color: scoreColor(score), lineHeight: 1 }}>{score}</div>
      <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>/100</div>
      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 8 }}>{subtitle}</div>
    </div>
  );
}

function MetricCard({ icon, label, value, detail }: { icon: string; label: string; value: string; detail?: string }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 20 }}>{icon}</span>
        <span style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>{label}</span>
      </div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
      {detail && <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>{detail}</div>}
    </div>
  );
}

export default function ComputerUsageDashboard() {
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'sessions' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/computer-usage-metadata/signals/default`, { params: { days } })
      .then(res => {
        if (!cancelled) {
          const data = res.data?.signals;
          setSignals(data?.risk_label && data.risk_label !== 'No Data' ? data : null);
        }
      })
      .catch(() => { if (!cancelled) setSignals(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [days]);

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '📊' },
    { id: 'sessions' as const, label: 'Sessions & Breaks', icon: '⏱' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Computer Usage Metadata</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>Activity levels only — no screen capture, keystroke content, or app names.</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={7}>7 days</option><option value={14}>14 days</option><option value={30}>30 days</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>🔒</span> Activity levels only — no screen recording, no keystroke logging
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #10b981' : '2px solid transparent', background: 'none', color: tab === t.id ? '#10b981' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading...</div>
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🖥</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Desktop Agent Connected</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Deploy the lightweight desktop agent to analyze workstation activity metadata.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '⌨️', label: 'Keyboard activity (rate, not keystrokes)' },
                { icon: '🖱', label: 'Mouse activity (rate, not coordinates)' },
                { icon: '🔄', label: 'Application switching frequency' },
                { icon: '💤', label: 'Idle time detection' },
                { icon: '⏱', label: 'Continuous work sessions' },
                { icon: '🌙', label: 'After-hours computer use' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Capture:</strong> Screen content, keystroke text, application names, URLs, or mouse click targets.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
              <MetricCard icon="⏱" label="Avg Active Hours" value={`${signals.avg_daily_active_hours}h`} detail="per day" />
              <MetricCard icon="🔄" label="App Switches" value={`${signals.app_switches_per_hour}/hr`} detail="context switches" />
              <MetricCard icon="📊" label="Avg Session" value={`${signals.avg_session_duration_min}m`} detail={`max: ${signals.max_session_duration_min}m`} />
              <MetricCard icon="⚠️" label="Sessions >3h" value={`${signals.sessions_over_3h}`} detail="without break" />
              <MetricCard icon="🌙" label="After Hours" value={`${(signals.after_hours_ratio * 100).toFixed(1)}%`} detail="of activity" />
              <MetricCard icon="🕐" label="Workday Span" value={`${signals.avg_workday_span_hours}h`} detail="first to last activity" />
            </div>
          )}
          {tab === 'sessions' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
              <ScoreGauge label="Work Intensity" score={signals.work_intensity_score} subtitle="Sustained high activity" />
              <ScoreGauge label="Break Deficit" score={signals.break_deficit_score} subtitle="Insufficient rest breaks" />
              <ScoreGauge label="Context Switching" score={signals.context_switching_score} subtitle="App switches/hour" />
            </div>
          )}
          {tab === 'burnout' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
              <ScoreGauge label="Work Intensity" score={signals.work_intensity_score} subtitle="Activity pressure" />
              <ScoreGauge label="Break Deficit" score={signals.break_deficit_score} subtitle="No rest" />
              <ScoreGauge label="Boundary Erosion" score={signals.boundary_erosion_score} subtitle="After-hours" />
              <ScoreGauge label="Burnout Risk" score={signals.burnout_risk_score} subtitle={signals.risk_label} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
