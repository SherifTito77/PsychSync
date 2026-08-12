import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface ScoreFactors {
  [key: string]: number;
}

interface Trend {
  direction: 'improving' | 'declining' | 'stable';
  change_pct: number;
}

interface Score {
  score: number;
  label: string;
  trend: Trend;
  factors: ScoreFactors;
  recommendations: string[];
  member_count?: number;
}

interface TeamResult {
  team_id: string;
  team_name: string;
  member_count: number;
  scores: {
    team_health: number;
    collaboration: number;
    manager_health: number;
    psychological_safety: number;
    change_readiness: number;
    friction_index: number;
  };
  top_risk: string;
}

interface OrgDashboard {
  organization_id: string;
  team_count: number;
  scores: { [key: string]: number };
  teams: TeamResult[];
  executive_summary: string;
  generated_at: string;
  lookback_days?: number;
}

interface TeamAllScores {
  team_id: string;
  lookback_days: number;
  scores: {
    team_health: Score;
    collaboration: Score;
    manager_health: Score;
    psychological_safety: Score;
    change_readiness: Score;
    friction_index: Score;
  };
}

const SCORE_CONFIGS = [
  { key: 'team_health', label: 'Team Health', color: 'emerald', icon: '💚', higherBetter: true },
  { key: 'collaboration', label: 'Collaboration', color: 'blue', icon: '🤝', higherBetter: true },
  { key: 'manager_health', label: 'Manager Health', color: 'purple', icon: '👔', higherBetter: true },
  { key: 'psychological_safety', label: 'Psych Safety', color: 'amber', icon: '🛡', higherBetter: true },
  { key: 'change_readiness', label: 'Change Readiness', color: 'cyan', icon: '🔄', higherBetter: true },
  { key: 'friction_index', label: 'Friction Index', color: 'red', icon: '⚡', higherBetter: false },
] as const;

function scoreColor(score: number, higherBetter: boolean): string {
  const effective = higherBetter ? score : 100 - score;
  if (effective >= 80) return 'text-emerald-400';
  if (effective >= 60) return 'text-blue-400';
  if (effective >= 40) return 'text-amber-400';
  return 'text-red-400';
}

function scoreBg(score: number, higherBetter: boolean): string {
  const effective = higherBetter ? score : 100 - score;
  if (effective >= 80) return 'bg-emerald-500/10 border-emerald-500/30';
  if (effective >= 60) return 'bg-blue-500/10 border-blue-500/30';
  if (effective >= 40) return 'bg-amber-500/10 border-amber-500/30';
  return 'bg-red-500/10 border-red-500/30';
}

function trendIcon(trend: Trend): string {
  if (trend.direction === 'improving') return '↑';
  if (trend.direction === 'declining') return '↓';
  return '→';
}

function trendColor(trend: Trend, higherBetter: boolean): string {
  if (trend.direction === 'improving') return higherBetter ? 'text-emerald-400' : 'text-red-400';
  if (trend.direction === 'declining') return higherBetter ? 'text-red-400' : 'text-emerald-400';
  return 'text-slate-400';
}

