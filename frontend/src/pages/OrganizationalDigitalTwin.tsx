import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

// ── Types ──

interface SubMetrics {
  [key: string]: number | string;
}

interface Dimension {
  score: number;
  highlights: string[];
  sub_metrics: SubMetrics;
}

interface Interconnection {
  type: string;
  dimensions: string[];
  severity: string;
  narrative: string;
}

interface TwinState {
  id: string;
  organization_id: string;
  version: number;
  computed_at: string;
  overall_health_score: number;
  overall_trend: string;
  dimensions: {
    teams: Dimension;
    managers: Dimension;
    collaboration: Dimension;
    performance: Dimension;
    turnover_risk: Dimension;
    engagement: Dimension;
    culture: Dimension;
  };
  data_sources: Record<string, boolean>;
  interconnections?: Interconnection[];
}

interface EvolutionPoint {
  version: number;
  computed_at: string;
  overall_health_score: number;
  overall_trend: string;
  scores: Record<string, number>;
}

interface SimulationResult {
  scenario: Record<string, string | number>;
  baseline: Record<string, number>;
  predicted: Record<string, number>;
  deltas: Record<string, number>;
  risk_narrative: string;
  confidence: number;
  error?: string;
}

// ── Constants ──

const DIMENSIONS = [
  { key: 'teams', label: 'Teams', icon: '👥', color: 'blue', desc: 'Team structure, sizes & health' },
  { key: 'managers', label: 'Managers', icon: '👔', color: 'indigo', desc: 'Leadership dependency & bus factor' },
  { key: 'collaboration', label: 'Collaboration', icon: '🤝', color: 'teal', desc: 'Network density, communities & cross-team' },
  { key: 'performance', label: 'Performance', icon: '⚡', color: 'amber', desc: 'Role effectiveness & fit' },
  { key: 'turnover_risk', label: 'Turnover Risk', icon: '🚪', color: 'red', desc: 'Churn prediction & burnout signals', inverted: true },
  { key: 'engagement', label: 'Engagement', icon: '💚', color: 'emerald', desc: 'Wellness, morale & participation' },
  { key: 'culture', label: 'Culture', icon: '🏛', color: 'violet', desc: 'Psych safety, trust, innovation & inclusivity' },
] as const;

const SCENARIOS = [
  { type: 'key_person_departure', label: 'Key Person Leaves', icon: '🚪', desc: 'Impact of losing a manager, influencer, or bridge' },
  { type: 'team_merge', label: 'Team Merger', icon: '🔀', desc: 'Short-term disruption from combining two teams' },
  { type: 'engagement_shift', label: 'Engagement Shift', icon: '📉', desc: 'Cascading effects of engagement changes' },
  { type: 'rapid_growth', label: 'Rapid Growth', icon: '📈', desc: 'Culture dilution from fast hiring' },
];

// ── Helpers ──

function scoreColor(score: number): string {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 55) return 'text-blue-400';
  if (score >= 35) return 'text-amber-400';
  return 'text-red-400';
}

function scoreBg(score: number): string {
  if (score >= 75) return 'bg-emerald-500';
  if (score >= 55) return 'bg-blue-500';
  if (score >= 35) return 'bg-amber-500';
  return 'bg-red-500';
}

function trendIcon(trend: string): string {
  if (trend === 'improving') return '↑';
  if (trend === 'declining') return '↓';
  return '→';
}

function trendColor(trend: string): string {
  if (trend === 'improving') return 'text-emerald-400';
  if (trend === 'declining') return 'text-red-400';
  return 'text-slate-400';
}

function severityBorder(severity: string): string {
  switch (severity) {
    case 'critical': return 'border-red-500/40 bg-red-500/5';
    case 'high': return 'border-orange-500/40 bg-orange-500/5';
    case 'moderate': return 'border-amber-500/40 bg-amber-500/5';
    case 'positive': return 'border-emerald-500/40 bg-emerald-500/5';
    default: return 'border-slate-700 bg-slate-800/30';
  }
}

function deltaColor(d: number): string {
  if (d > 2) return 'text-emerald-400';
  if (d < -2) return 'text-red-400';
  return 'text-slate-400';
}

// ── Component ──

