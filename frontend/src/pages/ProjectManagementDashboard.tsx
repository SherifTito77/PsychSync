import { useState, useEffect } from 'react';
import axios from '../api/axios';

function scoreColor(s: number) { return s >= 70 ? '#ef4444' : s >= 45 ? '#f97316' : s >= 25 ? '#eab308' : '#22c55e'; }
function riskColor(l: string) { return l === 'Critical' ? '#ef4444' : l === 'Elevated' ? '#f97316' : l === 'Monitor' ? '#eab308' : l === 'Healthy' ? '#22c55e' : '#6b7280'; }
function invertedColor(s: number) { return s >= 70 ? '#22c55e' : s >= 45 ? '#eab308' : s >= 25 ? '#f97316' : '#ef4444'; }

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

function ScoreGauge({ label, score, subtitle, inverted }: { label: string; score: number; subtitle: string; inverted?: boolean }) {
  const color = inverted ? invertedColor(score) : scoreColor(score);
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#6b7280', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 42, fontWeight: 700, color, lineHeight: 1 }}>{score}</div>
      <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>/100</div>
      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 8 }}>{subtitle}</div>
    </div>
  );
}

function ProgressBar({ value, max, color, label }: { value: number; max: number; color: string; label: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div style={{ height: 8, background: '#f3f4f6', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.3s' }} />
      </div>
    </div>
  );
}

export default function ProjectManagementDashboard() {
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'workload' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/project-management-metadata/signals/default`, { params: { days } })
      .then(res => {
        if (!cancelled) {
          const d = res.data?.data;
          setData(d?.risk_label && d.risk_label !== 'No Data' ? d : null);
        }
      })
      .catch(() => { if (!cancelled) setData(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [days]);

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '\uD83D\uDCCA' },
    { id: 'workload' as const, label: 'Team Workload', icon: '\uD83D\uDCCB' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '\uD83D\uDD25' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Project Management Metadata</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>Workload, delivery health, and deadline pressure — no task descriptions, comments, or content.</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={7}>7 days</option><option value={14}>14 days</option><option value={30}>30 days</option><option value={90}>90 days</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>{'\uD83D\uDD12'}</span> Metadata only — no descriptions, comments, or attachments
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #14b8a6' : '2px solid transparent', background: 'none', color: tab === t.id ? '#14b8a6' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading...</div>
      ) : !data ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>{'\uD83D\uDCCB'}</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Project Management Data Connected</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect your Jira, Asana, or Linear workspace to analyze project management patterns.
            Task metadata reveals <strong>workload imbalance and deadline pressure</strong> — key early warning signals for team burnout.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '\uD83D\uDCE6', label: 'Task assignment & completion counts' },
                { icon: '\u23F1\uFE0F', label: 'Cycle time & lead time' },
                { icon: '\uD83D\uDEA7', label: 'Blocked & overdue task ratios' },
                { icon: '\uD83C\uDFAF', label: 'Active project count (focus)' },
                { icon: '\uD83C\uDFC3', label: 'Sprint velocity & commitment' },
                { icon: '\uD83E\uDD1D', label: 'Collaboration patterns' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Task descriptions, comment content, attachments, linked documents, or any free-text fields.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div>
              {/* Risk banner */}
              <div style={{ background: '#fff', border: `2px solid ${riskColor(data.risk_label)}`, borderRadius: 16, padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Project Burnout Risk</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(data.risk_label) }}>
                    {data.burnout_composite}
                    <span style={{ fontSize: 16, fontWeight: 500, marginLeft: 8 }}>{data.risk_label}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20 }}>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Workload</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(data.workload_score) }}>{data.workload_score}</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Delivery</div><div style={{ fontSize: 20, fontWeight: 600, color: invertedColor(data.delivery_health) }}>{data.delivery_health}</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Focus</div><div style={{ fontSize: 20, fontWeight: 600, color: invertedColor(data.focus_score) }}>{data.focus_score}</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Deadline</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(data.deadline_pressure) }}>{data.deadline_pressure}</div></div>
                </div>
              </div>

              {/* Score cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
                <ScoreGauge label="Workload Score" score={data.workload_score} subtitle="Backlog growth vs completion" />
                <ScoreGauge label="Delivery Health" score={data.delivery_health} subtitle="Completion rate + cycle time" inverted />
                <ScoreGauge label="Focus Score" score={data.focus_score} subtitle="Project sprawl (1=focused)" inverted />
                <ScoreGauge label="Deadline Pressure" score={data.deadline_pressure} subtitle="Overdue + blocked ratio" />
              </div>

              {/* Summary metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
                <MetricCard icon={'\uD83D\uDCE5'} label="Assigned" value={`${data.signals?.workload?.assigned ?? 0}`} detail="total tasks" />
                <MetricCard icon={'\u2705'} label="Completed" value={`${data.signals?.workload?.completed ?? 0}`} detail={`rate: ${((data.signals?.completion_rate?.rate ?? 0) * 100).toFixed(0)}%`} />
                <MetricCard icon={'\u23F0'} label="Overdue" value={`${data.signals?.workload?.overdue ?? 0}`} alert={(data.signals?.workload?.overdue ?? 0) > 0} />
                <MetricCard icon={'\uD83D\uDEA7'} label="Blocked" value={`${data.signals?.workload?.blocked ?? 0}`} alert={(data.signals?.workload?.blocked ?? 0) > 0} />
                <MetricCard icon={'\u23F1\uFE0F'} label="Avg Cycle Time" value={`${data.signals?.cycle_time?.avg_cycle_hours ?? 0}h`} detail="start to done" />
                <MetricCard icon={'\uD83C\uDFAF'} label="Active Projects" value={`${data.signals?.focus?.avg_active_projects ?? 0}`} detail="avg per person" alert={(data.signals?.focus?.avg_active_projects ?? 0) > 4} />
              </div>
            </div>
          )}

          {tab === 'workload' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              {/* Task breakdown */}
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Task Breakdown</h3>
                {(() => {
                  const w = data.signals?.workload ?? {};
                  const total = w.assigned || 1;
                  return (
                    <>
                      <ProgressBar value={w.completed ?? 0} max={total} color="#22c55e" label="Completed" />
                      <ProgressBar value={w.in_progress ?? 0} max={total} color="#3b82f6" label="In Progress" />
                      <ProgressBar value={w.overdue ?? 0} max={total} color="#ef4444" label="Overdue" />
                      <ProgressBar value={w.blocked ?? 0} max={total} color="#f97316" label="Blocked" />
                    </>
                  );
                })()}
              </div>

              {/* Cycle time */}
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Cycle & Lead Time</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Cycle Time</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: (data.signals?.cycle_time?.avg_cycle_hours ?? 0) > 72 ? '#f97316' : '#14b8a6' }}>
                      {(data.signals?.cycle_time?.avg_cycle_hours ?? 0) < 1 ? '<1h' : `${(data.signals?.cycle_time?.avg_cycle_hours ?? 0).toFixed(0)}h`}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>start to done</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Lead Time</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: (data.signals?.cycle_time?.avg_lead_hours ?? 0) > 120 ? '#ef4444' : '#22c55e' }}>
                      {(data.signals?.cycle_time?.avg_lead_hours ?? 0) < 1 ? '<1h' : `${(data.signals?.cycle_time?.avg_lead_hours ?? 0).toFixed(0)}h`}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>created to done</div>
                  </div>
                </div>

                {/* Sprint health */}
                {data.signals?.sprint_health?.avg_velocity != null && (
                  <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #f3f4f6' }}>
                    <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Sprint Health</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                      <div>
                        <div style={{ fontSize: 12, color: '#9ca3af' }}>Velocity</div>
                        <div style={{ fontSize: 24, fontWeight: 700 }}>{data.signals.sprint_health.avg_velocity}</div>
                        <div style={{ fontSize: 11, color: '#9ca3af' }}>avg points</div>
                      </div>
                      {data.signals.sprint_health.avg_commitment_ratio != null && (
                        <div>
                          <div style={{ fontSize: 12, color: '#9ca3af' }}>Commitment Ratio</div>
                          <div style={{ fontSize: 24, fontWeight: 700, color: data.signals.sprint_health.avg_commitment_ratio < 0.7 ? '#ef4444' : '#22c55e' }}>
                            {(data.signals.sprint_health.avg_commitment_ratio * 100).toFixed(0)}%
                          </div>
                          <div style={{ fontSize: 11, color: '#9ca3af' }}>completed / committed</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Priority distribution */}
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Priority Distribution</h3>
                {(() => {
                  const pd = data.signals?.completion_rate?.priority_distribution ?? {};
                  const total = Object.values(pd).reduce((a: number, b: any) => a + (b as number), 0) as number || 1;
                  const priorities = [
                    { key: 'critical', color: '#ef4444', label: 'Critical' },
                    { key: 'high', color: '#f97316', label: 'High' },
                    { key: 'medium', color: '#eab308', label: 'Medium' },
                    { key: 'low', color: '#22c55e', label: 'Low' },
                  ];
                  return priorities.map(p => (
                    <ProgressBar key={p.key} value={pd[p.key] ?? 0} max={total} color={p.color} label={`${p.label} (${pd[p.key] ?? 0})`} />
                  ));
                })()}
              </div>

              {/* Collaboration */}
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Collaboration Balance</h3>
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 42, fontWeight: 700, color: Math.abs(data.collaboration_balance - 50) > 20 ? '#f97316' : '#14b8a6' }}>
                    {data.collaboration_balance}
                  </div>
                  <div style={{ fontSize: 12, color: '#9ca3af' }}>50 = balanced give/take</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
                  <div style={{ padding: 12, background: '#f0fdf4', borderRadius: 8 }}>
                    <div style={{ color: '#16a34a', fontWeight: 600 }}>Given</div>
                    <div style={{ color: '#374151' }}>Comments: {data.signals?.collaboration?.comments_given ?? 0}</div>
                    <div style={{ color: '#374151' }}>Delegated: {data.signals?.collaboration?.tasks_assigned_to_others ?? 0}</div>
                  </div>
                  <div style={{ padding: 12, background: '#fef2f2', borderRadius: 8 }}>
                    <div style={{ color: '#dc2626', fontWeight: 600 }}>Received</div>
                    <div style={{ color: '#374151' }}>Comments: {data.signals?.collaboration?.comments_received ?? 0}</div>
                    <div style={{ color: '#374151' }}>Assigned: {data.signals?.collaboration?.tasks_assigned_by_others ?? 0}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {tab === 'burnout' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                {/* Recommendations */}
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Recommendations</h3>
                  {(data.recommendations ?? []).map((rec: string, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: 8, padding: '10px 0', borderBottom: '1px solid #f3f4f6' }}>
                      <span style={{ color: '#14b8a6', flexShrink: 0 }}>{'\u25CF'}</span>
                      <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{rec}</span>
                    </div>
                  ))}
                </div>

                {/* Burnout signal gauges */}
                <div style={{ display: 'grid', gridTemplateRows: '1fr 1fr', gap: 12 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <ScoreGauge label="Overdue Ratio" score={Math.round((data.burnout_signals?.overdue_ratio ?? 0) * 100)} subtitle="% tasks past deadline" />
                    <ScoreGauge label="Multitasking Index" score={Math.round(data.burnout_signals?.multitasking_index ?? 0)} subtitle="Project sprawl pressure" />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <ScoreGauge label="Velocity Decline" score={Math.round((data.burnout_signals?.velocity_decline ?? 0) * 100)} subtitle="Sprint output trending down" />
                    <ScoreGauge label="Blocked Ratio" score={Math.round((data.burnout_signals?.blocked_ratio ?? 0) * 100)} subtitle="% tasks blocked" />
                  </div>
                </div>
              </div>

              {/* Composite breakdown */}
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Burnout Composite Breakdown</h3>
                <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 16 }}>
                  Composite score is weighted: workload (30%) + deadline pressure (25%) + multitasking (20%) + delivery gap (15%) + velocity decline (10%)
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
                  {[
                    { label: 'Workload', score: data.workload_score, weight: '30%' },
                    { label: 'Deadline', score: data.deadline_pressure, weight: '25%' },
                    { label: 'Multitasking', score: Math.round(data.burnout_signals?.multitasking_index ?? 0), weight: '20%' },
                    { label: 'Delivery Gap', score: Math.round(100 - data.delivery_health), weight: '15%' },
                    { label: 'Vel. Decline', score: Math.round((data.burnout_signals?.velocity_decline ?? 0) * 100), weight: '10%' },
                  ].map(item => (
                    <div key={item.label} style={{ textAlign: 'center', padding: 12, background: '#f9fafb', borderRadius: 8 }}>
                      <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4 }}>{item.label}</div>
                      <div style={{ fontSize: 24, fontWeight: 700, color: scoreColor(item.score) }}>{item.score}</div>
                      <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 2 }}>weight: {item.weight}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
