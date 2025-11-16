// frontend/src/pages/TeamOptimizer.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import apiClient from '../services/api';

interface TeamMember {
  id: number;
  name: string;
  email?: string;
  role: 'developer' | 'designer' | 'pm' | 'qa' | 'devops' | 'data_scientist' | 'architect' | 'scrum_master';
  traits: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
    leadership_potential?: number;
    collaboration_index?: number;
  };
  skills: string[];
  experience_years?: number;
  availability: number;
}

interface ProjectRequirements {
  project_type: string;
  duration_weeks: number;
  complexity: 'low' | 'medium' | 'high' | 'critical';
  required_skills: string[];
  team_size_min: number;
  team_size_max: number;
  budget_level?: 'low' | 'medium' | 'high';
  remote_friendly: boolean;
}

interface OptimizationObjective {
  primary_goal: 'maximize_performance' | 'minimize_conflicts' | 'balance_diversity' | 'optimize_collaboration';
  weights: Record<string, number>;
}

interface TeamGroup {
  member_ids: number[];
  roles_distribution: Record<string, number>;
  compatibility_score: number;
  skill_coverage: number;
  diversity_score: number;
  estimated_velocity?: number;
  strengths: string[];
  risks: string[];
}

interface OptimizationMetrics {
  total_candidates_evaluated: number;
  optimization_time_seconds: number;
  confidence_score: number;
  algorithm_used: string;
  iterations: number;
}

interface OptimizationResult {
  recommended_teams: TeamGroup[];
  overall_score: number;
  metrics: OptimizationMetrics;
  insights: string[];
  warnings: string[];
  alternative_compositions?: TeamGroup[];
  timestamp: string;
}

