/**
 * PsychSync Mobile Integration
 * Demonstrates how the mobile optimization system integrates with existing PsychSync components
 */

import React, { useState, useEffect } from 'react';
import {
  TeamOptimizationComponent,
  AssessmentResultsComponent,
  UserDashboardComponent
} from '../components';
import {
  SimpleResponsiveList,
  VirtualizedList,
  useMobileResponsive,
  useCrossPlatformOptimizations
} from '../components/mobile';
import {
  mobileBrowserCompatibility,
  UXUsabilityDefectDetector
} from '../utils';

// Mock PsychSync-specific data structures
interface PsychSyncUser {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'team_lead';
  department: string;
  personalityType?: string;
  strengths: string[];
}

interface PsychSyncAssessment {
  id: string;
  userId: string;
  type: 'big_five' | 'mbti' | 'enneagram' | 'predictive_index';
  completedAt: string;
  score: number;
  insights: string[];
  recommendations: string[];
}

interface PsychSyncTeam {
  id: string;
  name: string;
  memberCount: number;
  avgPerformance: number;
  cohesionScore: number;
  recentActivity: string;
}

// Mock service layer (simulates existing PsychSync services)
class PsychSyncService {
  static async getUserTeams(): Promise<PsychSyncTeam[]> {
    // Simulate API call
    return [
      {
        id: '1',
        name: 'Product Development',
        memberCount: 12,
        avgPerformance: 87,
        cohesionScore: 92,
        recentActivity: 'Completed team assessment'
      },
      {
        id: '2',
        name: 'Marketing & Growth',
        memberCount: 8,
        avgPerformance: 91,
        cohesionScore: 88,
        recentActivity: 'Onboarding new member'
      },
      {
        id: '3',
        name: 'Customer Success',
        memberCount: 6,
        avgPerformance: 94,
        cohesionScore: 95,
        recentActivity: 'Quarterly review completed'
      }
    ];
  }

  static async getTeamMembers(teamId: string): Promise<PsychSyncUser[]> {
    // Simulate API call with mock data
    return Array.from({ length: 15 }, (_, i) => ({
      id: `${teamId}-${i + 1}`,
      name: `Team Member ${i + 1}`,
      email: `member${i + 1}@company.com`,
      role: ['admin', 'user', 'team_lead'][i % 3] as 'admin' | 'user' | 'team_lead',
      department: 'Product Development',
      personalityType: ['ENFJ', 'ISTJ', 'ENTP', 'ISFP'][i % 4],
      strengths: ['Leadership', 'Communication', 'Problem Solving', 'Creativity'].slice(0, (i % 3) + 1)
    }));
  }

  static async getUserAssessments(userId: string): Promise<PsychSyncAssessment[]> {
    // Simulate API call
    return [
      {
        id: '1',
        userId,
        type: 'big_five',
        completedAt: '2024-01-15T10:30:00Z',
        score: 92,
        insights: ['High openness to experience', 'Strong conscientiousness', 'Excellent emotional stability'],
        recommendations: ['Consider leadership roles', 'Focus on creative problem-solving']
      },
      {
        id: '2',
        userId,
        type: 'mbti',
        completedAt: '2024-01-10T14:20:00Z',
        score: 88,
        insights: ['Strong intuitive preferences', 'Good thinking-feeling balance'],
        recommendations: ['Leverage intuition in decision-making', 'Balance analytical and emotional approaches']
      }
    ];
  }
}

