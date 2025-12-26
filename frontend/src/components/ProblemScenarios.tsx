/**
 * Real-World List Problem Scenarios
 * Demonstrates common responsive list rendering issues and their solutions
 */

import React, { useState } from 'react';
import ListProblemDetector, { useListProblemDetector } from './ProblemDetector';

// SCENARIO 1: Mobile Touch Target Problems
const ProblematicMobileList: React.FC = () => {
  const teamMembers = [
    'Dr. Alexandra Elizabeth Wellington-Thompson',
    'Michael Christopher Rodriguez-Smith-Johnson',
    'Jennifer Marie Antoinette De La Cruz Hernandez',
    'William James Alexander MacDonald O\'Brien',
    'Sarah Michelle Anderson Thompson'
  ];

  return (
    <div>
      <h3>❌ Problematic Mobile List</h3>
      <div style={{
        backgroundColor: '#ffebee',
        padding: '10px',
        borderRadius: '4px',
        marginBottom: '10px',
        fontSize: '12px'
      }}>
        <strong>Issues:</strong> Small touch targets, no spacing, horizontal scroll
      </div>
      <ul style={{
        listStyle: 'none',
        padding: 0,
        margin: 0,
        border: '1px solid #ddd',
        borderRadius: '4px',
        width: '300px',
        overflowX: 'auto'
      }}>
        {teamMembers.map((member, index) => (
          <li key={index} style={{
            padding: '4px 8px',
            height: '28px',
            lineHeight: '20px',
            borderBottom: '1px solid #eee',
            fontSize: '12px',
            whiteSpace: 'nowrap',
            cursor: 'pointer'
          }}>
            {member}
          </li>
        ))}
      </ul>
    </div>
  );
};

