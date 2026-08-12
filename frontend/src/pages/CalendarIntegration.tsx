import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface MeetingHealth {
  score: number;
  label: string;
  meeting_hours_per_week: number;
  focus_hours_per_week: number;
  after_hours_pct: number;
  back_to_back_rate: number;
  one_on_one_ratio: number;
  recurring_burden_pct: number;
  fragmentation_score: number;
  recommendations: string[];
}

interface DailyEntry {
  date: string;
  meetings: number;
  meeting_hours: number;
  focus_hours: number;
  after_hours: number;
  back_to_back: number;
  largest_focus_block_min: number;
}

interface ConnectorInfo {
  name: string;
  type: string;
}

const METRIC_CARDS = [
  { key: 'meeting_hours_per_week', label: 'Meeting Hours/Week', unit: 'h', threshold: 15, invert: true },
  { key: 'focus_hours_per_week', label: 'Focus Hours/Week', unit: 'h', threshold: 10, invert: false },
  { key: 'after_hours_pct', label: 'After-Hours', unit: '%', threshold: 15, invert: true },
  { key: 'recurring_burden_pct', label: 'Recurring Meetings', unit: '%', threshold: 60, invert: true },
  { key: 'fragmentation_score', label: 'Fragmentation', unit: '', threshold: 50, invert: true },
  { key: 'one_on_one_ratio', label: '1:1 Ratio', unit: '', threshold: 0.15, invert: false },
] as const;

