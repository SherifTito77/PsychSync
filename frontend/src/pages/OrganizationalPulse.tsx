import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

// ── Types ───────────────────────────────────────────────────────────

interface QuestionAnswer {
  question: string;
  answer: Record<string, unknown>[];
  count: number;
}

interface EarlyWarning {
  type: string;
  severity: string;
  team_name: string;
  message: string;
}

interface Intervention {
  priority: number;
  category: string;
  team_name: string;
  team_id?: string;
  action: string;
  details: string;
  expected_impact: string;
  urgency: string;
}

interface PulseData {
  organization_id: string;
  computed_at: string;
  overall_pulse_score: number;
  overall_trend: string;
  total_teams_analyzed: number;
  teams_at_risk: number;
  active_alerts: number;
  interventions_recommended: number;
  narrative: string;
  questions: {
    isolated_teams: QuestionAnswer;
    manager_burnout: QuestionAnswer;
    collaboration_effectiveness: QuestionAnswer;
    friction_trends: QuestionAnswer;
    flight_risk: QuestionAnswer;
    change_impact: QuestionAnswer;
    interventions: QuestionAnswer;
  };
  early_warnings: EarlyWarning[];
  computation_time_ms: number;
  data_sources: {
    behavioral_intelligence: boolean;
    network_analysis: boolean;
    temporal_snapshots: boolean;
  };
}

// ── Helpers ─────────────────────────────────────────────────────────

function pulseColor(score: number): string {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 55) return 'text-blue-400';
  if (score >= 35) return 'text-amber-400';
  return 'text-red-400';
}

function pulseBg(score: number): string {
  if (score >= 75) return 'from-emerald-900/30 to-emerald-800/20 border-emerald-500/30';
  if (score >= 55) return 'from-blue-900/30 to-blue-800/20 border-blue-500/30';
  if (score >= 35) return 'from-amber-900/30 to-amber-800/20 border-amber-500/30';
  return 'from-red-900/30 to-red-800/20 border-red-500/30';
}

function trendIcon(trend: string): string {
  switch (trend) {
    case 'improving': return '\u2191';
    case 'declining': return '\u2193';
    case 'critical': return '\u2193\u2193';
    default: return '\u2192';
  }
}

function trendColor(trend: string): string {
  switch (trend) {
    case 'improving': return 'text-emerald-400';
    case 'declining': return 'text-amber-400';
    case 'critical': return 'text-red-400';
    default: return 'text-slate-400';
  }
}

function severityBadge(severity: string): string {
  switch (severity) {
    case 'critical': return 'bg-red-500/20 text-red-300 border-red-500/30';
    case 'high': return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
    case 'moderate': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
    default: return 'bg-slate-500/20 text-slate-300 border-slate-500/30';
  }
}

function urgencyLabel(urgency: string): string {
  switch (urgency) {
    case 'immediate': return 'Act Now';
    case 'this_week': return 'This Week';
    case 'this_month': return 'This Month';
    default: return urgency;
  }
}

function urgencyColor(urgency: string): string {
  switch (urgency) {
    case 'immediate': return 'bg-red-500/20 text-red-300';
    case 'this_week': return 'bg-amber-500/20 text-amber-300';
    case 'this_month': return 'bg-blue-500/20 text-blue-300';
    default: return 'bg-slate-500/20 text-slate-300';
  }
}

function categoryIcon(category: string): string {
  switch (category) {
    case 'isolation': return '\uD83D\uDD17';
    case 'manager_effectiveness': return '\uD83D\uDC54';
    case 'retention': return '\uD83D\uDEA8';
    case 'friction_reduction': return '\u2699\uFE0F';
    case 'change_readiness': return '\uD83D\uDD04';
    default: return '\uD83D\uDCA1';
  }
}

