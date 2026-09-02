import { useState, useEffect } from 'react';
import axios from '../api/axios';

function scoreColor(s: number) { return s >= 70 ? '#ef4444' : s >= 45 ? '#f97316' : s >= 25 ? '#eab308' : '#22c55e'; }
function engColor(s: number) { return s >= 70 ? '#22c55e' : s >= 45 ? '#eab308' : s >= 25 ? '#f97316' : '#ef4444'; }
function riskColor(l: string) { return l === 'Critical' ? '#ef4444' : l === 'Elevated' ? '#f97316' : l === 'Monitor' ? '#eab308' : l === 'Healthy' ? '#22c55e' : '#6b7280'; }

function ScoreGauge({ label, score, subtitle, invert }: { label: string; score: number; subtitle: string; invert?: boolean }) {
  const color = invert ? engColor(score) : scoreColor(score);
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, textAlign: 'center' }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#6b7280', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 42, fontWeight: 700, color, lineHeight: 1 }}>{score}</div>
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

function SignalBar({ label, value, max = 100, invert }: { label: string; value: number; max?: number; invert?: boolean }) {
  const pct = Math.min(100, (value / max) * 100);
  const color = invert ? engColor(value) : scoreColor(value);
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
        <span style={{ color: '#374151' }}>{label}</span>
        <span style={{ fontWeight: 600, color }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ background: '#f3f4f6', borderRadius: 4, height: 8, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 4, background: color, transition: 'width 0.5s' }} />
      </div>
    </div>
  );
}

