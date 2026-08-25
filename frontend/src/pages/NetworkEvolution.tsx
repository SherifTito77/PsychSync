import { useState, useEffect, useCallback } from 'react';
import { networkAnalysisService, TemporalSnapshot } from '../services/networkAnalysisService';

export default function NetworkEvolution() {
  const [snapshots, setSnapshots] = useState<TemporalSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(90);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await networkAnalysisService.getTemporalEvolution('default', days);
      setSnapshots(data);
    } catch {
      setSnapshots([]);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Loading network history...</p>
        </div>
      </div>
    );
  }

  const latest = snapshots[snapshots.length - 1];
  const first = snapshots[0];
  const delta = (key: keyof TemporalSnapshot) => {
    if (!first || !latest) return null;
    const a = Number(first[key]) || 0;
    const b = Number(latest[key]) || 0;
    if (a === 0) return null;
    return ((b - a) / a * 100).toFixed(1);
  };

  // Compute max for sparkline scaling
  const maxNodes = Math.max(...snapshots.map(s => s.total_nodes), 1);
  const maxEdges = Math.max(...snapshots.map(s => s.total_edges), 1);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Network Evolution</h1>
          <p className="text-slate-400 text-sm mt-1">
            Track how your organizational network changes over time
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
            <option value={90}>90 days</option>
            <option value={180}>6 months</option>
            <option value={365}>1 year</option>
          </select>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {snapshots.length === 0 ? (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">📈</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Temporal Data Yet</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Network snapshots are saved each time a network analysis runs. Visit the Network Dashboard to generate your first snapshot.
          </p>
        </div>
      ) : (
        <>
          {/* Trend Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Nodes', value: latest?.total_nodes, change: delta('total_nodes'), color: 'text-white' },
              { label: 'Connections', value: latest?.total_edges, change: delta('total_edges'), color: 'text-cyan-400' },
              { label: 'Communities', value: latest?.num_communities, change: delta('num_communities'), color: 'text-purple-400' },
              { label: 'Isolated', value: latest?.num_isolates, change: delta('num_isolates'), color: 'text-red-400', invertColor: true },
            ].map(({ label, value, change, color, invertColor }) => (
              <div key={label} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                <div className="text-xs text-slate-400 mb-1">{label}</div>
                <div className={`text-2xl font-bold ${color}`}>{value ?? '-'}</div>
                {change !== null && (
                  <div className={`text-xs mt-1 ${
                    Number(change) > 0
                      ? (invertColor ? 'text-red-400' : 'text-emerald-400')
                      : Number(change) < 0
                        ? (invertColor ? 'text-emerald-400' : 'text-red-400')
                        : 'text-slate-500'
                  }`}>
                    {Number(change) > 0 ? '+' : ''}{change}% vs start
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Sparkline Table */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-700">
              <h3 className="text-sm font-semibold text-white">
                Timeline ({snapshots.length} snapshots)
              </h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-xs border-b border-slate-700">
                  <th className="text-left py-3 px-4">Date</th>
                  <th className="text-center py-3 px-3">Nodes</th>
                  <th className="text-center py-3 px-3">Edges</th>
                  <th className="text-center py-3 px-3">Density</th>
                  <th className="text-center py-3 px-3">Communities</th>
                  <th className="text-center py-3 px-3">Isolated</th>
                  <th className="text-center py-3 px-3">Influencers</th>
                  <th className="py-3 px-3">Connectivity</th>
                </tr>
              </thead>
              <tbody>
                {snapshots.map((snap) => (
                  <tr key={snap.date} className="border-t border-slate-700/50 hover:bg-slate-700/30">
                    <td className="py-3 px-4 text-white font-mono text-xs">{snap.date}</td>
                    <td className="text-center py-3 px-3 text-slate-300">{snap.total_nodes}</td>
                    <td className="text-center py-3 px-3 text-cyan-300">{snap.total_edges}</td>
                    <td className="text-center py-3 px-3 font-mono text-xs text-slate-300">
                      {(snap.density * 100).toFixed(1)}%
                    </td>
                    <td className="text-center py-3 px-3 text-purple-300">{snap.num_communities ?? '-'}</td>
                    <td className="text-center py-3 px-3">
                      <span className={(snap.num_isolates || 0) > 0 ? 'text-red-300' : 'text-emerald-300'}>
                        {snap.num_isolates ?? '-'}
                      </span>
                    </td>
                    <td className="text-center py-3 px-3 text-amber-300">{snap.num_influencers ?? '-'}</td>
                    <td className="py-3 px-3">
                      <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-teal-500 rounded-full"
                          style={{ width: `${Math.min(snap.avg_degree_centrality * 100 * 2, 100)}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
