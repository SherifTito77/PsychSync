import { useState, useEffect } from 'react';
import axios from '../api/axios';

interface SlackSignals {
  avg_daily_messages_sent: number;
  avg_daily_messages_received: number;
  total_active_channels: number;
  dm_ratio: number;
  thread_participation_rate: number;
  avg_thread_depth: number;
  reactions_given_per_day: number;
  reactions_received_per_day: number;
  reaction_reciprocity: number;
  after_hours_ratio: number;
  weekend_ratio: number;
  peak_hour: number;
  hourly_distribution: number[];
  channel_hops_per_hour: number;
  context_switching_score: number;
  communication_load_score: number;
  boundary_erosion_score: number;
  isolation_risk_score: number;
  burnout_risk_score: number;
  risk_label: string;
  recommendations: string[];
  daily_breakdown: DailyBreakdown[];
}

interface DailyBreakdown {
  date: string;
  sent: number;
  received: number;
  active_channels: number;
  dm_messages: number;
  public_messages: number;
  threads_participated: number;
  reactions_given: number;
  after_hours_messages: number;
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
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Hourly Message Heatmap</h3>
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
                    ? `rgba(99, 102, 241, ${0.2 + intensity * 0.8})`
                    : `rgba(239, 68, 68, ${0.2 + intensity * 0.8})`,
                  borderRadius: 3,
                }}
                title={`${formatHour(hour)}: ${count} messages`}
              />
              {hour % 3 === 0 && <span style={{ fontSize: 10, color: '#9ca3af' }}>{formatHour(hour)}</span>}
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 11, color: '#9ca3af' }}>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#6366f1', marginRight: 4 }} />Work hours</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#ef4444', marginRight: 4 }} />After hours</span>
      </div>
    </div>
  );
}