export default function OrganizationalDigitalTwin() {
  const [twin, setTwin] = useState<TwinState | null>(null);
  const [evolution, setEvolution] = useState<EvolutionPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'dimensions' | 'evolution' | 'simulate'>('overview');
  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  // Simulation form
  const [simType, setSimType] = useState('key_person_departure');
  const [simRole, setSimRole] = useState('manager');
  const [simShift, setSimShift] = useState(-15);
  const [simGrowth, setSimGrowth] = useState(30);

  const fetchTwin = useCallback(async (force = false) => {
    setLoading(true);
    try {
      const { data } = await axios.get<TwinState>(
        `/api/v1/org-digital-twin/default`,
        { params: { force_recompute: force } }
      );
      setTwin(data);
    } catch {
      setTwin(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEvolution = useCallback(async () => {
    try {
      const { data } = await axios.get<EvolutionPoint[]>(
        `/api/v1/org-digital-twin/default/evolution`
      );
      setEvolution(data);
    } catch {
      setEvolution([]);
    }
  }, []);

  useEffect(() => {
    fetchTwin();
    fetchEvolution();
  }, [fetchTwin, fetchEvolution]);

  const runSimulation = async () => {
    setSimLoading(true);
    try {
      const body: Record<string, string | number> = { type: simType };
      if (simType === 'key_person_departure') body.role = simRole;
      if (simType === 'engagement_shift') body.shift_pct = simShift;
      if (simType === 'rapid_growth') body.growth_pct = simGrowth;

      const { data } = await axios.post<SimulationResult>(
        `/api/v1/org-digital-twin/default/simulate`,
        body
      );
      setSimResult(data);
    } catch {
      setSimResult(null);
    } finally {
      setSimLoading(false);
    }
  };

  // ── Loading ──

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Building organizational digital twin...</p>
        </div>
      </div>
    );
  }

  // ── Empty State ──

  if (!twin) {
    return (
      <div className="space-y-6">
        <Header onRefresh={() => fetchTwin(true)} />
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🏗</div>
          <h3 className="text-lg font-semibold text-white mb-2">Digital Twin Not Yet Initialized</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Complete team assessments, collaboration surveys, and connect HRIS data
            to build the organizational digital twin.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Header onRefresh={() => fetchTwin(true)} version={twin.version} computedAt={twin.computed_at} />

      {/* Overall Health Ring */}
      <div className="bg-gradient-to-r from-violet-900/30 to-indigo-900/30 border border-violet-500/30 rounded-xl p-6">
        <div className="flex items-center gap-8">
          <div className="flex-shrink-0">
            <div className="relative w-28 h-28">
              <svg className="w-28 h-28 -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none" stroke="#334155" strokeWidth="10" />
                <circle
                  cx="60" cy="60" r="52" fill="none"
                  stroke={twin.overall_health_score >= 70 ? '#10b981' : twin.overall_health_score >= 45 ? '#3b82f6' : '#ef4444'}
                  strokeWidth="10"
                  strokeLinecap="round"
                  strokeDasharray={`${twin.overall_health_score * 3.27} 327`}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-2xl font-bold ${scoreColor(twin.overall_health_score)}`}>
                  {twin.overall_health_score.toFixed(0)}
                </span>
                <span className="text-xs text-slate-500">/ 100</span>
              </div>
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-lg font-semibold text-white">Organizational Health</h3>
              <span className={`text-sm font-medium ${trendColor(twin.overall_trend)}`}>
                {trendIcon(twin.overall_trend)} {twin.overall_trend}
              </span>
            </div>
            <p className="text-slate-400 text-sm mb-3">
              Living model combining 7 dimensions across teams, network, performance, and culture.
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(twin.data_sources).map(([k, v]) => (
                <span
                  key={k}
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    v ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-700 text-slate-500'
                  }`}
                >
                  {v ? '●' : '○'} {k.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        {([
          { key: 'overview', label: 'Overview' },
          { key: 'dimensions', label: 'Dimensions' },
          { key: 'evolution', label: 'Evolution' },
          { key: 'simulate', label: 'What-If Simulator' },
        ] as const).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-5 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-violet-400 border-b-2 border-violet-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Overview Tab ── */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* 7 Dimension Score Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {DIMENSIONS.map((dim) => {
              const d = twin.dimensions[dim.key as keyof typeof twin.dimensions];
              const effective = dim.key === 'turnover_risk' ? d.score : d.score;
              return (
                <button
                  key={dim.key}
                  onClick={() => { setExpandedDim(expandedDim === dim.key ? null : dim.key); setActiveTab('dimensions'); }}
                  className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center hover:border-violet-500/40 transition-colors"
                >
                  <div className="text-2xl mb-1">{dim.icon}</div>
                  <div className="text-xs text-slate-400 mb-1">{dim.label}</div>
                  <div className={`text-xl font-bold ${scoreColor(effective)}`}>
                    {d.score.toFixed(0)}
                  </div>
                  <div className="mt-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${scoreBg(effective)}`}
                      style={{ width: `${Math.min(d.score, 100)}%` }}
                    />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Interconnection Insights */}
          {twin.interconnections && twin.interconnections.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-white">Interconnection Insights</h3>
              {twin.interconnections.map((insight, i) => (
                <div
                  key={i}
                  className={`border rounded-xl p-4 ${severityBorder(insight.severity)}`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-slate-400 uppercase">
                      {insight.type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-slate-600">|</span>
                    {insight.dimensions.map((d) => (
                      <span key={d} className="text-xs bg-slate-700/50 px-2 py-0.5 rounded-full text-slate-300">
                        {d.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">{insight.narrative}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Dimensions Tab ── */}
      {activeTab === 'dimensions' && (
        <div className="space-y-3">
          {DIMENSIONS.map((dim) => {
            const d = twin.dimensions[dim.key as keyof typeof twin.dimensions];
            const isExpanded = expandedDim === dim.key;
            return (
              <div
                key={dim.key}
                className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setExpandedDim(isExpanded ? null : dim.key)}
                  className="w-full flex items-center gap-4 p-4 hover:bg-slate-700/20 transition-colors text-left"
                >
                  <span className="text-2xl">{dim.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium">{dim.label}</span>
                      <span className="text-xs text-slate-500">{dim.desc}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${scoreBg(d.score)}`}
                        style={{ width: `${Math.min(d.score, 100)}%` }}
                      />
                    </div>
                    <span className={`text-lg font-bold w-10 text-right ${scoreColor(d.score)}`}>
                      {d.score.toFixed(0)}
                    </span>
                    <svg
                      className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-slate-700/50 p-4 space-y-3">
                    {/* Highlights */}
                    {d.highlights.map((h, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <span className="text-violet-400 mt-0.5">●</span>
                        <span>{h}</span>
                      </div>
                    ))}

                    {/* Sub-metrics */}
                    {d.sub_metrics && Object.keys(d.sub_metrics).length > 0 && (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-3">
                        {Object.entries(d.sub_metrics).map(([k, v]) => (
                          <div key={k} className="bg-slate-900/50 rounded-lg p-2">
                            <div className="text-xs text-slate-500">{k.replace(/_/g, ' ')}</div>
                            <div className="text-sm font-medium text-slate-200">
                              {typeof v === 'number' ? v.toFixed(1) : String(v)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Evolution Tab ── */}
      {activeTab === 'evolution' && (
        <div className="space-y-4">
          {evolution.length === 0 ? (
            <div className="text-center py-10 text-slate-500 text-sm">
              Only one snapshot exists. Recompute over time to see temporal evolution.
            </div>
          ) : (
            <>
              <p className="text-slate-400 text-sm">
                {evolution.length} snapshot(s) — most recent first
              </p>
              <div className="space-y-2">
                {[...evolution].reverse().map((point, i) => (
                  <div
                    key={point.version}
                    className="bg-slate-800/50 border border-slate-700 rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-xs bg-slate-700 px-2 py-0.5 rounded-full text-slate-300">
                          v{point.version}
                        </span>
                        <span className="text-xs text-slate-500">
                          {new Date(point.computed_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-lg font-bold ${scoreColor(point.overall_health_score)}`}>
                          {point.overall_health_score.toFixed(0)}
                        </span>
                        <span className={`text-sm ${trendColor(point.overall_trend)}`}>
                          {trendIcon(point.overall_trend)}
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-7 gap-2">
                      {DIMENSIONS.map((dim) => {
                        const val = point.scores[dim.key] ?? 0;
                        const prevPoint = evolution[evolution.length - 1 - i - 1];
                        const prevVal = prevPoint?.scores[dim.key] ?? val;
                        const delta = val - prevVal;
                        return (
                          <div key={dim.key} className="text-center">
                            <div className="text-xs text-slate-500">{dim.icon}</div>
                            <div className={`text-sm font-medium ${scoreColor(val)}`}>
                              {val.toFixed(0)}
                            </div>
                            {i > 0 && Math.abs(delta) > 0.5 && (
                              <div className={`text-xs ${deltaColor(delta)}`}>
                                {delta > 0 ? '+' : ''}{delta.toFixed(0)}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Simulate Tab ── */}
      {activeTab === 'simulate' && (
        <div className="space-y-6">
          {/* Scenario Selector */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {SCENARIOS.map((s) => (
              <button
                key={s.type}
                onClick={() => { setSimType(s.type); setSimResult(null); }}
                className={`border rounded-xl p-4 text-left transition-colors ${
                  simType === s.type
                    ? 'border-violet-500 bg-violet-900/20'
                    : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                }`}
              >
                <div className="text-2xl mb-2">{s.icon}</div>
                <div className="text-sm font-medium text-white">{s.label}</div>
                <div className="text-xs text-slate-400 mt-1">{s.desc}</div>
              </button>
            ))}
          </div>

          {/* Scenario Parameters */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
            <h4 className="text-sm font-semibold text-white mb-4">Scenario Parameters</h4>

            {simType === 'key_person_departure' && (
              <div>
                <label className="text-xs text-slate-400 block mb-1">Who leaves?</label>
                <select
                  value={simRole}
                  onChange={(e) => setSimRole(e.target.value)}
                  className="bg-slate-900 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm w-full max-w-xs"
                >
                  <option value="manager">Manager (leadership role)</option>
                  <option value="influencer">Network Influencer (high centrality)</option>
                  <option value="bridge">Cross-Team Bridge (connector)</option>
                  <option value="member">Regular Team Member</option>
                </select>
              </div>
            )}

            {simType === 'engagement_shift' && (
              <div>
                <label className="text-xs text-slate-400 block mb-1">
                  Engagement change: {simShift > 0 ? '+' : ''}{simShift}%
                </label>
                <input
                  type="range"
                  min={-30}
                  max={30}
                  value={simShift}
                  onChange={(e) => setSimShift(Number(e.target.value))}
                  className="w-full max-w-xs"
                />
                <div className="flex justify-between text-xs text-slate-500 max-w-xs">
                  <span>-30%</span><span>0</span><span>+30%</span>
                </div>
              </div>
            )}

            {simType === 'rapid_growth' && (
              <div>
                <label className="text-xs text-slate-400 block mb-1">
                  Headcount growth: +{simGrowth}%
                </label>
                <input
                  type="range"
                  min={10}
                  max={100}
                  value={simGrowth}
                  onChange={(e) => setSimGrowth(Number(e.target.value))}
                  className="w-full max-w-xs"
                />
                <div className="flex justify-between text-xs text-slate-500 max-w-xs">
                  <span>10%</span><span>50%</span><span>100%</span>
                </div>
              </div>
            )}

            {simType === 'team_merge' && (
              <p className="text-xs text-slate-400">
                Simulates short-term impact of combining two teams into one.
              </p>
            )}

            <button
              onClick={runSimulation}
              disabled={simLoading}
              className="mt-4 px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 text-white rounded-lg text-sm transition-colors"
            >
              {simLoading ? 'Simulating...' : 'Run Simulation'}
            </button>
          </div>

          {/* Simulation Results */}
          {simResult && !simResult.error && (
            <div className="bg-slate-800/50 border border-violet-500/30 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white">Simulation Results</h4>
                <span className="text-xs text-slate-400">
                  Confidence: {(simResult.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/50 rounded-lg p-3">
                {simResult.risk_narrative}
              </p>

              {/* Delta Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {DIMENSIONS.map((dim) => {
                  const delta = simResult.deltas[dim.key] ?? 0;
                  const predicted = simResult.predicted[dim.key] ?? 0;
                  return (
                    <div key={dim.key} className="bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-center">
                      <div className="text-lg mb-1">{dim.icon}</div>
                      <div className="text-xs text-slate-400">{dim.label}</div>
                      <div className={`text-lg font-bold ${scoreColor(predicted)}`}>
                        {predicted.toFixed(0)}
                      </div>
                      {Math.abs(delta) > 0.1 && (
                        <div className={`text-xs font-medium ${deltaColor(delta)}`}>
                          {delta > 0 ? '+' : ''}{delta.toFixed(1)}
                        </div>
                      )}
                    </div>
                  );
                })}
                {/* Overall */}
                <div className="bg-slate-900/50 border border-violet-500/30 rounded-lg p-3 text-center">
                  <div className="text-lg mb-1">🏢</div>
                  <div className="text-xs text-slate-400">Overall</div>
                  <div className={`text-lg font-bold ${scoreColor(simResult.predicted.overall ?? 0)}`}>
                    {(simResult.predicted.overall ?? 0).toFixed(0)}
                  </div>
                  {Math.abs(simResult.deltas.overall ?? 0) > 0.1 && (
                    <div className={`text-xs font-medium ${deltaColor(simResult.deltas.overall ?? 0)}`}>
                      {(simResult.deltas.overall ?? 0) > 0 ? '+' : ''}{(simResult.deltas.overall ?? 0).toFixed(1)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Header ──

function Header({
  onRefresh,
  version,
  computedAt,
}: {
  onRefresh: () => void;
  version?: number;
  computedAt?: string;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-white">Organizational Digital Twin</h1>
        <p className="text-slate-400 text-sm mt-1">
          Living model: teams + managers + collaboration + performance + turnover + engagement + culture
        </p>
      </div>
      <div className="flex items-center gap-3">
        {version && (
          <span className="text-xs text-slate-500">
            v{version} | {computedAt ? new Date(computedAt).toLocaleString() : ''}
          </span>
        )}
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm transition-colors"
        >
          Recompute
        </button>
      </div>
    </div>
  );
}
