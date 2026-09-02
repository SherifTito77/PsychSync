import { useState, useEffect } from 'react';
import axios from '../api/axios';

interface EmailSignals {
  avg_daily_sent: number;
  avg_daily_received: number;
  sent_received_ratio: number;
  after_hours_ratio: number;
  weekend_ratio: number;
  peak_hour: number;
  hourly_distribution: number[];
  avg_response_time_min: number;
  p90_response_time_min: number;
  instant_reply_ratio: number;
  internal_ratio: number;
  avg_recipients_per_email: number;
  communication_load_score: number;
  boundary_erosion_score: number;
  burnout_risk_score: number;
  risk_label: string;
  recommendations: string[];
  daily_breakdown: DailyBreakdown[];
}

interface DailyBreakdown {
  date: string;
  sent: number;
  received: number;
  after_hours_sent: number;
  after_hours_received: number;
  avg_response_time_min: number | null;
  internal_ratio: number;
  external_contacts: number;
}

function riskColor(label: string): string {
  switch (label) {
    case 'Critical': return '#ef4444';
    case 'Elevated': return '#f97316';
    case 'Monitor': return '#eab308';
    case 'Healthy': return '#22c55e';
    default: return '#6b7280';
  }
}

function scoreColor(score: number): string {
  if (score >= 70) return '#ef4444';
  if (score >= 45) return '#f97316';
  if (score >= 25) return '#eab308';
  return '#22c55e';
}

function formatHour(h: number): string {
  if (h === 0) return '12a';
  if (h < 12) return `${h}a`;
  if (h === 12) return '12p';
  return `${h - 12}p`;
}

