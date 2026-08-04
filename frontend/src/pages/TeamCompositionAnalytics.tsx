// Team Composition Analytics - HRIS org structure + personality traits
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHRISData } from '@/hooks/useHRISData';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface PersonalityProfile {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

interface EmployeeProfile {
  id: string;
  name: string;
  department: string;
  position: string;
  personality: PersonalityProfile;
  strengths: string[];
  collaborationStyle: string;
  idealTeamRole: string;
}

const TeamCompositionAnalytics: React.FC = () => {
  const navigate = useNavigate();
  const { employees, departments, getEmployeesByDepartment } = useHRISData();
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [viewMode, setViewMode] = useState<'departments' | 'personalities' | 'roles'>('departments');

  // Mock personality profiles (in production, from assessment API)
  const employeeProfiles: EmployeeProfile[] = employees.map(emp => ({
    id: emp.id,
    name: emp.name,
    department: emp.department,
    position: emp.position,
    personality: {
      openness: 50 + Math.random() * 50,
      conscientiousness: 50 + Math.random() * 50,
      extraversion: 50 + Math.random() * 50,
      agreeableness: 50 + Math.random() * 50,
      neuroticism: Math.random() * 50,
    },
    strengths: [
      'Creative problem-solving',
      'Collaborative mindset',
      'Strong communication',
      'Analytical thinking',
    ].sort(() => Math.random() - 0.5).slice(0, 2),
    collaborationStyle: ['Facilitator', 'Executor', 'Innovator', 'Diplomat', 'Specialist'][Math.floor(Math.random() * 5)],
    idealTeamRole: ['Leader', 'Contributor', 'Specialist', 'Coordinator', 'Researcher'][Math.floor(Math.random() * 5)],
  }));

  const filteredProfiles = selectedDepartment === 'All'
    ? employeeProfiles
    : employeeProfiles.filter(p => p.department === selectedDepartment);

  // Calculate department personality averages
  const departmentPersonalities = departments.map(dept => {
    const deptProfiles = employeeProfiles.filter(p => p.department === dept);
    const avgPersonality = {
      openness: deptProfiles.reduce((sum, p) => sum + p.personality.openness, 0) / deptProfiles.length,
      conscientiousness: deptProfiles.reduce((sum, p) => sum + p.personality.conscientiousness, 0) / deptProfiles.length,
      extraversion: deptProfiles.reduce((sum, p) => sum + p.personality.extraversion, 0) / deptProfiles.length,
      agreeableness: deptProfiles.reduce((sum, p) => sum + p.personality.agreeableness, 0) / deptProfiles.length,
      neuroticism: deptProfiles.reduce((sum, p) => sum + p.personality.neuroticism, 0) / deptProfiles.length,
    };
    return {
      department: dept,
      profiles: deptProfiles,
      avgPersonality,
    };
  });

  // Get trait color
  const getTraitColor = (value: number) => {
    if (value >= 70) return 'text-green-600';
    if (value >= 50) return 'text-blue-600';
    return 'text-gray-600';
  };

  const getBarColor = (value: number) => {
    if (value >= 70) return 'bg-green-500';
    if (value >= 50) return 'bg-blue-500';
    return 'bg-gray-400';
  };

  // Render departments view
  const renderDepartmentsView = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Department Personality Profiles</h2>
      {departmentPersonalities.map(({ department, profiles, avgPersonality }) => (
        <Card key={department}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{department}</CardTitle>
              <span className="text-sm text-gray-600">{profiles.length} employees</span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="mb-6">
              <div className="text-sm font-medium text-gray-700 mb-4">Average Personality Traits</div>
              <div className="space-y-3">
                {Object.entries(avgPersonality).map(([trait, value]) => (
                  <div key={trait}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize text-gray-700">{trait}</span>
                      <span className={`font-medium ${getTraitColor(value)}`}>{value.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getBarColor(value)}`}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-sm font-medium text-gray-700 mb-3">Team Members</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {profiles.map(profile => (
                  <div
                    key={profile.id}
                    className="border border-gray-200 rounded-lg p-3 hover:border-indigo-300 transition-colors"
                  >
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                        {profile.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{profile.name}</div>
                        <div className="text-xs text-gray-600">{profile.position}</div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {profile.strengths.slice(0, 2).map((strength, idx) => (
                        <span key={idx} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                          {strength}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  // Render personalities view
  const renderPersonalitiesView = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Individual Personality Profiles</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredProfiles.map(profile => (
          <Card key={profile.id}>
            <CardContent className="p-6">
              <div className="flex items-center space-x-4 mb-4">
                <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                  {profile.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                  <div className="font-semibold text-gray-900">{profile.name}</div>
                  <div className="text-sm text-gray-600">{profile.position}</div>
                  <div className="text-xs text-indigo-600">{profile.department}</div>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                {Object.entries(profile.personality).map(([trait, value]) => (
                  <div key={trait} className="flex items-center justify-between text-sm">
                    <span className="capitalize text-gray-700">{trait}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getBarColor(value)}`}
                          style={{ width: `${value}%` }}
                        />
                      </div>
                      <span className={`font-medium w-10 text-right ${getTraitColor(value)}`}>
                        {value.toFixed(0)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t pt-3">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Style:</span>
                    <span className="ml-1 font-medium text-gray-900">{profile.collaborationStyle}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Role:</span>
                    <span className="ml-1 font-medium text-gray-900">{profile.idealTeamRole}</span>
                  </div>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                className="w-full mt-3"
                onClick={() => navigate(`/assessments?employee=${profile.id}`)}
              >
                View Full Profile
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  // Render team roles view
  const renderRolesView = () => {
    const roleDistribution = [
      'Leader',
      'Contributor',
      'Specialist',
      'Coordinator',
      'Researcher',
    ].map(role => ({
      role,
      count: filteredProfiles.filter(p => p.idealTeamRole === role).length,
      percentage: (filteredProfiles.filter(p => p.idealTeamRole === role).length / filteredProfiles.length) * 100,
    })).sort((a, b) => b.count - a.count);

    const styleDistribution = [
      'Facilitator',
      'Executor',
      'Innovator',
      'Diplomat',
      'Specialist',
    ].map(style => ({
      style,
      count: filteredProfiles.filter(p => p.collaborationStyle === style).length,
      percentage: (filteredProfiles.filter(p => p.collaborationStyle === style).length / filteredProfiles.length) * 100,
    })).sort((a, b) => b.count - a.count);

    return (
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-gray-900">Team Role Distribution</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Ideal Team Roles */}
          <Card>
            <CardHeader>
              <CardTitle>Ideal Team Roles</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {roleDistribution.map(({ role, count, percentage }) => (
                  <div key={role}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{role}</span>
                      <span className="text-sm text-gray-600">{count} ({percentage.toFixed(0)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-indigo-500 h-3 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Collaboration Styles */}
          <Card>
            <CardHeader>
              <CardTitle>Collaboration Styles</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {styleDistribution.map(({ style, count, percentage }) => (
                  <div key={style}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{style}</span>
                      <span className="text-sm text-gray-600">{count} ({percentage.toFixed(0)}%)</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-purple-500 h-3 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Team Balance Analysis */}
        <Card className="bg-gradient-to-r from-indigo-50 to-purple-50">
          <CardHeader>
            <CardTitle className="text-indigo-900">🤖 Team Balance Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm text-indigo-900">
              <div className="flex items-start">
                <span className="font-bold mr-2">✓</span>
                <span>
                  <strong>Role Distribution:</strong> {
                    roleDistribution[0].percentage > 40 ?
                    'May be over-reliant on one role type' :
                    'Well-balanced across different role types'
                  }
                </span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">✓</span>
                <span>
                  <strong>Collaboration Diversity:</strong> {
                    styleDistribution.filter(s => s.count > 0).length >= 4 ?
                    'Good variety of collaboration styles' :
                    'Consider recruiting for diverse collaboration styles'
                  }
                </span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">✓</span>
                <span>
                  <strong>Department Coverage:</strong> {
                    selectedDepartment === 'All' ?
                      `${departments.length} departments represented with diverse profiles` :
                      `Focusing on ${selectedDepartment} with ${filteredProfiles.length} profiles`
                  }
                </span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">→</span>
                <span>
                  <strong>Recommendation:</strong> Use Team Optimizer to create balanced teams based on these personality profiles
                </span>
              </div>
            </div>
            <Button
              className="mt-4"
              onClick={() => navigate('/team-optimizer')}
            >
              Go to Team Optimizer
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Team Composition Analytics</h1>
          <p className="text-gray-600 mt-1">
            HRIS organizational structure combined with personality assessment data
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate('/dashboard')}
        >
          ← Back to Dashboard
        </Button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-gray-600">Total Profiles</div>
            <div className="text-2xl font-bold text-gray-900">{filteredProfiles.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-gray-600">Departments</div>
            <div className="text-2xl font-bold text-gray-900">
              {selectedDepartment === 'All' ? departments.length : 1}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-gray-600">Avg Openness</div>
            <div className="text-2xl font-bold text-blue-600">
              {(filteredProfiles.reduce((sum, p) => sum + p.personality.openness, 0) / filteredProfiles.length).toFixed(0)}%
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-gray-600">Avg Conscientiousness</div>
            <div className="text-2xl font-bold text-green-600">
              {(filteredProfiles.reduce((sum, p) => sum + p.personality.conscientiousness, 0) / filteredProfiles.length).toFixed(0)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Department:</label>
              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="All">All Departments</option>
                {departments.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">View:</span>
              {[
                { value: 'departments', label: 'By Department' },
                { value: 'personalities', label: 'Personalities' },
                { value: 'roles', label: 'Team Roles' },
              ].map(mode => (
                <Button
                  key={mode.value}
                  variant={viewMode === mode.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode(mode.value as typeof viewMode)}
                >
                  {mode.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content */}
      {viewMode === 'departments' && renderDepartmentsView()}
      {viewMode === 'personalities' && renderPersonalitiesView()}
      {viewMode === 'roles' && renderRolesView()}
    </div>
  );
};

export default TeamCompositionAnalytics;
