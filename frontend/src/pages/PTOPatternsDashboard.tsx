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

function MetricCard({ icon, label, value, detail, alert }: { icon: string; label: string; value: string; detail?: string; alert?: boolean }) {
  return (
    <div style={{ background: '#fff', border: alert ? '2px solid #ef4444' : '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: 20 }}>{icon}</span>
        <span style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>{label}</span>
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: alert ? '#ef4444' : undefined }}>{value}</div>
      {detail && <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>{detail}</div>}
    </div>
  );
}

export default function PTOPatternsDashboard() {
  const [lookback, setLookback] = useState(365);
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'patterns' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/pto-patterns/signals/default`, { params: { days: lookback } })
      .then(res => {
        if (!cancelled) {
          const data = res.data?.signals;
          setSignals(data?.risk_label && data.risk_label !== 'No Data' ? data : null);
        }
      })
      .catch(() => { if (!cancelled) setSignals(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [lookback]);

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '📊' },
    { id: 'patterns' as const, label: 'Leave Patterns', icon: '📅' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>PTO Patterns Analysis</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>Leave booking, cancellation, and utilization patterns — no leave reasons or medical details.</p>
        </div>
        <select value={lookback} onChange={e => setLookback(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={180}>6 months</option><option value={365}>1 year</option><option value={730}>2 years</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>🔒</span> Dates and status only — no leave reasons or medical information
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #ec4899' : '2px solid transparent', background: 'none', color: tab === t.id ? '#ec4899' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading...</div>
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🏖</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No PTO Data Connected</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect your HRIS system to analyze PTO patterns.
            PTO avoidance is one of the <strong>strongest early burnout predictors</strong> —
            it surfaces risk 6-12 months before communication changes.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '🏖', label: 'Vacation days taken vs entitled' },
                { icon: '❌', label: 'Vacation cancellation pattern' },
                { icon: '🤒', label: 'Sick day frequency (count only)' },
                { icon: '📊', label: 'Leave balance utilization' },
                { icon: '⏰', label: 'Days since last real break' },
                { icon: '📈', label: 'Sick day trends over time' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Leave reasons, medical details, doctor notes, or any explanation text.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div>
              <div style={{ background: '#fff', border: `2px solid ${riskColor(signals.risk_label)}`, borderRadius: 16, padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>PTO Burnout Risk</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(signals.risk_label) }}>
                    {signals.burnout_risk_score}
                    <span style={{ fontSize: 16, fontWeight: 500, marginLeft: 8 }}>{signals.risk_label}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20 }}>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Avoidance</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.vacation_avoidance_score) }}>{signals.vacation_avoidance_score}</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Recovery</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.recovery_deficit_score) }}>{signals.recovery_deficit_score}</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Sick</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.sick_pattern_score) }}>{signals.sick_pattern_score}</div></div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                <MetricCard icon="🏖" label="Vacation Taken" value={`${signals.vacation_days_taken}d`} detail={`${signals.vacation_days_remaining}d remaining`} />
                <MetricCard icon="📊" label="Utilization" value={`${signals.vacation_utilization_pct}%`} detail={`expected: ${signals.expected_utilization_pct}%`} alert={signals.utilization_gap < -20} />
                <MetricCard icon="⏰" label="Since Last Vacation" value={`${signals.days_since_last_vacation}d`} detail="since 3+ day break" alert={signals.days_since_last_vacation > 90} />
                <MetricCard icon="❌" label="Cancellation Rate" value={`${(signals.cancellation_rate * 100).toFixed(0)}%`} detail={`${signals.vacations_cancelled} of ${signals.vacations_booked} booked`} alert={signals.cancellation_rate > 0.3} />
                <MetricCard icon="🤒" label="Sick Days (30d)" value={`${signals.sick_days_last_30}`} detail={`90d: ${signals.sick_days_last_90} | trend: ${signals.sick_day_trend}`} />
                <MetricCard icon="📈" label="Work Streak" value={`${signals.longest_streak_without_pto}d`} detail="longest without PTO" alert={signals.longest_streak_without_pto > 45} />
              </div>
            </div>
          )}

          {tab === 'patterns' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Utilization Gap</h3>
                <div style={{ fontSize: 48, fontWeight: 700, color: signals.utilization_gap < -20 ? '#ef4444' : '#22c55e', textAlign: 'center' }}>
                  {signals.utilization_gap > 0 ? '+' : ''}{signals.utilization_gap}%
                </div>
                <div style={{ textAlign: 'center', fontSize: 13, color: '#6b7280', marginTop: 8 }}>
                  {signals.utilization_gap < -20 ? 'Significantly under-using PTO' : signals.utilization_gap < 0 ? 'Slightly below expected' : 'On track'}
                </div>
              </div>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Sick Day Pattern</h3>
                <div style={{ display: 'flex', gap: 24, marginBottom: 12 }}>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Last 30 days</div><div style={{ fontSize: 28, fontWeight: 700 }}>{signals.sick_days_last_30}</div></div>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Last 90 days</div><div style={{ fontSize: 28, fontWeight: 700 }}>{signals.sick_days_last_90}</div></div>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Mon/Fri Ratio</div><div style={{ fontSize: 28, fontWeight: 700, color: signals.monday_friday_sick_ratio > 0.4 ? '#f97316' : '#22c55e' }}>{(signals.monday_friday_sick_ratio * 100).toFixed(0)}%</div></div>
                </div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Trend: <strong>{signals.sick_day_trend}</strong></div>
              </div>
            </div>
          )}

          {tab === 'burnout' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Recommendations</h3>
                  {signals.recommendations.map((rec: string, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                      <span style={{ color: '#ec4899', flexShrink: 0 }}>&#9679;</span>
                      <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{rec}</span>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'grid', gridTemplateRows: '1fr 1fr 1fr', gap: 12 }}>
                  <ScoreGauge label="Vacation Avoidance" score={signals.vacation_avoidance_score} subtitle="Not using available PTO" />
                  <ScoreGauge label="Recovery Deficit" score={signals.recovery_deficit_score} subtitle="Insufficient rest periods" />
                  <ScoreGauge label="Burnout Risk" score={signals.burnout_risk_score} subtitle={signals.risk_label} />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
