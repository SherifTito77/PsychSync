import { useState, useEffect, useCallback } from 'react';
import { networkAnalysisService, PersonalityNetworkInsight, CommunityProfile } from '../services/networkAnalysisService';

const INSIGHT_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  quiet_connector: { icon: '🤫', color: 'text-blue-300', bg: 'bg-blue-500/10 border-blue-500/30' },
  underutilized_performer: { icon: '💎', color: 'text-emerald-300', bg: 'bg-emerald-500/10 border-emerald-500/30' },
  friction_bridge: { icon: '⚡', color: 'text-amber-300', bg: 'bg-amber-500/10 border-amber-500/30' },
  innovation_catalyst: { icon: '🚀', color: 'text-purple-300', bg: 'bg-purple-500/10 border-purple-500/30' },
  burnout_risk: { icon: '🔥', color: 'text-red-300', bg: 'bg-red-500/10 border-red-500/30' },
};

const TRAIT_LABELS: Record<string, { label: string; color: string }> = {
  openness: { label: 'Openness', color: 'bg-purple-500' },
  conscientiousness: { label: 'Conscientiousness', color: 'bg-blue-500' },
  extraversion: { label: 'Extraversion', color: 'bg-amber-500' },
  agreeableness: { label: 'Agreeableness', color: 'bg-emerald-500' },
  neuroticism: { label: 'Neuroticism', color: 'bg-red-500' },
};

export default function PersonalityNetwork() {
  const [insights, setInsights] = useState<PersonalityNetworkInsight[]>([]);
  const [communityProfiles, setCommunityProfiles] = useState<CommunityProfile[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await networkAnalysisService.getPersonalityNetworkInsights('default', 60);
      setInsights(data.insights);
      setCommunityProfiles(data.community_profiles);
    } catch {
      setInsights([]);
      setCommunityProfiles([]);
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
          <p className="text-slate-400 text-sm">Analyzing personality-network overlay...</p>
        </div>
      </div>
    );
  }

  const groupedInsights = insights.reduce<Record<string, PersonalityNetworkInsight[]>>((acc, ins) => {
    (acc[ins.type] ||= []).push(ins);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Personality x Network Overlay</h1>
          <p className="text-slate-400 text-sm mt-1">
            Big Five personality traits overlaid on network positions — reveals quiet connectors, friction bridges, and burnout risks
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-sm transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Insight Count Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(INSIGHT_CONFIG).map(([type, cfg]) => {
          const count = groupedInsights[type]?.length || 0;
          return (
            <div key={type} className={`${cfg.bg} border rounded-xl p-4 text-center`}>
              <div className="text-2xl mb-1">{cfg.icon}</div>
              <div className={`text-xl font-bold ${cfg.color}`}>{count}</div>
              <div className="text-xs text-slate-400 capitalize">{type.replace(/_/g, ' ')}</div>
            </div>
          );
        })}
      </div>

      {/* Insights */}
      {insights.length === 0 ? (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🧠</div>
          <h3 className="text-lg font-semibold text-white mb-2">No Personality-Network Insights Yet</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Team members need to complete Big Five personality assessments to enable overlay analysis. The system matches personality traits against network positions to generate insights.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-white">
            Actionable Insights ({insights.length})
          </h3>
          {insights.map((ins, i) => {
            const cfg = INSIGHT_CONFIG[ins.type] || { icon: '📌', color: 'text-slate-300', bg: 'bg-slate-500/10 border-slate-500/30' };
            return (
              <div key={i} className={`${cfg.bg} border rounded-xl p-4`}>
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{cfg.icon}</span>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-sm font-semibold ${cfg.color}`}>{ins.name}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700/50 text-slate-400 capitalize">
                        {ins.type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300">{ins.message}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Community Personality Profiles */}
      {communityProfiles.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-white">Community Personality Profiles</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {communityProfiles.map((cp) => (
              <div key={cp.community_id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-semibold text-white">Community {cp.community_id + 1}</h4>
                  <span className="text-xs text-slate-400">{cp.size} members</span>
                </div>
                <div className="space-y-2">
                  {Object.entries(cp.avg_personality).map(([trait, score]) => {
                    const traitCfg = TRAIT_LABELS[trait];
                    return (
                      <div key={trait} className="flex items-center gap-3">
                        <span className="text-xs text-slate-400 w-28 text-right">{traitCfg?.label || trait}</span>
                        <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${traitCfg?.color || 'bg-slate-500'}`}
                            style={{ width: `${Math.min(score, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono text-slate-300 w-10">{score.toFixed(0)}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="mt-3 text-xs text-slate-400">
                  Dominant trait: <span className="text-white capitalize">{cp.dominant_trait}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
