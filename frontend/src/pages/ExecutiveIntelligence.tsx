import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface Signal {
  type: string;
  severity: string;
  message: string;
}

interface TeamNarrative {
  team_id: string;
  team_name: string;
  member_count: number;
  urgency_score: number;
  top_risk: string;
  scores: { [key: string]: number };
  signals: Signal[];
  narrative: string;
  recommended_actions: string[];
}

interface CrossTeamStory {
  type: string;
  teams: string[];
  severity: string;
  narrative: string;
  strength: number;
}

interface TrendAlert {
  type: string;
  severity: string;
  metric: string;
  message: string;
  change_pct?: number;
  change_absolute?: number;
  org_score?: number;
}

interface Briefing {
  organization_id: string;
  lookback_days: number;
  generated_at: string;
  executive_summary: string;
  org_scores: { [key: string]: number };
  team_narratives: TeamNarrative[];
  cross_team_stories: CrossTeamStory[];
  trend_alerts: TrendAlert[];
  data_sources: {
    behavioral_intelligence: boolean;
    network_analysis: boolean;
    temporal_snapshots: number;
  };
}

function severityColor(severity: string): string {
  switch (severity) {
    case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30';
    case 'high': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    case 'elevated': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    case 'moderate': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
    case 'positive': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
  }
}

function severityBadge(severity: string): string {
  switch (severity) {
    case 'critical': return 'bg-red-500/20 text-red-300';
    case 'high': return 'bg-orange-500/20 text-orange-300';
    case 'elevated': return 'bg-amber-500/20 text-amber-300';
    case 'moderate': return 'bg-yellow-500/20 text-yellow-300';
    case 'positive': return 'bg-emerald-500/20 text-emerald-300';
    default: return 'bg-slate-500/20 text-slate-300';
  }
}

