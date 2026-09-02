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

function SignalBar({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
        <span style={{ color: '#374151' }}>{label}</span>
        <span style={{ fontWeight: 600, color: scoreColor(value) }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ background: '#f3f4f6', borderRadius: 4, height: 8, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 4, background: scoreColor(value), transition: 'width 0.5s' }} />
      </div>
    </div>
  );
}

export default function VideoConferenceMetadataDashboard() {
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'engagement' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/video-conference-metadata/signals/default`, { params: { days } })
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
    { id: 'engagement' as const, label: 'Engagement', icon: '📹' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Video Conferencing Analysis</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>Camera engagement, meeting fatigue, and call patterns — no recordings or transcripts.</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={7}>7 days</option><option value={14}>14 days</option><option value={30}>30 days</option><option value={90}>90 days</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>🔒</span> Metadata only — no audio, video, transcripts, or screen content
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #8b5cf6' : '2px solid transparent', background: 'none', color: tab === t.id ? '#8b5cf6' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading...</div>
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📹</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Video Conferencing Data Connected</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect Zoom, Google Meet, or Teams to analyze video call patterns.
            Meeting metadata reveals <strong>engagement levels and meeting fatigue</strong> — back-to-back video calls are the #1 predictor of burnout in hybrid teams.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '📹', label: 'Camera on/off rates' },
                { icon: '⏱', label: 'Join latency (punctuality)' },
                { icon: '🔄', label: 'Back-to-back call density' },
                { icon: '📊', label: 'Meeting duration vs scheduled' },
                { icon: '🌙', label: 'After-hours video calls' },
                { icon: '👥', label: 'Meeting load per person' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Audio, video streams, transcripts, screen shares, chat messages, or recording content.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div>
              <div style={{ background: '#fff', border: `2px solid ${riskColor(signals.risk_label)}`, borderRadius: 16, padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Video Call Burnout Risk</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(signals.risk_label) }}>{signals.risk_label}</div>
                </div>
                <div style={{ display: 'flex', gap: 24 }}>
                  <ScoreGauge label="Fatigue" score={signals.meeting_fatigue_score} subtitle="Meeting fatigue" />
                  <ScoreGauge label="Overload" score={signals.overload_score} subtitle="Meeting overload" />
                  <ScoreGauge label="Engagement" score={signals.engagement_score} subtitle="Engagement score" />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
                <MetricCard icon="📹" label="Camera On Rate" value={`${signals.camera_on_rate}%`} detail="Meetings with >50% cameras on" />
                <MetricCard icon="📅" label="Daily Meetings" value={signals.avg_daily_meetings.toFixed(1)} detail={`Peak: ${signals.peak_daily_meetings} in one day`} alert={signals.avg_daily_meetings > 6} />
                <MetricCard icon="⏱" label="Daily Video Time" value={`${signals.avg_daily_video_minutes.toFixed(0)}m`} detail="Average minutes in video calls" alert={signals.avg_daily_video_minutes > 240} />
                <MetricCard icon="🔄" label="Back-to-Back" value={`${signals.back_to_back_rate.toFixed(0)}%`} detail="Calls with <5min gap" alert={signals.back_to_back_rate > 50} />
              </div>
              {signals.recommendations?.length > 0 && (
                <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 12, padding: 16 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>Recommendations</div>
                  {signals.recommendations.map((r: string, i: number) => (
                    <div key={i} style={{ fontSize: 13, color: '#92400e', marginBottom: 6, paddingLeft: 16, position: 'relative' }}>
                      <span style={{ position: 'absolute', left: 0 }}>•</span> {r}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {tab === 'engagement' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Engagement Signals</h3>
                  <SignalBar label="Camera On Rate" value={signals.camera_on_rate} />
                  <SignalBar label="Join Punctuality" value={signals.join_punctuality_score} />
                  <SignalBar label="Avg Participants" value={signals.meeting_participation_rate} max={20} />
                  <div style={{ marginTop: 16, fontSize: 13, color: '#6b7280' }}>
                    <strong>Recurring ratio:</strong> {(signals.recurring_meeting_ratio * 100).toFixed(0)}% of meetings are recurring
                  </div>
                </div>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Meeting Overrun</h3>
                  <div style={{ textAlign: 'center', marginBottom: 16 }}>
                    <div style={{ fontSize: 48, fontWeight: 700, color: scoreColor(signals.meeting_overrun_rate) }}>
                      {signals.meeting_overrun_rate.toFixed(0)}%
                    </div>
                    <div style={{ fontSize: 13, color: '#6b7280' }}>of meetings exceed scheduled duration</div>
                  </div>
                  <div style={{ fontSize: 13, color: '#6b7280', marginTop: 12 }}>
                    <strong>Weekend meetings:</strong> {signals.weekend_meeting_count}
                  </div>
                  <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
                    <strong>After-hours rate:</strong> {signals.after_hours_meeting_rate.toFixed(1)}%
                  </div>
                </div>
              </div>
              {signals.daily_breakdown?.length > 0 && (
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Daily Breakdown</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                          <th style={{ textAlign: 'left', padding: 8 }}>Date</th>
                          <th style={{ textAlign: 'right', padding: 8 }}>Meetings</th>
                          <th style={{ textAlign: 'right', padding: 8 }}>Minutes</th>
                          <th style={{ textAlign: 'right', padding: 8 }}>Back-to-Back</th>
                          <th style={{ textAlign: 'right', padding: 8 }}>Camera %</th>
                          <th style={{ textAlign: 'right', padding: 8 }}>Longest Gap</th>
                        </tr>
                      </thead>
                      <tbody>
                        {signals.daily_breakdown.slice(-14).map((d: any) => (
                          <tr key={d.date} style={{ borderBottom: '1px solid #f3f4f6' }}>
                            <td style={{ padding: 8 }}>{d.date}</td>
                            <td style={{ textAlign: 'right', padding: 8, fontWeight: 600, color: d.meetings > 6 ? '#ef4444' : undefined }}>{d.meetings}</td>
                            <td style={{ textAlign: 'right', padding: 8 }}>{d.minutes}m</td>
                            <td style={{ textAlign: 'right', padding: 8, color: d.back_to_back > 2 ? '#ef4444' : undefined }}>{d.back_to_back}</td>
                            <td style={{ textAlign: 'right', padding: 8 }}>{(d.camera_on_rate * 100).toFixed(0)}%</td>
                            <td style={{ textAlign: 'right', padding: 8 }}>{d.longest_gap_min}m</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'burnout' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
                <ScoreGauge label="Meeting Fatigue" score={signals.meeting_fatigue_score} subtitle="Back-to-back + duration + recovery gaps" />
                <ScoreGauge label="Overload" score={signals.overload_score} subtitle="Too many meetings, too much time" />
                <ScoreGauge label="Burnout Risk" score={signals.burnout_risk} subtitle="Combined video call burnout" />
              </div>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, marginBottom: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Burnout Signal Breakdown</h3>
                <SignalBar label="Back-to-Back Rate" value={signals.back_to_back_rate} />
                <SignalBar label="After-Hours Meetings" value={signals.after_hours_meeting_rate} />
                <SignalBar label="Meeting Fatigue" value={signals.meeting_fatigue_score} />
                <SignalBar label="Overload" value={signals.overload_score} />
                <div style={{ marginTop: 16, padding: 12, background: '#f9fafb', borderRadius: 8, fontSize: 13, color: '#6b7280' }}>
                  <strong>Recovery gap:</strong> Average longest break between meetings is <strong>{signals.avg_longest_gap_minutes.toFixed(0)} minutes</strong>. Less than 30 minutes indicates insufficient recovery time.
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
