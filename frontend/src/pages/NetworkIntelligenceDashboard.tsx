import { useState, useEffect } from 'react';
import axios from '../api/axios';

// ── Types ───────────────────────────────────────────────────────────

interface AffectedEntity {
  id: string;
  name: string;
  team: string;
  metrics: Record<string, number>;
}

interface Signal {
  signal_type: string;
  severity: 'info' | 'warning' | 'critical';
  severity_score: number;
  affected_entities: AffectedEntity[];
  description: string;
  recommendation: string;
  evidence: Record<string, number>;
}

interface AnalysisData {
  org_id: string;
  node_count: number;
  edge_count: number;
  density: number;
  health_score: number;
  signals: Signal[];
  team_interaction_matrix: Record<string, Record<string, number>>;
}

// ── Constants ───────────────────────────────────────────────────────

const SEVERITY_COLORS: Record<string, string> = {
  info: '#3B82F6',
  warning: '#F59E0B',
  critical: '#EF4444',
};

const SEVERITY_BG: Record<string, string> = {
  info: '#eff6ff',
  warning: '#fffbeb',
  critical: '#fef2f2',
};

const SEVERITY_BORDER: Record<string, string> = {
  info: '#bfdbfe',
  warning: '#fde68a',
  critical: '#fecaca',
};

const SIGNAL_META: Record<string, { label: string; icon: string }> = {
  isolated_employees: { label: 'Isolated Employees', icon: '🔴' },
  collaboration_bottlenecks: { label: 'Collaboration Bottlenecks', icon: '🔗' },
  overloaded_connectors: { label: 'Overloaded Connectors', icon: '⚡' },
  non_interacting_teams: { label: 'Non-Interacting Teams', icon: '🚧' },
  excessive_cross_team_dependency: { label: 'Excessive Cross-Team Dependency', icon: '🔀' },
  communication_concentration: { label: 'Communication Concentration', icon: '📡' },
  emerging_informal_leaders: { label: 'Emerging Informal Leaders', icon: '⭐' },
  organizational_silos: { label: 'Organizational Silos', icon: '🏢' },
};

// ── Helper components ───────────────────────────────────────────────

function HealthGauge({ score }: { score: number }) {
  const color = score > 70 ? '#10b981' : score > 40 ? '#F59E0B' : '#EF4444';
  const label = score > 70 ? 'Healthy' : score > 40 ? 'Moderate' : 'At Risk';
  const circumference = 2 * Math.PI * 54;
  const filled = (score / 100) * circumference;

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={140} height={140} viewBox="0 0 140 140">
        <circle cx={70} cy={70} r={54} fill="none" stroke="#f3f4f6" strokeWidth={10} />
        <circle
          cx={70} cy={70} r={54} fill="none"
          stroke={color} strokeWidth={10}
          strokeDasharray={`${filled} ${circumference}`}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dasharray 0.8s ease' }}
        />
        <text x={70} y={64} textAnchor="middle" fontSize={32} fontWeight={700} fill={color}>
          {score}
        </text>
        <text x={70} y={84} textAnchor="middle" fontSize={12} fill="#9ca3af">
          /100
        </text>
      </svg>
      <div style={{ fontSize: 13, fontWeight: 600, color, marginTop: 4, textTransform: 'uppercase', letterSpacing: 1 }}>
        {label}
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 10px', borderRadius: 12,
      fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5,
      color: '#fff', background: SEVERITY_COLORS[severity] || '#9ca3af',
    }}>
      {severity}
    </span>
  );
}

function SeverityBar({ score }: { score: number }) {
  const color = score >= 70 ? '#EF4444' : score >= 40 ? '#F59E0B' : '#3B82F6';
  return (
    <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 4, height: 8, maxWidth: 120 }}>
      <div style={{
        width: `${Math.min(score, 100)}%`, height: '100%',
        background: color, borderRadius: 4, transition: 'width 0.5s ease',
      }} />
    </div>
  );
}

// ── Signal Card ─────────────────────────────────────────────────────

