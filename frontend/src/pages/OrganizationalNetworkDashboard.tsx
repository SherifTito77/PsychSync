import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface NetworkNode {
  user_id: string;
  name: string;
  degree_centrality: number;
  betweenness_centrality: number;
  bridging_score: number;
  team_count: number;
  role: 'influencer' | 'bridge' | 'connector' | 'isolated' | 'regular';
  teams: string[];
}

interface NetworkEdge {
  source: string;
  target: string;
  weight: number;
}

interface CrossTeamCollab {
  team_a: { id: string; name: string };
  team_b: { id: string; name: string };
  collaboration_strength: number;
  label: string;
}

interface ManagerDep {
  team_id: string;
  dependency_ratio: number;
  key_person: string;
  risk_level: 'high' | 'moderate';
}

interface NetworkAnalysis {
  organization_id: string;
  lookback_days: number;
  network_stats: {
    total_nodes: number;
    total_edges: number;
    density: number;
    avg_degree_centrality: number;
  };
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  insights: {
    influencers: NetworkNode[];
    isolated: NetworkNode[];
    bridges: NetworkNode[];
  };
  cross_team_collaboration: CrossTeamCollab[];
  manager_dependency: ManagerDep[];
  recommendations: string[];
  generated_at: string;
}

const ROLE_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  influencer: { label: 'Hidden Influencer', color: 'text-purple-400', bg: 'bg-purple-500/20 border-purple-500/30' },
  bridge: { label: 'Knowledge Bridge', color: 'text-cyan-400', bg: 'bg-cyan-500/20 border-cyan-500/30' },
  connector: { label: 'Connector', color: 'text-blue-400', bg: 'bg-blue-500/20 border-blue-500/30' },
  isolated: { label: 'Isolated', color: 'text-red-400', bg: 'bg-red-500/20 border-red-500/30' },
  regular: { label: 'Regular', color: 'text-slate-400', bg: 'bg-slate-500/20 border-slate-500/30' },
};

function nodeImportanceScore(node: NetworkNode): number {
  return node.degree_centrality * 0.4 + node.betweenness_centrality * 0.4 + node.bridging_score * 0.2;
}

