import { useState, useEffect, useCallback } from 'react';
import axios from '../api/axios';

interface CoachingRec {
  type: 'urgent' | 'development' | 'strength';
  title: string;
  message: string;
}

interface GrowthArea {
  area: string;
  current: number;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
}

interface CoachingProfile {
  user_id: string;
  user_name: string;
  personality_profile: Record<string, number>;
  work_style: Record<string, string>;
  stress_indicators: { level: string; score: number; indicators: string[] };
  growth_areas: GrowthArea[];
  coaching_recommendations: CoachingRec[];
  communication_guide: Record<string, string>;
  team_context: { team_count: number; team_names: string[] };
}

interface DigitalTwin {
  user_id: string;
  user_name: string;
  behavioral_dna: Record<string, number>;
  work_preferences: Record<string, string>;
  collaboration_style: Record<string, string>;
  stress_resilience: number;
  change_adaptability: number;
  engagement_pattern: { status: string; total_responses: number; trend: string };
  predicted_responses: Record<string, { reaction: string; recommendation: string }>;
}

const TRAIT_LABELS: Record<string, string> = {
  openness: 'Openness',
  conscientiousness: 'Conscientiousness',
  extraversion: 'Extraversion',
  agreeableness: 'Agreeableness',
  neuroticism: 'Neuroticism',
};

const REC_TYPE_STYLES: Record<string, { icon: string; bg: string; color: string }> = {
  urgent: { icon: '🚨', bg: 'bg-red-500/10 border-red-500/30', color: 'text-red-300' },
  development: { icon: '📈', bg: 'bg-amber-500/10 border-amber-500/30', color: 'text-amber-300' },
  strength: { icon: '⭐', bg: 'bg-emerald-500/10 border-emerald-500/30', color: 'text-emerald-300' },
};

