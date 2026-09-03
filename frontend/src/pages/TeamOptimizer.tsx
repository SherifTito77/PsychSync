import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import api from '../services/api';
import { useFormPersistence, useSessionExpiryHandler } from '../hooks/useFormPersistence';
import { TeamRadarChart } from '../components/teams/team-optimizer/components/TeamRadarChart';
import { SkillGapAnalysis } from '../components/teams/team-optimizer/components/SkillGapAnalysis';

// --- Extended traits configuration ---
const PRIMARY_TRAITS = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];

const SECONDARY_NUMERIC_TRAITS = [
  'empathy', 'self_regulation', 'social_awareness',
  'risk_tolerance', 'autonomy_preference', 'detail_orientation',
  'feedback_receptivity', 'leadership_emergence', 'cognitive_load_preference',
];

const CONFLICT_STYLES = ['competing', 'avoiding', 'collaborating', 'accommodating', 'compromising'];

const TRAIT_LABELS: Record<string, string> = {
  empathy: 'Empathy', self_regulation: 'Self-Regulation', social_awareness: 'Social Awareness',
  risk_tolerance: 'Risk Tolerance', autonomy_preference: 'Autonomy', detail_orientation: 'Detail Orientation',
  feedback_receptivity: 'Feedback Receptivity', leadership_emergence: 'Leadership', cognitive_load_preference: 'Cognitive Load Pref.',
};

const ROLE_PRESETS: Record<string, Record<string, number | string>> = {
  developer: { openness: 0.6, conscientiousness: 0.7, extraversion: 0.4, agreeableness: 0.5, neuroticism: 0.3, risk_tolerance: 0.5, autonomy_preference: 0.7, detail_orientation: 0.7, feedback_receptivity: 0.7, cognitive_load_preference: 0.7 },
  designer: { openness: 0.85, conscientiousness: 0.5, extraversion: 0.5, agreeableness: 0.6, neuroticism: 0.3, empathy: 0.8, detail_orientation: 0.6, feedback_receptivity: 0.8, cognitive_load_preference: 0.5 },
  pm: { openness: 0.6, conscientiousness: 0.75, extraversion: 0.7, agreeableness: 0.65, neuroticism: 0.25, empathy: 0.7, social_awareness: 0.8, risk_tolerance: 0.6, leadership_emergence: 0.7, cognitive_load_preference: 0.8 },
  qa: { openness: 0.4, conscientiousness: 0.85, extraversion: 0.4, agreeableness: 0.5, neuroticism: 0.3, detail_orientation: 0.9, autonomy_preference: 0.5, feedback_receptivity: 0.6, cognitive_load_preference: 0.6 },
  devops: { openness: 0.5, conscientiousness: 0.8, extraversion: 0.4, agreeableness: 0.5, neuroticism: 0.2, self_regulation: 0.8, risk_tolerance: 0.4, autonomy_preference: 0.8, cognitive_load_preference: 0.8 },
  lead: { openness: 0.6, conscientiousness: 0.7, extraversion: 0.65, agreeableness: 0.6, neuroticism: 0.2, empathy: 0.7, social_awareness: 0.75, self_regulation: 0.8, leadership_emergence: 0.85, feedback_receptivity: 0.7 },
};