export default function ExecutiveIntelligence() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [lookbackDays, setLookbackDays] = useState(45);
  const [activeTab, setActiveTab] = useState<'overview' | 'teams' | 'cross-team' | 'trends'>('overview');

  const fetchBriefing = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<Briefing>(
        `/api/v1/executive-intelligence/briefing/default`,
        { params: { lookback_days: lookbackDays } }
      );
      setBriefing(data);
    } catch {
      setBriefing(null);
    } finally {
      setLoading(false);
    }
  }, [lookbackDays]);

  useEffect(() => { fetchBriefing(); }, [fetchBriefing]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Generating executive intelligence...</p>
        </div>
      </div>
    );
  }

  const hasData = briefing && (briefing.team_narratives.length > 0 || briefing.trend_alerts.length > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Executive Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">
            Behavioral signals + Network analysis + HRIS data = organizational narratives
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
            onClick={fetchBriefing}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      {briefing?.executive_summary && (
        <div className="bg-gradient-to-r from-violet-900/30 to-indigo-900/30 border border-violet-500/30 rounded-xl p-6">
          <h3 className="text-xs font-semibold text-violet-400 uppercase tracking-wider mb-3">
            Executive Intelligence Brief
          </h3>
          <p className="text-slate-200 text-sm leading-relaxed">
            {briefing.executive_summary}
          </p>
          <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
            <span>Generated: {new Date(briefing.generated_at).toLocaleString()}</span>
            <span>Lookback: {briefing.lookback_days} days</span>
            {briefing.data_sources.temporal_snapshots > 0 && (
              <span>{briefing.data_sources.temporal_snapshots} network snapshots</span>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!hasData && (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🧠</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            Executive Intelligence Engine Ready
          </h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Complete team assessments, collaboration surveys, and connect HRIS data to generate
            executive-grade organizational narratives.
          </p>
        </div>
      )}

      {/* Tabs */}
      {hasData && (
        <>
          <div className="flex border-b border-slate-700">
            {([
              { key: 'overview', label: 'Overview', count: briefing?.team_narratives.length },
              { key: 'teams', label: 'Team Narratives', count: briefing?.team_narratives.length },
              { key: 'cross-team', label: 'Cross-Team', count: briefing?.cross_team_stories.length },
              { key: 'trends', label: 'Trend Alerts', count: briefing?.trend_alerts.length },
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
                  <span className="text-xs bg-slate-700 rounded-full px-2 py-0.5">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && briefing && (
            <div className="space-y-6">
              {/* Org Score Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                {Object.entries(briefing.org_scores).map(([key, val]) => {
                  const isInverse = key === 'friction_index' || key === 'burnout_risk';
                  const effective = isInverse ? 100 - val : val;
                  const color = effective >= 70 ? 'text-emerald-400' : effective >= 50 ? 'text-blue-400' : effective >= 30 ? 'text-amber-400' : 'text-red-400';
                  return (
                    <div key={key} className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
                      <div className="text-xs text-slate-400 mb-1">{key.replace(/_/g, ' ')}</div>
                      <div className={`text-2xl font-bold ${color}`}>{val || '--'}</div>
                    </div>
                  );
                })}
              </div>

              {/* Urgent Team Narratives */}
              {briefing.team_narratives.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-white">Teams Requiring Attention</h3>
                  {briefing.team_narratives.slice(0, 5).map((tn) => (
                    <div
                      key={tn.team_id}
                      className="bg-slate-800/50 border border-slate-700 rounded-xl p-5"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            tn.urgency_score > 8 ? 'bg-red-500' :
                            tn.urgency_score > 5 ? 'bg-orange-500' : 'bg-amber-500'
                          }`} />
                          <span className="text-white font-medium">{tn.team_name}</span>
                          <span className="text-xs text-slate-500">{tn.member_count} members</span>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${severityBadge(
                          tn.urgency_score > 8 ? 'critical' : tn.urgency_score > 5 ? 'high' : 'moderate'
                        )}`}>
                          Urgency: {tn.urgency_score}
                        </span>
                      </div>
                      <p className="text-slate-300 text-sm leading-relaxed">{tn.narrative}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Quick Trend Alerts */}
              {briefing.trend_alerts.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-white">Active Alerts</h3>
                  {briefing.trend_alerts.slice(0, 3).map((alert, i) => (
                    <div
                      key={i}
                      className={`border rounded-lg p-3 flex items-start gap-3 ${severityColor(alert.severity)}`}
                    >
                      <span className="text-lg">{alert.severity === 'high' ? '🔴' : '🟡'}</span>
                      <p className="text-sm">{alert.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Teams Tab */}
          {activeTab === 'teams' && briefing && (
            <div className="space-y-4">
              {briefing.team_narratives.map((tn) => (
                <div
                  key={tn.team_id}
                  className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-white font-semibold">{tn.team_name}</h3>
                      <p className="text-xs text-slate-500">{tn.member_count} members | Top risk: {tn.top_risk}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${severityBadge(
                      tn.urgency_score > 8 ? 'critical' : tn.urgency_score > 5 ? 'high' : 'moderate'
                    )}`}>
                      Urgency: {tn.urgency_score}
                    </span>
                  </div>

                  <p className="text-slate-300 text-sm leading-relaxed">{tn.narrative}</p>

                  {/* Signals */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-slate-400 uppercase">Signals</div>
                    {tn.signals.map((sig, i) => (
                      <div key={i} className={`text-xs px-3 py-2 rounded-lg border ${severityColor(sig.severity)}`}>
                        {sig.message}
                      </div>
                    ))}
                  </div>

                  {/* Recommended Actions */}
                  {tn.recommended_actions.length > 0 && (
                    <div className="border-t border-slate-700/50 pt-3">
                      <div className="text-xs font-semibold text-slate-400 uppercase mb-2">Recommended Actions</div>
                      {tn.recommended_actions.map((action, i) => (
                        <div key={i} className="flex items-start gap-2 text-sm text-slate-300 mb-1">
                          <span className="text-violet-400 mt-0.5">→</span>
                          <span>{action}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {briefing.team_narratives.length === 0 && (
                <div className="text-center py-10 text-slate-500 text-sm">
                  All teams are operating within healthy parameters.
                </div>
              )}
            </div>
          )}

          {/* Cross-Team Tab */}
          {activeTab === 'cross-team' && briefing && (
            <div className="space-y-4">
              {briefing.cross_team_stories.map((story, i) => (
                <div
                  key={i}
                  className={`border rounded-xl p-5 ${severityColor(story.severity)}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {story.type === 'silo_detected' ? '🧱' :
                         story.type === 'completely_isolated' ? '🏝' :
                         story.type === 'strong_partnership' ? '🤝' : '📊'}
                      </span>
                      <span className="text-sm font-medium">
                        {story.teams.join(' ↔ ')}
                      </span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${severityBadge(story.severity)}`}>
                      {story.type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed">{story.narrative}</p>
                </div>
              ))}

              {briefing.cross_team_stories.length === 0 && (
                <div className="text-center py-10 text-slate-500 text-sm">
                  No cross-team relationship issues detected. Complete collaboration surveys for deeper analysis.
                </div>
              )}
            </div>
          )}

          {/* Trends Tab */}
          {activeTab === 'trends' && briefing && (
            <div className="space-y-3">
              {briefing.trend_alerts.map((alert, i) => (
                <div
                  key={i}
                  className={`border rounded-xl p-5 ${severityColor(alert.severity)}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${severityBadge(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-500">
                      {alert.metric.replace(/_/g, ' ')}
                      {alert.change_pct !== undefined && ` (${alert.change_pct > 0 ? '+' : ''}${alert.change_pct}%)`}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed">{alert.message}</p>
                </div>
              ))}

              {briefing.trend_alerts.length === 0 && (
                <div className="text-center py-10 text-slate-500 text-sm">
                  No trend alerts. Continue collecting data for temporal analysis.
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
