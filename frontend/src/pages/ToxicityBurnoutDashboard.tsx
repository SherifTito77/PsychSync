import { useState, useEffect, useCallback } from 'react';
import axios from '../services/axios';

interface CompositeResult {
  burnout_score: number;
  toxicity_score: number;
  combined_risk: number;
  cross_contamination_multiplier: number;
  burnout_label: string;
  toxicity_label: string;
  combined_label: string;
  burnout_signals: Record<string, number>;
  toxicity_signals: Record<string, number>;
  active_burnout_sources: number;
  active_toxicity_sources: number;
  overlap_patterns: string[];
  recommendations: string[];
}

interface DataSource {
  name: string;
  available: boolean;
  category: string;
}

const LABEL_COLORS: Record<string, string> = {
  Healthy: '#10b981',
  Monitor: '#f59e0b',
  Elevated: '#f97316',
  Critical: '#ef4444',
  'No Data': '#9ca3af',
};

const SIGNAL_LABELS: Record<string, string> = {
  pto_avoidance: 'PTO Avoidance',
  login_span_expansion: 'Login Span Expansion',
  break_deficit: 'Break Deficit',
  calendar_fragmentation: 'Calendar Fragmentation',
  after_hours_trend: 'After-Hours Trend',
  quality_degradation: 'Quality Degradation',
  speaking_imbalance: 'Speaking Imbalance',
  reaction_asymmetry: 'Reaction Asymmetry',
  review_hostility: 'Review Hostility',
  one_on_one_cancellation: '1:1 Cancellation',
  invite_exclusion: 'Invite Exclusion',
  response_asymmetry: 'Response Asymmetry',
  attrition_clustering: 'Attrition Clustering',
};

function ScoreGauge({ score, label, title }: { score: number; label: string; title: string }) {
  const color = LABEL_COLORS[label] || '#9ca3af';
  return (
    <div style={{ textAlign: 'center', flex: 1 }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: '#374151' }}>{title}</div>
      <div
        style={{
          width: 120, height: 120, borderRadius: '50%',
          border: `6px solid ${color}`,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          margin: '0 auto',
        }}
      >
        <div style={{ fontSize: 28, fontWeight: 700, color }}>{score.toFixed(0)}</div>
        <div style={{ fontSize: 11, color: '#6b7280' }}>/100</div>
      </div>
      <div
        style={{
          marginTop: 8, fontSize: 12, fontWeight: 600,
          color, textTransform: 'uppercase', letterSpacing: 1,
        }}
      >
        {label}
      </div>
    </div>
  );
}

function SignalBar({ name, score }: { name: string; score: number }) {
  const barColor =
    score >= 70 ? '#ef4444' : score >= 45 ? '#f97316' : score >= 25 ? '#f59e0b' : '#10b981';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
      <div style={{ width: 160, fontSize: 13, color: '#374151', flexShrink: 0 }}>
        {SIGNAL_LABELS[name] || name}
      </div>
      <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 4, height: 20, position: 'relative' }}>
        <div
          style={{
            width: `${Math.min(score, 100)}%`, height: '100%',
            background: barColor, borderRadius: 4,
            transition: 'width 0.6s ease',
          }}
        />
        <span
          style={{
            position: 'absolute', right: 8, top: 1,
            fontSize: 12, fontWeight: 600, color: score > 60 ? '#fff' : '#374151',
          }}
        >
          {score.toFixed(1)}
        </span>
      </div>
    </div>
  );
}

