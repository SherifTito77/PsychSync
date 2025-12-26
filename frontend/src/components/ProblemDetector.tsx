/**
 * Real-Time List Problem Detector
 * Identifies potential responsive list issues during development
 */

import React, { useState, useEffect } from 'react';
import { listProblemPredictor, type ListConfiguration, type ListProblem } from '../utils/responsive/problemPredictor';

interface ProblemDetectorProps {
  configuration?: Partial<ListConfiguration>;
  onProblemDetected?: (problems: ListProblem[]) => void;
  showInDevelopment?: boolean;
}

export const ListProblemDetector: React.FC<ProblemDetectorProps> = ({
  configuration = {},
  onProblemDetected,
  showInDevelopment = true
}) => {
  const [isDevelopment, setIsDevelopment] = useState(false);
  const [currentConfig, setCurrentConfig] = useState<ListConfiguration>({
    itemCount: 50,
    contentTypes: ['text'],
    targetDevices: ['mobile', 'tablet', 'desktop'],
    interactionType: 'display',
    dataComplexity: 'simple',
    scrollBehavior: 'none',
    ...configuration
  });
  const [problems, setProblems] = useState<ListProblem[]>([]);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Check if we're in development mode
    setIsDevelopment(
      process.env.NODE_ENV === 'development' ||
      window.location.hostname === 'localhost'
    );
  }, []);

  useEffect(() => {
    const updatedConfig = { ...currentConfig, ...configuration };
    setCurrentConfig(updatedConfig);

    // Predict problems for current configuration
    const predictedProblems = listProblemPredictor.predictProblems(updatedConfig);
    setProblems(predictedProblems);

    if (onProblemDetected) {
      onProblemDetected(predictedProblems);
    }
  }, [configuration]);

  // Don't show in production unless explicitly requested
  if (!showInDevelopment || !isDevelopment) {
    return null;
  }

  const riskAssessment = listProblemPredictor.getRiskAssessment(currentConfig);
  const implementationPlan = listProblemPredictor.generateImplementationPlan(currentConfig);

  const getSeverityColor = (severity: number) => {
    if (severity >= 70) return '#f44336'; // Red
    if (severity >= 50) return '#ff9800'; // Orange
    if (severity >= 30) return '#ffc107'; // Yellow
    return '#4caf50'; // Green
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return '#f44336';
      case 'high': return '#ff9800';
      case 'medium': return '#ffc107';
      case 'low': return '#4caf50';
      default: return '#9e9e9e';
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: 9999,
      minWidth: '320px',
      maxWidth: '400px'
    }}>
      {/* Problem Indicator */}
      <div
        onClick={() => setShowDetails(!showDetails)}
        style={{
          backgroundColor: getRiskColor(riskAssessment.riskLevel),
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '14px',
          fontWeight: '600'
        }}
      >
        <div>
          <div>🔍 List Issues: {problems.length}</div>
          <div style={{ fontSize: '12px', opacity: 0.9, marginTop: '2px' }}>
            Risk: {riskAssessment.riskLevel.toUpperCase()}
          </div>
        </div>
        <div style={{ fontSize: '18px' }}>
          {showDetails ? '▼' : '▶'}
        </div>
      </div>

      {/* Detailed Problem Panel */}
      {showDetails && (
        <div
          style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
            marginTop: '10px',
            maxHeight: '70vh',
            overflowY: 'auto'
          }}
        >
          {/* Header */}
          <div style={{
            padding: '16px',
            borderBottom: '1px solid #eee',
            backgroundColor: '#f8f9fa'
          }}>
            <h3 style={{ margin: 0, color: '#333', fontSize: '16px' }}>
              List Rendering Analysis
            </h3>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              Configuration: {currentConfig.itemCount} items, {currentConfig.targetDevices.join(', ')}
            </div>
          </div>

          {/* Risk Summary */}
          <div style={{ padding: '16px', borderBottom: '1px solid #eee' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center' }}>
              <div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: getRiskColor(riskAssessment.riskLevel) }}>
                  {riskAssessment.totalProblems}
                </div>
                <div style={{ fontSize: '10px', color: '#666' }}>Total Issues</div>
              </div>
              <div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f44336' }}>
                  {riskAssessment.criticalProblems}
                </div>
                <div style={{ fontSize: '10px', color: '#666' }}>Critical</div>
              </div>
              <div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ff9800' }}>
                  {riskAssessment.majorProblems}
                </div>
                <div style={{ fontSize: '10px', color: '#666' }}>Major</div>
              </div>
              <div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#4caf50' }}>
                  {problems.length - riskAssessment.criticalProblems - riskAssessment.majorProblems}
                </div>
                <div style={{ fontSize: '10px', color: '#666' }}>Minor</div>
              </div>
            </div>
          </div>

          {/* Implementation Plan */}
          <div style={{ padding: '16px', borderBottom: '1px solid #eee' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '14px' }}>
              📋 Implementation Plan
            </h4>
            <div style={{ backgroundColor: '#e3f2fd', padding: '10px', borderRadius: '4px', fontSize: '12px' }}>
              <div style={{ fontWeight: '600', color: '#1976d2' }}>
                {implementationPlan.phase}
              </div>
              <div style={{ color: '#666', marginTop: '4px' }}>
                ⏱️ {implementationPlan.time} | Priority: {implementationPlan.priority}
              </div>
            </div>
            <div style={{ marginTop: '8px' }}>
              <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px' }}>
                {implementationPlan.steps.slice(0, 3).map((step, index) => (
                  <li key={index} style={{ marginBottom: '4px' }}>{step}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Problem List */}
          {problems.length > 0 && (
            <div style={{ padding: '16px' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '14px' }}>
                ⚠️ Predicted Problems
              </h4>
              {problems.slice(0, 5).map((problem, index) => (
                <div
                  key={problem.id}
                  style={{
                    marginBottom: '12px',
                    padding: '12px',
                    border: `1px solid ${getSeverityColor(problem.severity)}33`,
                    borderRadius: '6px',
                    backgroundColor: `${getSeverityColor(problem.severity)}11`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1, marginRight: '8px' }}>
                      <div style={{
                        fontWeight: '600',
                        color: '#333',
                        fontSize: '13px',
                        marginBottom: '4px'
                      }}>
                        {problem.title}
                      </div>
                      <div style={{ color: '#666', fontSize: '11px', marginBottom: '6px' }}>
                        {problem.description}
                      </div>
                      <div style={{ fontSize: '10px', color: '#888' }}>
                        <span style={{ color: getSeverityColor(problem.severity) }}>
                          {problem.likelihood}% likelihood
                        </span>
                        {' • '}
                        <span>Complexity: {problem.fixComplexity}</span>
                      </div>
                    </div>
                    <div
                      style={{
                        backgroundColor: getSeverityColor(problem.severity),
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        fontSize: '10px',
                        fontWeight: '600',
                        flexShrink: 0
                      }}
                    >
                      {Math.round(problem.severity)}%
                    </div>
                  </div>
                </div>
              ))}

              {problems.length > 5 && (
                <div style={{ textAlign: 'center', fontSize: '12px', color: '#666' }}>
                  ... and {problems.length - 5} more issues
                </div>
              )}
            </div>
          )}

          {/* Quick Actions */}
          <div style={{ padding: '16px', borderTop: '1px solid #eee' }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '14px' }}>
              🚀 Quick Actions
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(currentConfig, null, 2));
                  alert('Configuration copied to clipboard!');
                }}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#4caf50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                📋 Copy Config
              </button>
              <button
                onClick={() => window.open('https://github.com/psychsync/list-rendering-guide', '_blank')}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#2196f3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                📚 View Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Hook for programmatic problem detection
