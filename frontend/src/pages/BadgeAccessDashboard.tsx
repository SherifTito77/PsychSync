import { useState, useEffect } from 'react';
import axios from '../api/axios';

function scoreColor(s: number) { return s >= 70 ? '#ef4444' : s >= 45 ? '#f97316' : s >= 25 ? '#eab308' : '#22c55e'; }
function riskColor(l: string) { return l === 'Critical' ? '#ef4444' : l === 'Elevated' ? '#f97316' : l === 'Monitor' ? '#eab308' : l === 'Healthy' ? '#22c55e' : '#6b7280'; }

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

export default function BadgeAccessDashboard() {
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'trends' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/badge-access-metadata/signals/default`, { params: { days } })
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
    { id: 'trends' as const, label: 'Hours Trends', icon: '📈' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Badge Access Metadata</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>Office entry/exit timestamps — no room-level or movement tracking.</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={14}>14 days</option><option value={30}>30 days</option><option value={60}>60 days</option><option value={90}>90 days</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>🔒</span> Building entry/exit only — no room-level tracking
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #f59e0b' : '2px solid transparent', background: 'none', color: tab === t.id ? '#f59e0b' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading...</div>
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🏢</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Badge System Connected</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect your building access control system to analyze physical presence patterns.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '🚪', label: 'Office entry timestamps' },
                { icon: '🚶', label: 'Office exit timestamps' },
                { icon: '⏰', label: 'Hours in office per day' },
                { icon: '🌙', label: 'Late departures (after 8 PM)' },
                { icon: '📅', label: 'Weekend office presence' },
                { icon: '📈', label: 'Hours trend (increasing?)' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
              <MetricCard icon="⏰" label="Avg Office Hours" value={`${signals.avg_office_hours}h`} detail={`median: ${signals.median_office_hours}h`} />
              <MetricCard icon="📈" label="Max Hours" value={`${signals.max_office_hours}h`} detail="single day" />
              <MetricCard icon="⚠️" label="Long Days (>12h)" value={`${signals.long_day_count}`} detail={`very long (>14h): ${signals.very_long_day_count}`} />
              <MetricCard icon="🌙" label="Late Exits" value={`${(signals.late_departure_ratio * 100).toFixed(0)}%`} detail="after 8 PM" />
              <MetricCard icon="📅" label="Weekend Days" value={`${signals.weekend_days_present}`} detail="in office on weekends" />
              <MetricCard icon="📊" label="Hours Trend" value={signals.hours_trend} detail={`${((signals.recent_vs_baseline_hours - 1) * 100).toFixed(0)}% vs baseline`} />
            </div>
          )}
          {tab === 'trends' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Arrival & Departure</h3>
                <div style={{ display: 'flex', gap: 24 }}>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Arrival</div><div style={{ fontSize: 28, fontWeight: 700 }}>{Math.floor(signals.avg_arrival_hour)}:{String(Math.round((signals.avg_arrival_hour % 1) * 60)).padStart(2, '0')}</div></div>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Departure</div><div style={{ fontSize: 28, fontWeight: 700 }}>{Math.floor(signals.avg_departure_hour)}:{String(Math.round((signals.avg_departure_hour % 1) * 60)).padStart(2, '0')}</div></div>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Consistency</div><div style={{ fontSize: 28, fontWeight: 700 }}>{signals.arrival_consistency < 1 ? 'High' : signals.arrival_consistency < 2 ? 'Medium' : 'Low'}</div></div>
                </div>
              </div>
              <ScoreGauge label="Overwork Score" score={signals.overwork_score} subtitle="Time in office + long days" />
            </div>
          )}
          {tab === 'burnout' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
              <ScoreGauge label="Overwork" score={signals.overwork_score} subtitle="Physical presence" />
              <ScoreGauge label="Boundary Erosion" score={signals.boundary_erosion_score} subtitle="Late + weekend" />
              <ScoreGauge label="Burnout Risk" score={signals.burnout_risk_score} subtitle={signals.risk_label} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
