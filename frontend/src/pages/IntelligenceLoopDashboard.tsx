import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../api/axios';

// ── Types ───────────────────────────────────────────────────────────

interface DataSource {
  name: string;
  connected: boolean;
  signal_count: number;
  health: 'healthy' | 'stale' | 'missing' | 'error';
}

interface Risk {
  risk_id: string;
  risk_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  severity_score: number;
  title: string;
  explanation: string;
  contributing_signals: string[];
  affected_scope: string;
  affected_name: string;
  recommendation: string;
}

interface ImprovementMetric {
  metric_name: string;
  baseline_value: number;
  current_value: number;
  delta: number;
  delta_percent: number;
  direction: 'improving' | 'stable' | 'worsening';
}

interface CycleData {
  org_id: string;
  cycle_timestamp: string;
  cycle_duration_ms: number;
  data_sources: DataSource[];
  total_signals_collected: number;
  signal_summary: Record<string, number>;
  network_health: number;
  network_signal_count: number;
  risks: Risk[];
  risk_summary: Record<string, number>;
  narrative_summary: string;
  active_interventions: number;
  improvement_metrics: ImprovementMetric[];
  overall_health_score: number;
}

// ── Pipeline stages ─────────────────────────────────────────────────

const PIPELINE_STAGES = [
  'Connect', 'Collect', 'Normalize', 'Network',
  'Patterns', 'Risks', 'Explain', 'Intervene', 'Measure',
] as const;

// ── Severity helpers ────────────────────────────────────────────────

const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

function severityBadgeClass(severity: string): string {
  switch (severity) {
    case 'critical': return 'bg-red-500/20 text-red-300 border-red-500/30';
    case 'high':     return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
    case 'medium':   return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    case 'low':      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    default:         return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  }
}

function healthScoreColor(score: number): string {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 55) return 'text-blue-400';
  if (score >= 35) return 'text-amber-400';
  return 'text-red-400';
}

function healthScoreBg(score: number): string {
  if (score >= 75) return 'from-emerald-900/30 to-emerald-800/20 border-emerald-500/30';
  if (score >= 55) return 'from-blue-900/30 to-blue-800/20 border-blue-500/30';
  if (score >= 35) return 'from-amber-900/30 to-amber-800/20 border-amber-500/30';
  return 'from-red-900/30 to-red-800/20 border-red-500/30';
}

function healthLabel(score: number): string {
  if (score >= 75) return 'Healthy';
  if (score >= 55) return 'Stable';
  if (score >= 35) return 'At Risk';
  return 'Critical';
}

function sourceHealthDot(health: string): string {
  switch (health) {
    case 'healthy': return 'bg-emerald-400';
    case 'stale':   return 'bg-amber-400';
    case 'missing': return 'bg-slate-500';
    case 'error':   return 'bg-red-400';
    default:        return 'bg-slate-500';
  }
}

const SOURCE_ICONS: Record<string, string> = {
  hris: 'H',  calendar: 'Ca', slack: 'Sl', teams: 'Te',
  email: 'Em', git: 'Gi',     badge: 'Bd', pto: 'PT',
  project_management: 'PM',
};

// Signal bar color: some categories are "higher = worse"
const INVERTED_SIGNALS = new Set(['workload', 'wellbeing']);

function signalBarColor(category: string, score: number): string {
  const inverted = INVERTED_SIGNALS.has(category);
  if (inverted) {
    if (score >= 70) return 'bg-red-500';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-emerald-500';
  }
  if (score >= 70) return 'bg-emerald-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-red-500';
}

const SIGNAL_LABELS: Record<string, string> = {
  workload: 'Workload Pressure',
  collaboration: 'Collaboration',
  wellbeing: 'Wellbeing Concerns',
  lifecycle: 'Employee Lifecycle',
  knowledge: 'Knowledge Sharing',
};

// ── Component ───────────────────────────────────────────────────────

