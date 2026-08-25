import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface OrgMember {
  id: string;
  full_name: string;
  email: string;
}

interface Nomination {
  nominee_id: string;
  network_type: 'advice' | 'trust' | 'energy' | 'collaboration';
  strength: number;
}

const NETWORK_TYPES = [
  { key: 'advice' as const, label: 'Advice Network', question: 'Who do you go to for work-related advice?', icon: '💡', color: 'purple' },
  { key: 'trust' as const, label: 'Trust Network', question: 'Who do you trust to share concerns or challenges with?', icon: '🤝', color: 'blue' },
  { key: 'energy' as const, label: 'Energy Network', question: 'Who energizes and motivates you at work?', icon: '⚡', color: 'amber' },
  { key: 'collaboration' as const, label: 'Collaboration Network', question: 'Who do you collaborate with most frequently?', icon: '🔗', color: 'emerald' },
];

export default function CollaborationSurvey() {
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [nominations, setNominations] = useState<Nomination[]>([]);
  const [currentType, setCurrentType] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    axios.get('/api/v1/users?limit=200').then(({ data }) => {
      const list = Array.isArray(data) ? data : data.users || [];
      setMembers(list);
    }).catch(() => setMembers([]));
  }, []);

  const networkType = NETWORK_TYPES[currentType];
  const selectedForType = nominations.filter(n => n.network_type === networkType.key);

  const toggleNomination = (memberId: string) => {
    const exists = nominations.find(
      n => n.nominee_id === memberId && n.network_type === networkType.key
    );
    if (exists) {
      setNominations(nominations.filter(
        n => !(n.nominee_id === memberId && n.network_type === networkType.key)
      ));
    } else {
      setNominations([...nominations, {
        nominee_id: memberId,
        network_type: networkType.key,
        strength: 3,
      }]);
    }
  };

  const updateStrength = (memberId: string, strength: number) => {
    setNominations(nominations.map(n =>
      n.nominee_id === memberId && n.network_type === networkType.key
        ? { ...n, strength }
        : n
    ));
  };

  const handleSubmit = async () => {
    if (nominations.length === 0) return;
    setLoading(true);
    try {
      await axios.post('/api/v1/organizational-network/survey/default', {
        nominations,
        survey_round: new Date().toISOString().slice(0, 7),
      });
      setSubmitted(true);
    } catch {
      alert('Failed to submit survey. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredMembers = members.filter(m =>
    !search || m.full_name?.toLowerCase().includes(search.toLowerCase()) || m.email?.toLowerCase().includes(search.toLowerCase())
  );

  if (submitted) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="text-6xl">🎉</div>
          <h2 className="text-2xl font-bold text-white">Survey Submitted</h2>
          <p className="text-slate-400">
            Thank you! Your responses help build a more accurate organizational network map.
            <br />You nominated <span className="text-teal-400 font-semibold">{nominations.length}</span> connections across {NETWORK_TYPES.length} network types.
          </p>
          <button
            onClick={() => { setSubmitted(false); setNominations([]); setCurrentType(0); }}
            className="px-6 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg transition-colors"
          >
            Take Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white">Collaboration Network Survey</h1>
        <p className="text-slate-400 text-sm mt-1">
          Help map how your organization really works. Your responses are used to build network insights — individual nominations are not shared.
        </p>
      </div>

      {/* Progress */}
      <div className="flex gap-2">
        {NETWORK_TYPES.map((nt, i) => (
          <button
            key={nt.key}
            onClick={() => setCurrentType(i)}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
              i === currentType
                ? `bg-${nt.color}-500/20 border border-${nt.color}-500/50 text-${nt.color}-300`
                : 'bg-slate-800/50 border border-slate-700 text-slate-400 hover:text-slate-300'
            }`}
          >
            <span className="text-lg mr-1">{nt.icon}</span>
            {nt.label}
            {nominations.filter(n => n.network_type === nt.key).length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-teal-500/20 text-teal-300 rounded-full text-xs">
                {nominations.filter(n => n.network_type === nt.key).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Question */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-1">
          {networkType.icon} {networkType.question}
        </h2>
        <p className="text-xs text-slate-400">Select up to 10 people and rate connection strength (1-5)</p>
      </div>

      {/* Search */}
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search colleagues..."
        className="w-full bg-slate-800 border border-slate-700 text-slate-300 rounded-lg px-4 py-3 text-sm"
      />

      {/* Member List */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl overflow-hidden max-h-[400px] overflow-y-auto">
        {filteredMembers.slice(0, 50).map(member => {
          const isSelected = selectedForType.some(n => n.nominee_id === member.id);
          const nomination = selectedForType.find(n => n.nominee_id === member.id);
          return (
            <div
              key={member.id}
              className={`flex items-center justify-between px-4 py-3 border-b border-slate-700/50 cursor-pointer transition-colors ${
                isSelected ? 'bg-teal-900/20' : 'hover:bg-slate-700/30'
              }`}
              onClick={() => toggleNomination(member.id)}
            >
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  isSelected ? 'bg-teal-500 text-white' : 'bg-slate-700 text-slate-300'
                }`}>
                  {isSelected ? '✓' : (member.full_name?.[0] || member.email[0]).toUpperCase()}
                </div>
                <div>
                  <div className="text-sm text-white">{member.full_name || member.email}</div>
                  <div className="text-xs text-slate-500">{member.email}</div>
                </div>
              </div>
              {isSelected && nomination && (
                <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
                  {[1, 2, 3, 4, 5].map(s => (
                    <button
                      key={s}
                      onClick={() => updateStrength(member.id, s)}
                      className={`w-7 h-7 rounded text-xs font-medium transition-colors ${
                        s <= nomination.strength
                          ? 'bg-teal-500 text-white'
                          : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentType(Math.max(0, currentType - 1))}
          disabled={currentType === 0}
          className="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg disabled:opacity-30 hover:bg-slate-600 transition-colors"
        >
          Previous
        </button>
        <span className="text-sm text-slate-400">
          {nominations.length} total nominations
        </span>
        {currentType < NETWORK_TYPES.length - 1 ? (
          <button
            onClick={() => setCurrentType(currentType + 1)}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg transition-colors"
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={nominations.length === 0 || loading}
            className="px-6 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg disabled:opacity-50 transition-colors"
          >
            {loading ? 'Submitting...' : 'Submit Survey'}
          </button>
        )}
      </div>
    </div>
  );
}
