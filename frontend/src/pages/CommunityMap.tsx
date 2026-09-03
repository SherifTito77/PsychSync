import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface Community {
  id: number;
  members: string[];
  size: number;
  internal_density: number;
  health_score: number | null;
}

interface NetworkNode {
  user_id: string;
  name: string;
  degree_centrality: number;
  betweenness_centrality: number;
  role: string;
  community_id: number | null;
}

interface Analysis {
  communities: Community[];
  nodes: NetworkNode[];
  network_stats: {
    total_nodes: number;
    total_edges: number;
    density: number;
    num_communities: number;
  };
}

const COMMUNITY_COLORS = [
  { bg: 'bg-purple-500/15', border: 'border-purple-500/30', text: 'text-purple-300', bar: 'bg-purple-500' },
  { bg: 'bg-cyan-500/15', border: 'border-cyan-500/30', text: 'text-cyan-300', bar: 'bg-cyan-500' },
  { bg: 'bg-amber-500/15', border: 'border-amber-500/30', text: 'text-amber-300', bar: 'bg-amber-500' },
  { bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', text: 'text-emerald-300', bar: 'bg-emerald-500' },
  { bg: 'bg-rose-500/15', border: 'border-rose-500/30', text: 'text-rose-300', bar: 'bg-rose-500' },
  { bg: 'bg-indigo-500/15', border: 'border-indigo-500/30', text: 'text-indigo-300', bar: 'bg-indigo-500' },
  { bg: 'bg-orange-500/15', border: 'border-orange-500/30', text: 'text-orange-300', bar: 'bg-orange-500' },
  { bg: 'bg-teal-500/15', border: 'border-teal-500/30', text: 'text-teal-300', bar: 'bg-teal-500' },
];

export default function CommunityMap() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedCommunity, setExpandedCommunity] = useState<number | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get('/api/v1/organizational-network/analyze/default', {
        params: { lookback_days: 60 },
      });
      setAnalysis(data);
    } catch {
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Detecting communities...</p>
        </div>
      </div>
    );
  }

  const communities = analysis?.communities || [];
  const nodeMap = new Map((analysis?.nodes || []).map(n => [n.user_id, n]));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Community Map</h1>
          <p className="text-slate-400 text-sm mt-1">
            Detected clusters of tightly connected employees — identifies silos, shadow teams, and cross-functional groups
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-sm transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-teal-400">{communities.length}</div>
          <div className="text-xs text-slate-400">Communities</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-white">{analysis?.network_stats.total_nodes || 0}</div>
          <div className="text-xs text-slate-400">Total Members</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-purple-400">
            {communities.length > 0 ? Math.max(...communities.map(c => c.size)) : 0}
          </div>
          <div className="text-xs text-slate-400">Largest Community</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-amber-400">
            {communities.filter(c => c.size === 1).length}
          </div>
          <div className="text-xs text-slate-400">Singletons (Isolated)</div>
        </div>
      </div>

      {/* Communities Grid */}
      {communities.length === 0 ? (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🏘</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Communities Yet</h3>
          <p className="text-slate-400 text-sm">Complete assessments and collaboration surveys to enable community detection.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {communities
            .filter(c => c.size > 1)
            .map((comm) => {
              const colors = COMMUNITY_COLORS[comm.id % COMMUNITY_COLORS.length];
              const isExpanded = expandedCommunity === comm.id;
              const commMembers = comm.members
                .map(uid => nodeMap.get(uid))
                .filter(Boolean)
                .sort((a, b) => (b?.betweenness_centrality || 0) - (a?.betweenness_centrality || 0));

              return (
                <div key={comm.id} className={`${colors.bg} border ${colors.border} rounded-xl overflow-hidden`}>
                  <button
                    onClick={() => setExpandedCommunity(isExpanded ? null : comm.id)}
                    className="w-full flex items-center justify-between p-5 text-left"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full ${colors.bar} flex items-center justify-center text-white font-bold`}>
                        {comm.id + 1}
                      </div>
                      <div>
                        <h3 className={`font-semibold ${colors.text}`}>Community {comm.id + 1}</h3>
                        <p className="text-xs text-slate-400">{comm.size} members</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      {comm.health_score !== null && (
                        <div className="text-right">
                          <div className={`text-sm font-mono font-bold ${
                            comm.health_score >= 70 ? 'text-emerald-400' :
                            comm.health_score >= 40 ? 'text-amber-400' : 'text-red-400'
                          }`}>{comm.health_score}</div>
                          <div className="text-xs text-slate-400">Health</div>
                        </div>
                      )}
                      <div className="text-right">
                        <div className="text-sm text-white font-mono">{(comm.internal_density * 100).toFixed(0)}%</div>
                        <div className="text-xs text-slate-400">Density</div>
                      </div>
                      <svg
                        className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="border-t border-slate-700/30 px-5 pb-5">
                      <table className="w-full text-sm mt-3">
                        <thead>
                          <tr className="text-slate-400 text-xs">
                            <th className="text-left py-2">Member</th>
                            <th className="text-center py-2">Network Role</th>
                            <th className="text-center py-2">Centrality</th>
                          </tr>
                        </thead>
                        <tbody>
                          {commMembers.map(node => node && (
                            <tr key={node.user_id} className="border-t border-slate-700/20">
                              <td className="py-2 text-white">{node.name}</td>
                              <td className="text-center py-2">
                                <span className="text-xs px-2 py-1 rounded-full bg-slate-700/50 text-slate-300">
                                  {node.role}
                                </span>
                              </td>
                              <td className="text-center py-2 font-mono text-xs text-slate-300">
                                {(node.betweenness_centrality * 100).toFixed(1)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
          })}
        </div>
      )}
    </div>
  );
}