const TeamOptimizer: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showNotification } = useNotification();

  const [members, setMembers] = useState<TeamMember[]>([]);
  const [projectReqs, setProjectReqs] = useState<ProjectRequirements>({
    project_type: 'web_app',
    duration_weeks: 12,
    complexity: 'medium',
    required_skills: [],
    team_size_min: 3,
    team_size_max: 6,
    remote_friendly: true
  });
  const [objective, setObjective] = useState<OptimizationObjective>({
    primary_goal: 'maximize_performance',
    weights: {
      skill_match: 0.30,
      personality_compatibility: 0.25,
      experience_balance: 0.20,
      diversity: 0.15,
      availability: 0.10
    }
  });
  const [optimization, setOptimization] = useState<OptimizationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check authentication
  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  const addMember = () => {
    const newMember: TeamMember = {
      id: Date.now(),
      name: '',
      role: 'developer',
      traits: {
        openness: 0.5,
        conscientiousness: 0.5,
        extraversion: 0.5,
        agreeableness: 0.5,
        neuroticism: 0.5,
        leadership_potential: undefined,
        collaboration_index: undefined
      },
      skills: [],
      experience_years: 0,
      availability: 1.0
    };
    setMembers([...members, newMember]);
  };

  const updateMember = (id: number, field: string, value: any) => {
    setMembers(members.map(m =>
      m.id === id ? { ...m, [field]: value } : m
    ));
  };

  const updateTrait = (memberId: number, trait: string, value: number) => {
    setMembers(members.map(m =>
      m.id === memberId
        ? { ...m, traits: { ...m.traits, [trait]: value } }
        : m
    ));
  };

  const removeMember = (id: number) => {
    setMembers(members.filter(m => m.id !== id));
  };

  const addSkill = (memberId: number, skill: string) => {
    if (!skill.trim()) return;

    setMembers(members.map(m =>
      m.id === memberId
        ? { ...m, skills: [...new Set([...m.skills, skill.trim()])] }
        : m
    ));
  };

  const removeSkill = (memberId: number, skillToRemove: string) => {
    setMembers(members.map(m =>
      m.id === memberId
        ? { ...m, skills: m.skills.filter(skill => skill !== skillToRemove) }
        : m
    ));
  };

  const runOptimization = async () => {
    if (!user) {
      setError('You must be logged in to use the team optimizer');
      return;
    }

    if (members.length < projectReqs.team_size_min) {
      setError(`Please add at least ${projectReqs.team_size_min} team members`);
      return;
    }

    // Validate all members have names
    const incompleteMember = members.find(m => !m.name.trim());
    if (incompleteMember) {
      setError('Please provide names for all team members');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Since the team optimization endpoint is currently disabled, we'll use the recommendation service directly
      // This is a temporary solution until the team optimization API is fully integrated
      const response = await apiClient.post('/team-optimizer/optimize', {
        members: members.map(m => ({
          ...m,
          id: Number(m.id) // Ensure ID is a number
        })),
        project_requirements: projectReqs,
        objective: objective,
        existing_team_id: null
      });

      setOptimization(response.data);
      showNotification('Team optimization completed successfully!', 'success');

    } catch (err: any) {
      console.error('Optimization error:', err);

      // Check if it's a 404 (endpoint not available)
      if (err.response?.status === 404) {
        setError('Team optimization API is currently being integrated. Please try again later.');
        showNotification('Team optimization feature coming soon!', 'warning');
      } else {
        const errorMessage = err.response?.data?.detail || err.message || 'Optimization failed';
        setError(errorMessage);
        showNotification(errorMessage, 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const resetOptimization = () => {
    setOptimization(null);
    setMembers([]);
    setError(null);
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-blue-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeColor = (score: number): string => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-blue-100 text-blue-800';
    if (score >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Team Optimizer</h1>
              <p className="text-gray-600 mt-2">
                Create optimal team compositions using AI-powered personality and skill analysis
              </p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={resetOptimization}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Reset
              </button>
            </div>
          </div>

          {/* Project Requirements Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Project Requirements</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Type
                </label>
                <select
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  value={projectReqs.project_type}
                  onChange={(e) => setProjectReqs({...projectReqs, project_type: e.target.value})}
                >
                  <option value="web_app">Web Application</option>
                  <option value="mobile_app">Mobile Application</option>
                  <option value="data_pipeline">Data Pipeline</option>
                  <option value="ml_project">Machine Learning Project</option>
                  <option value="infrastructure">Infrastructure</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Duration (weeks)
                </label>
                <input
                  type="number"
                  min="1"
                  max="52"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  value={projectReqs.duration_weeks}
                  onChange={(e) => setProjectReqs({...projectReqs, duration_weeks: parseInt(e.target.value)})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Complexity
                </label>
                <select
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  value={projectReqs.complexity}
                  onChange={(e) => setProjectReqs({...projectReqs, complexity: e.target.value as any})}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Team Size Range
                </label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    min="2"
                    max="20"
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    value={projectReqs.team_size_min}
                    onChange={(e) => setProjectReqs({...projectReqs, team_size_min: parseInt(e.target.value)})}
                    placeholder="Min"
                  />
                  <input
                    type="number"
                    min="2"
                    max="20"
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    value={projectReqs.team_size_max}
                    onChange={(e) => setProjectReqs({...projectReqs, team_size_max: parseInt(e.target.value)})}
                    placeholder="Max"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Remote Friendly
                </label>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="remote_friendly"
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    checked={projectReqs.remote_friendly}
                    onChange={(e) => setProjectReqs({...projectReqs, remote_friendly: e.target.checked})}
                  />
                  <label htmlFor="remote_friendly" className="ml-2 block text-sm text-gray-700">
                    Remote work compatible
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Team Members Section */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Team Members ({members.length}/{projectReqs.team_size_max})
              </h2>
              <button
                onClick={addMember}
                disabled={members.length >= projectReqs.team_size_max}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                + Add Member
              </button>
            </div>

            {members.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-gray-400 mb-2">
                  <svg className="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 100-5.646 5.646" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12a8 8 0 11-16 0" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="m20 12 4-4m0 0l-4 4m-7.354-5.646a4 4 0 10-5.646 5.646" />
                  </svg>
                </div>
                <p className="text-gray-500">No team members added yet. Click "Add Member" to get started.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {members.map((member) => (
                  <div key={member.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Name *
                        </label>
                        <input
                          type="text"
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          value={member.name}
                          onChange={(e) => updateMember(member.id, 'name', e.target.value)}
                          placeholder="Enter member name"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Role
                        </label>
                        <select
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          value={member.role}
                          onChange={(e) => updateMember(member.id, 'role', e.target.value as any)}
                        >
                          <option value="developer">Developer</option>
                          <option value="designer">Designer</option>
                          <option value="pm">Product Manager</option>
                          <option value="qa">QA Engineer</option>
                          <option value="devops">DevOps Engineer</option>
                          <option value="data_scientist">Data Scientist</option>
                          <option value="architect">Architect</option>
                          <option value="scrum_master">Scrum Master</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Experience (years)
                        </label>
                        <input
                          type="number"
                          min="0"
                          step="0.5"
                          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          value={member.experience_years}
                          onChange={(e) => updateMember(member.id, 'experience_years', parseFloat(e.target.value) || 0)}
                        />
                      </div>

                      <div className="flex items-end">
                        <button
                          onClick={() => removeMember(member.id)}
                          className="w-full bg-red-500 text-white px-3 py-2 rounded-md hover:bg-red-600"
                        >
                          Remove
                        </button>
                      </div>
                    </div>

                    {/* Personality Traits */}
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Personality Traits (Big Five)</h4>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        {Object.entries(member.traits).map(([trait, value]) => (
                          <div key={trait}>
                            <label className="block text-xs text-gray-600 mb-1 capitalize">
                              {trait.replace('_', ' ')}
                            </label>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.1"
                              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                              value={value}
                              onChange={(e) => updateTrait(member.id, trait, parseFloat(e.target.value))}
                            />
                            <div className="text-xs text-center text-gray-500 mt-1">
                              {value.toFixed(1)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Skills */}
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Skills</h4>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {member.skills.map((skill, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-indigo-100 text-indigo-800"
                          >
                            {skill}
                            <button
                              onClick={() => removeSkill(member.id, skill)}
                              className="ml-1 text-indigo-600 hover:text-indigo-900"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex">
                        <input
                          type="text"
                          className="flex-1 border border-gray-300 rounded-l-md px-3 py-1 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          placeholder="Add a skill"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              addSkill(member.id, e.currentTarget.value);
                              e.currentTarget.value = '';
                            }
                          }}
                        />
                        <button
                          onClick={() => addSkill(member.id, (e.target as HTMLInputElement).value)}
                          className="px-3 py-1 bg-indigo-600 text-white rounded-r-md text-sm hover:bg-indigo-700"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Optimization Objective */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Optimization Objective</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Goal
                </label>
                <select
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  value={objective.primary_goal}
                  onChange={(e) => setObjective({...objective, primary_goal: e.target.value as any})}
                >
                  <option value="maximize_performance">Maximize Performance</option>
                  <option value="minimize_conflicts">Minimize Conflicts</option>
                  <option value="balance_diversity">Balance Diversity</option>
                  <option value="optimize_collaboration">Optimize Collaboration</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Weighting Strategy
                </label>
                <div className="space-y-2 text-sm">
                  {Object.entries(objective.weights).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-gray-700 capitalize">{key.replace('_', ' ')}</span>
                      <span className="text-gray-500 font-mono">{value.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Optimize Button */}
          <div className="mb-8">
            <button
              onClick={runOptimization}
              disabled={loading || members.length < projectReqs.team_size_min}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading && <LoadingSpinner size="small" color="white" className="mr-2" />}
              {loading ? 'Optimizing...' : 'Optimize Team Composition'}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-8 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              <div className="flex">
                <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 0 4-2 8 0 00-16 0zm1 9H1a1 1 0 01-2V9a1 1 0 012-2V9a1 1 0 012 2z" clipRule="evenodd" />
                </svg>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Optimization Results */}
          {optimization && (
            <div className="space-y-8">
              <h2 className="text-2xl font-bold text-gray-900">Optimization Results</h2>

              {/* Overall Score */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8 text-center">
                <div className="text-5xl font-bold text-indigo-600 mb-2">
                  {(optimization.overall_score * 100).toFixed(1)}%
                </div>
                <div className="text-gray-600">Overall Team Score</div>
              </div>

              {/* Recommended Teams */}
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  Recommended Teams ({optimization.recommended_teams.length})
                </h3>
                {optimization.recommended_teams.map((team, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-6 mb-4">
                    <div className="flex justify-between items-center mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">
                        Team Option {idx + 1}
                      </h4>
                      <div className={`text-2xl font-bold ${getScoreColor(team.compatibility_score)}`}>
                        {(team.compatibility_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center">
                        <div className={`text-sm text-gray-600 mb-1`}>Compatibility</div>
                        <div className={`text-2xl font-bold ${getScoreColor(team.compatibility_score)}`}>
                          {(team.compatibility_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className={`text-sm text-gray-600 mb-1`}>Skill Coverage</div>
                        <div className={`text-2xl font-bold ${getScoreColor(team.skill_coverage)}`}>
                          {(team.skill_coverage * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className={`text-sm text-gray-600 mb-1`}>Diversity</div>
                        <div className={`text-2xl font-bold ${getScoreColor(team.diversity_score)}`}>
                          {(team.diversity_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="text-center">
                        <div className={`text-sm text-gray-600 mb-1`}>Est. Velocity</div>
                        <div className="text-2xl font-bold text-gray-900">
                          {team.estimated_velocity ? `${team.estimated_velocity.toFixed(1)}` : 'N/A'}
                        </div>
                      </div>
                    </div>

                    {/* Team Members */}
                    <div className="mb-6">
                      <h5 className="font-medium text-gray-900 mb-3">Team Members:</h5>
                      <div className="flex flex-wrap gap-2">
                        {team.member_ids.map((memberId) => {
                          const member = members.find(m => m.id === memberId);
                          return member ? (
                            <span
                              key={memberId}
                              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-200 text-gray-700"
                            >
                              {member.name} ({member.role})
                            </span>
                          ) : null;
                        })}
                      </div>
                    </div>

                    {/* Strengths */}
                    {team.strengths && team.strengths.length > 0 && (
                      <div className="mb-4">
                        <h5 className="font-medium text-green-800 mb-2">Strengths:</h5>
                        <ul className="space-y-1">
                          {team.strengths.map((strength, i) => (
                            <li key={i} className="flex items-start text-sm text-gray-700">
                              <span className="text-green-500 mr-2">✓</span>
                              <span>{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Risks */}
                    {team.risks && team.risks.length > 0 && (
                      <div>
                        <h5 className="font-medium text-red-800 mb-2">Risks:</h5>
                        <ul className="space-y-1">
                          {team.risks.map((risk, i) => (
                            <li key={i} className="flex items-start text-sm text-gray-700">
                              <span className="text-red-500 mr-2">⚠</span>
                              <span>{risk}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Insights */}
              {optimization.insights && optimization.insights.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Key Insights</h3>
                  <div className="space-y-3">
                    {optimization.insights.map((insight, i) => (
                      <div key={i} className="flex items-start">
                        <span className="text-yellow-600 mr-3 text-xl">💡</span>
                        <span className="text-gray-700">{insight}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metrics */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Optimization Metrics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Candidates Evaluated</span>
                    <div className="font-semibold text-gray-900">
                      {optimization.metrics.total_candidates_evaluated}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600">Processing Time</span>
                    <div className="font-semibold text-gray-900">
                      {optimization.metrics.optimization_time_seconds.toFixed(2)}s
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600">Confidence</span>
                    <div className="font-semibold text-gray-900">
                      {(optimization.metrics.confidence_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-600">Algorithm</span>
                    <div className="font-semibold text-gray-900">
                      {optimization.metrics.algorithm_used}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamOptimizer;