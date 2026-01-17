import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Team Optimizer Component
export default function TeamOptimizer() {
  const [members, setMembers] = useState([]);
  const [projectReqs, setProjectReqs] = useState({
    project_type: 'web_app',
    duration_weeks: 12,
    complexity: 'medium',
    required_skills: [],
    team_size_min: 3,
    team_size_max: 6
  });
  const [optimization, setOptimization] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMembers, setSelectedMembers] = useState(new Set());

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
    setMembers(members.map(m =>
      m.id === id ? { ...m, [field]: value } : m
    ));
  };

  const updateTrait = (memberId, trait, value) => {
    setMembers(members.map(m =>
      m.id === memberId
        ? { ...m, traits: { ...m.traits, [trait]: parseFloat(value) } }
        : m
    ));
  };

  const removeMember = (id) => {
    setMembers(members.filter(m => m.id !== id));
  };

  const runOptimization = async () => {
    if (members.length < 2) {
      setError('Please add at least 2 team members');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/v1/team-optimizer/optimize', {
        members: members,
        project_requirements: projectReqs,
        objective: {
          primary_goal: 'maximize_performance',
          weights: {
            skill_match: 0.30,
            personality_compatibility: 0.25,
            experience_balance: 0.20,
            diversity: 0.15,
            availability: 0.10
          }
        }
      });

      setOptimization(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            AI Team Optimizer
          </h1>

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
                  onChange={e => setProjectReqs({...projectReqs, duration_weeks: parseInt(e.target.value)})}
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
                      </select>
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

                  {/* Personality Traits */}
                  <div className="mt-4">
                    <h4 className="text-sm font-medium mb-2">Personality Traits</h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {Object.entries(member.traits).map(([trait, value]) => (
                        <div key={trait}>
                          <label className="block text-xs text-gray-600 mb-1 capitalize">
                            {trait}
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            className="w-full"
                            value={value as number}
                            onChange={e => updateTrait(member.id, trait, e.target.value)}
                          />
                          <div className="text-xs text-center text-gray-500">{(value as number).toFixed(1)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Optimize Button */}
          <div className="mb-8">
            <button
              onClick={runOptimization}
              disabled={loading || members.length < 2}
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
                    {(optimization.overall_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-gray-600 mt-2">Overall Team Score</div>
                </div>
              </div>

              {/* Recommended Teams */}
              <div>
                <h3 className="text-xl font-semibold mb-4">Recommended Teams</h3>
                {optimization.recommended_teams.map((team, idx) => (
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

                    <div className="mb-4">
                      <h5 className="font-medium mb-2">Team Members:</h5>
                      <div className="flex flex-wrap gap-2">
                        {team.member_ids.map(memberId => {
                          const member = members.find(m => m.id === memberId);
                          return member ? (
                            <span key={memberId} className="bg-gray-200 px-3 py-1 rounded-full text-sm">
                              {member.name} ({member.role})
                            </span>
                          ) : null;
                        })}
                      </div>
                    </div>

                    {team.strengths.length > 0 && (
                      <div className="mb-3">
                        <h5 className="font-medium mb-2 text-green-700">Strengths:</h5>
                        <ul className="list-disc list-inside text-sm text-gray-700">
                          {team.strengths.map((strength, i) => (
                            <li key={i}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {team.risks.length > 0 && (
                      <div>
                        <h5 className="font-medium mb-2 text-red-700">Risks:</h5>
                        <ul className="list-disc list-inside text-sm text-gray-700">
                          {team.risks.map((risk, i) => (
                            <li key={i}>{risk}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Insights */}
              {optimization.insights.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <h3 className="font-semibold mb-3">Key Insights</h3>
                  <ul className="space-y-2">
                    {optimization.insights.map((insight, i) => (
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
                    <div className="font-semibold">{optimization.metrics.total_candidates_evaluated}</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Time:</span>
                    <div className="font-semibold">{optimization.metrics.optimization_time_seconds.toFixed(2)}s</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Confidence:</span>
                    <div className="font-semibold">{(optimization.metrics.confidence_score * 100).toFixed(0)}%</div>
                  </div>
                  <div>
                    <span className="text-gray-600">Algorithm:</span>
                    <div className="font-semibold">{optimization.metrics.algorithm_used}</div>
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