export default function AIBehavioralCoach() {
  const [profile, setProfile] = useState<CoachingProfile | null>(null);
  const [twin, setTwin] = useState<DigitalTwin | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'coach' | 'twin' | 'guide'>('coach');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [profileRes, twinRes] = await Promise.allSettled([
        axios.get<CoachingProfile>('/api/v1/ai-coach/me'),
        axios.get<DigitalTwin>('/api/v1/digital-twin/me'),
      ]);
      if (profileRes.status === 'fulfilled') setProfile(profileRes.value.data);
      if (twinRes.status === 'fulfilled') setTwin(twinRes.value.data);
    } catch { /* empty state */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <div className="animate-spin w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-slate-400 text-sm">Building your behavioral profile...</p>
        </div>
      </div>
    );
  }

  const traits = profile?.personality_profile || twin?.behavioral_dna || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">AI Behavioral Coach</h1>
        <p className="text-slate-400 text-sm mt-1">
          Personalized coaching & Digital Twin powered by your behavioral data
        </p>
      </div>

      {/* Big Five Radar (simplified bar chart) */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-violet-400 uppercase tracking-wider mb-4">
          Behavioral DNA
        </h3>
        <div className="space-y-3">
          {Object.entries(TRAIT_LABELS).map(([key, label]) => {
            const val = traits[key] ?? 50;
            return (
              <div key={key} className="flex items-center gap-3">
                <div className="w-36 text-sm text-slate-300">{label}</div>
                <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 rounded-full transition-all"
                    style={{ width: `${val}%` }}
                  />
                </div>
                <div className="w-12 text-right text-sm font-mono text-slate-300">{val}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700">
        {(['coach', 'twin', 'guide'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-3 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'text-violet-400 border-b-2 border-violet-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab === 'coach' ? 'Coaching' : tab === 'twin' ? 'Digital Twin' : 'Communication Guide'}
          </button>
        ))}
      </div>

      {/* Coach Tab */}
      {activeTab === 'coach' && profile && (
        <div className="space-y-4">
          {/* Stress Level */}
          <div className={`border rounded-xl p-4 ${
            profile.stress_indicators.level === 'high' ? 'bg-red-500/10 border-red-500/30' :
            profile.stress_indicators.level === 'moderate' ? 'bg-amber-500/10 border-amber-500/30' :
            'bg-emerald-500/10 border-emerald-500/30'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white">Stress Level</span>
              <span className={`text-sm font-bold ${
                profile.stress_indicators.level === 'high' ? 'text-red-400' :
                profile.stress_indicators.level === 'moderate' ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {profile.stress_indicators.level.toUpperCase()}
              </span>
            </div>
            {profile.stress_indicators.indicators.map((ind, i) => (
              <p key={i} className="text-xs text-slate-400 mt-1">- {ind}</p>
            ))}
          </div>

          {/* Coaching Recommendations */}
          <h3 className="text-sm font-semibold text-white">Coaching Recommendations</h3>
          <div className="space-y-3">
            {profile.coaching_recommendations.map((rec, i) => {
              const style = REC_TYPE_STYLES[rec.type] || REC_TYPE_STYLES.development;
              return (
                <div key={i} className={`border rounded-xl p-4 ${style.bg}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span>{style.icon}</span>
                    <span className={`text-sm font-medium ${style.color}`}>{rec.title}</span>
                  </div>
                  <p className="text-sm text-slate-300">{rec.message}</p>
                </div>
              );
            })}
          </div>

          {/* Growth Areas */}
          {profile.growth_areas.length > 0 && (
            <>
              <h3 className="text-sm font-semibold text-white mt-4">Growth Areas</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {profile.growth_areas.map((area, i) => (
                  <div key={i} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-white font-medium">{area.area}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        area.priority === 'high' ? 'bg-red-500/20 text-red-300' :
                        area.priority === 'medium' ? 'bg-amber-500/20 text-amber-300' :
                        'bg-slate-500/20 text-slate-300'
                      }`}>
                        {area.priority}
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden mb-2">
                      <div
                        className="h-full bg-violet-500 rounded-full"
                        style={{ width: `${area.current}%` }}
                      />
                    </div>
                    <p className="text-xs text-slate-400">{area.suggestion}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Digital Twin Tab */}
      {activeTab === 'twin' && (twin || profile) && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
              <div className="text-xs text-slate-400 mb-1">Stress Resilience</div>
              <div className="text-2xl font-bold text-emerald-400">
                {twin?.stress_resilience ?? (100 - (traits.neuroticism ?? 50))}
              </div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
              <div className="text-xs text-slate-400 mb-1">Change Adaptability</div>
              <div className="text-2xl font-bold text-cyan-400">
                {twin?.change_adaptability ?? traits.openness ?? 50}
              </div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
              <div className="text-xs text-slate-400 mb-1">Engagement</div>
              <div className={`text-2xl font-bold ${
                twin?.engagement_pattern.status === 'active' ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {twin?.engagement_pattern.status ?? 'N/A'}
              </div>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center">
              <div className="text-xs text-slate-400 mb-1">Team Role</div>
              <div className="text-lg font-bold text-violet-400">
                {profile?.work_style?.team_role_affinity ?? 'Specialist'}
              </div>
            </div>
          </div>

          {/* Predicted Responses */}
          {twin?.predicted_responses && (
            <>
              <h3 className="text-sm font-semibold text-white">Predicted Behavioral Responses</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(twin.predicted_responses).map(([scenario, pred]) => (
                  <div key={scenario} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                    <div className="text-xs text-slate-400 mb-1">
                      {scenario.replace(/to_/g, '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                    <div className="text-sm font-medium text-white mb-1">
                      Reaction: <span className="text-violet-400">{pred.reaction}</span>
                    </div>
                    <p className="text-xs text-slate-400">{pred.recommendation}</p>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Work Preferences */}
          {(twin?.work_preferences || profile?.work_style) && (
            <>
              <h3 className="text-sm font-semibold text-white">Work Preferences</h3>
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(twin?.work_preferences || profile?.work_style || {}).map(([k, v]) => (
                    <div key={k}>
                      <div className="text-xs text-slate-500">{k.replace(/_/g, ' ')}</div>
                      <div className="text-sm text-white font-medium">{String(v)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Communication Guide Tab */}
      {activeTab === 'guide' && profile?.communication_guide && (
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-violet-500/10 to-indigo-500/10 border border-violet-500/30 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-violet-400 mb-1">
              How to Work With {profile.user_name}
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Share this guide with teammates for better collaboration
            </p>

            <div className="space-y-4">
              {Object.entries(profile.communication_guide).map(([key, value]) => (
                <div key={key} className="flex items-start gap-3">
                  <div className="w-40 text-xs text-slate-400 pt-0.5">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="text-sm text-white">{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Collaboration Style */}
          {twin?.collaboration_style && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-white mb-3">Collaboration Style</h3>
              <div className="space-y-3">
                {Object.entries(twin.collaboration_style).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3 text-sm">
                    <span className="text-slate-400 w-28">{key.replace(/_/g, ' ')}</span>
                    <span className="text-white">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Data State */}
      {!profile && !twin && !loading && (
        <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-10 text-center">
          <div className="text-5xl mb-4">🤖</div>
          <h3 className="text-lg font-semibold text-white mb-2">AI Coach Ready</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Complete personality assessments to activate your AI Behavioral Coach and Digital Twin profile.
          </p>
        </div>
      )}
    </div>
  );
}