export default function OrganizationalNetworkDashboard() {
  const [analysis, setAnalysis] = useState<NetworkAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [lookbackDays, setLookbackDays] = useState(60);
  const [activeTab, setActiveTab] = useState<'overview' | 'people' | 'cross-team' | 'risks'>('overview');
  const [roleFilter, setRoleFilter] = useState<string>('all');

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<NetworkAnalysis>(
        `/api/v1/organizational-network/analyze/default`,
        { params: { lookback_days: lookbackDays } }
      );
      setAnalysis(data);
    } catch {
      setAnalysis({
        organization_id: 'default',
        lookback_days: lookbackDays,
        network_stats: { total_nodes: 0, total_edges: 0, density: 0, avg_degree_centrality: 0 },
        nodes: [],
        edges: [],
        insights: { influencers: [], isolated: [], bridges: [] },
        cross_team_collaboration: [],
        manager_dependency: [],
        recommendations: ['Complete assessments across teams to enable network analysis.'],
        generated_at: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  }, [lookbackDays]);

  useEffect(() => { fetchAnalysis(); }, [fetchAnalysis]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Mapping organizational network...</p>
        </div>
      </div>
    );
  }

  const hasData = analysis && analysis.network_stats.total_nodes > 0;
  const stats = analysis?.network_stats;

  const filteredNodes = (analysis?.nodes ?? []).filter(
    (n) => roleFilter === 'all' || n.role === roleFilter
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Organizational Network Analysis</h1>
          <p className="text-slate-400 text-sm mt-1">
            Discover hidden influencers, isolated employees, and collaboration patterns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={lookbackDays}
            onChange={(e) => setLookbackDays(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
            <option value={180}>6 months</option>
          </select>
          <button
            onClick={fetchAnalysis}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      {hasData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{stats?.total_nodes}</div>
            <div className="text-xs text-slate-400">Employees</div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-cyan-400">{stats?.total_edges}</div>
            <div className="text-xs text-slate-400">Connections</div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-purple-400">
              {analysis?.insights.influencers.length}
            </div>
            <div className="text-xs text-slate-400">Hidden Influencers</div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
            <div className={`text-2xl font-bold ${(analysis?.insights.isolated.length ?? 0) > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {analysis?.insights.isolated.length}
            </div>
            <div className="text-xs text-slate-400">Isolated Employees</div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!hasData && (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🕸</div>
          <h3 className="text-lg font-semibold text-white mb-2">Network Analysis Ready</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Have team members complete shared assessments to build the organizational network graph.
            Connections form when employees participate in the same assessments.
          </p>
        </div>
      )}

      {/* Recommendations */}
      {analysis?.recommendations && analysis.recommendations.length > 0 && hasData && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <h3 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-3">
            Network Intelligence
          </h3>
          <ul className="space-y-2">
            {analysis.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-cyan-400 mt-0.5">-</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Tabs */}
      {hasData && (
        <>
          <div className="flex border-b border-slate-700">
            {(['overview', 'people', 'cross-team', 'risks'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'text-cyan-400 border-b-2 border-cyan-400'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                {tab === 'cross-team' ? 'Cross-Team' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Overview Tab — Insight Cards */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Influencers */}
              <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-purple-400 mb-3">
                  Hidden Influencers ({analysis?.insights.influencers.length})
                </h3>
                <p className="text-xs text-slate-400 mb-3">
                  High centrality without formal leadership — leverage as change champions
                </p>
                {analysis?.insights.influencers.slice(0, 5).map((n) => (
                  <div key={n.user_id} className="flex items-center justify-between py-2 border-t border-purple-500/20">
                    <span className="text-sm text-white">{n.name}</span>
                    <span className="text-xs text-purple-300 font-mono">
                      B:{(n.betweenness_centrality * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
                {(analysis?.insights.influencers.length ?? 0) === 0 && (
                  <p className="text-xs text-slate-500">None detected yet</p>
                )}
              </div>

              {/* Bridges */}
              <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-cyan-400 mb-3">
                  Knowledge Bridges ({analysis?.insights.bridges.length})
                </h3>
                <p className="text-xs text-slate-400 mb-3">
                  Connect different teams — critical for information flow
                </p>
                {analysis?.insights.bridges.slice(0, 5).map((n) => (
                  <div key={n.user_id} className="flex items-center justify-between py-2 border-t border-cyan-500/20">
                    <span className="text-sm text-white">{n.name}</span>
                    <span className="text-xs text-cyan-300 font-mono">
                      {n.team_count} teams
                    </span>
                  </div>
                ))}
                {(analysis?.insights.bridges.length ?? 0) === 0 && (
                  <p className="text-xs text-slate-500">None detected yet</p>
                )}
              </div>

              {/* Isolated */}
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-red-400 mb-3">
                  Isolated Employees ({analysis?.insights.isolated.length})
                </h3>
                <p className="text-xs text-slate-400 mb-3">
                  Low connectivity — disengagement or onboarding risk
                </p>
                {analysis?.insights.isolated.slice(0, 5).map((n) => (
                  <div key={n.user_id} className="flex items-center justify-between py-2 border-t border-red-500/20">
                    <span className="text-sm text-white">{n.name}</span>
                    <span className="text-xs text-red-300 font-mono">
                      D:{(n.degree_centrality * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
                {(analysis?.insights.isolated.length ?? 0) === 0 && (
                  <p className="text-xs text-slate-500">None detected</p>
                )}
              </div>
            </div>
          )}

          {/* People Tab */}
          {activeTab === 'people' && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="all">All Roles</option>
                  <option value="influencer">Influencers</option>
                  <option value="bridge">Bridges</option>
                  <option value="connector">Connectors</option>
                  <option value="isolated">Isolated</option>
                  <option value="regular">Regular</option>
                </select>
                <span className="text-xs text-slate-500">{filteredNodes.length} employees</span>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 text-xs border-b border-slate-700">
                      <th className="text-left py-3 px-4">Employee</th>
                      <th className="text-center py-3 px-3">Role</th>
                      <th className="text-center py-3 px-3">Degree</th>
                      <th className="text-center py-3 px-3">Betweenness</th>
                      <th className="text-center py-3 px-3">Bridge</th>
                      <th className="text-center py-3 px-3">Teams</th>
                      <th className="text-center py-3 px-3">Importance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredNodes
                      .sort((a, b) => nodeImportanceScore(b) - nodeImportanceScore(a))
                      .slice(0, 50)
                      .map((node) => {
                        const cfg = ROLE_CONFIG[node.role] || ROLE_CONFIG.regular;
                        return (
                          <tr key={node.user_id} className="border-t border-slate-700/50 hover:bg-slate-700/30">
                            <td className="py-3 px-4 text-white">{node.name}</td>
                            <td className="text-center py-3 px-3">
                              <span className={`text-xs px-2 py-1 rounded-full border ${cfg.bg} ${cfg.color}`}>
                                {cfg.label}
                              </span>
                            </td>
                            <td className="text-center py-3 px-3 font-mono text-xs text-slate-300">
                              {(node.degree_centrality * 100).toFixed(1)}%
                            </td>
                            <td className="text-center py-3 px-3 font-mono text-xs text-slate-300">
                              {(node.betweenness_centrality * 100).toFixed(1)}%
                            </td>
                            <td className="text-center py-3 px-3 font-mono text-xs text-slate-300">
                              {(node.bridging_score * 100).toFixed(0)}%
                            </td>
                            <td className="text-center py-3 px-3 text-slate-300">{node.team_count}</td>
                            <td className="text-center py-3 px-3">
                              <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden mx-auto">
                                <div
                                  className="h-full bg-cyan-500 rounded-full"
                                  style={{ width: `${Math.min(nodeImportanceScore(node) * 100, 100)}%` }}
                                />
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Cross-Team Tab */}
          {activeTab === 'cross-team' && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">
                Cross-Team Collaboration ({analysis?.cross_team_collaboration.length} pairs)
              </h3>
              {(analysis?.cross_team_collaboration.length ?? 0) === 0 ? (
                <div className="text-center py-10 text-slate-500 text-sm">
                  No cross-team connections detected yet
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {analysis?.cross_team_collaboration.map((ct, i) => (
                    <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-white font-medium">{ct.team_a.name}</span>
                          <span className="text-slate-500">↔</span>
                          <span className="text-white font-medium">{ct.team_b.name}</span>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          ct.label === 'Strong' ? 'bg-emerald-500/20 text-emerald-300' :
                          ct.label === 'Moderate' ? 'bg-amber-500/20 text-amber-300' :
                          'bg-red-500/20 text-red-300'
                        }`}>
                          {ct.label}
                        </span>
                      </div>
                      <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-cyan-500 rounded-full transition-all"
                          style={{ width: `${Math.min(ct.collaboration_strength * 10, 100)}%` }}
                        />
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {ct.collaboration_strength} shared assessment connections
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Risks Tab */}
          {activeTab === 'risks' && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">Manager Dependency Risk</h3>
              <p className="text-xs text-slate-400">
                Teams where a single member holds disproportionate network centrality — a "bus factor" risk
              </p>
              {(analysis?.manager_dependency.length ?? 0) === 0 ? (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6 text-center">
                  <div className="text-2xl mb-2">✓</div>
                  <p className="text-emerald-300 text-sm">No manager dependency risks detected</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {analysis?.manager_dependency.map((dep, i) => {
                    const keyPerson = analysis.nodes.find(n => n.user_id === dep.key_person);
                    return (
                      <div
                        key={i}
                        className={`border rounded-xl p-4 ${
                          dep.risk_level === 'high'
                            ? 'bg-red-500/10 border-red-500/30'
                            : 'bg-amber-500/10 border-amber-500/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-white font-medium">
                            Team: {dep.team_id.slice(0, 8)}...
                          </span>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            dep.risk_level === 'high' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'
                          }`}>
                            {dep.risk_level} risk
                          </span>
                        </div>
                        <p className="text-xs text-slate-400">
                          Key person: <span className="text-white">{keyPerson?.name || dep.key_person.slice(0, 8)}</span>
                          {' '} — dependency ratio: <span className="font-mono text-white">{dep.dependency_ratio}x</span> the team average
                        </p>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Network Density */}
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 mt-6">
                <h3 className="text-sm font-semibold text-white mb-3">Network Health</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Network Density</div>
                    <div className="text-lg font-bold text-white">
                      {((stats?.density ?? 0) * 100).toFixed(1)}%
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden mt-1">
                      <div
                        className="h-full bg-cyan-500 rounded-full"
                        style={{ width: `${Math.min((stats?.density ?? 0) * 100 * 5, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Avg Degree Centrality</div>
                    <div className="text-lg font-bold text-white">
                      {((stats?.avg_degree_centrality ?? 0) * 100).toFixed(1)}%
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden mt-1">
                      <div
                        className="h-full bg-purple-500 rounded-full"
                        style={{ width: `${Math.min((stats?.avg_degree_centrality ?? 0) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
