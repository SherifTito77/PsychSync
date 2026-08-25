import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

// ── Types ──

interface Signal {
  type: string;
  severity: string;
  message: string;
}

interface MemberRisk {
  user_id: string;
  name: string;
  risk_level: string;
  signals: Signal[];
  burnout_risk?: number;
  engagement?: number;
  churn_risk?: number;
  network_role?: { role: string; degree: number; betweenness: number };
}

interface ActionItem {
  priority: string;
  category: string;
  action: string;
  reason: string;
  timeframe: string;
}

interface CoachingPrompt {
  theme: string;
  prompt: string;
  source: string;
}

interface BIScoreData {
  score: number;
  label?: string;
  trend?: string;
  factors?: Record<string, number>;
  recommendations?: string[];
}

interface TeamPulse {
  score: number;
  status: string;
  label: string;
}

interface NetworkInsights {
  available: boolean;
  influencers?: Array<{ user_id: string; name: string; betweenness_centrality: number }>;
  isolated?: Array<{ user_id: string; name: string }>;
  bridges?: Array<{ user_id: string; name: string }>;
  network_density?: number;
}

interface Briefing {
  team_id: string;
  team_name: string;
  organization_id: string;
  member_count: number;
  generated_at: string;
  team_pulse: TeamPulse;
  bi_scores: Record<string, BIScoreData>;
  members: MemberRisk[];
  network_insights: NetworkInsights;
  action_items: ActionItem[];
  coaching_prompts: CoachingPrompt[];
}

interface TeamOption {
  team_id: string;
  team_name: string;
  member_count: number;
}

// ── Constants ──

const BI_LABELS: Record<string, { label: string; icon: string; inverted?: boolean }> = {
  team_health: { label: 'Team Health', icon: '💚' },
  collaboration: { label: 'Collaboration', icon: '🤝' },
  manager_health: { label: 'Manager Health', icon: '👔' },
  psychological_safety: { label: 'Psych Safety', icon: '🛡' },
  change_readiness: { label: 'Change Ready', icon: '🔄' },
  friction_index: { label: 'Friction', icon: '⚡', inverted: true },
  burnout_risk: { label: 'Burnout Risk', icon: '🔥', inverted: true },
};

// ── Helpers ──

function pulseColor(status: string): string {
  switch (status) {
    case 'healthy': return 'text-emerald-400';
    case 'moderate': return 'text-blue-400';
    case 'at_risk': return 'text-amber-400';
    case 'critical': return 'text-red-400';
    default: return 'text-slate-400';
  }
}

function pulseBg(status: string): string {
  switch (status) {
    case 'healthy': return 'bg-emerald-500';
    case 'moderate': return 'bg-blue-500';
    case 'at_risk': return 'bg-amber-500';
    case 'critical': return 'bg-red-500';
    default: return 'bg-slate-500';
  }
}

function riskBadge(level: string): string {
  switch (level) {
    case 'critical': return 'bg-red-500/20 text-red-300 border-red-500/30';
    case 'elevated': return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
    case 'moderate': return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    default: return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
  }
}

function priorityColor(priority: string): string {
  switch (priority) {
    case 'urgent': return 'border-red-500/40 bg-red-500/5';
    case 'high': return 'border-orange-500/40 bg-orange-500/5';
    case 'medium': return 'border-amber-500/40 bg-amber-500/5';
    default: return 'border-slate-700 bg-slate-800/30';
  }
}

function priorityLabel(priority: string): string {
  switch (priority) {
    case 'urgent': return 'bg-red-500/20 text-red-300';
    case 'high': return 'bg-orange-500/20 text-orange-300';
    case 'medium': return 'bg-amber-500/20 text-amber-300';
    default: return 'bg-slate-700 text-slate-300';
  }
}

function scoreColor(score: number): string {
  if (score >= 70) return 'text-emerald-400';
  if (score >= 50) return 'text-blue-400';
  if (score >= 30) return 'text-amber-400';
  return 'text-red-400';
}

function scoreBg(score: number): string {
  if (score >= 70) return 'bg-emerald-500';
  if (score >= 50) return 'bg-blue-500';
  if (score >= 30) return 'bg-amber-500';
  return 'bg-red-500';
}