const FixedMobileList: React.FC = () => {
  const teamMembers = [
    { id: 1, name: 'Dr. Alexandra Wellington-Thompson', role: 'Senior Researcher' },
    { id: 2, name: 'Michael Rodriguez-Smith', role: 'Lead Developer' },
    { id: 3, name: 'Jennifer De La Cruz', role: 'UX Designer' },
    { id: 4, name: 'William MacDonald', role: 'Project Manager' },
    { id: 5, name: 'Sarah Anderson', role: 'QA Engineer' }
  ];

  return (
    <div>
      <h3>✅ Fixed Mobile List</h3>
      <div style={{
        backgroundColor: '#e8f5e8',
        padding: '10px',
        borderRadius: '4px',
        marginBottom: '10px',
        fontSize: '12px'
      }}>
        <strong>Fixes:</strong> 44px touch targets, proper spacing, text truncation
      </div>
      <ul style={{
        listStyle: 'none',
        padding: 0,
        margin: 0,
        border: '1px solid #ddd',
        borderRadius: '4px',
        width: '300px'
      }}>
        {teamMembers.map((member) => (
          <li key={member.id} style={{
            padding: '12px 16px',
            minHeight: '44px',
            borderBottom: '1px solid #eee',
            display: 'flex',
            flexDirection: 'column',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease'
          }}>
            <div style={{
              fontWeight: '600',
              color: '#333',
              fontSize: '14px',
              lineHeight: '1.4',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {member.name}
            </div>
            <div style={{
              color: '#666',
              fontSize: '12px',
              marginTop: '2px'
            }}>
              {member.role}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

// SCENARIO 2: Large List Performance Problems
const ProblematicLargeList: React.FC = () => {
  // Simulate 1000 items without optimization
  const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
    id: i + 1,
    name: `User ${i + 1}`,
    email: `user${i + 1}@company.com`,
    department: ['Engineering', 'Design', 'Marketing', 'Sales', 'HR'][i % 5]
  }));

  return (
    <div>
      <h3>❌ Problematic Large List</h3>
      <div style={{
        backgroundColor: '#ffebee',
        padding: '10px',
        borderRadius: '4px',
        marginBottom: '10px',
        fontSize: '12px'
      }}>
        <strong>Issues:</strong> Renders all 1000 items, slow performance, high memory usage
      </div>
      <div style={{
        border: '1px solid #ddd',
        borderRadius: '4px',
        height: '300px',
        overflowY: 'auto'
      }}>
        {largeDataset.map((user) => (
          <div key={user.id} style={{
            padding: '8px 12px',
            borderBottom: '1px solid #eee',
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '12px'
          }}>
            <div>
              <div style={{ fontWeight: '600' }}>{user.name}</div>
              <div style={{ color: '#666' }}>{user.email}</div>
            </div>
            <div style={{ color: '#007aff' }}>{user.department}</div>
          </div>
        ))}
      </div>
      <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
        ⚠️ This will render 1000 DOM nodes!
      </div>
    </div>
  );
};

const OptimizedLargeList: React.FC = () => {
  // Virtual rendering simulation - only show visible items
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 20 });
  const containerHeight = 300;
  const itemHeight = 50;

  const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
    id: i + 1,
    name: `User ${i + 1}`,
    email: `user${i + 1}@company.com`,
    department: ['Engineering', 'Design', 'Marketing', 'Sales', 'HR'][i % 5]
  }));

  const visibleItems = largeDataset.slice(visibleRange.start, visibleRange.end);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = e.currentTarget.scrollTop;
    const newStart = Math.floor(scrollTop / itemHeight);
    const newEnd = Math.min(newStart + Math.ceil(containerHeight / itemHeight) + 1, largeDataset.length);
    setVisibleRange({ start: newStart, end: newEnd });
  };

  return (
    <div>
      <h3>✅ Optimized Large List</h3>
      <div style={{
        backgroundColor: '#e8f5e8',
        padding: '10px',
        borderRadius: '4px',
        marginBottom: '10px',
        fontSize: '12px'
      }}>
        <strong>Fixes:</strong> Virtual scrolling, only renders visible items
      </div>
      <div style={{
        border: '1px solid #ddd',
        borderRadius: '4px',
        height: `${containerHeight}px`,
        overflowY: 'auto',
        position: 'relative'
      }}
      onScroll={handleScroll}>
        <div style={{ height: largeDataset.length * itemHeight, position: 'relative' }}>
          {visibleItems.map((user, index) => (
            <div
              key={user.id}
              style={{
                position: 'absolute',
                top: (visibleRange.start + index) * itemHeight,
                left: 0,
                right: 0,
                height: itemHeight,
                padding: '8px 12px',
                borderBottom: '1px solid #eee',
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '12px',
                backgroundColor: 'white'
              }}
            >
              <div>
                <div style={{ fontWeight: '600' }}>{user.name}</div>
                <div style={{ color: '#666' }}>{user.email}</div>
              </div>
              <div style={{ color: '#007aff' }}>{user.department}</div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
        ✅ Only {visibleItems.length} of {largeDataset.length} items rendered
      </div>
    </div>
  );
};

// SCENARIO 3: Accessibility Problems
const ProblematicAccessibilityList: React.FC = () => {
  const menuItems = ['Home', 'Profile', 'Settings', 'Help', 'Logout'];

  return (
    <div>
      <h3>❌ Problematic Accessibility</h3>
      <div style={{
        backgroundColor: '#ffebee',
        padding: '10px',
        borderRadius: '4px',
        marginBottom: '10px',
        fontSize: '12px'
      }}>
        <strong>Issues:</strong> No ARIA labels, no keyboard navigation, no semantic HTML
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {menuItems.map((item, index) => (
          <div
            key={index}
            onClick={() => alert(`Clicked ${item}`)}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f5f5f5',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {item}
          </div>
        ))}
      </div>
    </div>
  );
};

const AccessibleList: React.FC = () => {
  const menuItems = ['Home', 'Profile', 'Settings', 'Help', 'Logout'];
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % menuItems.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + menuItems.length) % menuItems.length);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        alert(`Navigated to ${menuItems[index]}`);
        break;
    }
  };

  return (
    <div>
      <h3>✅ Accessible List</h3>
      <div style={{
        backgroundColor: '#e8f5e8',
        padding: '10px',
        borderRadius: '4px',
        marginBottom: '10px',
        fontSize: '12px'
      }}>
        <strong>Fixes:</strong> Semantic HTML, ARIA labels, keyboard navigation
      </div>
      <nav role="navigation" aria-label="Main menu">
        <ul role="menubar" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {menuItems.map((item, index) => (
            <li key={index} role="none">
              <button
                role="menuitem"
                aria-label={`Navigate to ${item}`}
                onKeyDown={(e) => handleKeyDown(e, index)}
                onClick={() => alert(`Navigated to ${item}`)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  backgroundColor: selectedIndex === index ? '#e3f2fd' : '#f5f5f5',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px',
                  marginBottom: '4px',
                  borderRadius: '4px',
                  outline: selectedIndex === index ? '2px solid #007aff' : 'none'
                }}
              >
                {item}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
};

// Main demonstration component
export const ListProblemScenarios: React.FC = () => {
  const [activeScenario, setActiveScenario] = useState<'mobile' | 'performance' | 'accessibility'>('mobile');

  // Problem detection for current scenario
  const scenarioConfigs = {
    mobile: {
      itemCount: 10,
      contentTypes: ['text', 'metadata'],
      targetDevices: ['mobile', 'tablet'],
      interactionType: 'selection' as const,
      dataComplexity: 'simple' as const
    },
    performance: {
      itemCount: 1000,
      contentTypes: ['text', 'metadata'],
      targetDevices: ['desktop', 'tablet'],
      interactionType: 'display' as const,
      dataComplexity: 'medium' as const
    },
    accessibility: {
      itemCount: 5,
      contentTypes: ['text'],
      targetDevices: ['mobile', 'tablet', 'desktop'],
      interactionType: 'selection' as const,
      dataComplexity: 'simple' as const
    }
  };

  const { problems, risk } = useListProblemDetector(scenarioConfigs[activeScenario]);

  return (
    <div style={{ padding: '20px' }}>
      <h1>🔍 Real-World List Rendering Problems</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>
        Common scenarios where responsive list rendering problems occur and how to fix them.
      </p>

      {/* Problem Detection */}
      <ListProblemDetector
        configuration={scenarioConfigs[activeScenario]}
        showInDevelopment={true}
      />

      {/* Scenario Selector */}
      <div style={{
        marginBottom: '30px',
        display: 'flex',
        gap: '10px',
        flexWrap: 'wrap'
      }}>
        {(['mobile', 'performance', 'accessibility'] as const).map((scenario) => (
          <button
            key={scenario}
            onClick={() => setActiveScenario(scenario)}
            style={{
              padding: '10px 20px',
              backgroundColor: activeScenario === scenario ? '#007aff' : '#f5f5f5',
              color: activeScenario === scenario ? 'white' : '#333',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: activeScenario === scenario ? '600' : 'normal'
            }}
          >
            {scenario === 'mobile' && '📱 Mobile Touch'}
            {scenario === 'performance' && '⚡ Performance'}
            {scenario === 'accessibility' && '♿ Accessibility'}
          </button>
        ))}
      </div>

      {/* Current Scenario Analysis */}
      <div style={{
        backgroundColor: '#fff3cd',
        border: '1px solid #ffeaa7',
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '30px'
      }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#856404' }}>
          Current Analysis: {activeScenario.charAt(0).toUpperCase() + activeScenario.slice(1)} Scenario
        </h3>
        <div style={{ fontSize: '14px', color: '#856404' }}>
          <strong>Detected Issues:</strong> {problems.length} problems identified<br />
          <strong>Risk Level:</strong> <span style={{
            backgroundColor: risk.riskLevel === 'critical' ? '#f44336' :
                          risk.riskLevel === 'high' ? '#ff9800' :
                          risk.riskLevel === 'medium' ? '#ffc107' : '#4caf50',
            color: 'white',
            padding: '2px 8px',
            borderRadius: '3px',
            fontSize: '12px'
          }}>
            {risk.riskLevel.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Scenarios */}
      {activeScenario === 'mobile' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
          <ProblematicMobileList />
          <FixedMobileList />
        </div>
      )}

      {activeScenario === 'performance' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
          <ProblematicLargeList />
          <OptimizedLargeList />
        </div>
      )}

      {activeScenario === 'accessibility' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
          <ProblematicAccessibilityList />
          <AccessibleList />
        </div>
      )}

      {/* Instructions */}
      <div style={{
        marginTop: '40px',
        padding: '20px',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        fontSize: '14px'
      }}>
        <h3 style={{ marginTop: 0 }}>🧪 How to Test</h3>
        <ol>
          <li><strong>Mobile Scenario:</strong> Try tapping items on a mobile device or simulate with touch</li>
          <li><strong>Performance Scenario:</strong> Observe scrolling performance with 1000 items</li>
          <li><strong>Accessibility Scenario:</strong> Try keyboard navigation (Tab, Arrow keys, Enter)</li>
        </ol>

        <h4>Developer Tools:</h4>
        <ul>
          <li>Open browser DevTools and simulate mobile devices</li>
          <li>Use screen reader to test accessibility</li>
          <li>Monitor Performance tab for render times</li>
        </ul>
      </div>
    </div>
  );
};

export default ListProblemScenarios;