function TrendBadge({ trend }: { trend: string }) {
  const config: Record<string, { bg: string; color: string; arrow: string }> = {
    increasing: { bg: '#dcfce7', color: '#16a34a', arrow: '↑' },
    stable: { bg: '#f3f4f6', color: '#6b7280', arrow: '→' },
    decreasing: { bg: '#fee2e2', color: '#dc2626', arrow: '↓' },
  };
  const c = config[trend] || config.stable;
  return (
    <span style={{ background: c.bg, color: c.color, padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
      {c.arrow} {trend}
    </span>
  );
}

export default function KnowledgeBaseAnalyticsDashboard() {
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'contributors' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/knowledge-base-metadata/signals/default`, { params: { days } })
      .then(res => {
        if (!cancelled) {
          const data = res.data?.signals;
          setSignals(data?.risk_label ? data : null);
        }
      })
      .catch(() => { if (!cancelled) setSignals(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [days]);

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '📊' },
    { id: 'contributors' as const, label: 'Contributors', icon: '👥' },
    { id: 'burnout' as const, label: 'Health Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Knowledge Base Analytics</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>Documentation activity patterns — who creates, edits, and maintains knowledge. No page content analyzed.</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={14}>14 days</option><option value={30}>30 days</option><option value={60}>60 days</option><option value={90}>90 days</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>🔒</span> Metadata only — no page titles, text content, or attachments
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '10px 20px', border: 'none', borderBottom: tab === t.id ? '2px solid #6366f1' : '2px solid transparent', background: 'none', color: tab === t.id ? '#6366f1' : '#6b7280', fontWeight: tab === t.id ? 600 : 400, cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>Loading...</div>
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📚</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Knowledge Base Connected</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect Confluence, Notion, or SharePoint to analyze documentation patterns.
            Knowledge base activity is a leading indicator of <strong>team health and onboarding effectiveness</strong>.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '📝', label: 'Page creation frequency' },
                { icon: '✏️', label: 'Edit and update patterns' },
                { icon: '👁', label: 'View/consumption ratios' },
                { icon: '💬', label: 'Comment & feedback activity' },
                { icon: '📊', label: 'Contributor concentration' },
                { icon: '🔗', label: 'Cross-team knowledge sharing' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Page titles, text content, attachments, embedded files, or document templates.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div>
              <div style={{ background: '#fff', border: `2px solid ${riskColor(signals.risk_label)}`, borderRadius: 16, padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Documentation Health</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(signals.risk_label) }}>{signals.risk_label}</div>
                  <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                    <span style={{ fontSize: 13, color: '#6b7280' }}>Creation: <TrendBadge trend={signals.creation_trend} /></span>
                    <span style={{ fontSize: 13, color: '#6b7280' }}>Activity: <TrendBadge trend={signals.contribution_trend} /></span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 24 }}>
                  <ScoreGauge label="Knowledge Sharing" score={signals.knowledge_sharing_score} subtitle="Sharing culture" invert />
                  <ScoreGauge label="Engagement" score={signals.engagement_score} subtitle="Doc engagement" invert />
                  <ScoreGauge label="Burnout Risk" score={signals.burnout_risk} subtitle="Disengagement signal" />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
                <MetricCard icon="📝" label="Pages Created" value={String(signals.total_pages_created)} detail={`${signals.doc_creation_rate.toFixed(1)} per person/week`} />
                <MetricCard icon="✏️" label="Total Edits" value={String(signals.total_edits)} detail={`${signals.edit_frequency.toFixed(1)} per person/week`} />
                <MetricCard icon="👁" label="Total Views" value={String(signals.total_views)} detail={`${signals.consumption_ratio.toFixed(1)}:1 view/edit ratio`} alert={signals.consumption_ratio > 10} />
                <MetricCard icon="👥" label="Contributors" value={String(signals.unique_contributors)} detail={`Concentration: ${(signals.contributor_concentration * 100).toFixed(0)}%`} alert={signals.contributor_concentration > 0.7} />
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

          {tab === 'contributors' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Collaboration Signals</h3>
                  <SignalBar label="Knowledge Sharing" value={signals.knowledge_sharing_score} invert />
                  <SignalBar label="Cross-Space Contribution" value={signals.cross_space_ratio * 100} invert />
                  <SignalBar label="Comment-to-Edit Ratio" value={Math.min(100, signals.comment_to_edit_ratio * 100)} invert />
                  <SignalBar label="Contributor Concentration" value={signals.contributor_concentration * 100} />
                </div>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Content Health</h3>
                  <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: 32, fontWeight: 700, color: engColor((1 - signals.stale_content_ratio) * 100) }}>
                        {((1 - signals.stale_content_ratio) * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: 12, color: '#6b7280' }}>Active pages</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 32, fontWeight: 700, color: scoreColor(signals.stale_content_ratio * 100) }}>
                        {(signals.stale_content_ratio * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: 12, color: '#6b7280' }}>Stale pages</div>
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: '#6b7280' }}>
                    <strong>Avg edits per page:</strong> {signals.avg_edits_per_page.toFixed(1)}
                  </div>
                </div>
              </div>

              {signals.top_contributors?.length > 0 && (
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Top Contributors</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                        <th style={{ textAlign: 'left', padding: 8 }}>User</th>
                        <th style={{ textAlign: 'right', padding: 8 }}>Created</th>
                        <th style={{ textAlign: 'right', padding: 8 }}>Edited</th>
                        <th style={{ textAlign: 'right', padding: 8 }}>Comments</th>
                        <th style={{ textAlign: 'right', padding: 8 }}>Words Added</th>
                        <th style={{ textAlign: 'right', padding: 8 }}>Spaces</th>
                      </tr>
                    </thead>
                    <tbody>
                      {signals.top_contributors.map((c: any) => (
                        <tr key={c.user_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                          <td style={{ padding: 8, fontWeight: 500 }}>{c.user_id}</td>
                          <td style={{ textAlign: 'right', padding: 8 }}>{c.created}</td>
                          <td style={{ textAlign: 'right', padding: 8 }}>{c.edited}</td>
                          <td style={{ textAlign: 'right', padding: 8 }}>{c.comments}</td>
                          <td style={{ textAlign: 'right', padding: 8 }}>{c.words_added.toLocaleString()}</td>
                          <td style={{ textAlign: 'right', padding: 8 }}>{c.spaces}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {tab === 'burnout' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
                <ScoreGauge label="Burnout Risk" score={signals.burnout_risk} subtitle="Declining contribution signal" />
                <ScoreGauge label="Knowledge Sharing" score={signals.knowledge_sharing_score} subtitle="Sharing culture health" invert />
                <ScoreGauge label="Engagement" score={signals.engagement_score} subtitle="Documentation engagement" invert />
              </div>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, marginBottom: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Risk Signal Breakdown</h3>
                <SignalBar label="Burnout Risk" value={signals.burnout_risk} />
                <SignalBar label="Stale Content" value={signals.stale_content_ratio * 100} />
                <SignalBar label="Contributor Concentration" value={signals.contributor_concentration * 100} />
                <div style={{ display: 'flex', gap: 16, marginTop: 16, fontSize: 13, color: '#6b7280' }}>
                  <span>Creation trend: <TrendBadge trend={signals.creation_trend} /></span>
                  <span>Activity trend: <TrendBadge trend={signals.contribution_trend} /></span>
                </div>
              </div>
              <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Why Knowledge Base Activity Matters</div>
                <div style={{ fontSize: 13, color: '#6b7280', lineHeight: 1.8 }}>
                  Declining documentation activity is a <strong>leading indicator of disengagement</strong> —
                  people stop contributing knowledge before they stop doing other work. High contributor
                  concentration means a <strong>bus factor risk</strong>: if one or two key contributors leave,
                  institutional knowledge leaves with them.
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
