import { useState, useEffect } from 'react';
import axios from '../api/axios';

interface TeamsSignals {
  avg_daily_chats_sent: number;
  avg_daily_calls: number;
  avg_daily_meetings: number;
  total_active_channels: number;
  private_chat_ratio: number;
  avg_call_duration_min: number;
  avg_meeting_duration_min: number;
  calls_vs_chats_ratio: number;
  meeting_hours_per_week: number;
  back_to_back_meetings: number;
  meeting_fatigue_score: number;
  after_hours_ratio: number;
  weekend_ratio: number;
  peak_hour: number;
  hourly_distribution: number[];
  avg_daily_available_hours: number;
  dnd_usage_ratio: number;
  communication_load_score: number;
  boundary_erosion_score: number;
  burnout_risk_score: number;
  risk_label: string;
  recommendations: string[];
  daily_breakdown: DailyBreakdown[];
}

interface DailyBreakdown {
  date: string;
  chats: number;
  channel_messages: number;
  calls: number;
  meetings: number;
  call_meeting_minutes: number;
  after_hours_activity: number;
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

function DailyChart({ data }: { data: DailyBreakdown[] }) {
  const maxVol = Math.max(...data.map(d => d.chats + d.channel_messages + d.calls + d.meetings), 1);
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Daily Activity</h3>
      <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 140 }}>
        {data.map(d => {
          const total = d.chats + d.channel_messages + d.calls + d.meetings;
          const pct = (total / maxVol) * 100;
          const callPct = ((d.calls + d.meetings) / Math.max(total, 1)) * 100;
          return (
            <div key={d.date} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <div style={{ fontSize: 10, color: '#6b7280' }}>{total}</div>
              <div style={{ width: '100%', position: 'relative', height: `${Math.max(pct, 4)}%`, borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ position: 'absolute', bottom: 0, width: '100%', height: '100%', background: '#8b5cf6', borderRadius: 4 }} />
                {callPct > 0 && (
                  <div style={{ position: 'absolute', top: 0, width: '100%', height: `${callPct}%`, background: '#ec4899', borderRadius: '4px 4px 0 0' }} />
                )}
              </div>
              <span style={{ fontSize: 9, color: '#9ca3af', writingMode: 'vertical-rl', transform: 'rotate(180deg)', maxHeight: 50, overflow: 'hidden' }}>{d.date.slice(5)}</span>
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 11, color: '#9ca3af' }}>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#8b5cf6', marginRight: 4 }} />Chats</span>
        <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 2, background: '#ec4899', marginRight: 4 }} />Calls & Meetings</span>
      </div>
    </div>
  );
}