// Team Optimizer Component with form persistence
export default function TeamOptimizer() {
  const [optimization, setOptimization] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMembers, setSelectedMembers] = useState(new Set());
  const hasSanitizedRef = useRef(false);
  const [expandedTraits, setExpandedTraits] = useState<Set<number>>(new Set());

  const toggleSecondaryTraits = (memberId: number) => {
    setExpandedTraits(prev => {
      const next = new Set(prev);
      if (next.has(memberId)) next.delete(memberId);
      else next.add(memberId);
      return next;
    });
  };

  const applyRolePreset = (memberId: number, role: string) => {
    const preset = ROLE_PRESETS[role];
    if (!preset) return;
    setMembers(members.map(m => {
      if (m.id !== memberId) return m;
      const newTraits = { ...m.traits };
      for (const [key, val] of Object.entries(preset)) {
        newTraits[key] = val;
      }
      return { ...m, traits: newTraits };
    }));
    setExpandedTraits(prev => new Set(prev).add(memberId));
  };

  // Form persistence for members
  const {
    data: members,
    setData: setMembers,
    hasSavedData: hasSavedMembers,
    clearSavedData: clearMembers,
    restoreDefault: restoreMembersDefault,
  } = useFormPersistence({
    storageKey: 'team_optimizer_members',
    defaultValue: [],
    enabled: true,
    debounceMs: 500,
  });

  // Form persistence for project requirements
  const {
    data: projectReqs,
    setData: setProjectReqs,
    hasSavedData: hasSavedProjectReqs,
    clearSavedData: clearProjectReqs,
    restoreDefault: restoreProjectReqsDefault,
  } = useFormPersistence({
    storageKey: 'team_optimizer_project_reqs',
    defaultValue: {
      project_type: 'web_app',
      duration_weeks: 12,
      complexity: 'medium',
      required_skills: [],
      team_size_min: 3,
      team_size_max: 6
    },
    enabled: true,
    debounceMs: 500,
  });

  // Save data when session is expiring
  const saveCurrentData = useCallback(() => {
    // Data is already being saved by useFormPersistence
    console.log('[TeamOptimizer] Saving data before session expiry');
  }, []);

  useSessionExpiryHandler(saveCurrentData);

  // Prepare chart data for personality balance
  const personalityRadarData = useMemo(() => {
    if (!optimization) return [];

    const traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];

    // Get the first recommended team
    const bestTeam = (optimization.recommended_teams || optimization.recommended_groups)?.[0];
    if (!bestTeam) return [];

    const teamMemberIds = bestTeam.member_ids || [];
    const teamMembers = (members || []).filter((m: any) =>
      teamMemberIds.some((id: any) => String(id) === String(m.id))
    );

    // Calculate average for the optimized team
    const optimizedAvg: Record<string, number> = {};
    traits.forEach(trait => {
      const sum = teamMembers.reduce((total, m: any) => total + (m.traits?.[trait] || 0.5), 0);
      optimizedAvg[trait] = sum / (teamMembers.length || 1);
    });

    // Calculate average for the initial pool (current)
    const currentAvg: Record<string, number> = {};
    traits.forEach(trait => {
      const sum = (members || []).reduce((total, m: any) => total + (m.traits?.[trait] || 0.5), 0);
      currentAvg[trait] = sum / (members.length || 1);
    });

    return traits.map(trait => ({
      trait: trait.charAt(0).toUpperCase() + trait.slice(1),
      current: currentAvg[trait],
      optimal: 0.7, // Target baseline
      optimized: optimizedAvg[trait]
    }));
  }, [optimization, members]);

  // Prepare chart data for skill coverage
  const skillCoverageData = useMemo(() => {
    if (!optimization) return [];

    const coverage = optimization.skill_coverage || {};
    const skillList = Object.keys(coverage);

    if (skillList.length === 0) {
      // Fallback if skill_coverage is empty but we have recommended teams
      const bestTeam = (optimization.recommended_teams || optimization.recommended_groups)?.[0];
      if (bestTeam && bestTeam.roles_distribution) {
        return Object.entries(bestTeam.roles_distribution).map(([role, count]) => ({
          skill: role,
          coverage: (count as number) * 50, // Mocked coverage based on roles
          weight: 100
        }));
      }
      return [];
    }

    return Object.entries(coverage).map(([skill, value]) => ({
      skill,
      coverage: typeof value === 'number' ? value : 0,
      weight: 100 // Default weight
    }));
  }, [optimization]);

  // Show notification if saved data was restored
  useEffect(() => {
    if (hasSavedMembers || hasSavedProjectReqs) {
      console.log('[TeamOptimizer] Previous form data restored');
      // Optionally show a toast notification here
    }
  }, [hasSavedMembers, hasSavedProjectReqs]);

  // Sanitize members to prevent NaN values (run once on mount after data restoration)
  useEffect(() => {
    if (hasSanitizedRef.current || !members || !Array.isArray(members) || members.length === 0) {
      return;
    }

    const sanitizedMembers = members.map(member => ({
      ...member,
      experience_years: typeof member.experience_years === 'number' && isNaN(member.experience_years)
        ? 0
        : member.experience_years ?? 0,
      availability: typeof member.availability === 'number' && isNaN(member.availability)
        ? 1.0
        : member.availability ?? 1.0,
      traits: Object.fromEntries(
        Object.entries(member.traits || {}).filter(([_, val]) => val != null).map(([key, val]) => [
          key,
          typeof val === 'string' ? val : (typeof val === 'number' && isNaN(val) ? 0.5 : Math.max(0, Math.min(1, val ?? 0.5)))
        ])
      )
    }));

    // Only update if there are NaN values to fix
    const hasNaN = JSON.stringify(members) !== JSON.stringify(sanitizedMembers);
    if (hasNaN) {
      console.log('[TeamOptimizer] Sanitizing NaN values in members data');
      setMembers(sanitizedMembers);
    }

    hasSanitizedRef.current = true;
  }, [members]);

  // Sample member data structure
  const addMember = () => {
    const newMember = {
      id: Date.now(),
      name: '',
      role: 'developer',
      traits: {
        openness: 0.5,
        conscientiousness: 0.5,
        extraversion: 0.5,
        agreeableness: 0.5,
        neuroticism: 0.5
      },
      skills: [],
      experience_years: 0,
      availability: 1.0
    };
    setMembers([...members, newMember]);
  };

  const updateMember = (id, field, value) => {
    // Handle undefined/null values to prevent issues
    let safeValue;

    // Handle number fields to prevent NaN
    if (field === 'experience_years') {
      const parsed = typeof value === 'string' ? parseFloat(value) : value;
      safeValue = !isNaN(parsed) && parsed !== null && parsed !== undefined ? parsed : 0;
    } else if (field === 'availability') {
      const parsed = typeof value === 'string' ? parseFloat(value) : value;
      safeValue = !isNaN(parsed) && parsed !== null && parsed !== undefined ? parsed : 1.0;
    } else {
      safeValue = value !== undefined && value !== null ? value : '';
    }

    setMembers(members.map(m =>
      m.id === id ? { ...m, [field]: safeValue } : m
    ));
  };

  const updateTrait = (memberId, trait, value) => {
    let safeValue: any;

    if (trait === 'conflict_style') {
      // String trait — pass through (null clears it)
      safeValue = value || null;
    } else {
      // Numeric trait — parse and clamp
      const parsedValue = value !== undefined && value !== null && value !== ''
        ? parseFloat(value)
        : 0.5;
      safeValue = isNaN(parsedValue) ? 0.5 : Math.max(0, Math.min(1, parsedValue));
    }

    setMembers(members.map(m =>
      m.id === memberId
        ? { ...m, traits: { ...m.traits, [trait]: safeValue } }
        : m
    ));
  };

  const removeMember = (id) => {
    setMembers(members.filter(m => m.id !== id));
  };

  const runOptimization = async () => {
    if (members.length < 3) {
      setError('Please add at least 3 team members');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Sanitize members data before sending to API
      const sanitizedMembers = members.map(member => ({
        ...member,
        experience_years: typeof member.experience_years === 'number' && isNaN(member.experience_years)
          ? 0
          : member.experience_years ?? 0,
        availability: typeof member.availability === 'number' && isNaN(member.availability)
          ? 1.0
          : member.availability ?? 1.0,
        traits: Object.fromEntries(
          Object.entries(member.traits || {}).map(([key, val]) => [
            key,
            typeof val === 'number' && isNaN(val) ? 0.5 : Math.max(0, Math.min(1, val ?? 0.5))
          ])
        )
      }));

      // Backend expects 'objective' as a string, not an object
      const response = await api.post('/team-optimizer/optimize', {
        members: sanitizedMembers,
        project_requirements: projectReqs,
        objective: 'maximize_performance'
      });

      setOptimization(response.data);

      // Clear saved data on successful optimization
      // (optional - depends on whether you want to keep form data after success)
      // clearMembers();
      // clearProjectReqs();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Optimization failed';
      setError(errorMessage);

      // If it's an auth error, data is already saved by useFormPersistence
      console.log('[TeamOptimizer] Optimization failed, data preserved:', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Data Restored Banner */}
        {(hasSavedMembers || hasSavedProjectReqs) && (
          <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-blue-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="font-medium text-blue-900">Previous work restored</p>
                <p className="text-sm text-blue-700">Your team configuration has been restored from a previous session.</p>
              </div>
            </div>
            <button
              onClick={() => {
                clearMembers();
                clearProjectReqs();
                restoreMembersDefault();
                restoreProjectReqsDefault();
              }}
              className="px-4 py-2 text-sm bg-blue-100 text-blue-800 rounded hover:bg-blue-200"
            >
              Clear & Start Fresh
            </button>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">
              AI Team Optimizer
            </h1>
            {(hasSavedMembers || hasSavedProjectReqs) && (
              <button
                onClick={() => {
                  clearMembers();
                  clearProjectReqs();
                  restoreMembersDefault();
                  restoreProjectReqsDefault();
                }}
                className="text-sm text-gray-600 hover:text-gray-800 underline"
              >
                Clear Saved Data
              </button>
            )}
          </div>

          {/* Project Requirements Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Project Requirements</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Project Type</label>
                <select
                  className="w-full border rounded px-3 py-2"
                  value={projectReqs.project_type}
                  onChange={e => setProjectReqs({...projectReqs, project_type: e.target.value})}
                >
                  <option value="web_app">Web Application</option>
                  <option value="mobile_app">Mobile Application</option>
                  <option value="data_pipeline">Data Pipeline</option>
                  <option value="ml_project">ML Project</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Duration (weeks)</label>
                <input
                  type="number"
                  className="w-full border rounded px-3 py-2"
                  value={projectReqs.duration_weeks}
                  onChange={e => setProjectReqs({...projectReqs, duration_weeks: parseInt(e.target.value) || 12})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Complexity</label>
                <select
                  className="w-full border rounded px-3 py-2"
                  value={projectReqs.complexity}
                  onChange={e => setProjectReqs({...projectReqs, complexity: e.target.value})}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
          </div>

          {/* Team Members Section */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Team Members ({members.length})</h2>
              <button
                onClick={addMember}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                + Add Member
              </button>
            </div>

            <div className="space-y-4">
              {members.map(member => (
                <div key={member.id} className="border rounded-lg p-4 bg-gray-50">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Name</label>
                      <input
                        type="text"
                        className="w-full border rounded px-3 py-2"
                        value={member.name}
                        onChange={e => updateMember(member.id, 'name', e.target.value)}
                        placeholder="Enter name"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Role</label>
                      <select
                        className="w-full border rounded px-3 py-2"
                        value={member.role}
                        onChange={e => updateMember(member.id, 'role', e.target.value)}
                      >
                        <option value="developer">Developer</option>
                        <option value="designer">Designer</option>
                        <option value="pm">Product Manager</option>
                        <option value="qa">QA Engineer</option>
                        <option value="devops">DevOps</option>
                        <option value="lead">Team Lead</option>
                      </select>
                      <button
                        onClick={() => applyRolePreset(member.id, member.role)}
                        className="mt-1 text-xs text-indigo-600 hover:text-indigo-800 underline"
                        title="Auto-fill traits based on role ideal profile"
                      >
                        Apply Role Preset
                      </button>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Experience (years)</label>
                      <input
                        type="number"
                        className="w-full border rounded px-3 py-2"
                        value={member.experience_years}
                        onChange={e => updateMember(member.id, 'experience_years', parseFloat(e.target.value))}
                      />
                    </div>

                    <div className="flex items-end">
                      <button
                        onClick={() => removeMember(member.id)}
                        className="w-full bg-red-500 text-white px-3 py-2 rounded hover:bg-red-600"
                      >
                        Remove
                      </button>
                    </div>
                  </div>

                  {/* Skills Section */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">Skills (comma separated)</label>
                    <input
                      type="text"
                      className="w-full border rounded px-3 py-2"
                      value={member.skills?.join(', ') || ''}
                      onChange={e => updateMember(member.id, 'skills', e.target.value.split(',').map(s => s.trim()).filter(s => s !== ''))}
                      placeholder="e.g. React, Python, AWS, Mobile Development"
                    />
                  </div>

                  {/* Primary Personality Traits (Big Five) */}
                  <div className="mt-4">
                    <h4 className="text-sm font-medium mb-2">Personality Traits (OCEAN)</h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {PRIMARY_TRAITS.map(trait => {
                        const value = member.traits?.[trait] ?? 0.5;
                        return (
                          <div key={trait}>
                            <label className="block text-xs text-gray-600 mb-1 capitalize">{trait}</label>
                            <input type="range" min="0" max="1" step="0.1" className="w-full"
                              value={isNaN(value) ? 0.5 : value}
                              onChange={e => updateTrait(member.id, trait, e.target.value)} />
                            <div className="text-xs text-center text-gray-500">{isNaN(value) ? '0.5' : value.toFixed(1)}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Secondary Traits (Toggleable) */}
                  <div className="mt-3">
                    <button
                      onClick={() => toggleSecondaryTraits(member.id)}
                      className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                    >
                      <span>{expandedTraits.has(member.id) ? '- Hide' : '+ Show'} Secondary Traits</span>
                      <span className="text-xs text-gray-400">(EI, Cognitive, Collaboration)</span>
                    </button>

                    {expandedTraits.has(member.id) && (
                      <div className="mt-3 border-t pt-3">
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                          {SECONDARY_NUMERIC_TRAITS.map(trait => {
                            const value = member.traits?.[trait];
                            const hasValue = value != null;
                            return (
                              <div key={trait} className={!hasValue ? 'opacity-50' : ''}>
                                <label className="block text-xs text-gray-600 mb-1">
                                  {TRAIT_LABELS[trait] || trait}
                                </label>
                                <input type="range" min="0" max="1" step="0.1" className="w-full"
                                  value={hasValue ? (isNaN(value) ? 0.5 : value) : 0.5}
                                  onChange={e => updateTrait(member.id, trait, e.target.value)} />
                                <div className="text-xs text-center text-gray-500">
                                  {hasValue ? (isNaN(value) ? '0.5' : value.toFixed(1)) : 'unset'}
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {/* Conflict Style Dropdown */}
                        <div className="mt-3">
                          <label className="block text-xs text-gray-600 mb-1">Conflict Style (Thomas-Kilmann)</label>
                          <select className="border rounded px-3 py-1.5 text-sm w-48"
                            value={member.traits?.conflict_style || ''}
                            onChange={e => updateTrait(member.id, 'conflict_style', e.target.value || null)}
                          >
                            <option value="">-- Not set --</option>
                            {CONFLICT_STYLES.map(s => (
                              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Optimize Button */}
          <div className="mb-8">
            <button
              onClick={runOptimization}
              disabled={loading || members.length < 3}
              className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400"
            >
              {loading ? 'Optimizing...' : 'Optimize Team Composition'}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-8 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Optimization Results */}
          {optimization && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Optimization Results</h2>

              {/* Overall Score */}
              <div className="bg-blue-50 rounded-lg p-6">
                <div className="text-center">
                  <div className="text-4xl font-bold text-blue-600">
                    {optimization.overall_score.toFixed(1)}%
                  </div>
                  <div className="text-gray-600 mt-2">Overall Team Score</div>
                </div>
              </div>

              {/* Visual Analysis Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-4 border rounded-lg shadow-sm">
                  <TeamRadarChart data={personalityRadarData} />
                </div>
                <div className="bg-white p-4 border rounded-lg shadow-sm">
                  <SkillGapAnalysis data={skillCoverageData} />
                </div>
              </div>

              {/* Recommended Teams */}
              <div>
                <h3 className="text-xl font-semibold mb-4">Recommended Teams</h3>
                {optimization.recommended_teams?.map((team, idx) => (
                  <div key={idx} className="border rounded-lg p-6 mb-4">
                    <h4 className="font-semibold text-lg mb-3">Team Option {idx + 1}</h4>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="bg-green-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Compatibility</div>
                        <div className="text-xl font-bold text-green-600">
                          {(team.compatibility_score * 100).toFixed(0)}%
                        </div>
                      </div>

                      <div className="bg-blue-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Skill Coverage</div>
                        <div className="text-xl font-bold text-blue-600">
                          {(team.skill_coverage * 100).toFixed(0)}%
                        </div>
                      </div>

                      <div className="bg-purple-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Diversity</div>
                        <div className="text-xl font-bold text-purple-600">
                          {(team.diversity_score * 100).toFixed(0)}%
                        </div>
                      </div>

                      <div className="bg-orange-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Est. Velocity</div>
                        <div className="text-xl font-bold text-orange-600">
                          {team.estimated_velocity || 'N/A'}
                        </div>
                      </div>
                    </div>

                    {/* Extended Scores (when available) */}
                    {(team.role_fit != null || team.ei_score != null) && (
                      <div className="grid grid-cols-3 md:grid-cols-5 gap-3 mb-4">
                        {team.role_fit != null && (
                          <div className="bg-indigo-50 p-2 rounded text-center">
                            <div className="text-xs text-gray-500">Role Fit</div>
                            <div className={`text-lg font-bold ${team.role_fit > 0.7 ? 'text-indigo-600' : team.role_fit < 0.4 ? 'text-red-500' : 'text-gray-600'}`}>
                              {(team.role_fit * 100).toFixed(0)}%
                            </div>
                          </div>
                        )}
                        {team.ei_score != null && (
                          <div className="bg-pink-50 p-2 rounded text-center">
                            <div className="text-xs text-gray-500">Team EI</div>
                            <div className={`text-lg font-bold ${team.ei_score > 0.7 ? 'text-pink-600' : team.ei_score < 0.35 ? 'text-red-500' : 'text-gray-600'}`}>
                              {(team.ei_score * 100).toFixed(0)}%
                            </div>
                          </div>
                        )}
                        {team.collaboration_score != null && (
                          <div className="bg-teal-50 p-2 rounded text-center">
                            <div className="text-xs text-gray-500">Collaboration</div>
                            <div className="text-lg font-bold text-teal-600">
                              {(team.collaboration_score * 100).toFixed(0)}%
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Composite Scores (Layer 3) */}
                    {team.composites && (
                      <div className="mb-4 border rounded p-3 bg-gray-50">
                        <h5 className="text-sm font-medium mb-2 text-gray-700">Team Composite Analysis</h5>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
                          {[
                            { key: 'cognitive_diversity_score', label: 'Cognitive Diversity', warn: 0.35, good: 0.7 },
                            { key: 'conflict_potential_index', label: 'Conflict Potential', warn: 0.6, good: -1, invert: true },
                            { key: 'bandwidth_alignment', label: 'Bandwidth Fit', warn: 0.4, good: 0.7 },
                            { key: 'risk_profile_match', label: 'Risk Match', warn: 0.4, good: 0.7 },
                            { key: 'communication_style_spread', label: 'Comm. Spread', warn: 0.35, good: 0.7 },
                          ].map(({ key, label, warn, good, invert }) => {
                            const val = team.composites[key] ?? 0;
                            const isWarning = invert ? val > warn : val < warn;
                            const isGood = invert ? val < 0.3 : val > good;
                            return (
                              <div key={key} className={`p-2 rounded text-center ${isWarning ? 'bg-red-50 border border-red-200' : isGood ? 'bg-green-50' : 'bg-white'}`}>
                                <div className="text-xs text-gray-500">{label}</div>
                                <div className={`font-bold ${isWarning ? 'text-red-600' : isGood ? 'text-green-600' : 'text-gray-700'}`}>
                                  {(val * 100).toFixed(0)}%
                                  {isWarning && ' \u26A0'}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    <div className="mb-4">
                      <h5 className="font-medium mb-2">Team Members:</h5>
                      <div className="flex flex-wrap gap-2">
                        {team.member_ids?.map(memberId => {
                          const member = members.find(m => m.id === memberId);
                          return member ? (
                            <span key={memberId} className="bg-gray-200 px-3 py-1 rounded-full text-sm">
                              {member.name} ({member.role})
                            </span>
                          ) : null;
                        })}
                      </div>
                    </div>

                    {team.strengths?.length > 0 && (
                      <div className="mb-3">
                        <h5 className="font-medium mb-2 text-green-700">Strengths:</h5>
                        <ul className="list-disc list-inside text-sm text-gray-700">
                          {team.strengths?.map((strength, i) => (
                            <li key={i}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {team.risks?.length > 0 && (
                      <div>
                        <h5 className="font-medium mb-2 text-red-700">Risks:</h5>
                        <ul className="list-disc list-inside text-sm text-gray-700">
                          {team.risks?.map((risk, i) => (
                            <li key={i}>{risk}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Insights */}
              {optimization.insights?.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <h3 className="font-semibold mb-3">Key Insights</h3>
                  <ul className="space-y-2">
                    {optimization.insights?.map((insight, i) => (
                      <li key={i} className="flex items-start">
                        <span className="text-yellow-600 mr-2">💡</span>
                        <span className="text-gray-700">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Metrics */}
              <div className="bg-gray-100 rounded-lg p-6">
                <h3 className="font-semibold mb-3">Optimization Metrics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Candidates Evaluated:</span>
                    <div className="font-semibold">{optimization.metrics?.total_candidates_evaluated}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Time:</span>
                    <div className="font-semibold">{optimization.metrics?.optimization_time_seconds?.toFixed(2)}s</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Confidence:</span>
                    <div className="font-semibold">{(optimization.metrics?.confidence_score * 100)?.toFixed(0)}%</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Algorithm:</span>
                    <div className="font-semibold">{optimization.metrics?.algorithm_used}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