export default function SlackMetadataDashboard() {
  const [signals, setSignals] = useState<SlackSignals | null>(null);
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'overview' | 'engagement' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/slack-metadata/signals/default`, { params: { days } })
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
    { id: 'engagement' as const, label: 'Engagement & Isolation', icon: '🕸' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Slack Metadata Analysis</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>
            Behavioral signals from Slack metadata only — message content is never accessed.
          </p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>🔒</span> Metadata only — analytics API, no message history scopes
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #6366f1' : '2px solid transparent', background: 'none', color: tab === t.id ? '#6366f1' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading Slack metadata signals...</div>
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Slack Connector Active</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect your Slack workspace to analyze communication metadata.
            PsychSync uses the <strong>admin.analytics</strong> API — it reads activity counts
            and timestamps. It never accesses message content.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze (Metadata Only)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '💬', label: 'Message counts (sent/received)' },
                { icon: '📢', label: 'Channel participation breadth' },
                { icon: '🔒', label: 'DM vs public ratio' },
                { icon: '🧵', label: 'Thread depth & replies' },
                { icon: '👍', label: 'Reaction frequency' },
                { icon: '🟢', label: 'Presence / status patterns' },
                { icon: '🌙', label: 'After-hours activity' },
                { icon: '🔄', label: 'Context switching rate' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Message text, file contents, DM conversations, or any Slack message body.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div>
              <div style={{ background: '#fff', border: `2px solid ${riskColor(signals.risk_label)}`, borderRadius: 16, padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Slack Burnout Risk</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(signals.risk_label) }}>
                    {signals.burnout_risk_score}
                    <span style={{ fontSize: 16, fontWeight: 500, marginLeft: 8 }}>{signals.risk_label}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20 }}>
                  {[
                    { label: 'Load', score: signals.communication_load_score },
                    { label: 'Boundary', score: signals.boundary_erosion_score },
                    { label: 'Isolation', score: signals.isolation_risk_score },
                    { label: 'Switching', score: signals.context_switching_score },
                  ].map(s => (
                    <div key={s.label} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: '#9ca3af' }}>{s.label}</div>
                      <div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(s.score) }}>{s.score}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
                <MetricCard icon="💬" label="Avg Daily Sent" value={`${signals.avg_daily_messages_sent}`} detail="messages/day" />
                <MetricCard icon="📥" label="Avg Daily Received" value={`${signals.avg_daily_messages_received}`} detail="messages/day" />
                <MetricCard icon="📢" label="Active Channels" value={`${signals.total_active_channels}`} detail="channels with activity" />
                <MetricCard icon="🔒" label="DM Ratio" value={`${(signals.dm_ratio * 100).toFixed(0)}%`} detail="private vs public" />
                <MetricCard icon="🌙" label="After Hours" value={`${(signals.after_hours_ratio * 100).toFixed(1)}%`} detail="of messages" />
                <MetricCard icon="🔄" label="Channel Hops/hr" value={`${signals.channel_hops_per_hour}`} detail="context switches" />
              </div>

              <HourlyHeatmap distribution={signals.hourly_distribution} />
            </div>
          )}

          {tab === 'engagement' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Thread Engagement</h3>
                  <div style={{ display: 'flex', gap: 24 }}>
                    <div>
                      <div style={{ fontSize: 12, color: '#9ca3af' }}>Thread Participation</div>
                      <div style={{ fontSize: 28, fontWeight: 700 }}>{(signals.thread_participation_rate * 100).toFixed(0)}%</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Depth</div>
                      <div style={{ fontSize: 28, fontWeight: 700 }}>{signals.avg_thread_depth}</div>
                    </div>
                  </div>
                </div>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Reactions</h3>
                  <div style={{ display: 'flex', gap: 24 }}>
                    <div>
                      <div style={{ fontSize: 12, color: '#9ca3af' }}>Given/day</div>
                      <div style={{ fontSize: 28, fontWeight: 700 }}>{signals.reactions_given_per_day}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 12, color: '#9ca3af' }}>Received/day</div>
                      <div style={{ fontSize: 28, fontWeight: 700 }}>{signals.reactions_received_per_day}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 12, color: '#9ca3af' }}>Reciprocity</div>
                      <div style={{ fontSize: 28, fontWeight: 700 }}>{signals.reaction_reciprocity}x</div>
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
                <ScoreGauge label="Isolation Risk" score={signals.isolation_risk_score} subtitle="Channel breadth + engagement" />
                <ScoreGauge label="Context Switching" score={signals.context_switching_score} subtitle="Channel hops/hour" />
                <ScoreGauge label="Communication Load" score={signals.communication_load_score} subtitle="Volume + sprawl" />
                <ScoreGauge label="Boundary Erosion" score={signals.boundary_erosion_score} subtitle="After-hours + presence" />
              </div>
            </div>
          )}

          {tab === 'burnout' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Signal Breakdown</h3>
                  {[
                    { label: 'After-Hours Ratio', value: signals.after_hours_ratio, threshold: 0.20, unit: '%', mult: 100 },
                    { label: 'Weekend Ratio', value: signals.weekend_ratio, threshold: 0.10, unit: '%', mult: 100 },
                    { label: 'DM Ratio', value: signals.dm_ratio, threshold: 0.70, unit: '%', mult: 100 },
                    { label: 'Channel Hops/hr', value: signals.channel_hops_per_hour, threshold: 3, unit: '', mult: 1 },
                  ].map(s => {
                    const val = s.value * s.mult;
                    const over = s.value > s.threshold;
                    return (
                      <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                        <span style={{ fontSize: 13, color: '#374151' }}>{s.label}</span>
                        <span style={{ fontSize: 15, fontWeight: 600, color: over ? '#ef4444' : '#22c55e' }}>{val.toFixed(1)}{s.unit}</span>
                      </div>
                    );
                  })}
                </div>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Recommendations</h3>
                  {signals.recommendations.map((rec, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                      <span style={{ color: '#6366f1', flexShrink: 0 }}>&#9679;</span>
                      <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
                <ScoreGauge label="Communication Load" score={signals.communication_load_score} subtitle="Volume + sprawl" />
                <ScoreGauge label="Boundary Erosion" score={signals.boundary_erosion_score} subtitle="After-hours + presence" />
                <ScoreGauge label="Isolation Risk" score={signals.isolation_risk_score} subtitle="Breadth + engagement" />
                <ScoreGauge label="Burnout Risk" score={signals.burnout_risk_score} subtitle={signals.risk_label} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