export default function BehavioralIntelligenceDashboard() {
  const [orgDashboard, setOrgDashboard] = useState<OrgDashboard | null>(null);
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [teamDetail, setTeamDetail] = useState<TeamAllScores | null>(null);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [teamLoading, setTeamLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'teams' | 'recommendations'>('overview');

  const fetchOrgDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Try org dashboard first, fall back to demo data
      const { data } = await axios.get<OrgDashboard>(
        `/api/v1/behavioral-intelligence/organization/default/dashboard`,
        { params: { lookback_days: lookbackDays } }
      );
      setOrgDashboard(data);
    } catch {
      // No org data yet — show empty state
      setOrgDashboard({
        organization_id: 'default',
        team_count: 0,
        scores: {},
        teams: [],
        executive_summary: 'Complete assessments across your teams to generate behavioral intelligence insights.',
        generated_at: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  }, [lookbackDays]);

  const fetchTeamDetail = useCallback(async (teamId: string) => {
    setTeamLoading(true);
    try {
      const { data } = await axios.get<TeamAllScores>(
        `/api/v1/behavioral-intelligence/team/${teamId}/all`,
        { params: { lookback_days: lookbackDays } }
      );
      setTeamDetail(data);
    } catch {
      setTeamDetail(null);
    } finally {
      setTeamLoading(false);
    }
  }, [lookbackDays]);

  useEffect(() => {
    fetchOrgDashboard();
  }, [fetchOrgDashboard]);

  useEffect(() => {
    if (selectedTeamId) fetchTeamDetail(selectedTeamId);
  }, [selectedTeamId, fetchTeamDetail]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Analyzing behavioral signals...</p>
        </div>
      </div>
    );
  }

  const hasData = orgDashboard && orgDashboard.team_count > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Behavioral Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">
            Behavior → Pattern → Prediction → Recommendation
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={lookbackDays}
            onChange={(e) => setLookbackDays(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
          </select>
          <button
            onClick={fetchOrgDashboard}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      {orgDashboard?.executive_summary && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">
            Executive Intelligence Brief
          </h3>
          <p className="text-slate-300 text-sm leading-relaxed">
            {orgDashboard.executive_summary}
          </p>
          {orgDashboard.generated_at && (
            <p className="text-slate-500 text-xs mt-2">
              Generated: {new Date(orgDashboard.generated_at).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {/* Empty State */}
      {!hasData && (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🧠</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            Behavioral Intelligence Engine Ready
          </h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
            Create teams and have members complete personality assessments (Big Five, MBTI, etc.) to
            generate real behavioral intelligence scores.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-lg mx-auto">
            {SCORE_CONFIGS.map((s) => (
              <div key={s.key} className="bg-slate-800/50 rounded-lg p-3 text-center">
                <div className="text-xl mb-1">{s.icon}</div>
                <div className="text-xs text-slate-400">{s.label}</div>
                <div className="text-lg font-bold text-slate-600 mt-1">--</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      {hasData && (
        <>
          <div className="flex border-b border-slate-700">
            {(['overview', 'teams', 'recommendations'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'text-indigo-400 border-b-2 border-indigo-400'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Score Cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {SCORE_CONFIGS.map((cfg) => {
                  const val = orgDashboard?.scores?.[cfg.key] ?? 0;
                  return (
                    <div
                      key={cfg.key}
                      className={`border rounded-xl p-4 text-center ${scoreBg(val, cfg.higherBetter)}`}
                    >
                      <div className="text-xl mb-1">{cfg.icon}</div>
                      <div className="text-xs text-slate-400 mb-2">{cfg.label}</div>
                      <div className={`text-3xl font-bold ${scoreColor(val, cfg.higherBetter)}`}>
                        {val > 0 ? val : '--'}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Team Heatmap */}
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-white mb-4">
                  Team Score Heatmap ({orgDashboard?.team_count} teams)
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-400 text-xs">
                        <th className="text-left py-2 px-3">Team</th>
                        {SCORE_CONFIGS.map((c) => (
                          <th key={c.key} className="text-center py-2 px-2">
                            {c.icon}
                          </th>
                        ))}
                        <th className="text-center py-2 px-3">Top Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orgDashboard?.teams?.map((team) => (
                        <tr
                          key={team.team_id}
                          onClick={() => {
                            setSelectedTeamId(team.team_id);
                            setActiveTab('teams');
                          }}
                          className="border-t border-slate-700/50 hover:bg-slate-700/30 cursor-pointer transition-colors"
                        >
                          <td className="py-3 px-3">
                            <div className="text-white font-medium">{team.team_name}</div>
                            <div className="text-slate-500 text-xs">{team.member_count} members</div>
                          </td>
                          {SCORE_CONFIGS.map((cfg) => {
                            const v = team.scores[cfg.key as keyof typeof team.scores];
                            return (
                              <td key={cfg.key} className="text-center py-3 px-2">
                                <span className={`font-mono text-sm ${scoreColor(v, cfg.higherBetter)}`}>
                                  {v}
                                </span>
                              </td>
                            );
                          })}
                          <td className="text-center py-3 px-3">
                            <span className="text-xs bg-red-500/20 text-red-300 px-2 py-1 rounded-full">
                              {team.top_risk}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Teams Tab */}
          {activeTab === 'teams' && (
            <div className="space-y-4">
              {/* Team selector */}
              <div className="flex items-center gap-3">
                <select
                  value={selectedTeamId ?? ''}
                  onChange={(e) => setSelectedTeamId(e.target.value || null)}
                  className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm flex-1 max-w-xs"
                >
                  <option value="">Select a team...</option>
                  {orgDashboard?.teams?.map((t) => (
                    <option key={t.team_id} value={t.team_id}>
                      {t.team_name} ({t.member_count} members)
                    </option>
                  ))}
                </select>
              </div>

              {/* Team Detail */}
              {teamLoading && (
                <div className="text-center py-10 text-slate-400 text-sm">
                  Loading team scores...
                </div>
              )}

              {!teamLoading && teamDetail && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {SCORE_CONFIGS.map((cfg) => {
                    const detail = teamDetail.scores[cfg.key as keyof typeof teamDetail.scores];
                    if (!detail) return null;
                    return (
                      <div
                        key={cfg.key}
                        className={`border rounded-xl p-5 ${scoreBg(detail.score, cfg.higherBetter)}`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{cfg.icon}</span>
                            <span className="text-sm font-medium text-white">{cfg.label}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className={`text-xs ${trendColor(detail.trend, cfg.higherBetter)}`}>
                              {trendIcon(detail.trend)} {Math.abs(detail.trend.change_pct)}%
                            </span>
                          </div>
                        </div>

                        <div className={`text-4xl font-bold mb-1 ${scoreColor(detail.score, cfg.higherBetter)}`}>
                          {detail.score}
                        </div>
                        <div className="text-xs text-slate-400 mb-4">{detail.label}</div>

                        {/* Factors */}
                        {detail.factors && Object.keys(detail.factors).length > 0 && (
                          <div className="space-y-2 mb-4">
                            <div className="text-xs font-semibold text-slate-400 uppercase">Factors</div>
                            {Object.entries(detail.factors).map(([k, v]) => (
                              <div key={k} className="flex items-center justify-between">
                                <span className="text-xs text-slate-400">
                                  {k.replace(/_/g, ' ')}
                                </span>
                                <div className="flex items-center gap-2">
                                  <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-indigo-500 rounded-full transition-all"
                                      style={{ width: `${Math.min(v, 100)}%` }}
                                    />
                                  </div>
                                  <span className="text-xs text-slate-300 font-mono w-8 text-right">
                                    {v}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Recommendations */}
                        {detail.recommendations?.length > 0 && (
                          <div className="border-t border-slate-700/50 pt-3">
                            {detail.recommendations.map((rec, i) => (
                              <p key={i} className="text-xs text-slate-400 leading-relaxed mb-1">
                                {rec}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {!teamLoading && !selectedTeamId && (
                <div className="text-center py-16 text-slate-500 text-sm">
                  Select a team above to see detailed behavioral intelligence scores
                </div>
              )}
            </div>
          )}

          {/* Recommendations Tab */}
          {activeTab === 'recommendations' && teamDetail && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">
                Actionable Recommendations for {orgDashboard?.teams?.find(t => t.team_id === selectedTeamId)?.team_name || 'Selected Team'}
              </h3>
              {SCORE_CONFIGS.map((cfg) => {
                const detail = teamDetail.scores[cfg.key as keyof typeof teamDetail.scores];
                if (!detail?.recommendations?.length) return null;
                return (
                  <div key={cfg.key} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span>{cfg.icon}</span>
                      <span className="text-sm font-medium text-white">{cfg.label}</span>
                      <span className={`text-sm font-bold ml-auto ${scoreColor(detail.score, cfg.higherBetter)}`}>
                        {detail.score}
                      </span>
                    </div>
                    <ul className="space-y-2">
                      {detail.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <span className="text-indigo-400 mt-0.5">-</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}

              {!selectedTeamId && (
                <div className="text-center py-10 text-slate-500 text-sm">
                  Select a team from the Teams tab to view recommendations
                </div>
              )}
            </div>
          )}

          {activeTab === 'recommendations' && !teamDetail && (
            <div className="text-center py-10 text-slate-500 text-sm">
              Select a team from the Teams tab to view recommendations
            </div>
          )}
        </>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-300 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