const QUESTION_META: Record<string, { icon: string; color: string; label: string }> = {
  isolated_teams:              { icon: '\uD83D\uDD17', color: 'text-red-400',     label: 'Team Isolation' },
  manager_burnout:             { icon: '\uD83D\uDC54', color: 'text-orange-400',  label: 'Manager Burnout' },
  collaboration_effectiveness: { icon: '\uD83E\uDD1D', color: 'text-emerald-400', label: 'Collaboration' },
  friction_trends:             { icon: '\u26A1',       color: 'text-amber-400',   label: 'Friction Trends' },
  flight_risk:                 { icon: '\uD83D\uDEA8', color: 'text-red-400',     label: 'Flight Risk' },
  change_impact:               { icon: '\uD83D\uDD04', color: 'text-violet-400',  label: 'Change Impact' },
  interventions:               { icon: '\uD83D\uDCA1', color: 'text-cyan-400',    label: 'Interventions' },
};

interface HistoryPoint {
  date: string;
  pulse_score: number;
  trend: string;
  teams_analyzed: number;
  teams_at_risk: number;
  active_alerts: number;
  interventions: number;
}

// ── Component ───────────────────────────────────────────────────────

type Tab = 'pulse' | 'questions' | 'warnings' | 'interventions';

export default function OrganizationalPulse() {
  const [pulse, setPulse] = useState<PulseData | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [lookbackDays, setLookbackDays] = useState(45);
  const [activeTab, setActiveTab] = useState<Tab>('pulse');
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);

  const fetchPulse = useCallback(async () => {
    setLoading(true);
    try {
      const [pulseRes, historyRes] = await Promise.all([
        axios.get<PulseData>(`/api/v1/pulse/default`, { params: { lookback_days: lookbackDays } }),
        axios.get<HistoryPoint[]>(`/api/v1/pulse/default/history`, { params: { days: 90 } }).catch(() => ({ data: [] as HistoryPoint[] })),
      ]);
      setPulse(pulseRes.data);
      setHistory(historyRes.data);
    } catch {
      setPulse(null);
    } finally {
      setLoading(false);
    }
  }, [lookbackDays]);

  useEffect(() => { fetchPulse(); }, [fetchPulse]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Computing organizational pulse...</p>
        </div>
      </div>
    );
  }

  if (!pulse) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4 max-w-md">
          <div className="text-4xl">💓</div>
          <h2 className="text-lg font-semibold text-white">No Pulse Data Available</h2>
          <p className="text-slate-400 text-sm">
            The Organizational Pulse requires team assessment data to generate predictions.
            Ensure at least one team has completed assessments within the lookback window.
          </p>
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-4 text-left text-xs text-slate-500 space-y-1">
            <div>Checklist:</div>
            <div>1. Teams exist with members assigned</div>
            <div>2. Members have completed assessments</div>
            <div>3. Lookback window covers the assessment period</div>
          </div>
          <button onClick={fetchPulse} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: 'pulse', label: 'Pulse Overview' },
    { key: 'questions', label: '7 Key Questions' },
    { key: 'warnings', label: 'Early Warnings', count: pulse.active_alerts },
    { key: 'interventions', label: 'Interventions', count: pulse.interventions_recommended },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Organizational Pulse</h1>
          <p className="text-slate-400 text-sm mt-1">
            Predictive behavioral intelligence — answers before you ask the questions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={lookbackDays}
            onChange={(e) => setLookbackDays(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={45}>45 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
          </select>
          <button
            onClick={fetchPulse}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Pulse Score Hero */}
      <div className={`bg-gradient-to-r ${pulseBg(pulse.overall_pulse_score)} border rounded-xl p-6`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className={`text-5xl font-bold ${pulseColor(pulse.overall_pulse_score)}`}>
                {Math.round(pulse.overall_pulse_score)}
              </div>
              <div className="text-xs text-slate-400 mt-1">PULSE SCORE</div>
              <div className={`text-xs mt-0.5 ${pulseColor(pulse.overall_pulse_score)}`}>
                {pulse.overall_pulse_score >= 75 ? 'Healthy' : pulse.overall_pulse_score >= 55 ? 'Stable' : pulse.overall_pulse_score >= 35 ? 'At Risk' : 'Critical'}
              </div>
            </div>
            <div className={`flex items-center gap-2 ${trendColor(pulse.overall_trend)}`}>
              <span className="text-2xl">{trendIcon(pulse.overall_trend)}</span>
              <span className="text-sm font-medium capitalize">{pulse.overall_trend}</span>
            </div>
          </div>

          <div className="flex items-center gap-8 text-center">
            <div>
              <div className="text-2xl font-bold text-white">{pulse.total_teams_analyzed}</div>
              <div className="text-xs text-slate-400">Teams Analyzed</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${pulse.teams_at_risk > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {pulse.teams_at_risk}
              </div>
              <div className="text-xs text-slate-400">Teams at Risk</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${pulse.active_alerts > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {pulse.active_alerts}
              </div>
              <div className="text-xs text-slate-400">Active Alerts</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-cyan-400">{pulse.interventions_recommended}</div>
              <div className="text-xs text-slate-400">Interventions</div>
            </div>
          </div>
        </div>

        {/* Data source indicators */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>Computed: {new Date(pulse.computed_at).toLocaleString()}</span>
            <span>{pulse.computation_time_ms}ms</span>
            {pulse.data_sources.behavioral_intelligence && <span className="text-emerald-500">BI</span>}
            {pulse.data_sources.network_analysis && <span className="text-emerald-500">ONA</span>}
            {pulse.data_sources.temporal_snapshots && <span className="text-emerald-500">Temporal</span>}
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> 75+ Healthy</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> 55-74 Stable</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> 35-54 At Risk</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> &lt;35 Critical</span>
          </div>
        </div>
      </div>

      {/* Executive Narrative */}
      {pulse.narrative && (
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">
            Pulse Intelligence Brief
          </h3>
          <p className="text-sm text-slate-200 leading-relaxed">{pulse.narrative}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-700 flex gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
              activeTab === tab.key
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
            {tab.count != null && tab.count > 0 && (
              <span className="ml-2 px-1.5 py-0.5 text-xs rounded-full bg-red-500/20 text-red-300">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'pulse' && <PulseOverview pulse={pulse} history={history} />}
      {activeTab === 'questions' && (
        <QuestionsView
          questions={pulse.questions}
          expanded={expandedQuestion}
          onToggle={(key) => setExpandedQuestion(expandedQuestion === key ? null : key)}
        />
      )}
      {activeTab === 'warnings' && <WarningsView warnings={pulse.early_warnings} />}
      {activeTab === 'interventions' && (
        <InterventionsView interventions={pulse.questions.interventions.answer as unknown as Intervention[]} />
      )}
    </div>
  );
}

// ── Pulse Overview ──────────────────────────────────────────────────

function PulseOverview({ pulse, history }: { pulse: PulseData; history: HistoryPoint[] }) {
  const questionKeys = Object.keys(pulse.questions) as (keyof PulseData['questions'])[];

  return (
    <div className="space-y-6">
      {/* Pulse History Trend */}
      {history.length > 1 && (
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Pulse Trend (Last 90 Days)</h3>
          <div className="flex items-end gap-1 h-24">
            {history.map((point, i) => {
              const height = Math.max(4, point.pulse_score);
              const color = point.pulse_score >= 75 ? 'bg-emerald-500'
                : point.pulse_score >= 55 ? 'bg-blue-500'
                : point.pulse_score >= 35 ? 'bg-amber-500'
                : 'bg-red-500';
              return (
                <div
                  key={i}
                  className="flex-1 group relative"
                  style={{ height: '100%', display: 'flex', alignItems: 'flex-end' }}
                >
                  <div
                    className={`w-full ${color} rounded-t opacity-80 hover:opacity-100 transition-opacity min-w-[3px]`}
                    style={{ height: `${height}%` }}
                  />
                  <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs text-white whitespace-nowrap z-10">
                    <div>{new Date(point.date).toLocaleDateString()}</div>
                    <div>Pulse: {Math.round(point.pulse_score)}</div>
                    <div>At Risk: {point.teams_at_risk}</div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-xs text-slate-500 mt-2">
            <span>{new Date(history[0].date).toLocaleDateString()}</span>
            <span>{new Date(history[history.length - 1].date).toLocaleDateString()}</span>
          </div>
        </div>
      )}

      {/* 7 Questions Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {questionKeys.filter(k => k !== 'interventions').map((key) => {
          const q = pulse.questions[key];
          const meta = QUESTION_META[key];
          const isPositive = key === 'collaboration_effectiveness';
          return (
            <div key={key} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{meta.icon}</span>
                <span className={`text-sm font-medium ${meta.color}`}>{meta.label}</span>
              </div>
              <div className="text-2xl font-bold text-white mb-1">{q.count}</div>
              <p className="text-xs text-slate-400">
                {isPositive
                  ? `${q.count} teams ranked`
                  : q.count === 0
                    ? 'No issues detected'
                    : `${q.count} ${q.count === 1 ? 'team' : 'teams'} flagged`}
              </p>
            </div>
          );
        })}

        {/* Interventions card */}
        <div className="bg-gradient-to-br from-cyan-900/30 to-cyan-800/20 border border-cyan-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">{QUESTION_META.interventions.icon}</span>
            <span className="text-sm font-medium text-cyan-400">Interventions</span>
          </div>
          <div className="text-2xl font-bold text-white mb-1">{pulse.interventions_recommended}</div>
          <p className="text-xs text-slate-400">Proactive actions recommended</p>
        </div>
      </div>

      {/* Top Early Warnings */}
      {pulse.early_warnings.length > 0 && (
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Priority Alerts</h3>
          <div className="space-y-3">
            {pulse.early_warnings.slice(0, 5).map((w, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className={`px-2 py-0.5 text-xs rounded border ${severityBadge(w.severity)}`}>
                  {w.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-white font-medium">{w.team_name}</span>
                  <p className="text-xs text-slate-400 mt-0.5">{w.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── 7 Questions View ────────────────────────────────────────────────

function QuestionsView({
  questions,
  expanded,
  onToggle,
}: {
  questions: PulseData['questions'];
  expanded: string | null;
  onToggle: (key: string) => void;
}) {
  const questionKeys = Object.keys(questions).filter(k => k !== 'interventions') as (keyof PulseData['questions'])[];

  return (
    <div className="space-y-3">
      {questionKeys.map((key) => {
        const q = questions[key];
        const meta = QUESTION_META[key];
        const isExpanded = expanded === key;
        const answers = q.answer as Record<string, unknown>[];

        return (
          <div key={key} className="bg-slate-800/60 border border-slate-700/50 rounded-xl overflow-hidden">
            <button
              onClick={() => onToggle(key)}
              className="w-full flex items-center justify-between p-4 hover:bg-slate-700/30 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{meta.icon}</span>
                <div>
                  <div className={`text-sm font-medium ${meta.color}`}>{meta.label}</div>
                  <div className="text-xs text-slate-400">{q.question}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-lg font-bold ${q.count > 0 ? meta.color : 'text-slate-500'}`}>
                  {q.count}
                </span>
                <span className="text-slate-500 text-sm">{isExpanded ? '\u25B2' : '\u25BC'}</span>
              </div>
            </button>

            {isExpanded && (
              <div className="border-t border-slate-700/50 p-4">
                {answers.length === 0 ? (
                  <p className="text-sm text-slate-500 italic">No issues detected in this area.</p>
                ) : (
                  <div className="space-y-3">
                    {answers.map((item, i) => (
                      <QuestionDetailItem key={i} item={item} questionKey={key} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function QuestionDetailItem({ item, questionKey }: { item: Record<string, unknown>; questionKey: string }) {
  const teamName = (item.team_name as string) || 'Unknown';
  const severity = (item.severity as string) || (item.risk_level as string) || (item.status as string) || '';
  const signal = (item.signal as string) || '';
  const score = (item.collaboration_score as number)
    ?? (item.friction_score as number)
    ?? (item.flight_risk_score as number)
    ?? (item.vulnerability_score as number)
    ?? (item.composite_score as number)
    ?? null;

  return (
    <div className="flex items-start gap-3 bg-slate-900/40 rounded-lg p-3">
      {severity && (
        <span className={`px-2 py-0.5 text-xs rounded border shrink-0 ${severityBadge(severity)}`}>
          {severity}
        </span>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">{teamName}</span>
          {score !== null && (
            <span className="text-xs text-slate-400">{Math.round(score as number)}/100</span>
          )}
        </div>
        {signal && <p className="text-xs text-slate-400 mt-1">{signal}</p>}

        {/* Risk scenarios for change impact */}
        {questionKey === 'change_impact' && Array.isArray(item.risk_scenarios) && (
          <div className="mt-2 space-y-1">
            {(item.risk_scenarios as Record<string, string>[]).map((s, j) => (
              <div key={j} className="text-xs text-slate-500">
                <span className="text-slate-400">{s.scenario}:</span> {s.impact}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Early Warnings View ─────────────────────────────────────────────

function WarningsView({ warnings }: { warnings: EarlyWarning[] }) {
  if (warnings.length === 0) {
    return (
      <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-8 text-center">
        <p className="text-emerald-400 text-lg font-medium">All Clear</p>
        <p className="text-slate-400 text-sm mt-1">No early warnings detected. Organization is healthy.</p>
      </div>
    );
  }

  const grouped = warnings.reduce<Record<string, EarlyWarning[]>>((acc, w) => {
    acc[w.type] = acc[w.type] || [];
    acc[w.type].push(w);
    return acc;
  }, {});

  const typeLabels: Record<string, string> = {
    isolation: 'Team Isolation',
    manager_burnout: 'Manager-Attributed Burnout',
    friction: 'Organizational Friction',
    flight_risk: 'Talent Flight Risk',
  };

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([type, items]) => (
        <div key={type} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">
            {typeLabels[type] || type} ({items.length})
          </h3>
          <div className="space-y-3">
            {items.map((w, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className={`px-2 py-0.5 text-xs rounded border shrink-0 ${severityBadge(w.severity)}`}>
                  {w.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-white font-medium">{w.team_name}</span>
                  <p className="text-xs text-slate-400 mt-0.5">{w.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Interventions View ──────────────────────────────────────────────

function InterventionsView({ interventions }: { interventions: Intervention[] }) {
  if (!interventions || interventions.length === 0) {
    return (
      <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-8 text-center">
        <p className="text-emerald-400 text-lg font-medium">No Interventions Needed</p>
        <p className="text-slate-400 text-sm mt-1">All teams are operating within healthy parameters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {interventions.map((intervention, i) => (
        <div key={i} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <span className="text-lg">{categoryIcon(intervention.category)}</span>
              <div>
                <div className="text-sm font-medium text-white">{intervention.action}</div>
                <div className="text-xs text-slate-400">{intervention.team_name}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 text-xs rounded ${urgencyColor(intervention.urgency)}`}>
                {urgencyLabel(intervention.urgency)}
              </span>
              <span className="text-xs text-slate-500">P{intervention.priority}</span>
            </div>
          </div>

          <p className="text-sm text-slate-300 mb-3">{intervention.details}</p>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>Expected:</span>
            <span className="text-cyan-400">{intervention.expected_impact}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