// ── Component ──

export default function ManagerIntelligence() {
  const [teams, setTeams] = useState<TeamOption[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'members' | 'actions' | 'coaching'>('overview');

  // Fetch teams list
  useEffect(() => {
    (async () => {
      try {
        const { data } = await axios.get<TeamOption[]>('/api/v1/manager-intelligence/teams');
        setTeams(data);
        if (data.length > 0) setSelectedTeam(data[0].team_id);
      } catch {
        setTeams([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Fetch briefing when team changes
  const fetchBriefing = useCallback(async () => {
    if (!selectedTeam) return;
    setLoading(true);
    try {
      const { data } = await axios.get<Briefing>(
        `/api/v1/manager-intelligence/team/${selectedTeam}`
      );
      setBriefing(data);
    } catch {
      setBriefing(null);
    } finally {
      setLoading(false);
    }
  }, [selectedTeam]);

  useEffect(() => { fetchBriefing(); }, [fetchBriefing]);

  // ── Loading ──
  if (loading && !briefing) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Loading manager intelligence...</p>
        </div>
      </div>
    );
  }

  // ── No Teams ──
  if (teams.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Manager Intelligence</h1>
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">👔</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Teams Found</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            You need to be a member of at least one team to access manager intelligence.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Manager Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">
            Your team's health, risks, and action items — powered by behavioral intelligence
          </p>
        </div>
        <div className="flex items-center gap-3">
          {teams.length > 1 && (
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm"
            >
              {teams.map((t) => (
                <option key={t.team_id} value={t.team_id}>
                  {t.team_name} ({t.member_count})
                </option>
              ))}
            </select>
          )}
          <button
            onClick={fetchBriefing}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {briefing && (
        <>
          {/* Team Pulse Banner */}
          <div className="bg-gradient-to-r from-slate-800/80 to-slate-900/80 border border-slate-700 rounded-xl p-6">
            <div className="flex items-center gap-6">
              {/* Pulse Ring */}
              <div className="flex-shrink-0">
                <div className="relative w-24 h-24">
                  <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#334155" strokeWidth="8" />
                    <circle
                      cx="50" cy="50" r="42" fill="none"
                      className={`stroke-current ${pulseColor(briefing.team_pulse.status)}`}
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={`${briefing.team_pulse.score * 2.64} 264`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`text-xl font-bold ${pulseColor(briefing.team_pulse.status)}`}>
                      {briefing.team_pulse.score.toFixed(0)}
                    </span>
                    <span className="text-xs text-slate-500">pulse</span>
                  </div>
                </div>
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-lg font-semibold text-white">{briefing.team_name}</h2>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${riskBadge(
                    briefing.team_pulse.status === 'healthy' ? 'low' :
                    briefing.team_pulse.status === 'critical' ? 'critical' :
                    briefing.team_pulse.status === 'at_risk' ? 'elevated' : 'moderate'
                  )}`}>
                    {briefing.team_pulse.label}
                  </span>
                </div>
                <p className="text-slate-400 text-sm">
                  {briefing.member_count} members | {briefing.action_items.filter(a => a.priority === 'urgent').length} urgent actions
                  {briefing.members.filter(m => m.risk_level === 'critical').length > 0 &&
                    ` | ${briefing.members.filter(m => m.risk_level === 'critical').length} at-risk member(s)`
                  }
                </p>
              </div>

              {/* Quick BI Scores */}
              <div className="hidden lg:grid grid-cols-4 gap-2">
                {Object.entries(briefing.bi_scores).slice(0, 4).map(([key, data]) => {
                  const meta = BI_LABELS[key];
                  if (!meta) return null;
                  const effective = meta.inverted ? 100 - data.score : data.score;
                  return (
                    <div key={key} className="text-center px-2">
                      <div className="text-sm">{meta.icon}</div>
                      <div className={`text-sm font-bold ${scoreColor(effective)}`}>
                        {data.score.toFixed(0)}
                      </div>
                      <div className="text-xs text-slate-500">{meta.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-slate-700">
            {([
              { key: 'overview', label: 'Overview', count: undefined },
              { key: 'members', label: 'Team Members', count: briefing.members.filter(m => m.risk_level !== 'low').length },
              { key: 'actions', label: 'Action Items', count: briefing.action_items.length },
              { key: 'coaching', label: 'Coaching', count: briefing.coaching_prompts.length },
            ] as const).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-5 py-3 text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeTab === tab.key
                    ? 'text-violet-400 border-b-2 border-violet-400'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="text-xs bg-slate-700 rounded-full px-2 py-0.5">{tab.count}</span>
                )}
              </button>
            ))}
          </div>

          {/* ── Overview Tab ── */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* BI Score Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                {Object.entries(briefing.bi_scores).map(([key, data]) => {
                  const meta = BI_LABELS[key];
                  if (!meta) return null;
                  const effective = meta.inverted ? 100 - data.score : data.score;
                  return (
                    <div key={key} className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
                      <div className="text-xl mb-1">{meta.icon}</div>
                      <div className="text-xs text-slate-400 mb-1">{meta.label}</div>
                      <div className={`text-xl font-bold ${scoreColor(effective)}`}>{data.score.toFixed(0)}</div>
                      <div className="mt-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${scoreBg(effective)}`} style={{ width: `${Math.min(data.score, 100)}%` }} />
                      </div>
                      {data.trend && (
                        <div className={`text-xs mt-1 ${data.trend === 'improving' ? 'text-emerald-400' : data.trend === 'declining' ? 'text-red-400' : 'text-slate-500'}`}>
                          {data.trend === 'improving' ? '↑' : data.trend === 'declining' ? '↓' : '→'} {data.trend}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Top Risks Summary */}
              {briefing.members.filter(m => m.risk_level !== 'low').length > 0 && (
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-3">Members Needing Attention</h3>
                  <div className="space-y-2">
                    {briefing.members.filter(m => m.risk_level !== 'low').slice(0, 5).map((m) => (
                      <div key={m.user_id} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            m.risk_level === 'critical' ? 'bg-red-500' :
                            m.risk_level === 'elevated' ? 'bg-orange-500' : 'bg-amber-500'
                          }`} />
                          <span className="text-white text-sm">{m.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {m.signals.slice(0, 2).map((s, i) => (
                            <span key={i} className="text-xs text-slate-400">{s.type}</span>
                          ))}
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${riskBadge(m.risk_level)}`}>
                            {m.risk_level}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Top Action Items */}
              {briefing.action_items.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-white">Priority Actions</h3>
                  {briefing.action_items.slice(0, 3).map((item, i) => (
                    <div key={i} className={`border rounded-xl p-4 ${priorityColor(item.priority)}`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${priorityLabel(item.priority)}`}>
                          {item.priority}
                        </span>
                        <span className="text-xs text-slate-500">{item.timeframe}</span>
                      </div>
                      <p className="text-sm text-slate-200">{item.action}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Network Highlights */}
              {briefing.network_insights.available && (
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-white mb-3">Network Insights</h3>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl mb-1">🌟</div>
                      <div className="text-lg font-bold text-violet-400">
                        {briefing.network_insights.influencers?.length ?? 0}
                      </div>
                      <div className="text-xs text-slate-400">Influencers</div>
                    </div>
                    <div>
                      <div className="text-2xl mb-1">🔗</div>
                      <div className="text-lg font-bold text-teal-400">
                        {briefing.network_insights.bridges?.length ?? 0}
                      </div>
                      <div className="text-xs text-slate-400">Bridges</div>
                    </div>
                    <div>
                      <div className="text-2xl mb-1">🏝</div>
                      <div className="text-lg font-bold text-amber-400">
                        {briefing.network_insights.isolated?.length ?? 0}
                      </div>
                      <div className="text-xs text-slate-400">Isolated</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Members Tab ── */}
          {activeTab === 'members' && (
            <div className="space-y-3">
              {briefing.members.map((m) => (
                <div
                  key={m.user_id}
                  className="bg-slate-800/50 border border-slate-700 rounded-xl p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${
                        m.risk_level === 'critical' ? 'bg-red-500 animate-pulse' :
                        m.risk_level === 'elevated' ? 'bg-orange-500' :
                        m.risk_level === 'moderate' ? 'bg-amber-500' : 'bg-emerald-500'
                      }`} />
                      <span className="text-white font-medium">{m.name}</span>
                      {m.network_role && (
                        <span className="text-xs bg-slate-700 px-2 py-0.5 rounded-full text-slate-300">
                          {m.network_role.role}
                        </span>
                      )}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${riskBadge(m.risk_level)}`}>
                      {m.risk_level}
                    </span>
                  </div>

                  {/* Metric pills */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {m.burnout_risk !== undefined && (
                      <span className={`text-xs px-2 py-1 rounded-lg ${
                        m.burnout_risk > 7 ? 'bg-red-500/10 text-red-400' :
                        m.burnout_risk > 5 ? 'bg-amber-500/10 text-amber-400' :
                        'bg-emerald-500/10 text-emerald-400'
                      }`}>
                        Burnout: {m.burnout_risk.toFixed(1)}/10
                      </span>
                    )}
                    {m.engagement !== undefined && (
                      <span className={`text-xs px-2 py-1 rounded-lg ${
                        m.engagement < 4 ? 'bg-red-500/10 text-red-400' :
                        m.engagement < 6 ? 'bg-amber-500/10 text-amber-400' :
                        'bg-emerald-500/10 text-emerald-400'
                      }`}>
                        Engagement: {m.engagement.toFixed(1)}/10
                      </span>
                    )}
                    {m.churn_risk !== undefined && (
                      <span className={`text-xs px-2 py-1 rounded-lg ${
                        m.churn_risk > 70 ? 'bg-red-500/10 text-red-400' :
                        m.churn_risk > 40 ? 'bg-amber-500/10 text-amber-400' :
                        'bg-emerald-500/10 text-emerald-400'
                      }`}>
                        Churn: {m.churn_risk}/100
                      </span>
                    )}
                  </div>

                  {/* Signals */}
                  {m.signals.length > 0 && (
                    <div className="space-y-1">
                      {m.signals.map((s, i) => (
                        <div key={i} className="text-xs text-slate-400 flex items-start gap-2">
                          <span className={
                            s.severity === 'critical' ? 'text-red-400' :
                            s.severity === 'high' ? 'text-orange-400' :
                            s.severity === 'elevated' ? 'text-amber-400' : 'text-slate-500'
                          }>●</span>
                          <span>{s.message}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {m.signals.length === 0 && (
                    <p className="text-xs text-slate-500">No risk signals detected.</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* ── Actions Tab ── */}
          {activeTab === 'actions' && (
            <div className="space-y-3">
              {briefing.action_items.length === 0 ? (
                <div className="text-center py-10 text-slate-500 text-sm">
                  No action items — your team looks healthy.
                </div>
              ) : (
                briefing.action_items.map((item, i) => (
                  <div key={i} className={`border rounded-xl p-5 ${priorityColor(item.priority)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${priorityLabel(item.priority)}`}>
                          {item.priority}
                        </span>
                        <span className="text-xs bg-slate-700/50 px-2 py-0.5 rounded-full text-slate-300">
                          {item.category}
                        </span>
                      </div>
                      <span className="text-xs text-slate-500">{item.timeframe}</span>
                    </div>
                    <p className="text-sm text-slate-200 font-medium mb-1">{item.action}</p>
                    <p className="text-xs text-slate-400">{item.reason}</p>
                  </div>
                ))
              )}
            </div>
          )}

          {/* ── Coaching Tab ── */}
          {activeTab === 'coaching' && (
            <div className="space-y-4">
              {briefing.coaching_prompts.length === 0 ? (
                <div className="text-center py-10 text-slate-500 text-sm">
                  Complete team assessments to unlock coaching insights.
                </div>
              ) : (
                briefing.coaching_prompts.map((prompt, i) => (
                  <div
                    key={i}
                    className="bg-gradient-to-r from-violet-900/20 to-indigo-900/20 border border-violet-500/30 rounded-xl p-5"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">
                        {prompt.theme}
                      </span>
                      <span className="text-xs text-slate-600">|</span>
                      <span className="text-xs text-slate-500">{prompt.source.replace(/_/g, ' ')}</span>
                    </div>
                    <p className="text-sm text-slate-200 leading-relaxed">{prompt.prompt}</p>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