function CrossContaminationGauge({ multiplier }: { multiplier: number }) {
  const pct = ((multiplier - 1.0) / 1.0) * 100;

  const tier = multiplier >= 1.8
    ? { color: '#ef4444', bg: '#fef2f2', border: '#fecaca', icon: '\u{1F6A8}',
        headline: 'Self-Reinforcing Spiral',
        detail: 'Toxicity and burnout are feeding each other. Burned-out managers generate toxicity, '
              + 'and toxic environments accelerate burnout. Immediate intervention needed.' }
    : multiplier >= 1.4
    ? { color: '#f97316', bg: '#fff7ed', border: '#fed7aa', icon: '\u26A0\uFE0F',
        headline: 'Feedback Loop Forming',
        detail: 'Early signs of toxicity-burnout interaction. Both problems are starting to amplify each other. '
              + 'Address the stronger signal now before the loop locks in.' }
    : multiplier >= 1.2
    ? { color: '#f59e0b', bg: '#fffbeb', border: '#fde68a', icon: '\u{1F50D}',
        headline: 'Mild Interaction Detected',
        detail: 'Slight overlap between toxicity and burnout signals. Monitor closely — '
              + 'this can escalate quickly if workload or interpersonal issues worsen.' }
    : { color: '#10b981', bg: '#f0fdf4', border: '#bbf7d0', icon: '\u{1F6E1}\uFE0F',
        headline: 'No Feedback Loop',
        detail: 'Toxicity and burnout signals are independent. Any issues present can be addressed '
              + 'individually without worrying about cascading effects.' };

  return (
    <div style={{
      padding: 20, background: tier.bg, borderRadius: 12,
      border: `1px solid ${tier.border}`, marginTop: 20,
      display: 'flex', gap: 20, alignItems: 'center',
    }}>
      {/* Left: multiplier value + bar */}
      <div style={{ textAlign: 'center', minWidth: 120 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 6 }}>
          Feedback Loop
        </div>
        <div style={{ fontSize: 36, fontWeight: 700, color: tier.color }}>
          {multiplier.toFixed(2)}x
        </div>
        <div style={{
          width: '100%', background: '#e5e7eb', borderRadius: 4,
          height: 6, marginTop: 8, overflow: 'hidden',
        }}>
          <div style={{
            width: `${Math.min(pct, 100)}%`, height: '100%',
            background: tier.color, borderRadius: 4,
            transition: 'width 0.6s ease',
          }} />
        </div>
        <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 4 }}>
          1.0x &rarr; 2.0x
        </div>
      </div>

      {/* Right: contextual explanation */}
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 20 }}>{tier.icon}</span>
          <span style={{ fontSize: 15, fontWeight: 700, color: tier.color }}>
            {tier.headline}
          </span>
        </div>
        <div style={{ fontSize: 13, color: '#4b5563', lineHeight: 1.5 }}>
          {tier.detail}
        </div>
      </div>
    </div>
  );
}

interface TrendPoint {
  date: string;
  burnout_score: number;
  toxicity_score: number;
  combined_risk: number;
}

interface TrendData {
  snapshots: TrendPoint[];
  trend_direction: string;
  period_days: number;
}

function TrendChart({ data }: { data: TrendPoint[] }) {
  if (data.length < 2) {
    return <div style={{ color: '#9ca3af', fontSize: 13, textAlign: 'center', padding: 40 }}>
      Not enough data points yet. Check back after a few days of monitoring.
    </div>;
  }

  const W = 700, H = 200, PAD = 40;
  const xScale = (i: number) => PAD + (i / (data.length - 1)) * (W - PAD * 2);
  const yScale = (v: number) => H - PAD - (v / 100) * (H - PAD * 2);

  const makePath = (key: keyof TrendPoint) =>
    data.map((p, i) => `${i === 0 ? 'M' : 'L'}${xScale(i).toFixed(1)},${yScale(p[key] as number).toFixed(1)}`).join(' ');

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxHeight: 220 }}>
      {/* Grid lines */}
      {[0, 25, 50, 75, 100].map(v => (
        <g key={v}>
          <line x1={PAD} x2={W - PAD} y1={yScale(v)} y2={yScale(v)} stroke="#f3f4f6" strokeWidth={1} />
          <text x={PAD - 6} y={yScale(v) + 4} textAnchor="end" fill="#9ca3af" fontSize={10}>{v}</text>
        </g>
      ))}
      {/* Lines */}
      <path d={makePath('burnout_score')} fill="none" stroke="#f97316" strokeWidth={2} />
      <path d={makePath('toxicity_score')} fill="none" stroke="#8b5cf6" strokeWidth={2} />
      <path d={makePath('combined_risk')} fill="none" stroke="#ef4444" strokeWidth={2.5} />
      {/* Date labels */}
      {data.filter((_, i) => i === 0 || i === data.length - 1 || i === Math.floor(data.length / 2)).map((p, _i, arr) => {
        const idx = data.indexOf(p);
        return <text key={p.date} x={xScale(idx)} y={H - 8} textAnchor="middle" fill="#9ca3af" fontSize={10}>{p.date.slice(5)}</text>;
      })}
      {/* Legend */}
      <circle cx={PAD + 10} cy={12} r={4} fill="#f97316" />
      <text x={PAD + 20} y={16} fill="#374151" fontSize={10}>Burnout</text>
      <circle cx={PAD + 90} cy={12} r={4} fill="#8b5cf6" />
      <text x={PAD + 100} y={16} fill="#374151" fontSize={10}>Toxicity</text>
      <circle cx={PAD + 170} cy={12} r={4} fill="#ef4444" />
      <text x={PAD + 180} y={16} fill="#374151" fontSize={10}>Combined</text>
    </svg>
  );
}