export default function IntelligenceLoopDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<CycleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState<string>('all');

  const orgId = 'default';

  const fetchCycle = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get<CycleData>(`/api/v1/intelligence/${orgId}/cycle`);
      setData(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load intelligence cycle');
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  const runCycle = useCallback(async () => {
    setRunning(true);
    try {
      await axios.post(`/api/v1/intelligence/${orgId}/cycle`);
      await fetchCycle();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to run intelligence cycle');
    } finally {
      setRunning(false);
    }
  }, [orgId, fetchCycle]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get<CycleData>(`/api/v1/intelligence/${orgId}/cycle`);
        if (!cancelled) setData(res.data);
      } catch (err: any) {
        if (!cancelled) setError(err?.response?.data?.detail || 'Failed to load intelligence cycle');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [orgId]);

  // ── Loading state ───────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Loading intelligence cycle...</p>
        </div>
      </div>
    );
  }

  // ── Error state ─────────────────────────────────────────────────
  if (error && !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4 max-w-md">
          <h2 className="text-lg font-semibold text-white">Intelligence Loop Unavailable</h2>
          <p className="text-slate-400 text-sm">{error}</p>
          <button
            onClick={fetchCycle}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const sortedRisks = [...data.risks].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9),
  );
  const filteredRisks = riskFilter === 'all'
    ? sortedRisks
    : sortedRisks.filter(r => r.severity === riskFilter);

  const totalRisks = data.risks.length;
  const cycleAgo = formatAgo(data.cycle_timestamp);
  const connectedCount = data.data_sources.filter(s => s.connected).length;
  const signalEntries = Object.entries(data.signal_summary);

  return (
    <div className="space-y-6">
      {/* ────────────────────────────────────────────────────────────
          Section 1: Health Score + Cycle Status
          ──────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Intelligence Loop</h1>
          <p className="text-slate-400 text-sm mt-1">
            Full-cycle command center — from data sources to measured outcomes
          </p>
        </div>
        <button
          onClick={runCycle}
          disabled={running}
          className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          {running ? 'Running...' : 'Run Cycle'}
        </button>
      </div>

      {error && (
        <div className="px-4 py-3 bg-red-900/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Hero score + pipeline */}
      <div className={`bg-gradient-to-r ${healthScoreBg(data.overall_health_score)} border rounded-xl p-6`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="text-center">
              <div className={`text-6xl font-bold ${healthScoreColor(data.overall_health_score)}`}>
                {Math.round(data.overall_health_score)}
              </div>
              <div className="text-xs text-slate-400 mt-1">ORG HEALTH</div>
              <div className={`text-xs font-medium mt-0.5 ${healthScoreColor(data.overall_health_score)}`}>
                {healthLabel(data.overall_health_score)}
              </div>
            </div>
            <div className="text-left space-y-1">
              <div className="text-sm text-slate-300">
                <span className="text-slate-500">Last cycle:</span>{' '}
                <span className="text-white font-medium">{cycleAgo}</span>
                <span className="text-slate-500 ml-2">({data.cycle_duration_ms}ms)</span>
              </div>
              <div className="text-sm text-slate-300">
                <span className="text-slate-500">Sources:</span>{' '}
                <span className="text-white font-medium">{connectedCount}/{data.data_sources.length} connected</span>
              </div>
              <div className="text-sm text-slate-300">
                <span className="text-slate-500">Signals:</span>{' '}
                <span className="text-white font-medium">{data.total_signals_collected} collected</span>
              </div>
            </div>
          </div>

          {/* Summary stats */}
          <div className="flex items-center gap-6 text-center">
            <div>
              <div className={`text-2xl font-bold ${totalRisks > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {totalRisks}
              </div>
              <div className="text-xs text-slate-400">Active Risks</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-cyan-400">{data.active_interventions}</div>
              <div className="text-xs text-slate-400">Interventions</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-400">{data.improvement_metrics.length}</div>
              <div className="text-xs text-slate-400">Metrics Tracked</div>
            </div>
          </div>
        </div>

        {/* Pipeline visualization */}
        <div className="mt-6 flex items-center justify-between">
          {PIPELINE_STAGES.map((stage, i) => {
            const stageComplete = isPipelineStageComplete(stage, data);
            return (
              <div key={stage} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-4 h-4 rounded-full border-2 transition-colors ${
                      stageComplete
                        ? 'bg-emerald-500 border-emerald-400'
                        : 'bg-slate-700 border-slate-600'
                    }`}
                  />
                  <span className={`text-[10px] mt-1.5 font-medium ${
                    stageComplete ? 'text-emerald-400' : 'text-slate-500'
                  }`}>
                    {stage}
                  </span>
                </div>
                {i < PIPELINE_STAGES.length - 1 && (
                  <div className={`w-8 sm:w-12 md:w-16 h-px mx-1 ${
                    stageComplete && isPipelineStageComplete(PIPELINE_STAGES[i + 1], data)
                      ? 'bg-emerald-500/60'
                      : 'bg-slate-700'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          Section 2: Data Sources (Connect & Collect)
          ──────────────────────────────────────────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Data Sources
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {data.data_sources.map((src) => (
            <div
              key={src.name}
              className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 flex flex-col items-center text-center"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-700/80 flex items-center justify-center text-sm font-bold text-slate-300 mb-2">
                {SOURCE_ICONS[src.name] || src.name.slice(0, 2).toUpperCase()}
              </div>
              <div className="flex items-center gap-1.5 mb-1">
                <span className={`w-2 h-2 rounded-full ${sourceHealthDot(src.health)}`} />
                <span className="text-xs font-medium text-white capitalize">{src.name.replace(/_/g, ' ')}</span>
              </div>
              {src.connected ? (
                <span className="text-xs text-slate-400">{src.signal_count} signals</span>
              ) : (
                <span className="text-xs text-slate-500">Not connected</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          Section 3: Signal Summary (Normalize)
          ──────────────────────────────────────────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Signal Summary
        </h2>
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 space-y-4">
          {signalEntries.map(([category, score]) => (
            <div key={category} className="flex items-center gap-4">
              <span className="w-36 text-sm text-slate-300 shrink-0">
                {SIGNAL_LABELS[category] || category.replace(/_/g, ' ')}
              </span>
              <div className="flex-1 bg-slate-700/60 rounded-full h-5 relative overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${signalBarColor(category, score)}`}
                  style={{ width: `${Math.min(score, 100)}%` }}
                />
                <span className="absolute inset-0 flex items-center justify-end pr-2 text-[11px] font-semibold text-white/80">
                  {score}
                </span>
              </div>
            </div>
          ))}

          {/* Network health as a separate bar */}
          <div className="flex items-center gap-4 pt-2 border-t border-slate-700/50">
            <span className="w-36 text-sm text-slate-300 shrink-0">Network Health</span>
            <div className="flex-1 bg-slate-700/60 rounded-full h-5 relative overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  data.network_health >= 70 ? 'bg-emerald-500'
                    : data.network_health >= 40 ? 'bg-amber-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(data.network_health, 100)}%` }}
              />
              <span className="absolute inset-0 flex items-center justify-end pr-2 text-[11px] font-semibold text-white/80">
                {data.network_health}
              </span>
            </div>
            <span className="text-xs text-slate-500 shrink-0">{data.network_signal_count} signals</span>
          </div>
        </div>
      </div>

      {/* ────────────────────────────────────────────────────────────
          Section 4: Active Risks (Patterns + Risks)
          ──────────────────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
            Active Risks
          </h2>
          <div className="flex items-center gap-1">
            {(['all', 'critical', 'high', 'medium', 'low'] as const).map((level) => {
              const count = level === 'all' ? totalRisks : (data.risk_summary[level] ?? 0);
              return (
                <button
                  key={level}
                  onClick={() => setRiskFilter(level)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors capitalize ${
                    riskFilter === level
                      ? level === 'all'
                        ? 'bg-slate-600 border-slate-500 text-white'
                        : severityBadgeClass(level) + ' border'
                      : 'bg-transparent border-slate-700 text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {level} ({count})
                </button>
              );
            })}
          </div>
        </div>

        {filteredRisks.length === 0 ? (
          <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-8 text-center">
            <p className="text-emerald-400 text-lg font-medium">No Risks Detected</p>
            <p className="text-slate-400 text-sm mt-1">
              {riskFilter === 'all'
                ? 'All signals are within healthy parameters.'
                : `No ${riskFilter}-severity risks found.`}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredRisks.map((risk) => (
              <div key={risk.risk_id} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
                <div className="flex items-start gap-3 mb-3">
                  <span className={`px-2.5 py-0.5 text-xs rounded border font-medium uppercase ${severityBadgeClass(risk.severity)}`}>
                    {risk.severity}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-white">{risk.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-500 capitalize">{risk.affected_scope}</span>
                      <span className="text-xs text-slate-600">|</span>
                      <span className="text-xs text-slate-400">{risk.affected_name}</span>
                      <span className="text-xs text-slate-600">|</span>
                      <span className="text-xs text-slate-500">Score: {risk.severity_score}</span>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-slate-300 leading-relaxed mb-3">{risk.explanation}</p>

                {risk.recommendation && (
                  <div className="bg-blue-900/20 border border-blue-500/20 rounded-lg p-3 mb-2">
                    <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider">Recommendation</span>
                    <p className="text-sm text-blue-200 mt-1">{risk.recommendation}</p>
                  </div>
                )}

                {risk.contributing_signals.length > 0 && (
                  <div className="text-xs text-slate-500">
                    {risk.contributing_signals.length} contributing signal{risk.contributing_signals.length !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ────────────────────────────────────────────────────────────
          Section 5: Interventions & Improvement (Intervene + Measure)
          ──────────────────────────────────────────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Interventions & Improvement
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: Active Interventions */}
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 flex flex-col items-center justify-center text-center">
            <div className="text-4xl font-bold text-cyan-400 mb-1">{data.active_interventions}</div>
            <div className="text-sm text-slate-300 mb-4">Active Interventions</div>
            <button
              onClick={() => navigate('/action-plans')}
              className="px-4 py-2 bg-cyan-600/20 border border-cyan-500/30 hover:bg-cyan-600/30 text-cyan-400 rounded-lg text-sm transition-colors"
            >
              View Action Plans
            </button>
          </div>

          {/* Right: Improvement Metrics */}
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Improvement Metrics
            </h3>
            {data.improvement_metrics.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No tracked metrics yet.</p>
            ) : (
              <div className="space-y-3">
                {data.improvement_metrics.map((m, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-white truncate">{m.metric_name}</div>
                      <div className="text-xs text-slate-500">
                        {m.baseline_value} &rarr; {m.current_value}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-3">
                      <span className={`text-sm font-semibold ${directionColor(m.direction)}`}>
                        {directionArrow(m.direction)} {Math.abs(m.delta_percent).toFixed(1)}%
                      </span>
                      <span className={`px-2 py-0.5 text-[10px] rounded-full font-medium uppercase ${directionBadge(m.direction)}`}>
                        {m.direction}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Narrative summary */}
        {data.narrative_summary && (
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 mt-4">
            <h3 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">
              Intelligence Brief
            </h3>
            <blockquote className="border-l-2 border-cyan-500/40 pl-4 text-sm text-slate-200 leading-relaxed italic">
              {data.narrative_summary}
            </blockquote>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Pure helpers ─────────────────────────────────────────────────────

function formatAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 0) return 'just now';
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function isPipelineStageComplete(stage: string, data: CycleData): boolean {
  switch (stage) {
    case 'Connect':   return data.data_sources.some(s => s.connected);
    case 'Collect':   return data.total_signals_collected > 0;
    case 'Normalize': return Object.values(data.signal_summary).some(v => v > 0);
    case 'Network':   return data.network_health > 0;
    case 'Patterns':  return data.risks.length > 0 || data.overall_health_score > 0;
    case 'Risks':     return data.risks.length > 0 || Object.values(data.risk_summary).some(v => v > 0);
    case 'Explain':   return !!data.narrative_summary;
    case 'Intervene': return data.active_interventions > 0;
    case 'Measure':   return data.improvement_metrics.length > 0;
    default:          return false;
  }
}

function directionArrow(d: string): string {
  switch (d) {
    case 'improving': return '\u2193';
    case 'worsening': return '\u2191';
    default:          return '\u2192';
  }
}

function directionColor(d: string): string {
  switch (d) {
    case 'improving': return 'text-emerald-400';
    case 'worsening': return 'text-red-400';
    default:          return 'text-slate-400';
  }
}

function directionBadge(d: string): string {
  switch (d) {
    case 'improving': return 'bg-emerald-500/20 text-emerald-300';
    case 'worsening': return 'bg-red-500/20 text-red-300';
    default:          return 'bg-slate-500/20 text-slate-300';
  }
}
