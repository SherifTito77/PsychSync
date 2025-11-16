/**
 * File Path: frontend/src/components/team_optimizer.tsx
 * Team Optimization UI Component
 * AI-powered team composition and analysis
 */
import React, { useState, useEffect } from 'react';
import { Users, Target, TrendingUp, AlertCircle, CheckCircle, Loader } from 'lucide-react';
// =================================================================
// TYPES
// =================================================================
interface TeamMember {
  user_id: number;
  name: string;
  email: string;
  department: string;
  seniority_level: string;
  availability: number;
  skills: { [key: string]: number };
  personality_traits: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
  };
}
interface OptimizedTeam {
  team_name: string;
  members: TeamMember[];
  overall_score: number;
  compatibility_score: number;
  skill_coverage_score: number;
  diversity_score: number;
  strengths: string[];
  gaps: string[];
  recommendations: string[];
}
// =================================================================
// MAIN COMPONENT
// =================================================================
const TeamOptimizer: React.FC = () => {
  const [step, setStep] = useState<'requirements' | 'results'>('requirements');
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<TeamMember[]>([]);
  const [optimizedTeam, setOptimizedTeam] = useState<OptimizedTeam | null>(null);
  // Form state
  const [teamName, setTeamName] = useState('');
  const [targetSize, setTargetSize] = useState(5);
  const [requiredRoles, setRequiredRoles] = useState<{ [key: string]: number }>({});
  const [requiredSkills, setRequiredSkills] = useState<{ [key: string]: number }>({});
  useEffect(() => {
    fetchCandidates();
  }, []);
  // =================================================================
  // API CALLS
  // =================================================================
  const fetchCandidates = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/optimizer/candidates', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCandidates(data);
      }
    } catch (error) {
      console.error('Error fetching candidates:', error);
    }
  };
  const optimizeTeam = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/optimizer/optimize', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          team_name: teamName,
          target_size: targetSize,
          required_roles: requiredRoles,
          required_skills: requiredSkills,
          min_personality_diversity: 0.3
        })
      });
      if (response.ok) {
        const data = await response.json();
        setOptimizedTeam(data);
        setStep('results');
      }
    } catch (error) {
      console.error('Error optimizing team:', error);
    } finally {
      setLoading(false);
    }
  };
  // =================================================================
  // RENDER: REQUIREMENTS STEP
  // =================================================================
  const renderRequirementsStep = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Team Requirements</h2>
        {/* Team Name */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Team Name
          </label>
          <input
            type="text"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g., Product Development Team"
          />
        </div>
        {/* Target Size */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Target Team Size
          </label>
          <input
            type="number"
            value={targetSize}
            onChange={(e) => setTargetSize(parseInt(e.target.value))}
            min={3}
            max={20}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        {/* Required Roles */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Required Roles
          </label>
          <div className="space-y-2">
            {Object.entries(requiredRoles).map(([role, count]) => (
              <div key={role} className="flex items-center space-x-2">
                <input
                  type="text"
                  value={role}
                  onChange={(e) => {
                    const newRoles = { ...requiredRoles };
                    delete newRoles[role];
                    newRoles[e.target.value] = count;
                    setRequiredRoles(newRoles);
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="Role name"
                />
                <input
                  type="number"
                  value={count}
                  onChange={(e) => setRequiredRoles({
                    ...requiredRoles,
                    [role]: parseInt(e.target.value)
                  })}
                  min={1}
                  className="w-20 px-3 py-2 border border-gray-300 rounded-lg"
                />
                <button
                  onClick={() => {
                    const newRoles = { ...requiredRoles };
                    delete newRoles[role];
                    setRequiredRoles(newRoles);
                  }}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              onClick={() => setRequiredRoles({ ...requiredRoles, 'New Role': 1 })}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              + Add Role
            </button>
          </div>
        </div>
        {/* Required Skills */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Required Skills (Min Level 0-100)
          </label>
          <div className="space-y-2">
            {Object.entries(requiredSkills).map(([skill, level]) => (
              <div key={skill} className="flex items-center space-x-2">
                <input
                  type="text"
                  value={skill}
                  onChange={(e) => {
                    const newSkills = { ...requiredSkills };
                    delete newSkills[skill];
                    newSkills[e.target.value] = level;
                    setRequiredSkills(newSkills);
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="Skill name"
                />
                <input
                  type="number"
                  value={level}
                  onChange={(e) => setRequiredSkills({
                    ...requiredSkills,
                    [skill]: parseFloat(e.target.value)
                  })}
                  min={0}
                  max={100}
                  className="w-24 px-3 py-2 border border-gray-300 rounded-lg"
                />
                <button
                  onClick={() => {
                    const newSkills = { ...requiredSkills };
                    delete newSkills[skill];
                    setRequiredSkills(newSkills);
                  }}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              onClick={() => setRequiredSkills({ ...requiredSkills, 'New Skill': 70 })}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              + Add Skill
            </button>
          </div>
        </div>
        {/* Candidate Pool Info */}
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <Users className="w-5 h-5 text-blue-600 mr-2" />
            <span className="text-sm text-blue-900">
              {candidates.length} candidates available for optimization
            </span>
          </div>
        </div>
        {/* Optimize Button */}
        <button
          onClick={optimizeTeam}
          disabled={loading || !teamName}
          className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
            loading || !teamName
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <Loader className="w-5 h-5 mr-2 animate-spin" />
              Optimizing Team...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              <Target className="w-5 h-5 mr-2" />
              Optimize Team
            </span>
          )}
        </button>
      </div>
    </div>
  );
  // =================================================================
  // RENDER: RESULTS STEP
  // =================================================================
  const renderResultsStep = () => {
    if (!optimizedTeam) return null;
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">
              {optimizedTeam.team_name}
            </h2>
            <button
              onClick={() => setStep('requirements')}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              ← Back to Requirements
            </button>
          </div>
          {/* Score Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <ScoreCard
              score={optimizedTeam.overall_score}
              color="blue"
            />
            <ScoreCard
              score={optimizedTeam.compatibility_score}
              color="green"
            />
            <ScoreCard
              score={optimizedTeam.skill_coverage_score}
              color="purple"
            />
            <ScoreCard
              score={optimizedTeam.diversity_score}
              color="orange"
            />
          </div>
        </div>
        {/* Team Members */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Selected Team Members ({optimizedTeam.members.length})
          </h3>
          <div className="space-y-3">
            {optimizedTeam.members.map((member) => (
              <MemberCard key={member.user_id} member={member} />
            ))}
          </div>
        </div>
        {/* Analysis */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Strengths */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Strengths</h3>
            </div>
            <ul className="space-y-2">
              {optimizedTeam.strengths.map((strength, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  <span className="text-sm text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </div>
          {/* Gaps */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center mb-4">
              <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Areas for Growth</h3>
            </div>
            <ul className="space-y-2">
              {optimizedTeam.gaps.map((gap, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-yellow-600 mr-2">!</span>
                  <span className="text-sm text-gray-700">{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        {/* Recommendations */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="w-5 h-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
          </div>
          <ul className="space-y-2">
            {optimizedTeam.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-blue-600 mr-2">→</span>
                <span className="text-sm text-gray-700">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button className="flex-1 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
            Create This Team
          </button>
          <button className="flex-1 py-3 px-4 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium">
            Download Report
          </button>
        </div>
      </div>
    );
  };
  // =================================================================
  // SUB-COMPONENTS
  // =================================================================
  const ScoreCard: React.FC<{ title: string; score: number; color: string }> = ({
    title,
    score,
    color
  }) => {
    const colorClasses = {
      blue: 'bg-blue-100 text-blue-900',
      green: 'bg-green-100 text-green-900',
      purple: 'bg-purple-100 text-purple-900',
      orange: 'bg-orange-100 text-orange-900'
    };
    return (
      <div className={`rounded-lg p-4 ${colorClasses[color as keyof typeof colorClasses]}`}>
        <div className="text-sm font-medium mb-1">{title}</div>
        <div className="text-3xl font-bold">{score.toFixed(0)}</div>
        <div className="text-xs mt-1">out of 100</div>
      </div>
    );
  };
  const MemberCard: React.FC<{ member: TeamMember }> = ({ member }) => (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
      <div className="flex items-center space-x-4">
        <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
          {member.name.split(' ').map(n => n[0]).join('')}
        </div>
        <div>
          <div className="font-medium text-gray-900">{member.name}</div>
          <div className="text-sm text-gray-600">{member.department} • {member.seniority_level}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm text-gray-600">Availability</div>
        <div className="font-semibold text-gray-900">{member.availability}%</div>
      </div>
    </div>
  );
  // =================================================================
  // MAIN RENDER
  // =================================================================
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AI Team Optimizer</h1>
        <p className="text-gray-600 mt-2">
          Create optimal teams based on personality, skills, and diversity
        </p>
      </div>
      {step === 'requirements' && renderRequirementsStep()}
      {step === 'results' && renderResultsStep()}
    </div>
  );
};
export default TeamOptimizer;
