import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface Connector {
  name: string;
  type: string;
  source: string;
}

interface WorkloadItem {
  user: string;
  email: string;
  open_items: number;
  in_progress: number;
  story_points: number;
  overcommitment_score: number;
}

interface BehavioralSignals {
  connector: string;
  project_key: string;
  total_items: number;
  workload: WorkloadItem[];
  cycle_times: { avg_hours: number; median_hours: number; trend: string; count: number };
  collaboration_edges: { person_a: string; person_b: string; shared_contexts: number }[];
}

const CONNECTOR_TYPES = [
  { id: 'jira', name: 'Jira', icon: '🔵', fields: ['base_url', 'email', 'api_token'] },
  { id: 'azure_devops', name: 'Azure DevOps', icon: '🟦', fields: ['organization', 'project', 'pat'] },
  { id: 'asana', name: 'Asana', icon: '🟠', fields: ['access_token'] },
  { id: 'monday', name: 'Monday.com', icon: '🟡', fields: ['api_key'] },
];

export default function WorkSystemsIntegration() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedType, setSelectedType] = useState('jira');
  const [formData, setFormData] = useState<Record<string, string>>({ name: '' });
  const [signals, setSignals] = useState<BehavioralSignals | null>(null);
  const [signalsLoading, setSignalsLoading] = useState(false);

  const fetchConnectors = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ connectors: Connector[] }>('/api/v1/work-systems/connectors');
      setConnectors(data.connectors || []);
    } catch {
      setConnectors([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchConnectors(); }, [fetchConnectors]);

  const handleAddConnector = async () => {
    try {
      const payload = { type: selectedType, ...formData };
      const { data } = await axios.post<{ success: boolean }>('/api/v1/work-systems/connectors', payload);
      if (data.success) {
        setShowAddForm(false);
        setFormData({ name: '' });
        fetchConnectors();
      }
    } catch { /* handled by UI */ }
  };

  const fetchSignals = async (connectorName: string) => {
    setSignalsLoading(true);
    try {
      const { data } = await axios.get<BehavioralSignals>(
        `/api/v1/work-systems/connectors/${connectorName}/behavioral-signals`,
        { params: { project_key: 'DEFAULT' } }
      );
      setSignals(data);
    } catch {
      setSignals(null);
    } finally {
      setSignalsLoading(false);
    }
  };

  const typeConfig = CONNECTOR_TYPES.find(t => t.id === selectedType);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Work Systems Integration</h1>
          <p className="text-slate-400 text-sm mt-1">
            Connect Jira, Azure DevOps, Asana, or Monday.com to derive behavioral signals
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm transition-colors"
        >
          {showAddForm ? 'Cancel' : '+ Add Connector'}
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">New Work System Connector</h3>

          <div className="grid grid-cols-4 gap-3">
            {CONNECTOR_TYPES.map((ct) => (
              <button
                key={ct.id}
                onClick={() => setSelectedType(ct.id)}
                className={`p-3 rounded-lg border text-center transition-colors ${
                  selectedType === ct.id
                    ? 'border-indigo-500 bg-indigo-500/20 text-white'
                    : 'border-slate-700 bg-slate-800 text-slate-400 hover:border-slate-600'
                }`}
              >
                <div className="text-xl mb-1">{ct.icon}</div>
                <div className="text-xs">{ct.name}</div>
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Connector Name</label>
              <input
                type="text"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm"
                placeholder="e.g., production-jira"
              />
            </div>
            {typeConfig?.fields.map((field) => (
              <div key={field}>
                <label className="text-xs text-slate-400 block mb-1">
                  {field.replace(/_/g, ' ')}
                </label>
                <input
                  type={field.includes('token') || field.includes('key') || field === 'pat' ? 'password' : 'text'}
                  value={formData[field] || ''}
                  onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm"
                  placeholder={field}
                />
              </div>
            ))}
          </div>

          <button
            onClick={handleAddConnector}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm transition-colors"
          >
            Connect & Test
          </button>
        </div>
      )}

      {/* Connected Systems */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {CONNECTOR_TYPES.map((ct) => {
          const connected = connectors.filter(c => c.type.toLowerCase().includes(ct.id.replace('_', '')));
          return (
            <div key={ct.id} className={`border rounded-xl p-5 ${
              connected.length > 0
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : 'bg-slate-800/30 border-slate-700/50'
            }`}>
              <div className="text-2xl mb-2">{ct.icon}</div>
              <div className="text-sm font-medium text-white">{ct.name}</div>
              <div className={`text-xs mt-1 ${connected.length > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
                {connected.length > 0 ? `${connected.length} connected` : 'Not connected'}
              </div>
              {connected.map((c) => (
                <button
                  key={c.name}
                  onClick={() => fetchSignals(c.name)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 mt-2 block"
                >
                  View signals →
                </button>
              ))}
            </div>
          );
        })}
      </div>

      {/* No Connectors */}
      {!loading && connectors.length === 0 && !showAddForm && (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🔌</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Work Systems Connected</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Connect your project management tools to extract behavioral signals like workload distribution,
            cycle time trends, and collaboration patterns.
          </p>
        </div>
      )}

      {/* Behavioral Signals */}
      {signalsLoading && (
        <div className="text-center py-8 text-slate-400 text-sm">Loading behavioral signals...</div>
      )}
      {signals && !signalsLoading && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-white">
            Behavioral Signals — {signals.connector} ({signals.total_items} items)
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Cycle Times */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-2">Cycle Time</div>
              <div className="text-2xl font-bold text-white">{signals.cycle_times.avg_hours}h</div>
              <div className="text-xs text-slate-500">avg ({signals.cycle_times.median_hours}h median)</div>
              <div className={`text-xs mt-1 ${
                signals.cycle_times.trend === 'improving' ? 'text-emerald-400' :
                signals.cycle_times.trend === 'slowing' ? 'text-red-400' : 'text-slate-400'
              }`}>
                Trend: {signals.cycle_times.trend}
              </div>
            </div>

            {/* Workload */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-2">Team Workload</div>
              <div className="text-2xl font-bold text-white">{signals.workload.length}</div>
              <div className="text-xs text-slate-500">active contributors</div>
              {signals.workload.filter(w => w.overcommitment_score > 70).length > 0 && (
                <div className="text-xs text-red-400 mt-1">
                  {signals.workload.filter(w => w.overcommitment_score > 70).length} overcommitted
                </div>
              )}
            </div>

            {/* Collaboration */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
              <div className="text-xs text-slate-400 mb-2">Collaboration Pairs</div>
              <div className="text-2xl font-bold text-cyan-400">{signals.collaboration_edges.length}</div>
              <div className="text-xs text-slate-500">shared work contexts</div>
            </div>
          </div>

          {/* Workload Table */}
          {signals.workload.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 text-xs border-b border-slate-700">
                    <th className="text-left py-3 px-4">Person</th>
                    <th className="text-center py-3 px-3">Open</th>
                    <th className="text-center py-3 px-3">In Progress</th>
                    <th className="text-center py-3 px-3">Story Pts</th>
                    <th className="text-center py-3 px-3">Overcommitment</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.workload.slice(0, 15).map((w, i) => (
                    <tr key={i} className="border-t border-slate-700/50">
                      <td className="py-2 px-4 text-white">{w.user}</td>
                      <td className="text-center py-2 px-3 text-slate-300">{w.open_items}</td>
                      <td className="text-center py-2 px-3 text-slate-300">{w.in_progress}</td>
                      <td className="text-center py-2 px-3 text-slate-300">{w.story_points}</td>
                      <td className="text-center py-2 px-3">
                        <span className={`text-xs font-mono ${
                          w.overcommitment_score > 70 ? 'text-red-400' :
                          w.overcommitment_score > 40 ? 'text-amber-400' : 'text-emerald-400'
                        }`}>
                          {w.overcommitment_score}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