function SignalCard({ signal, expanded, onToggle }: {
  signal: Signal;
  expanded: boolean;
  onToggle: () => void;
}) {
  const meta = SIGNAL_META[signal.signal_type] || { label: signal.signal_type, icon: '📊' };
  const isPositive = signal.signal_type === 'emerging_informal_leaders';

  return (
    <div style={{
      background: '#fff', border: `1px solid ${SEVERITY_BORDER[signal.severity] || '#e5e7eb'}`,
      borderRadius: 12, overflow: 'hidden',
      borderLeft: `4px solid ${SEVERITY_COLORS[signal.severity] || '#9ca3af'}`,
    }}>
      <button
        onClick={onToggle}
        style={{
          width: '100%', padding: 16, border: 'none', background: 'transparent',
          cursor: 'pointer', textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <span style={{ fontSize: 20 }}>{meta.icon}</span>
          <span style={{ fontSize: 14, fontWeight: 600, flex: 1 }}>{meta.label}</span>
          <SeverityBadge severity={signal.severity} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
          <SeverityBar score={signal.severity_score} />
          <span style={{ fontSize: 12, fontWeight: 600, color: '#374151', minWidth: 28 }}>
            {signal.severity_score}
          </span>
        </div>
        <div style={{ fontSize: 13, color: '#4b5563', lineHeight: 1.4 }}>
          {signal.description}
        </div>
        <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 6 }}>
          {signal.affected_entities.length} affected {signal.affected_entities.length === 1 ? 'entity' : 'entities'}
          <span style={{ marginLeft: 8 }}>{expanded ? '▲ Collapse' : '▼ Expand'}</span>
        </div>
      </button>

      {expanded && (
        <div style={{
          padding: '0 16px 16px', borderTop: '1px solid #f3f4f6',
        }}>
          {/* Recommendation */}
          <div style={{
            margin: '12px 0', padding: 12,
            background: isPositive ? '#f0fdf4' : SEVERITY_BG[signal.severity] || '#f9fafb',
            borderRadius: 8, fontSize: 13, color: isPositive ? '#166534' : '#374151',
            borderLeft: `3px solid ${isPositive ? '#22c55e' : SEVERITY_COLORS[signal.severity]}`,
          }}>
            <span style={{ fontWeight: 600 }}>Recommendation: </span>
            {signal.recommendation}
          </div>

          {/* Evidence */}
          {Object.keys(signal.evidence).length > 0 && (
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
              {Object.entries(signal.evidence).map(([key, val]) => (
                <div key={key} style={{
                  padding: '6px 12px', background: '#f9fafb', borderRadius: 8,
                  fontSize: 12, border: '1px solid #e5e7eb',
                }}>
                  <span style={{ color: '#6b7280' }}>{key.replace(/_/g, ' ')}: </span>
                  <span style={{ fontWeight: 600 }}>{typeof val === 'number' ? val.toFixed(2) : val}</span>
                </div>
              ))}
            </div>
          )}

          {/* Affected entities table */}
          {signal.affected_entities.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#6b7280', fontWeight: 600 }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#6b7280', fontWeight: 600 }}>Team</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#6b7280', fontWeight: 600 }}>Key Metrics</th>
                  </tr>
                </thead>
                <tbody>
                  {signal.affected_entities.map((entity) => (
                    <tr key={entity.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '8px 12px', fontWeight: 500 }}>{entity.name}</td>
                      <td style={{ padding: '8px 12px', color: '#6b7280' }}>{entity.team}</td>
                      <td style={{ padding: '8px 12px' }}>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                          {Object.entries(entity.metrics).map(([k, v]) => (
                            <span key={k} style={{
                              padding: '2px 8px', background: '#f3f4f6', borderRadius: 6, fontSize: 11,
                            }}>
                              {k.replace(/_/g, ' ')}: {typeof v === 'number' ? v.toFixed(2) : v}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Heatmap ─────────────────────────────────────────────────────────

function TeamHeatmap({ matrix }: { matrix: Record<string, Record<string, number>> }) {
  const teams = Object.keys(matrix).sort();
  if (teams.length === 0) {
    return <div style={{ color: '#9ca3af', fontSize: 13, textAlign: 'center', padding: 40 }}>No team interaction data available</div>;
  }

  // Find max density for color scaling
  let maxDensity = 0;
  teams.forEach(r => teams.forEach(c => {
    const val = matrix[r]?.[c] ?? 0;
    if (val > maxDensity) maxDensity = val;
  }));
  if (maxDensity === 0) maxDensity = 1;

  const cellSize = Math.max(36, Math.min(64, 600 / teams.length));
  const labelWidth = 120;

  return (
    <div style={{ overflowX: 'auto' }}>
      {/* Column headers */}
      <div style={{ display: 'flex', marginLeft: labelWidth }}>
        {teams.map(t => (
          <div key={t} style={{
            width: cellSize, fontSize: 10, color: '#6b7280', fontWeight: 500,
            textAlign: 'center', padding: '4px 2px', overflow: 'hidden',
            textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            transform: teams.length > 6 ? 'rotate(-45deg)' : undefined,
            transformOrigin: 'center bottom',
            height: teams.length > 6 ? 60 : 20,
          }} title={t}>
            {t.length > 10 ? t.slice(0, 9) + '...' : t}
          </div>
        ))}
      </div>

      {/* Rows */}
      {teams.map(row => (
        <div key={row} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: labelWidth, fontSize: 12, color: '#374151', fontWeight: 500,
            padding: '4px 8px 4px 0', textAlign: 'right', overflow: 'hidden',
            textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexShrink: 0,
          }} title={row}>
            {row}
          </div>
          {teams.map(col => {
            const val = matrix[row]?.[col] ?? 0;
            const intensity = val / maxDensity;
            const isDiagonal = row === col;
            return (
              <div
                key={col}
                title={`${row} ↔ ${col}: ${val.toFixed(3)}`}
                style={{
                  width: cellSize, height: cellSize, flexShrink: 0,
                  background: isDiagonal
                    ? `rgba(99, 102, 241, ${0.15 + intensity * 0.7})`
                    : `rgba(16, 185, 129, ${0.05 + intensity * 0.8})`,
                  border: '1px solid #fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 10, color: intensity > 0.6 ? '#fff' : '#374151',
                  fontWeight: intensity > 0.5 ? 600 : 400,
                  cursor: 'default',
                }}
              >
                {val > 0 ? val.toFixed(2) : ''}
              </div>
            );
          })}
        </div>
      ))}

      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16, fontSize: 11, color: '#9ca3af' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 12, height: 12, borderRadius: 2, background: 'rgba(99, 102, 241, 0.6)' }} />
          Internal density
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 12, height: 12, borderRadius: 2, background: 'rgba(16, 185, 129, 0.6)' }} />
          Cross-team density
        </span>
        <span>Darker = stronger interaction</span>
      </div>
    </div>
  );
}

// ── People List ─────────────────────────────────────────────────────

function PeopleSection({ title, subtitle, people, metricLabel, metricKey, color }: {
  title: string;
  subtitle: string;
  people: AffectedEntity[];
  metricLabel: string;
  metricKey: string;
  color: string;
}) {
  if (people.length === 0) {
    return (
      <div style={{
        background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 20,
      }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: 13, color: '#9ca3af' }}>No signals detected</div>
      </div>
    );
  }

  return (
    <div style={{
      background: '#fff', border: '1px solid #e5e7eb', borderRadius: 12, padding: 20,
    }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4, color: '#111827' }}>{title}</div>
      <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 16 }}>{subtitle}</div>
      {people.map(person => {
        const metricVal = person.metrics[metricKey] ?? Object.values(person.metrics)[0] ?? 0;
        return (
          <div key={person.id} style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '10px 0', borderBottom: '1px solid #f3f4f6',
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              background: `${color}15`, color,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 14, fontWeight: 700, flexShrink: 0,
            }}>
              {person.name.charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>{person.name}</div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>{person.team}</div>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color }}>{typeof metricVal === 'number' ? metricVal.toFixed(2) : metricVal}</div>
              <div style={{ fontSize: 10, color: '#9ca3af' }}>{metricLabel}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main Dashboard ──────────────────────────────────────────────────

export default function NetworkIntelligenceDashboard() {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'signals' | 'teams' | 'people'>('signals');
  const [expandedSignal, setExpandedSignal] = useState<string | null>(null);

  const orgId = 'default';

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    axios.get(`/api/v1/network-intelligence/${orgId}/analysis`)
      .then(res => {
        if (!cancelled) setData(res.data);
      })
      .catch(err => {
        if (!cancelled) setError(err?.response?.data?.detail || 'Failed to load network intelligence data');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [orgId]);

  const tabs = [
    { id: 'signals' as const, label: 'Signal Overview' },
    { id: 'teams' as const, label: 'Team Interactions' },
    { id: 'people' as const, label: 'People Insights' },
  ];

  // Extract people lists from signals for the People tab
  const bottlenecks = data?.signals.find(s => s.signal_type === 'collaboration_bottlenecks')?.affected_entities ?? [];
  const overloaded = data?.signals.find(s => s.signal_type === 'overloaded_connectors')?.affected_entities ?? [];
  const informalLeaders = data?.signals.find(s => s.signal_type === 'emerging_informal_leaders')?.affected_entities ?? [];

  // Extract non-interacting and strongest pairs for Team tab
  const matrix = data?.team_interaction_matrix ?? {};
  const teamNames = Object.keys(matrix).sort();
  const teamPairs: { a: string; b: string; density: number }[] = [];
  for (let i = 0; i < teamNames.length; i++) {
    for (let j = i + 1; j < teamNames.length; j++) {
      const d = matrix[teamNames[i]]?.[teamNames[j]] ?? 0;
      teamPairs.push({ a: teamNames[i], b: teamNames[j], density: d });
    }
  }
  const nonInteracting = teamPairs.filter(p => p.density < 0.01).sort((a, b) => a.density - b.density);
  const strongest = [...teamPairs].sort((a, b) => b.density - a.density).slice(0, 5);

  // Sort signals: critical first, then warning, then info
  const severityOrder: Record<string, number> = { critical: 0, warning: 1, info: 2 };
  const sortedSignals = [...(data?.signals ?? [])].sort(
    (a, b) => (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3)
  );

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 8 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Network Intelligence</h1>
        <p style={{ color: '#6b7280', fontSize: 14 }}>
          Structural risk signals detected from organizational relationship patterns.
        </p>
      </div>

      {/* Privacy note */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 20,
        padding: '4px 14px', fontSize: 12, color: '#16a34a', fontWeight: 600, marginBottom: 24,
      }}>
        <span>&#x1F512;</span> Analyzes relationship patterns and interaction metadata only — never message content
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: '10px 20px', border: 'none', cursor: 'pointer',
              fontSize: 14, fontWeight: tab === t.id ? 600 : 400,
              color: tab === t.id ? '#4f46e5' : '#6b7280',
              borderBottom: tab === t.id ? '2px solid #4f46e5' : '2px solid transparent',
              background: 'transparent',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>
          Loading network intelligence...
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{
          padding: 16, background: '#fef2f2', border: '1px solid #fecaca',
          borderRadius: 8, color: '#991b1b', marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {/* ── Tab 1: Signal Overview ────────────────────────────────── */}
      {!loading && !error && data && tab === 'signals' && (
        <>
          {/* Top stats row */}
          <div style={{
            display: 'flex', gap: 24, marginBottom: 24, alignItems: 'center',
            background: '#fff', padding: 24, borderRadius: 12, border: '1px solid #e5e7eb',
          }}>
            <HealthGauge score={data.health_score} />
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#111827' }}>{data.node_count}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>People</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#111827' }}>{data.edge_count}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Connections</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#111827' }}>{data.density.toFixed(3)}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Graph Density</div>
              </div>
            </div>
          </div>

          {/* Signal cards grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
            {sortedSignals.map(signal => (
              <SignalCard
                key={signal.signal_type}
                signal={signal}
                expanded={expandedSignal === signal.signal_type}
                onToggle={() => setExpandedSignal(
                  expandedSignal === signal.signal_type ? null : signal.signal_type
                )}
              />
            ))}
          </div>

          {sortedSignals.length === 0 && (
            <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af', fontSize: 14 }}>
              No network signals detected. The organization graph may not have enough data yet.
            </div>
          )}
        </>
      )}

      {/* ── Tab 2: Team Interactions ──────────────────────────────── */}
      {!loading && !error && data && tab === 'teams' && (
        <>
          {/* Heatmap */}
          <div style={{
            background: '#fff', padding: 24, borderRadius: 12,
            border: '1px solid #e5e7eb', marginBottom: 24,
          }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4, color: '#111827' }}>
              Team Interaction Matrix
            </h2>
            <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 20 }}>
              Density of collaboration connections between teams. Diagonal cells show internal team density.
            </p>
            <TeamHeatmap matrix={matrix} />
          </div>

          {/* Non-interacting pairs + Strongest connections side by side */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* Non-interacting */}
            <div style={{
              background: '#fff', padding: 20, borderRadius: 12,
              border: '1px solid #e5e7eb',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <span style={{ fontSize: 18 }}>&#x1F6A7;</span>
                <span style={{ fontWeight: 700, fontSize: 15 }}>Non-Interacting Pairs</span>
                <span style={{
                  marginLeft: 'auto', padding: '2px 8px', borderRadius: 10,
                  background: nonInteracting.length > 0 ? '#fef2f2' : '#f0fdf4',
                  color: nonInteracting.length > 0 ? '#991b1b' : '#166534',
                  fontSize: 12, fontWeight: 600,
                }}>
                  {nonInteracting.length}
                </span>
              </div>
              {nonInteracting.length === 0 ? (
                <div style={{ color: '#9ca3af', fontSize: 13 }}>
                  All teams have at least some cross-team interaction.
                </div>
              ) : (
                nonInteracting.map((pair, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    padding: '8px 0', borderBottom: '1px solid #f3f4f6',
                    fontSize: 13,
                  }}>
                    <span style={{ fontWeight: 500, color: '#374151' }}>{pair.a}</span>
                    <span style={{ color: '#d1d5db' }}>&#x2194;</span>
                    <span style={{ fontWeight: 500, color: '#374151' }}>{pair.b}</span>
                    <span style={{ marginLeft: 'auto', color: '#ef4444', fontSize: 12, fontWeight: 600 }}>
                      {pair.density.toFixed(3)}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Strongest connections */}
            <div style={{
              background: '#fff', padding: 20, borderRadius: 12,
              border: '1px solid #e5e7eb',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <span style={{ fontSize: 18 }}>&#x1F91D;</span>
                <span style={{ fontWeight: 700, fontSize: 15 }}>Strongest Connections</span>
              </div>
              {strongest.length === 0 ? (
                <div style={{ color: '#9ca3af', fontSize: 13 }}>No team pairs found.</div>
              ) : (
                strongest.map((pair, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    padding: '8px 0', borderBottom: '1px solid #f3f4f6',
                    fontSize: 13,
                  }}>
                    <span style={{
                      width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                      background: '#4f46e5', color: '#fff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 11, fontWeight: 700,
                    }}>
                      {i + 1}
                    </span>
                    <span style={{ fontWeight: 500, color: '#374151' }}>{pair.a}</span>
                    <span style={{ color: '#d1d5db' }}>&#x2194;</span>
                    <span style={{ fontWeight: 500, color: '#374151' }}>{pair.b}</span>
                    <span style={{ marginLeft: 'auto', color: '#10b981', fontSize: 12, fontWeight: 600 }}>
                      {pair.density.toFixed(3)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}

      {/* ── Tab 3: People Insights ────────────────────────────────── */}
      {!loading && !error && data && tab === 'people' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <PeopleSection
            title="Collaboration Bottlenecks"
            subtitle="Employees with high betweenness centrality — information flows through them disproportionately"
            people={bottlenecks}
            metricLabel="betweenness"
            metricKey="betweenness_centrality"
            color="#EF4444"
          />
          <PeopleSection
            title="Overloaded Connectors"
            subtitle="Employees managing too many concurrent collaboration connections"
            people={overloaded}
            metricLabel="connections"
            metricKey="connection_count"
            color="#F59E0B"
          />
          <PeopleSection
            title="Emerging Informal Leaders"
            subtitle="Non-managers with high network centrality — potential for formal leadership roles"
            people={informalLeaders}
            metricLabel="centrality"
            metricKey="centrality_score"
            color="#10b981"
          />
        </div>
      )}
    </div>
  );
}