export const useListProblemDetector = (config: Partial<ListConfiguration>) => {
  const [problems, setProblems] = useState<ListProblem[]>([]);
  const [risk, setRisk] = useState<any>(null);

  useEffect(() => {
    const fullConfig: ListConfiguration = {
      itemCount: 50,
      contentTypes: ['text'],
      targetDevices: ['mobile', 'tablet', 'desktop'],
      interactionType: 'display',
      dataComplexity: 'simple',
      scrollBehavior: 'none',
      ...config
    };

    const predictedProblems = listProblemPredictor.predictProblems(fullConfig);
    const riskAssessment = listProblemPredictor.getRiskAssessment(fullConfig);

    setProblems(predictedProblems);
    setRisk(riskAssessment);
  }, [config]);

  return { problems, risk, predictor: listProblemPredictor };
};

// Development toolbar component
export const ListProblemDevToolbar: React.FC = () => {
  const [testConfig, setTestConfig] = useState<Partial<ListConfiguration>>({
    itemCount: 50,
    contentTypes: ['text'],
    targetDevices: ['mobile', 'tablet', 'desktop'],
    interactionType: 'display',
    dataComplexity: 'simple'
  });

  const { problems, risk } = useListProblemDetector(testConfig);

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      left: '20px',
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      padding: '16px',
      minWidth: '280px',
      zIndex: 9999,
      fontSize: '12px'
    }}>
      <h4 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>🧪 Test Configuration</h4>

      <div style={{ marginBottom: '12px' }}>
        <label>Item Count:</label>
        <input
          type="range"
          min="10"
          max="1000"
          step="10"
          value={testConfig.itemCount}
          onChange={(e) => setTestConfig({...testConfig, itemCount: parseInt(e.target.value)})}
          style={{ width: '100%' }}
        />
        <div>{testConfig.itemCount} items</div>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Complexity:</label>
        <select
          value={testConfig.dataComplexity}
          onChange={(e) => setTestConfig({...testConfig, dataComplexity: e.target.value as any})}
          style={{ width: '100%', padding: '4px' }}
        >
          <option value="simple">Simple</option>
          <option value="medium">Medium</option>
          <option value="complex">Complex</option>
        </select>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>Devices:</label>
        <div>
          {['mobile', 'tablet', 'desktop'].map(device => (
            <label key={device} style={{ marginRight: '12px' }}>
              <input
                type="checkbox"
                checked={testConfig.targetDevices?.includes(device as any)}
                onChange={(e) => {
                  const devices = testConfig.targetDevices || [];
                  if (e.target.checked) {
                    setTestConfig({...testConfig, targetDevices: [...devices, device as any]});
                  } else {
                    setTestConfig({...testConfig, targetDevices: devices.filter(d => d !== device)});
                  }
                }}
              />
              {device}
            </label>
          ))}
        </div>
      </div>

      <div style={{
        padding: '8px',
        backgroundColor: risk ? `rgba(244, 67, 54, ${1 - risk.totalProblems / 10})` : '#e8f5e8',
        borderRadius: '4px',
        textAlign: 'center'
      }}>
        <div style={{ fontWeight: 'bold' }}>
          {problems.length} Issues Detected
        </div>
        <div style={{ fontSize: '10px', color: '#666' }}>
          Risk: {risk?.riskLevel}
        </div>
      </div>
    </div>
  );
};

export default ListProblemDetector;