function ScoreGauge({ label, score, subtitle }: { label: string; score: number; subtitle: string }) {
  const color = scoreColor(score);
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#6b7280', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 42, fontWeight: 700, color, lineHeight: 1 }}>{score}</div>
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

function HourlyHeatmap({ distribution }: { distribution: number[] }) {
  const max = Math.max(...distribution, 1);
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Hourly Activity Heatmap</h3>
      <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end', height: 120 }}>
        {distribution.map((count, hour) => {
          const intensity = count / max;
          const isWorkHours = hour >= 9 && hour < 18;
          return (
            <div key={hour} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <div
                style={{
                  width: '100%',
                  height: `${Math.max(intensity * 100, 2)}%`,
                  background: isWorkHours
                    ? `rgba(59, 130, 246, ${0.2 + intensity * 0.8})`
                    : `rgba(239, 68, 68, ${0.2 + intensity * 0.8})`,
                  borderRadius: 3,
                  transition: 'height 0.3s',
                }}
                title={`${formatHour(hour)}: ${count} emails`}
              />
              {hour % 3 === 0 && (
                <span style={{ fontSize: 10, color: '#9ca3af' }}>{formatHour(hour)}</span>
              )}
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 11, color: '#9ca3af' }}>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#3b82f6', marginRight: 4 }} />Work hours (9a-6p)</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#ef4444', marginRight: 4 }} />After hours</span>
      </div>
    </div>
  );
}

function DailyChart({ data }: { data: DailyBreakdown[] }) {
  const maxVol = Math.max(...data.map(d => d.sent + d.received), 1);
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Daily Volume</h3>
      <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 140 }}>
        {data.map(d => {
          const total = d.sent + d.received;
          const pct = (total / maxVol) * 100;
          const ahPct = ((d.after_hours_sent + d.after_hours_received) / Math.max(total, 1)) * 100;
          return (
            <div key={d.date} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <div style={{ fontSize: 10, color: '#6b7280' }}>{total}</div>
              <div style={{ width: '100%', position: 'relative', height: `${Math.max(pct, 4)}%`, borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ position: 'absolute', bottom: 0, width: '100%', height: '100%', background: '#3b82f6', borderRadius: 4 }} />
                {ahPct > 0 && (
                  <div style={{ position: 'absolute', top: 0, width: '100%', height: `${ahPct}%`, background: '#ef4444', borderRadius: '4px 4px 0 0' }} />
                )}
              </div>
              <span style={{ fontSize: 9, color: '#9ca3af', writingMode: 'vertical-rl', transform: 'rotate(180deg)', maxHeight: 50, overflow: 'hidden' }}>
                {d.date.slice(5)}
              </span>
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 11, color: '#9ca3af' }}>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#3b82f6', marginRight: 4 }} />Work hours</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#ef4444', marginRight: 4 }} />After hours</span>
      </div>
    </div>
  );
}

export default function EmailMetadataDashboard() {
  const [signals, setSignals] = useState<EmailSignals | null>(null);
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'overview' | 'timing' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/email-metadata/signals/default`, { params: { days } })
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
    { id: 'timing' as const, label: 'Timing & Patterns', icon: '🕐' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Email Metadata Analysis</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>
            Behavioral signals from email metadata only — message content is never accessed.
          </p>
        </div>
        <select
          value={days}
          onChange={e => setDays(Number(e.target.value))}
          style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Privacy badge */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20,
        padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24,
      }}>
        <span>🔒</span> Metadata only — zero email content accessed
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb', paddingBottom: 0 }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: '10px 20px',
              border: 'none',
              borderBottom: tab === t.id ? '2px solid #3b82f6' : '2px solid transparent',
              background: 'none',
              color: tab === t.id ? '#3b82f6' : '#6b7280',
              fontWeight: tab === t.id ? 600 : 400,
              cursor: 'pointer',
              fontSize: 14,
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading email metadata signals...</div>
      ) : !signals ? (
        /* Empty / not connected state */
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📧</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Email Connector Active</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect your email provider to start analyzing metadata patterns.
            PsychSync uses the <strong>metadata-only</strong> OAuth scope — it reads
            timestamps, sender/recipient domains, and thread info. It never accesses
            email subjects or bodies.
          </p>
          <div style={{
            background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16,
            padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left',
          }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze (Metadata Only)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '📤', label: 'Emails sent (count)' },
                { icon: '📥', label: 'Emails received (count)' },
                { icon: '🕐', label: 'Send timestamps' },
                { icon: '⏱️', label: 'Response times' },
                { icon: '🏢', label: 'Internal vs. external' },
                { icon: '🌙', label: 'After-hours activity' },
                { icon: '📅', label: 'Weekend activity' },
                { icon: '🔗', label: 'Thread depth' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Email subjects, body text, attachments, or any message content.
            </div>
          </div>
        </div>
      ) : (
        /* Data loaded — render based on active tab */
        <>
          {tab === 'overview' && (
            <div>
              {/* Risk banner */}
              <div style={{
                background: '#fff', border: `2px solid ${riskColor(signals.risk_label)}`,
                borderRadius: 16, padding: 20, marginBottom: 24,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Email Burnout Risk</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(signals.risk_label) }}>
                    {signals.burnout_risk_score}
                    <span style={{ fontSize: 16, fontWeight: 500, marginLeft: 8 }}>{signals.risk_label}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 24 }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>Load</div>
                    <div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.communication_load_score) }}>
                      {signals.communication_load_score}
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>Boundary</div>
                    <div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.boundary_erosion_score) }}>
                      {signals.boundary_erosion_score}
                    </div>
                  </div>
                </div>
              </div>

              {/* Key metrics grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
                <MetricCard icon="📤" label="Avg Daily Sent" value={`${signals.avg_daily_sent}`} detail="emails/day" />
                <MetricCard icon="📥" label="Avg Daily Received" value={`${signals.avg_daily_received}`} detail="emails/day" />
                <MetricCard icon="🌙" label="After Hours" value={`${(signals.after_hours_ratio * 100).toFixed(1)}%`} detail="of all emails" />
                <MetricCard icon="📅" label="Weekend" value={`${(signals.weekend_ratio * 100).toFixed(1)}%`} detail="of all emails" />
                <MetricCard icon="⏱️" label="Avg Response" value={`${signals.avg_response_time_min}m`} detail={`P90: ${signals.p90_response_time_min}m`} />
                <MetricCard icon="🏢" label="Internal" value={`${(signals.internal_ratio * 100).toFixed(0)}%`} detail={`${(100 - signals.internal_ratio * 100).toFixed(0)}% external`} />
              </div>

              {/* Daily chart */}
              {signals.daily_breakdown.length > 0 && <DailyChart data={signals.daily_breakdown} />}
            </div>
          )}

          {tab === 'timing' && (
            <div>
              <HourlyHeatmap distribution={signals.hourly_distribution} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 24 }}>
                <ScoreGauge label="Communication Load" score={signals.communication_load_score} subtitle="Volume + broadcast pressure" />
                <ScoreGauge label="Boundary Erosion" score={signals.boundary_erosion_score} subtitle="After-hours + weekend + instant replies" />
                <ScoreGauge label="Burnout Risk" score={signals.burnout_risk_score} subtitle="Composite behavioral signal" />
              </div>

              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, marginTop: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Response Pattern</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Average Response</div>
                    <div style={{ fontSize: 28, fontWeight: 700 }}>{signals.avg_response_time_min}<span style={{ fontSize: 14, color: '#9ca3af' }}>min</span></div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>P90 Response</div>
                    <div style={{ fontSize: 28, fontWeight: 700 }}>{signals.p90_response_time_min}<span style={{ fontSize: 14, color: '#9ca3af' }}>min</span></div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Instant Replies (&lt;5m)</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: signals.instant_reply_ratio > 0.3 ? '#ef4444' : '#22c55e' }}>
                      {(signals.instant_reply_ratio * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {tab === 'burnout' && (
            <div>
              {/* Burnout detail */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Signal Breakdown</h3>
                  {[
                    { label: 'After-Hours Ratio', value: signals.after_hours_ratio, threshold: 0.25, unit: '%', mult: 100 },
                    { label: 'Weekend Ratio', value: signals.weekend_ratio, threshold: 0.15, unit: '%', mult: 100 },
                    { label: 'Instant Reply Rate', value: signals.instant_reply_ratio, threshold: 0.30, unit: '%', mult: 100 },
                    { label: 'Sent/Received Ratio', value: signals.sent_received_ratio, threshold: 1.5, unit: 'x', mult: 1 },
                  ].map(s => {
                    const val = s.value * s.mult;
                    const over = s.value > s.threshold;
                    return (
                      <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                        <span style={{ fontSize: 13, color: '#374151' }}>{s.label}</span>
                        <span style={{ fontSize: 15, fontWeight: 600, color: over ? '#ef4444' : '#22c55e' }}>
                          {val.toFixed(1)}{s.unit}
                        </span>
                      </div>
                    );
                  })}
                </div>

                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Recommendations</h3>
                  {signals.recommendations.map((rec, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                      <span style={{ color: '#f97316', flexShrink: 0 }}>&#9679;</span>
                      <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Composite gauges */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <ScoreGauge label="Communication Load" score={signals.communication_load_score} subtitle="Volume + broadcast" />
                <ScoreGauge label="Boundary Erosion" score={signals.boundary_erosion_score} subtitle="After-hours + weekend" />
                <ScoreGauge label="Burnout Risk" score={signals.burnout_risk_score} subtitle={signals.risk_label} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