function ToxicityBurnoutDashboard() {
  const [activeTab, setActiveTab] = useState<'composite' | 'signals' | 'sources' | 'trend'>('composite');
  const [composite, setComposite] = useState<CompositeResult | null>(null);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = 'current';

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [compositeRes, sourcesRes, trendRes] = await Promise.all([
        axios.get(`/api/v1/toxicity-burnout/${orgId}/composite`),
        axios.get(`/api/v1/toxicity-burnout/${orgId}/data-sources`),
        axios.get(`/api/v1/toxicity-burnout/${orgId}/trend?days=30`),
      ]);
      setComposite(compositeRes.data);
      setDataSources(sourcesRes.data.sources || []);
      setTrendData(trendRes.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load toxicity/burnout data');
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const tabs = [
    { key: 'composite' as const, label: 'Composite Risk' },
    { key: 'signals' as const, label: 'Signal Breakdown' },
    { key: 'trend' as const, label: 'Trend' },
    { key: 'sources' as const, label: 'Data Sources' },
  ];

  const sortedBurnoutSignals = composite
    ? Object.entries(composite.burnout_signals).sort(([, a], [, b]) => b - a)
    : [];
  const sortedToxicitySignals = composite
    ? Object.entries(composite.toxicity_signals).sort(([, a], [, b]) => b - a)
    : [];

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>
          Toxicity & Burnout Intelligence
        </h1>
        <p style={{ color: '#6b7280', fontSize: 14 }}>
          Passive detection from infrastructure metadata. Zero surveys, zero human input.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e5e7eb' }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 20px', border: 'none', cursor: 'pointer',
              fontSize: 14, fontWeight: activeTab === tab.key ? 600 : 400,
              color: activeTab === tab.key ? '#4f46e5' : '#6b7280',
              borderBottom: activeTab === tab.key ? '2px solid #4f46e5' : '2px solid transparent',
              background: 'transparent',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: 60, color: '#9ca3af' }}>
          Loading passive signals...
        </div>
      )}

      {error && (
        <div style={{
          padding: 16, background: '#fef2f2', border: '1px solid #fecaca',
          borderRadius: 8, color: '#991b1b', marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {!loading && !error && composite && activeTab === 'composite' && (
        <>
          {/* Score Gauges */}
          <div style={{
            display: 'flex', gap: 24, marginBottom: 24,
            background: '#fff', padding: 24, borderRadius: 12,
            border: '1px solid #e5e7eb',
          }}>
            <ScoreGauge score={composite.burnout_score} label={composite.burnout_label} title="Burnout" />
            <ScoreGauge score={composite.toxicity_score} label={composite.toxicity_label} title="Toxicity" />
            <ScoreGauge score={composite.combined_risk} label={composite.combined_label} title="Combined Risk" />
          </div>

          {/* Cross-contamination */}
          <CrossContaminationGauge multiplier={composite.cross_contamination_multiplier} />

          {/* Overlap Patterns */}
          {composite.overlap_patterns.length > 0 && (
            <div style={{
              marginTop: 20, padding: 20, background: '#fef3c7',
              border: '1px solid #fcd34d', borderRadius: 12,
            }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12, color: '#92400e' }}>
                Dangerous Overlap Patterns
              </div>
              {composite.overlap_patterns.map((pattern, i) => (
                <div
                  key={i}
                  style={{
                    padding: '10px 14px', background: '#fffbeb',
                    borderRadius: 8, marginBottom: 8, fontSize: 13,
                    color: '#78350f', borderLeft: '3px solid #f59e0b',
                  }}
                >
                  {pattern}
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          {composite.recommendations.length > 0 && (
            <div style={{
              marginTop: 20, padding: 20, background: '#f0fdf4',
              border: '1px solid #86efac', borderRadius: 12,
            }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12, color: '#166534' }}>
                Recommended Interventions
              </div>
              {composite.recommendations.map((rec, i) => (
                <div
                  key={i}
                  style={{
                    padding: '10px 14px', background: '#f0fdf4',
                    borderRadius: 8, marginBottom: 8, fontSize: 13,
                    color: '#14532d', borderLeft: '3px solid #22c55e',
                  }}
                >
                  {rec}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {!loading && !error && composite && activeTab === 'signals' && (
        <div style={{ display: 'flex', gap: 24 }}>
          {/* Burnout signals */}
          <div style={{
            flex: 1, background: '#fff', padding: 20,
            borderRadius: 12, border: '1px solid #e5e7eb',
          }}>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16, color: '#374151' }}>
              Burnout Signals ({composite.active_burnout_sources} sources)
            </div>
            {sortedBurnoutSignals.length === 0 ? (
              <div style={{ color: '#9ca3af', fontSize: 13 }}>No burnout signals available</div>
            ) : (
              sortedBurnoutSignals.map(([name, score]) => (
                <SignalBar key={name} name={name} score={score} />
              ))
            )}
          </div>

          {/* Toxicity signals */}
          <div style={{
            flex: 1, background: '#fff', padding: 20,
            borderRadius: 12, border: '1px solid #e5e7eb',
          }}>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16, color: '#374151' }}>
              Toxicity Signals ({composite.active_toxicity_sources} sources)
            </div>
            {sortedToxicitySignals.length === 0 ? (
              <div style={{ color: '#9ca3af', fontSize: 13 }}>No toxicity signals available</div>
            ) : (
              sortedToxicitySignals.map(([name, score]) => (
                <SignalBar key={name} name={name} score={score} />
              ))
            )}
          </div>
        </div>
      )}

      {!loading && !error && activeTab === 'trend' && (
        <div style={{
          background: '#fff', padding: 20,
          borderRadius: 12, border: '1px solid #e5e7eb',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ fontWeight: 700, fontSize: 16 }}>30-Day Trend</div>
            {trendData && (
              <span style={{
                fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 12,
                background: trendData.trend_direction === 'improving' ? '#dcfce7' : trendData.trend_direction === 'declining' ? '#fef2f2' : '#f3f4f6',
                color: trendData.trend_direction === 'improving' ? '#166534' : trendData.trend_direction === 'declining' ? '#991b1b' : '#6b7280',
              }}>
                {trendData.trend_direction === 'improving' ? 'Improving' : trendData.trend_direction === 'declining' ? 'Declining' : 'Stable'}
              </span>
            )}
          </div>
          <TrendChart data={trendData?.snapshots || []} />
        </div>
      )}

      {!loading && !error && activeTab === 'sources' && (
        <div style={{
          background: '#fff', padding: 20,
          borderRadius: 12, border: '1px solid #e5e7eb',
        }}>
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16 }}>
            Data Source Connectors
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {dataSources.map(source => (
              <div
                key={source.name}
                style={{
                  padding: '12px 16px', borderRadius: 8,
                  border: `1px solid ${source.available ? '#86efac' : '#e5e7eb'}`,
                  background: source.available ? '#f0fdf4' : '#fafafa',
                  display: 'flex', alignItems: 'center', gap: 10,
                }}
              >
                <div style={{
                  width: 10, height: 10, borderRadius: '50%',
                  background: source.available ? '#22c55e' : '#d1d5db',
                }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, textTransform: 'capitalize' }}>
                    {source.name.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', textTransform: 'capitalize' }}>
                    {source.category}
                  </div>
                </div>
              </div>
            ))}
          </div>
          {dataSources.length === 0 && (
            <div style={{ color: '#9ca3af', fontSize: 13, textAlign: 'center', padding: 40 }}>
              No data sources configured yet
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ToxicityBurnoutDashboard;
