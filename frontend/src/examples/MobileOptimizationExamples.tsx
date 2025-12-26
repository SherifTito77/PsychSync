/**
 * Mobile Optimization Examples - Practical Usage Demonstrations
 * Shows how to use the mobile-responsive ecosystem components in real applications
 */

import React, { useState, useEffect } from 'react';
import {
  MobileResponsiveDashboard,
  ListRenderingAnalyzer,
  SimpleResponsiveList,
  VirtualizedList
} from '../components/mobile';
import {
  mobileBrowserCompatibility,
  type BrowserInfo
} from '../utils/crossPlatform/mobileBrowserCompatibility';
import {
  UXUsabilityDefectDetector,
  type DefectReport
} from '../utils/ux/usabilityDefectDetector';

// Example data sets for different scenarios
const SAMPLE_DATA = {
  // Small list - perfect for SimpleResponsiveList
  teamMembers: [
    { id: 1, name: 'Sarah Chen', role: 'Product Manager', avatar: '👩‍💼', status: 'online' },
    { id: 2, name: 'Marcus Johnson', role: 'UX Designer', avatar: '👨‍🎨', status: 'online' },
    { id: 3, name: 'Elena Rodriguez', role: 'Frontend Dev', avatar: '👩‍💻', status: 'busy' },
    { id: 4, name: 'David Kim', role: 'Backend Dev', avatar: '👨‍💻', status: 'offline' },
    { id: 5, name: 'Amanda Foster', role: 'Data Analyst', avatar: '👩‍📊', status: 'online' },
  ],

  // Medium list - good for responsive testing
  assessmentResults: [
    { id: 1, userName: 'Alex Thompson', assessment: 'Big Five', score: 92, date: '2024-01-15', trend: 'up' },
    { id: 2, userName: 'Jessica Lee', assessment: 'MBTI', score: 88, date: '2024-01-14', trend: 'stable' },
    { id: 3, userName: 'Ryan Cooper', assessment: 'Enneagram', score: 76, date: '2024-01-13', trend: 'down' },
    { id: 4, userName: 'Maya Patel', assessment: 'Predictive Index', score: 94, date: '2024-01-12', trend: 'up' },
    { id: 5, userName: 'Thomas Wright', assessment: 'Clifton Strengths', score: 89, date: '2024-01-11', trend: 'up' },
    { id: 6, userName: 'Lisa Chang', assessment: 'Social Styles', score: 91, date: '2024-01-10', trend: 'stable' },
    { id: 7, userName: 'James Wilson', assessment: 'Big Five', score: 87, date: '2024-01-09', trend: 'up' },
    { id: 8, userName: 'Nina Garcia', assessment: 'MBTI', score: 93, date: '2024-01-08', trend: 'up' },
  ],

  // Large list - perfect for VirtualizedList
  allEmployees: Array.from({ length: 1000 }, (_, i) => ({
    id: i + 1,
    name: `Employee ${i + 1}`,
    department: ['Engineering', 'Design', 'Product', 'Marketing', 'Sales'][i % 5],
    email: `employee${i + 1}@company.com`,
    performance: Math.floor(Math.random() * 40) + 60,
    joinDate: new Date(2020 + Math.floor(Math.random() * 4), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString().split('T')[0]
  }))
};

export const MobileOptimizationExamples: React.FC = () => {
  const [activeExample, setActiveExample] = useState<'team' | 'assessments' | 'employees'>('team');
  const [browserInfo, setBrowserInfo] = useState<BrowserInfo | null>(null);
  const [showOptimizationPanel, setShowOptimizationPanel] = useState(false);
  const [defectReport, setDefectReport] = useState<DefectReport | null>(null);

  useEffect(() => {
    // Detect browser and get compatibility info
    const info = mobileBrowserCompatibility.getBrowserInfo();
    setBrowserInfo(info);

    // Run UX defect detection
    const detector = new UXUsabilityDefectDetector();
    const runDefectDetection = async () => {
      const container = document.getElementById('examples-container');
      if (container) {
        const report = await detector.analyzeLayout('MobileExamples', container);
        setDefectReport(report);
      }
    };
    runDefectDetection();
  }, []);

  const currentData = {
    team: SAMPLE_DATA.teamMembers,
    assessments: SAMPLE_DATA.assessmentResults,
    employees: SAMPLE_DATA.allEmployees
  }[activeExample];

  const renderTeamMember = (member: any) => (
    <div className="team-member-card">
      <div className="member-avatar">{member.avatar}</div>
      <div className="member-info">
        <h4 className="member-name">{member.name}</h4>
        <p className="member-role">{member.role}</p>
      </div>
      <div className={`member-status ${member.status}`} />
    </div>
  );

  const renderAssessment = (assessment: any) => (
    <div className="assessment-card">
      <div className="assessment-header">
        <h4 className="user-name">{assessment.userName}</h4>
        <span className={`trend-indicator ${assessment.trend}`}>
          {assessment.trend === 'up' ? '📈' : assessment.trend === 'down' ? '📉' : '➡️'}
        </span>
      </div>
      <div className="assessment-details">
        <p className="assessment-name">{assessment.assessment}</p>
        <div className="score-bar">
          <div className="score-fill" style={{ width: `${assessment.score}%` }} />
          <span className="score-text">{assessment.score}%</span>
        </div>
        <p className="assessment-date">{assessment.date}</p>
      </div>
    </div>
  );

  const renderEmployee = (employee: any) => (
    <div className="employee-row">
      <div className="employee-main">
        <h4 className="employee-name">{employee.name}</h4>
        <p className="employee-department">{employee.department}</p>
      </div>
      <div className="employee-metrics">
        <span className="performance-score">{employee.performance}%</span>
        <span className="join-date">{employee.joinDate}</span>
      </div>
    </div>
  );

  const getListItemConfig = (type: string) => {
    switch (type) {
      case 'team':
        return {
          renderItem: renderTeamMember,
          estimatedItemHeight: 80,
          className: 'team-list'
        };
      case 'assessments':
        return {
          renderItem: renderAssessment,
          estimatedItemHeight: 120,
          className: 'assessment-list'
        };
      case 'employees':
        return {
          renderItem: renderEmployee,
          estimatedItemHeight: 70,
          className: 'employee-list'
        };
      default:
        return {
          renderItem: (item: any) => <div>{JSON.stringify(item)}</div>,
          estimatedItemHeight: 50,
          className: 'default-list'
        };
    }
  };

  const config = getListItemConfig(activeExample);
  const shouldUseVirtualization = currentData.length > 100;

  return (
    <div id="examples-container" className="mobile-optimization-examples">
      <style jsx>{`
        .mobile-optimization-examples {
          max-width: 100%;
          margin: 0 auto;
          padding: 16px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .header {
          text-align: center;
          margin-bottom: 24px;
        }

        .header h1 {
          font-size: 24px;
          margin-bottom: 8px;
          color: #1a1a1a;
        }

        .browser-info {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
          margin-bottom: 16px;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 8px;
          font-size: 14px;
        }

        .platform-badge {
          padding: 4px 8px;
          border-radius: 4px;
          background: #007AFF;
          color: white;
          font-weight: 500;
        }

        .example-selector {
          display: flex;
          gap: 8px;
          margin-bottom: 24px;
          flex-wrap: wrap;
          justify-content: center;
        }

        .example-button {
          padding: 12px 20px;
          border: 2px solid #e0e0e0;
          background: white;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 14px;
          font-weight: 500;
        }

        .example-button:hover {
          border-color: #007AFF;
          background: #f8f9ff;
        }

        .example-button.active {
          border-color: #007AFF;
          background: #007AFF;
          color: white;
        }

        .optimization-toggle {
          display: flex;
          justify-content: center;
          margin-bottom: 16px;
        }

        .toggle-button {
          padding: 8px 16px;
          background: #28a745;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          transition: background 0.2s ease;
        }

        .toggle-button:hover {
          background: #218838;
        }

        .content-area {
          display: grid;
          grid-template-columns: 1fr;
          gap: 20px;
        }

        .optimization-panel {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .list-demo {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .demo-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .demo-title {
          font-size: 18px;
          font-weight: 600;
          color: #1a1a1a;
        }

        .item-count {
          background: #e3f2fd;
          color: #1976d2;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }

        /* List-specific styles */
        .team-member-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          border-bottom: 1px solid #f0f0f0;
        }

        .member-avatar {
          font-size: 24px;
          width: 40px;
          text-align: center;
        }

        .member-info {
          flex: 1;
        }

        .member-name {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 500;
        }

        .member-role {
          margin: 0;
          font-size: 14px;
          color: #666;
        }

        .member-status {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .member-status.online { background: #4caf50; }
        .member-status.busy { background: #ff9800; }
        .member-status.offline { background: #9e9e9e; }

        .assessment-card {
          padding: 16px;
          border-bottom: 1px solid #f0f0f0;
        }

        .assessment-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .user-name {
          margin: 0;
          font-size: 16px;
          font-weight: 500;
        }

        .trend-indicator {
          font-size: 14px;
        }

        .assessment-name {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #666;
        }

        .score-bar {
          position: relative;
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          margin-bottom: 8px;
        }

        .score-fill {
          height: 100%;
          background: linear-gradient(90deg, #4caf50, #8bc34a);
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .score-text {
          position: absolute;
          right: 0;
          top: -2px;
          font-size: 10px;
          font-weight: 500;
          color: #333;
        }

        .assessment-date {
          margin: 0;
          font-size: 12px;
          color: #999;
        }

        .employee-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          border-bottom: 1px solid #f0f0f0;
        }

        .employee-main {
          flex: 1;
        }

        .employee-name {
          margin: 0 0 4px 0;
          font-size: 14px;
          font-weight: 500;
        }

        .employee-department {
          margin: 0;
          font-size: 12px;
          color: #666;
        }

        .employee-metrics {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 4px;
        }

        .performance-score {
          font-size: 14px;
          font-weight: 600;
          color: #4caf50;
        }

        .join-date {
          font-size: 12px;
          color: #999;
        }

        @media (max-width: 768px) {
          .mobile-optimization-examples {
            padding: 12px;
          }

          .example-selector {
            flex-direction: column;
          }

          .example-button {
            width: 100%;
            text-align: center;
          }

          .content-area {
            gap: 16px;
          }
        }
      `}</style>

      {/* Header */}
      <div className="header">
        <h1>📱 Mobile Optimization Examples</h1>
        <p>See the cross-platform compatibility system in action</p>
      </div>

      {/* Browser Info */}
      {browserInfo && (
        <div className="browser-info">
          <span>Platform: <strong>{browserInfo.platform}</strong></span>
          <span>Browser: <strong>{browserInfo.browser}</strong></span>
          <span>Engine: <strong>{browserInfo.engine}</strong></span>
          <span className="platform-badge">{browserInfo.platform.toUpperCase()}</span>
        </div>
      )}

      {/* Example Selector */}
      <div className="example-selector">
        <button
          className={`example-button ${activeExample === 'team' ? 'active' : ''}`}
          onClick={() => setActiveExample('team')}
        >
          👥 Team Members ({SAMPLE_DATA.teamMembers.length})
        </button>
        <button
          className={`example-button ${activeExample === 'assessments' ? 'active' : ''}`}
          onClick={() => setActiveExample('assessments')}
        >
          📊 Assessment Results ({SAMPLE_DATA.assessmentResults.length})
        </button>
        <button
          className={`example-button ${activeExample === 'employees' ? 'active' : ''}`}
          onClick={() => setActiveExample('employees')}
        >
          👤 All Employees ({SAMPLE_DATA.allEmployees.length})
        </button>
      </div>

      {/* Optimization Panel Toggle */}
      <div className="optimization-toggle">
        <button
          className="toggle-button"
          onClick={() => setShowOptimizationPanel(!showOptimizationPanel)}
        >
          {showOptimizationPanel ? 'Hide' : 'Show'} Optimization Panel
        </button>
      </div>

      <div className="content-area">
        {/* Mobile Optimization Panel */}
        {showOptimizationPanel && (
          <div className="optimization-panel">
            <MobileResponsiveDashboard />
          </div>
        )}

        {/* List Demo */}
        <div className="list-demo">
          <div className="demo-header">
            <h3 className="demo-title">
              {activeExample === 'team' && 'Team Members List'}
              {activeExample === 'assessments' && 'Assessment Results'}
              {activeExample === 'employees' && 'Employee Directory'}
            </h3>
            <span className="item-count">
              {currentData.length} items
              {shouldUseVirtualization && ' (Virtualized)'}
            </span>
          </div>

          {/* Render the appropriate list component */}
          {shouldUseVirtualization ? (
            <VirtualizedList
              items={currentData}
              renderItem={config.renderItem}
              estimatedItemHeight={config.estimatedItemHeight}
              className={config.className}
            />
          ) : (
            <SimpleResponsiveList
              items={currentData}
              renderItem={config.renderItem}
              className={config.className}
            />
          )}
        </div>
      </div>

      {/* Defect Report Summary */}
      {defectReport && defectReport.issues.length > 0 && (
        <div style={{ marginTop: '20px', padding: '16px', background: '#fff3cd', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 8px 0', color: '#856404' }}>
            🚨 UX Issues Detected: {defectReport.issues.length}
          </h4>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#856404' }}>
            {defectReport.issues.slice(0, 3).map(issue => (
              <li key={issue.id}>{issue.title}</li>
            ))}
            {defectReport.issues.length > 3 && (
              <li>...and {defectReport.issues.length - 3} more issues</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MobileOptimizationExamples;