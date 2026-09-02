import { useState, useEffect } from 'react';
import axios from '../api/axios';

function scoreColor(s: number) { return s >= 70 ? '#ef4444' : s >= 45 ? '#f97316' : s >= 25 ? '#eab308' : '#22c55e'; }
function riskColor(l: string) { return l === 'Critical' ? '#ef4444' : l === 'Elevated' ? '#f97316' : l === 'Monitor' ? '#eab308' : l === 'Healthy' ? '#22c55e' : '#6b7280'; }
function formatHour(h: number) { return h === 0 ? '12a' : h < 12 ? `${h}a` : h === 12 ? '12p' : `${h - 12}p`; }

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

export default function GitMetadataDashboard() {
  const [days, setDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [signals, setSignals] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'prs' | 'burnout'>('overview');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    axios.get(`/api/v1/git-metadata/signals/default`, { params: { days } })
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
    { id: 'prs' as const, label: 'PR Lifecycle', icon: '🔀' },
    { id: 'burnout' as const, label: 'Burnout Signals', icon: '🔥' },
  ];

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Git/GitHub Metadata Analysis</h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>Commit patterns, PR lifecycle, and development cadence — no code content, diffs, or messages.</p>
        </div>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14 }}>
          <option value={7}>7 days</option><option value={14}>14 days</option><option value={30}>30 days</option><option value={90}>90 days</option>
        </select>
      </div>

      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20, padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24 }}>
        <span>🔒</span> Metadata only — no code, diffs, commit messages, or branch names
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
      ) : !signals ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🐙</div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No Git Data Connected</h2>
          <p style={{ color: '#6b7280', maxWidth: 500, margin: '0 auto 24px', lineHeight: 1.6 }}>
            Connect your GitHub organization to analyze development patterns.
            Git metadata reveals <strong>work intensity and boundary erosion</strong> — late-night commits correlate strongly with both burnout and error rates.
          </p>
          <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, maxWidth: 600, margin: '0 auto', textAlign: 'left' }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>What We Analyze</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { icon: '📝', label: 'Commit frequency & timing' },
                { icon: '📊', label: 'Lines changed (counts only)' },
                { icon: '🔀', label: 'PR open → review → merge cycle' },
                { icon: '⏱', label: 'Review turnaround time' },
                { icon: '🌙', label: 'After-hours coding patterns' },
                { icon: '📈', label: 'Code churn ratio' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#374151' }}>
                  <span>{item.icon}</span> {item.label}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: 12, color: '#92400e' }}>
              <strong>What We Never Access:</strong> Code content, diffs, commit messages, branch names, PR titles/descriptions, or file contents.
            </div>
          </div>
        </div>
      ) : (
        <>
          {tab === 'overview' && (
            <div>
              <div style={{ background: '#fff', border: `2px solid ${riskColor(signals.risk_label)}`, borderRadius: 16, padding: 20, marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Git Burnout Risk</div>
                  <div style={{ fontSize: 36, fontWeight: 700, color: riskColor(signals.risk_label) }}>
                    {signals.burnout_risk_score}
                    <span style={{ fontSize: 16, fontWeight: 500, marginLeft: 8 }}>{signals.risk_label}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20 }}>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Intensity</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.work_intensity_score) }}>{signals.work_intensity_score}</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Boundaries</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.boundary_erosion_score) }}>{signals.boundary_erosion_score}</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: 11, color: '#9ca3af' }}>Reviews</div><div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(signals.review_bottleneck_score) }}>{signals.review_bottleneck_score}</div></div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 24 }}>
                <MetricCard icon="📝" label="Avg Commits/Day" value={`${signals.avg_daily_commits}`} detail={`${signals.total_commits} total`} />
                <MetricCard icon="📊" label="Lines/Day" value={`${signals.avg_daily_lines_changed}`} detail={`churn: ${(signals.churn_ratio * 100).toFixed(0)}%`} />
                <MetricCard icon="🌙" label="After Hours" value={`${(signals.after_hours_ratio * 100).toFixed(0)}%`} detail="commits outside 9-6" alert={signals.after_hours_ratio > 0.25} />
                <MetricCard icon="📅" label="Weekend" value={`${(signals.weekend_ratio * 100).toFixed(0)}%`} detail="commits on weekends" alert={signals.weekend_ratio > 0.10} />
                <MetricCard icon="🔀" label="PRs Opened" value={`${signals.total_prs}`} detail={`merge rate: ${(signals.pr_merge_rate * 100).toFixed(0)}%`} />
                <MetricCard icon="📁" label="Files/Commit" value={`${signals.avg_files_per_commit}`} detail="avg breadth of change" alert={signals.avg_files_per_commit > 10} />
              </div>

              {/* Hourly heatmap */}
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Commit Activity by Hour</h3>
                <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end', height: 100 }}>
                  {signals.hourly_distribution.map((count: number, h: number) => {
                    const max = Math.max(...signals.hourly_distribution, 1);
                    const pct = (count / max) * 100;
                    const isAfterHours = h < 9 || h >= 18;
                    return (
                      <div key={h} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <div style={{ width: '100%', height: `${pct}%`, minHeight: count > 0 ? 4 : 0, background: isAfterHours ? '#f97316' : '#14b8a6', borderRadius: '4px 4px 0 0', transition: 'height 0.3s' }} />
                      </div>
                    );
                  })}
                </div>
                <div style={{ display: 'flex', gap: 2, marginTop: 4 }}>
                  {signals.hourly_distribution.map((_: number, h: number) => (
                    <div key={h} style={{ flex: 1, textAlign: 'center', fontSize: 9, color: '#9ca3af' }}>
                      {h % 3 === 0 ? formatHour(h) : ''}
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 12, color: '#6b7280' }}>
                  <span><span style={{ display: 'inline-block', width: 10, height: 10, background: '#14b8a6', borderRadius: 2, marginRight: 4 }} />Business hours</span>
                  <span><span style={{ display: 'inline-block', width: 10, height: 10, background: '#f97316', borderRadius: 2, marginRight: 4 }} />After hours</span>
                </div>
              </div>
            </div>
          )}

          {tab === 'prs' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>PR Lifecycle</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Cycle Time</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: signals.avg_pr_cycle_hours > 48 ? '#f97316' : '#14b8a6' }}>
                      {signals.avg_pr_cycle_hours < 1 ? '<1h' : signals.avg_pr_cycle_hours < 24 ? `${signals.avg_pr_cycle_hours.toFixed(0)}h` : `${(signals.avg_pr_cycle_hours / 24).toFixed(1)}d`}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>open → merge</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Avg Review Wait</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: signals.avg_review_wait_hours > 24 ? '#ef4444' : '#22c55e' }}>
                      {signals.avg_review_wait_hours < 1 ? '<1h' : `${signals.avg_review_wait_hours.toFixed(0)}h`}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>open → first review</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>P90 Review Wait</div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: signals.p90_review_wait_hours > 48 ? '#ef4444' : '#22c55e' }}>
                      {signals.p90_review_wait_hours < 1 ? '<1h' : `${signals.p90_review_wait_hours.toFixed(0)}h`}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>worst 10%</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>Reviewers/PR</div>
                    <div style={{ fontSize: 28, fontWeight: 700 }}>{signals.avg_reviewers_per_pr}</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>avg per PR</div>
                  </div>
                </div>
              </div>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Code Churn</h3>
                <div style={{ display: 'flex', gap: 24, marginBottom: 16 }}>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Additions/Commit</div><div style={{ fontSize: 28, fontWeight: 700, color: '#22c55e' }}>+{signals.avg_additions_per_commit}</div></div>
                  <div><div style={{ fontSize: 12, color: '#9ca3af' }}>Deletions/Commit</div><div style={{ fontSize: 28, fontWeight: 700, color: '#ef4444' }}>-{signals.avg_deletions_per_commit}</div></div>
                </div>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>Churn Ratio</div>
                  <div style={{ height: 8, background: '#f3f4f6', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ width: `${signals.churn_ratio * 100}%`, height: '100%', background: signals.churn_ratio > 0.5 ? '#f97316' : '#14b8a6', borderRadius: 4 }} />
                  </div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>
                    {(signals.churn_ratio * 100).toFixed(0)}% of changes are deletions
                    {signals.churn_ratio > 0.5 ? ' — high churn may indicate rework' : ''}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#9ca3af' }}>Merge Rate</div>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{(signals.pr_merge_rate * 100).toFixed(0)}%</div>
                  <div style={{ fontSize: 11, color: '#9ca3af' }}>PRs merged vs total</div>
                </div>
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
                      <span style={{ color: '#14b8a6', flexShrink: 0 }}>&#9679;</span>
                      <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.5 }}>{rec}</span>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'grid', gridTemplateRows: '1fr 1fr 1fr', gap: 12 }}>
                  <ScoreGauge label="Work Intensity" score={signals.work_intensity_score} subtitle="Commit volume + code churn" />
                  <ScoreGauge label="Boundary Erosion" score={signals.boundary_erosion_score} subtitle="After-hours + weekend coding" />
                  <ScoreGauge label="Review Bottleneck" score={signals.review_bottleneck_score} subtitle="PRs blocked waiting for review" />
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