export default function CalendarIntegration() {
  const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
  const [health, setHealth] = useState<MeetingHealth | null>(null);
  const [daily, setDaily] = useState<DailyEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSetup, setShowSetup] = useState(false);
  const [setupType, setSetupType] = useState<'google' | 'outlook'>('google');
  const [setupName, setSetupName] = useState('');

  const fetchConnectors = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<{ connectors: ConnectorInfo[] }>('/api/v1/calendar/connectors');
      setConnectors(data.connectors || []);
    } catch {
      setConnectors([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchConnectors(); }, [fetchConnectors]);

  const handleConnect = async () => {
    try {
      await axios.post('/api/v1/calendar/connectors', { type: setupType, name: setupName || setupType });
      setShowSetup(false);
      fetchConnectors();
    } catch { /* UI feedback */ }
  };

  const fetchHealth = async (connName: string) => {
    try {
      const [hRes, dRes] = await Promise.allSettled([
        axios.get<MeetingHealth>(`/api/v1/calendar/connectors/${connName}/health`, { params: { user_email: 'me', days: 14 } }),
        axios.get<{ daily: DailyEntry[] }>(`/api/v1/calendar/connectors/${connName}/daily`, { params: { user_email: 'me', days: 14 } }),
      ]);
      if (hRes.status === 'fulfilled') setHealth(hRes.value.data);
      if (dRes.status === 'fulfilled') setDaily(dRes.value.data.daily || []);
    } catch { /* handled */ }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Calendar Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">
            Meeting load, focus time, after-hours work & calendar fragmentation
          </p>
        </div>
        <button
          onClick={() => setShowSetup(!showSetup)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm transition-colors"
        >
          {showSetup ? 'Cancel' : '+ Connect Calendar'}
        </button>
      </div>

      {/* Setup */}
      {showSetup && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">Connect Calendar</h3>
          <div className="grid grid-cols-2 gap-3 max-w-md">
            <button
              onClick={() => setSetupType('google')}
              className={`p-4 rounded-lg border text-center ${setupType === 'google' ? 'border-indigo-500 bg-indigo-500/20' : 'border-slate-700 bg-slate-800'}`}
            >
              <div className="text-2xl mb-1">📅</div>
              <div className="text-xs text-slate-300">Google Calendar</div>
            </button>
            <button
              onClick={() => setSetupType('outlook')}
              className={`p-4 rounded-lg border text-center ${setupType === 'outlook' ? 'border-indigo-500 bg-indigo-500/20' : 'border-slate-700 bg-slate-800'}`}
            >
              <div className="text-2xl mb-1">📧</div>
              <div className="text-xs text-slate-300">Outlook</div>
            </button>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Connector Name</label>
            <input
              type="text"
              value={setupName}
              onChange={(e) => setSetupName(e.target.value)}
              placeholder={`my-${setupType}-calendar`}
              className="w-full max-w-xs bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <button onClick={handleConnect} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm">
            Connect
          </button>
        </div>
      )}

      {/* Connected Calendars */}
      <div className="grid grid-cols-2 gap-4">
        {['google', 'outlook'].map((type) => {
          const connected = connectors.filter(c => c.type.toLowerCase().includes(type));
          return (
            <div key={type} className={`border rounded-xl p-5 ${connected.length ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-800/30 border-slate-700/50'}`}>
              <div className="text-2xl mb-2">{type === 'google' ? '📅' : '📧'}</div>
              <div className="text-sm font-medium text-white">{type === 'google' ? 'Google Calendar' : 'Outlook'}</div>
              <div className={`text-xs mt-1 ${connected.length ? 'text-emerald-400' : 'text-slate-500'}`}>
                {connected.length ? `${connected.length} connected` : 'Not connected'}
              </div>
              {connected.map(c => (
                <button key={c.name} onClick={() => fetchHealth(c.name)} className="text-xs text-indigo-400 hover:text-indigo-300 mt-2 block">
                  Analyze →
                </button>
              ))}
            </div>
          );
        })}
      </div>

      {/* Meeting Health Score */}
      {health && (
        <>
          <div className={`border rounded-xl p-6 text-center ${
            health.score >= 70 ? 'bg-emerald-500/10 border-emerald-500/30' :
            health.score >= 50 ? 'bg-amber-500/10 border-amber-500/30' :
            'bg-red-500/10 border-red-500/30'
          }`}>
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Meeting Health Score</div>
            <div className={`text-5xl font-bold mb-1 ${
              health.score >= 70 ? 'text-emerald-400' : health.score >= 50 ? 'text-amber-400' : 'text-red-400'
            }`}>
              {health.score}
            </div>
            <div className="text-sm text-slate-300">{health.label}</div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {METRIC_CARDS.map((m) => {
              const val = health[m.key as keyof MeetingHealth] as number;
              const ok = m.invert ? val < m.threshold : val > m.threshold;
              return (
                <div key={m.key} className="bg-slate-800/50 border border-slate-700 rounded-xl p-3 text-center">
                  <div className="text-xs text-slate-400 mb-1">{m.label}</div>
                  <div className={`text-xl font-bold ${ok ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {typeof val === 'number' ? (val < 1 && m.unit === '' ? `${(val * 100).toFixed(0)}%` : `${val}${m.unit}`) : '--'}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recommendations */}
          {health.recommendations.length > 0 && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
              <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-3">Recommendations</h3>
              <ul className="space-y-2">
                {health.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                    <span className="text-indigo-400 mt-0.5">-</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Daily Breakdown */}
      {daily.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Daily Meeting Load</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-xs">
                  <th className="text-left py-2 px-3">Date</th>
                  <th className="text-center py-2 px-2">Meetings</th>
                  <th className="text-center py-2 px-2">Mtg Hours</th>
                  <th className="text-center py-2 px-2">Focus Hours</th>
                  <th className="text-center py-2 px-2">After Hrs</th>
                  <th className="text-center py-2 px-2">B2B</th>
                  <th className="text-center py-2 px-2">Longest Focus</th>
                </tr>
              </thead>
              <tbody>
                {daily.map((d) => (
                  <tr key={d.date} className="border-t border-slate-700/50">
                    <td className="py-2 px-3 text-white">{d.date}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{d.meetings}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{d.meeting_hours}h</td>
                    <td className={`text-center py-2 px-2 ${d.focus_hours < 2 ? 'text-red-400' : 'text-emerald-400'}`}>{d.focus_hours}h</td>
                    <td className={`text-center py-2 px-2 ${d.after_hours > 0 ? 'text-amber-400' : 'text-slate-500'}`}>{d.after_hours}</td>
                    <td className={`text-center py-2 px-2 ${d.back_to_back > 0 ? 'text-amber-400' : 'text-slate-500'}`}>{d.back_to_back}</td>
                    <td className="text-center py-2 px-2 text-slate-300">{d.largest_focus_block_min}min</td>
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
          <div className="text-5xl mb-4">📅</div>
          <h3 className="text-lg font-semibold text-white mb-2">Calendar Intelligence Ready</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Connect Google Calendar or Outlook to analyze meeting load, focus time, after-hours work,
            and get personalized recommendations for healthier meeting habits.
          </p>
        </div>
      )}
    </div>
  );
}