export default function TeamsMetadataDashboard() {
  const [signals, setSignals] = useState<TeamsSignals | null>(null);
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'overview' | 'meetings' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/teams-metadata/signals/default`, { params: { days } })
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
    { id: 'meetings' as const, label: 'Meeting Fatigue', icon: '📞' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Teams Metadata Analysis</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>
            Behavioral signals from Microsoft Teams metadata only — message content is never accessed.
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
        <span>🔒</span> Metadata only — Reports + Presence APIs, no message content permissions
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #8b5cf6' : '2px solid transparent', background: 'none', color: tab === t.id ? '#8b5cf6' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading Teams metadata signals...</div>
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🟣</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Teams Connector Active</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect Microsoft Teams to analyze communication metadata.
            PsychSync uses <strong>Reports + Presence APIs</strong> — it reads activity counts
            and call durations. It never accesses message content or call transcripts.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze (Metadata Only)</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '💬', label: 'Chat message counts' },
                { icon: '📞', label: 'Call frequency & duration' },
                { icon: '🎥', label: 'Meeting joins & duration' },
                { icon: '📢', label: 'Channel participation' },
                { icon: '🔒', label: '1:1 vs group ratio' },
                { icon: '🟢', label: 'Presence / status timeline' },
                { icon: '🌙', label: 'After-hours activity' },
                { icon: '🔕', label: 'Do Not Disturb usage' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Message text, call transcripts, shared files, or any content within Teams.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div>
              <div style={{ background: '#fff', border: `2px solid ${riskColor(signals.risk_label)}`, borderRadius: 16, padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Teams Burnout Risk</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(signals.risk_label) }}>
                    {signals.burnout_risk_score}
                    <span style={{ fontSize: 16, fontWeight: 500, marginLeft: 8 }}>{signals.risk_label}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20 }}>
                  {[
                    { label: 'Load', score: signals.communication_load_score },
                    { label: 'Boundary', score: signals.boundary_erosion_score },
                    { label: 'Meeting Fatigue', score: signals.meeting_fatigue_score },
                  ].map(s => (
                    <div key={s.label} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: '#9ca3af' }}>{s.label}</div>
                      <div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(s.score) }}>{s.score}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
                <MetricCard icon="💬" label="Daily Chats" value={`${signals.avg_daily_chats_sent}`} detail="messages/day" />
                <MetricCard icon="📞" label="Daily Calls" value={`${signals.avg_daily_calls}`} detail="calls/day" />
                <MetricCard icon="🎥" label="Daily Meetings" value={`${signals.avg_daily_meetings}`} detail="meetings/day" />
                <MetricCard icon="⏱" label="Avg Call Duration" value={`${signals.avg_call_duration_min}m`} detail="per call" />
                <MetricCard icon="🌙" label="After Hours" value={`${(signals.after_hours_ratio * 100).toFixed(1)}%`} detail="of activity" />
                <MetricCard icon="🔕" label="DND Usage" value={`${(signals.dnd_usage_ratio * 100).toFixed(0)}%`} detail={signals.dnd_usage_ratio < 0.05 ? 'Consider using more' : 'Good boundary setting'} />
              </div>

              {signals.daily_breakdown.length > 0 && <DailyChart data={signals.daily_breakdown} />}
            </div>
          )}

          {tab === 'meetings' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 24 }}>
                <ScoreGauge label="Meeting Fatigue" score={signals.meeting_fatigue_score} subtitle="Hours + density + back-to-back" />
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, textAlign: 'center' }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#6b7280', marginBottom: 8 }}>Meeting Hours/Week</div>
                  <div style={{ fontSize: 42, fontWeight: 700, color: signals.meeting_hours_per_week > 15 ? '#ef4444' : signals.meeting_hours_per_week > 10 ? '#f97316' : '#22c55e', lineHeight: 1 }}>
                    {signals.meeting_hours_per_week}
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>hours</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 8 }}>Healthy: &lt;10h | Elevated: 10-15h</div>
                </div>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, textAlign: 'center' }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#6b7280', marginBottom: 8 }}>Back-to-Back</div>
                  <div style={{ fontSize: 42, fontWeight: 700, color: signals.back_to_back_meetings > 5 ? '#ef4444' : '#22c55e', lineHeight: 1 }}>
                    {signals.back_to_back_meetings}
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>instances</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 8 }}>Meetings with &lt;5min gap</div>
                </div>
              </div>

              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Communication Style</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Sync vs Async</div>
                    <div style={{ fontSize: 24, fontWeight: 700 }}>{(signals.calls_vs_chats_ratio * 100).toFixed(0)}%</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>calls+meetings vs chats</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Private Chat Ratio</div>
                    <div style={{ fontSize: 24, fontWeight: 700 }}>{(signals.private_chat_ratio * 100).toFixed(0)}%</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>1:1 vs group</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Meeting</div>
                    <div style={{ fontSize: 24, fontWeight: 700 }}>{signals.avg_meeting_duration_min}m</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>duration</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Available Hours</div>
                    <div style={{ fontSize: 24, fontWeight: 700 }}>{signals.avg_daily_available_hours}h</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>avg per day</div>
                  </div>
                </div>
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
                    { label: 'Meeting Hours/Week', value: signals.meeting_hours_per_week, threshold: 15, unit: 'h', mult: 1 },
                    { label: 'DND Usage', value: signals.dnd_usage_ratio, threshold: -1, unit: '%', mult: 100 },
                  ].map(s => {
                    const val = s.value * s.mult;
                    const over = s.threshold >= 0 ? s.value > s.threshold : false;
                    const isProtective = s.label === 'DND Usage';
                    return (
                      <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                        <span style={{ fontSize: 13, color: '#374151' }}>{s.label} {isProtective && <span style={{ fontSize: 10, color: '#22c55e' }}>(protective)</span>}</span>
                        <span style={{ fontSize: 15, fontWeight: 600, color: isProtective ? '#22c55e' : over ? '#ef4444' : '#22c55e' }}>{val.toFixed(1)}{s.unit}</span>
                      </div>
                    );
                  })}
                </div>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Recommendations</h3>
                  {signals.recommendations.map((rec, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                      <span style={{ color: '#8b5cf6', flexShrink: 0 }}>&#9679;</span>
                      <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <ScoreGauge label="Communication Load" score={signals.communication_load_score} subtitle="Chat + call volume" />
                <ScoreGauge label="Meeting Fatigue" score={signals.meeting_fatigue_score} subtitle="Hours + back-to-back" />
                <ScoreGauge label="Burnout Risk" score={signals.burnout_risk_score} subtitle={signals.risk_label} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