// Enhanced PsychSync components with mobile optimization
export const EnhancedTeamOverview: React.FC = () => {
  const [teams, setTeams] = useState<PsychSyncTeam[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<PsychSyncTeam | null>(null);
  const [teamMembers, setTeamMembers] = useState<PsychSyncUser[]>([]);
  const [loading, setLoading] = useState(false);
  const { isMobile, breakpoints } = useMobileResponsive();
  const { platform, optimizations } = useCrossPlatformOptimizations();

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setLoading(true);
    try {
      const teamsData = await PsychSyncService.getUserTeams();
      setTeams(teamsData);
    } catch (error) {
      console.error('Failed to load teams:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTeamSelect = async (team: PsychSyncTeam) => {
    setSelectedTeam(team);
    setLoading(true);
    try {
      const members = await PsychSyncService.getTeamMembers(team.id);
      setTeamMembers(members);
    } catch (error) {
      console.error('Failed to load team members:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderTeam = (team: PsychSyncTeam) => (
    <div
      className={`team-card ${selectedTeam?.id === team.id ? 'selected' : ''}`}
      onClick={() => handleTeamSelect(team)}
    >
      <div className="team-header">
        <h3 className="team-name">{team.name}</h3>
        <span className="member-count">{team.memberCount} members</span>
      </div>

      <div className="team-metrics">
        <div className="metric">
          <span className="metric-label">Performance</span>
          <span className="metric-value">{team.avgPerformance}%</span>
        </div>
        <div className="metric">
          <span className="metric-label">Cohesion</span>
          <span className="metric-value">{team.cohesionScore}%</span>
        </div>
      </div>

      <div className="team-activity">
        <p className="activity-text">{team.recentActivity}</p>
      </div>
    </div>
  );

  const renderTeamMember = (member: PsychSyncUser) => (
    <div className="team-member-card">
      <div className="member-avatar">
        {member.name.split(' ').map(n => n[0]).join('')}
      </div>
      <div className="member-info">
        <h4 className="member-name">{member.name}</h4>
        <p className="member-role">{member.role.replace('_', ' ').toUpperCase()}</p>
        {member.personalityType && (
          <span className="personality-type">{member.personalityType}</span>
        )}
      </div>
      <div className="member-actions">
        <button className="action-button">View Profile</button>
      </div>
    </div>
  );

  return (
    <div className="enhanced-team-overview">
      <style jsx>{`
        .enhanced-team-overview {
          padding: ${isMobile ? '12px' : '24px'};
          max-width: 1200px;
          margin: 0 auto;
        }

        .header {
          text-align: center;
          margin-bottom: ${isMobile ? '20px' : '32px'};
        }

        .header h1 {
          font-size: ${isMobile ? '24px' : '32px'};
          margin-bottom: 8px;
        }

        .platform-info {
          display: flex;
          justify-content: center;
          gap: 12px;
          margin-bottom: 16px;
          font-size: 14px;
          color: #666;
        }

        .content-layout {
          display: ${isMobile ? 'block' : 'grid'};
          grid-template-columns: 1fr 1fr;
          gap: ${isMobile ? '16px' : '24px'};
        }

        .teams-section, .members-section {
          background: white;
          border-radius: 12px;
          padding: ${isMobile ? '16px' : '24px'};
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .section-title {
          font-size: ${isMobile ? '18px' : '20px'};
          font-weight: 600;
          margin-bottom: 16px;
        }

        .team-card {
          padding: 16px;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          margin-bottom: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .team-card:hover {
          border-color: #007AFF;
          transform: translateY(-2px);
        }

        .team-card.selected {
          border-color: #007AFF;
          background: #f8f9ff;
        }

        .team-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .team-name {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .member-count {
          background: #e3f2fd;
          color: #1976d2;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
        }

        .team-metrics {
          display: flex;
          gap: 24px;
          margin-bottom: 12px;
        }

        .metric {
          display: flex;
          flex-direction: column;
        }

        .metric-label {
          font-size: 12px;
          color: #666;
          margin-bottom: 2px;
        }

        .metric-value {
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }

        .activity-text {
          margin: 0;
          font-size: 14px;
          color: #666;
        }

        .team-member-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-bottom: 1px solid #f0f0f0;
        }

        .member-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #007AFF;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
        }

        .member-info {
          flex: 1;
        }

        .member-name {
          margin: 0 0 4px 0;
          font-size: 14px;
          font-weight: 500;
        }

        .member-role {
          margin: 0 0 4px 0;
          font-size: 12px;
          color: #666;
        }

        .personality-type {
          background: #f0f0f0;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 11px;
          color: #666;
        }

        .action-button {
          padding: 6px 12px;
          background: #007AFF;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .action-button:hover {
          background: #0056b3;
        }

        .empty-state {
          text-align: center;
          padding: 32px;
          color: #666;
        }

        @media (max-width: 768px) {
          .team-metrics {
            gap: 16px;
          }
        }
      `}</style>

      <div className="header">
        <h1>🏢 PsychSync Team Overview</h1>
        <p>Mobile-optimized team management with cross-platform compatibility</p>

        <div className="platform-info">
          <span>Platform: <strong>{platform}</strong></span>
          <span>Optimizations: <strong>{optimizations.length}</strong></span>
          <span>Screen: <strong>{isMobile ? 'Mobile' : 'Desktop'}</strong></span>
        </div>
      </div>

      <div className="content-layout">
        {/* Teams List */}
        <div className="teams-section">
          <h2 className="section-title">Your Teams</h2>

          {loading ? (
            <div>Loading teams...</div>
          ) : (
            <SimpleResponsiveList
              items={teams}
              renderItem={renderTeam}
              className="teams-list"
            />
          )}
        </div>

        {/* Team Members */}
        <div className="members-section">
          <h2 className="section-title">
            {selectedTeam ? `${selectedTeam.name} Members` : 'Select a Team'}
          </h2>

          {!selectedTeam ? (
            <div className="empty-state">
              <p>Select a team to view members</p>
            </div>
          ) : loading ? (
            <div>Loading members...</div>
          ) : (
            <SimpleResponsiveList
              items={teamMembers}
              renderItem={renderTeamMember}
              className="members-list"
            />
          )}
        </div>
      </div>
    </div>
  );
};

// Enhanced Assessment Results with mobile optimization
export const EnhancedAssessmentResults: React.FC = () => {
  const [assessments, setAssessments] = useState<PsychSyncAssessment[]>([]);
  const [loading, setLoading] = useState(false);
  const { isMobile } = useMobileResponsive();

  useEffect(() => {
    loadAssessments();
  }, []);

  const loadAssessments = async () => {
    setLoading(true);
    try {
      const assessmentData = await PsychSyncService.getUserAssessments('current-user');
      setAssessments(assessmentData);
    } catch (error) {
      console.error('Failed to load assessments:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderAssessment = (assessment: PsychSyncAssessment) => (
    <div className="assessment-result-card">
      <div className="assessment-header">
        <div className="assessment-type">
          <h3 className="type-name">{assessment.type.replace('_', ' ').toUpperCase()}</h3>
          <p className="completion-date">
            {new Date(assessment.completedAt).toLocaleDateString()}
          </p>
        </div>
        <div className="assessment-score">
          <div className="score-circle">{assessment.score}</div>
        </div>
      </div>

      <div className="assessment-insights">
        <h4 className="insights-title">Key Insights</h4>
        <ul className="insights-list">
          {assessment.insights.slice(0, 3).map((insight, index) => (
            <li key={index} className="insight-item">{insight}</li>
          ))}
        </ul>
      </div>

      <div className="assessment-recommendations">
        <h4 className="recommendations-title">Recommendations</h4>
        <div className="recommendations-list">
          {assessment.recommendations.slice(0, 2).map((rec, index) => (
            <div key={index} className="recommendation-item">{rec}</div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="enhanced-assessment-results">
      <style jsx>{`
        .enhanced-assessment-results {
          padding: ${isMobile ? '12px' : '24px'};
          max-width: 800px;
          margin: 0 auto;
        }

        .header {
          text-align: center;
          margin-bottom: ${isMobile ? '20px' : '32px'};
        }

        .header h1 {
          font-size: ${isMobile ? '24px' : '28px'};
          margin-bottom: 8px;
        }

        .assessment-result-card {
          background: white;
          border-radius: 12px;
          padding: ${isMobile ? '16px' : '24px'};
          margin-bottom: 16px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .assessment-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .type-name {
          margin: 0 0 4px 0;
          font-size: 18px;
          font-weight: 600;
          color: #333;
        }

        .completion-date {
          margin: 0;
          font-size: 14px;
          color: #666;
        }

        .score-circle {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: linear-gradient(135deg, #4caf50, #8bc34a);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 20px;
          font-weight: bold;
        }

        .assessment-insights {
          margin-bottom: 20px;
        }

        .insights-title, .recommendations-title {
          margin: 0 0 12px 0;
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }

        .insights-list {
          margin: 0;
          padding-left: 20px;
        }

        .insight-item {
          margin-bottom: 8px;
          font-size: 14px;
          color: #555;
        }

        .recommendations-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .recommendation-item {
          padding: 8px 12px;
          background: #f8f9ff;
          border-left: 3px solid #007AFF;
          border-radius: 4px;
          font-size: 14px;
          color: #555;
        }
      `}</style>

      <div className="header">
        <h1>📊 Your Assessment Results</h1>
        <p>Mobile-optimized view of your psychological assessment insights</p>
      </div>

      {loading ? (
        <div>Loading assessments...</div>
      ) : (
        <SimpleResponsiveList
          items={assessments}
          renderItem={renderAssessment}
          className="assessments-list"
        />
      )}
    </div>
  );
};

export default {
  EnhancedTeamOverview,
  EnhancedAssessmentResults
};