import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface ConnectorInfo { name: string; type: string }

interface CommHealth {
  score: number;
  label: string;
  active_users: number;
  msg_per_person_day: number;
  after_hours_rate: number;
  avg_response_time_min: number;
  sentiment_trend: string;
  engagement_distribution: string;
  recommendations: string[];
}

interface ChannelInfo {
  name: string;
  members: number;
  active: number;
  msgs_per_day: number;
  thread_depth: number;
  response_rate: number;
  healthy: boolean;
}

export default function CommunicationAnalytics() {
  const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
  const [health, setHealth] = useState<CommHealth | null>(null);
  const [channels, setChannels] = useState<ChannelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSetup, setShowSetup] = useState(false);
  const [setupType, setSetupType] = useState<'slack' | 'teams'>('slack');
  const [formData, setFormData] = useState<Record<string, string>>({ name: '' });

  const fetchConnectors = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ connectors: ConnectorInfo[] }>('/api/v1/communication-analytics/connectors');
      setConnectors(data.connectors || []);
    } catch { setConnectors([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchConnectors(); }, [fetchConnectors]);

  const handleConnect = async () => {
    try {
      const payload = { type: setupType, ...formData };
      const { data } = await axios.post<{ success: boolean }>('/api/v1/communication-analytics/connectors', payload);
      if (data.success) { setShowSetup(false); fetchConnectors(); }
    } catch { /* UI */ }
  };

  const fetchOrgHealth = async (name: string) => {
    try {
      const { data } = await axios.get<{ health: CommHealth; channels: ChannelInfo[] }>(
        `/api/v1/communication-analytics/connectors/${name}/org-health`
      );
      setHealth(data.health);
      setChannels(data.channels || []);
    } catch { /* handled */ }
  };

  const slackFields = ['bot_token', 'workspace_name'];
  const teamsFields = ['tenant_id', 'client_id', 'client_secret'];
  const fields = setupType === 'slack' ? slackFields : teamsFields;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Communication Analytics</h1>
          <p className="text-slate-400 text-sm mt-1">
            Slack & Teams messaging patterns, sentiment trends, and after-hours analysis
          </p>
        </div>
        <button
          onClick={() => setShowSetup(!showSetup)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm transition-colors"
        >
          {showSetup ? 'Cancel' : '+ Connect Platform'}
        </button>
      </div>

      {/* Setup */}
      {showSetup && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">Connect Communication Platform</h3>
          <div className="grid grid-cols-2 gap-3 max-w-md">
            {(['slack', 'teams'] as const).map(t => (
              <button key={t} onClick={() => setSetupType(t)}
                className={`p-4 rounded-lg border text-center ${setupType === t ? 'border-indigo-500 bg-indigo-500/20' : 'border-slate-700 bg-slate-800'}`}>
                <div className="text-2xl mb-1">{t === 'slack' ? '💬' : '🟦'}</div>
                <div className="text-xs text-slate-300">{t === 'slack' ? 'Slack' : 'Microsoft Teams'}</div>
              </button>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Connector Name</label>
              <input type="text" value={formData.name || ''} onChange={e => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm" placeholder="my-slack" />
            </div>
            {fields.map(f => (
              <div key={f}>
                <label className="text-xs text-slate-400 block mb-1">{f.replace(/_/g, ' ')}</label>
                <input type={f.includes('token') || f.includes('secret') ? 'password' : 'text'}
                  value={formData[f] || ''} onChange={e => setFormData({ ...formData, [f]: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm" placeholder={f} />
              </div>
            ))}
          </div>
          <button onClick={handleConnect} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm">
            Connect & Test
          </button>
        </div>
      )}

      {/* Platform Cards */}
      <div className="grid grid-cols-2 gap-4">
        {[{ id: 'slack', icon: '💬', name: 'Slack' }, { id: 'teams', icon: '🟦', name: 'Microsoft Teams' }].map(p => {
          const connected = connectors.filter(c => c.type.toLowerCase().includes(p.id));
          return (
            <div key={p.id} className={`border rounded-xl p-5 ${connected.length ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-800/30 border-slate-700/50'}`}>
              <div className="text-2xl mb-2">{p.icon}</div>
              <div className="text-sm font-medium text-white">{p.name}</div>
              <div className={`text-xs mt-1 ${connected.length ? 'text-emerald-400' : 'text-slate-500'}`}>
                {connected.length ? `${connected.length} connected` : 'Not connected'}
              </div>
              {connected.map(c => (
                <button key={c.name} onClick={() => fetchOrgHealth(c.name)} className="text-xs text-indigo-400 hover:text-indigo-300 mt-2 block">
                  View analytics →
                </button>
              ))}
            </div>
          );
        })}
      </div>

      {/* Health Score */}
      {health && (
        <>
          <div className={`border rounded-xl p-6 text-center ${
            health.score >= 70 ? 'bg-emerald-500/10 border-emerald-500/30' :
            health.score >= 50 ? 'bg-amber-500/10 border-amber-500/30' :
            'bg-red-500/10 border-red-500/30'
          }`}>
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Communication Health</div>
            <div className={`text-5xl font-bold mb-1 ${
              health.score >= 70 ? 'text-emerald-400' : health.score >= 50 ? 'text-amber-400' : 'text-red-400'
            }`}>{health.score || '--'}</div>
            <div className="text-sm text-slate-300">{health.label}</div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
              <div className="text-xs text-slate-400">Active Users</div>
              <div className="text-xl font-bold text-white">{health.active_users}</div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
              <div className="text-xs text-slate-400">Msgs/Person/Day</div>
              <div className="text-xl font-bold text-white">{health.msg_per_person_day}</div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
              <div className="text-xs text-slate-400">After-Hours Rate</div>
              <div className={`text-xl font-bold ${health.after_hours_rate > 20 ? 'text-red-400' : 'text-emerald-400'}`}>
                {health.after_hours_rate}%
              </div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
              <div className="text-xs text-slate-400">Avg Response Time</div>
              <div className="text-xl font-bold text-white">{health.avg_response_time_min}m</div>
            </div>
          </div>

          {/* Recommendations */}
          {health.recommendations.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
              <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-3">Recommendations</h3>
              <ul className="space-y-2">
                {health.recommendations.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="text-indigo-400 mt-0.5">-</span><span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Channel Health */}
      {channels.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Channel Health</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-xs">
                  <th className="text-left py-2 px-3">Channel</th>
                  <th className="text-center py-2 px-2">Members</th>
                  <th className="text-center py-2 px-2">Active</th>
                  <th className="text-center py-2 px-2">Msgs/Day</th>
                  <th className="text-center py-2 px-2">Thread Depth</th>
                  <th className="text-center py-2 px-2">Response Rate</th>
                  <th className="text-center py-2 px-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {channels.map((c, i) => (
                  <tr key={i} className="border-t border-slate-700/50">
                    <td className="py-2 px-3 text-white">{c.name}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{c.members}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{c.active}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{c.msgs_per_day.toFixed(1)}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{c.thread_depth.toFixed(1)}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{(c.response_rate * 100).toFixed(0)}%</td>
                    <td className="text-center py-2 px-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${c.healthy ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}`}>
                        {c.healthy ? 'Healthy' : 'Low'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!health && !loading && connectors.length === 0 && !showSetup && (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">💬</div>
          <h3 className="text-lg font-semibold text-white mb-2">Communication Analytics Ready</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Connect Slack or Microsoft Teams to analyze messaging patterns, response times,
            after-hours communication, and channel engagement health.
          </p>
        </div>
      )}
    </div>
  );
}
