/**
 * List Rendering Problem Prediction System
 * Anticipates responsive layout issues before they impact users
 */

export interface ListProblem {
  id: string;
  category: 'critical' | 'major' | 'minor';
  likelihood: number; // 0-100%
  impact: number; // 0-100%
  severity: number; // likelihood * impact
  title: string;
  description: string;
  scenarios: string[];
  warningSigns: string[];
  prevention: string[];
  codeExample?: string;
  fixComplexity: 'simple' | 'moderate' | 'complex';
}

export interface ListConfiguration {
  itemCount: number;
  contentTypes: ('text' | 'images' | 'actions' | 'metadata')[];
  targetDevices: ('mobile' | 'tablet' | 'desktop')[];
  interactionType: 'display' | 'selection' | 'multi-select' | 'drag-drop';
  dataComplexity: 'simple' | 'medium' | 'complex';
  scrollBehavior: 'none' | 'short' | 'long' | 'infinite';
}

export class ListRenderingProblemPredictor {
  private commonProblems: ListProblem[] = [
    // CRITICAL PROBLEMS
    {
      id: 'mobile-touch-failure',
      category: 'critical',
      likelihood: 85,
      impact: 95,
      severity: 80.75,
      title: 'Mobile Touch Target Failure',
      description: 'List items too small for reliable touch interaction on mobile devices',
      scenarios: [
        'Users with larger fingers or using phones one-handed',
        'Rapid scrolling environments where precision is reduced',
        'Accessibility users with motor impairments',
        'Outdoor use with screen glare reducing visibility'
      ],
      warningSigns: [
        'Tap targets smaller than 44px',
        'Buttons too close together (<8px spacing)',
        'No visual feedback on touch',
        'Inconsistent tap success rate'
      ],
      prevention: [
        'Minimum 44px touch targets',
        '8px spacing between interactive elements',
        'Visual feedback on all interactions',
        'Test with real users on actual devices'
      ],
      codeExample: `
❌ PROBLEMATIC:
.list-item { padding: 4px 8px; height: 32px; }

✅ SOLUTION:
.list-item {
  min-height: 44px;
  padding: 12px 16px;
  margin: 4px 0;
}
      `,
      fixComplexity: 'simple'
    },

    {
      id: 'horizontal-scroll-mobile',
      category: 'critical',
      likelihood: 90,
      impact: 85,
      severity: 76.5,
      title: 'Horizontal Scrolling on Mobile',
      description: 'Content overflows viewport width causing horizontal scrolling',
      scenarios: [
        'Long user names or emails without truncation',
        'Tables with too many columns for mobile',
        'Navigation items that wrap incorrectly',
        'Mixed content with fixed-width elements'
      ],
      warningSigns: [
        'Horizontal scrollbar appears',
        'Content gets cut off',
        'Users can\'t see all information',
        'Zooming behavior is inconsistent'
      ],
      prevention: [
        'Use text-overflow: ellipsis with titles',
        'Implement responsive column layouts',
        'Use word-wrap: break-word for text',
        'Test with longest possible content'
      ],
      codeExample: `
❌ PROBLEMATIC:
.long-text { white-space: nowrap; width: 100%; }

✅ SOLUTION:
.long-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
      `,
      fixComplexity: 'simple'
    },

    // MAJOR PROBLEMS
    {
      id: 'large-list-performance',
      category: 'major',
      likelihood: 70,
      impact: 90,
      severity: 63,
      title: 'Performance Degradation with Large Lists',
      description: 'Rendering becomes slow and unresponsive with many list items',
      scenarios: [
        'User directories with 1000+ entries',
        'Product catalogs with thousands of items',
        'Activity feeds with endless scrolling',
        'Data tables with complex filtering'
      ],
      warningSigns: [
        'Initial load time > 3 seconds',
        'Scrolling becomes jerky or freezes',
        'High memory usage in browser',
        'CPU usage spikes during interactions'
      ],
      prevention: [
        'Implement virtual scrolling for 500+ items',
        'Use React.memo for list item components',
        'Lazy load images and off-screen content',
        'Consider pagination for very large datasets'
      ],
      codeExample: `
❌ PROBLEMATIC:
{items.map(item => <ListItem item={item} />)}

✅ SOLUTION:
<VirtualizedList
  items={items}
  itemHeight={80}
  renderItem={({ item, index }) => <ListItem item={item} />}
/>
      `,
      fixComplexity: 'moderate'
    },

    {
      id: 'accessibility-navigation',
      category: 'major',
      likelihood: 80,
      impact: 75,
      severity: 60,
      title: 'Poor Accessibility and Navigation',
      description: 'Lists are not accessible to screen readers or keyboard users',
      scenarios: [
        'Visually impaired users using screen readers',
        'Users who cannot use mouse/touch input',
        'Mobile users with voice control',
        'Automated accessibility testing failures'
      ],
      warningSigns: [
        'No ARIA labels or roles',
        'Keyboard navigation doesn\'t work',
        'Screen readers announce "list with 0 items"',
        'Focus management is broken'
      ],
      prevention: [
        'Use semantic HTML (ul, ol, li)',
        'Add proper ARIA labels and roles',
        'Implement keyboard navigation',
        'Test with actual screen readers'
      ],
      codeExample: `
❌ PROBLEMATIC:
<div className="list">
  <div className="item">Item 1</div>
</div>

✅ SOLUTION:
<ul role="list" aria-label="Menu">
  <li role="listitem" aria-label="Item 1">Item 1</li>
</ul>
      `,
      fixComplexity: 'simple'
    },

    {
      id: 'inconsistent-responsive-behavior',
      category: 'major',
      likelihood: 75,
      impact: 70,
      severity: 52.5,
      title: 'Inconsistent Responsive Behavior',
      description: 'Lists behave differently across viewport sizes causing UX issues',
      scenarios: [
        'Layout breaks at specific breakpoints',
        'Different spacing rules on mobile vs desktop',
        'Content reflows unpredictably',
        'Touch targets shrink on larger screens'
      ],
      warningSigns: [
        'Layout changes suddenly at breakpoints',
        'Spacing is inconsistent between devices',
        'Content overlaps or creates gaps',
        'User confusion across devices'
      ],
      prevention: [
        'Use relative units (rem, em, %)',
        'Test at multiple viewport sizes',
        'Implement smooth transitions between breakpoints',
        'Maintain consistent spacing ratios'
      ],
      codeExample: `
❌ PROBLEMATIC:
.item { padding: 8px; }
@media (min-width: 768px) { .item { padding: 16px; } }

✅ SOLUTION:
.item { padding: 0.75rem 1rem; }
@media (min-width: 768px) { .item { padding: 1rem 1.5rem; } }
      `,
      fixComplexity: 'moderate'
    },

    // MINOR PROBLEMS
    {
      id: 'visual-hierarchy-issues',
      category: 'minor',
      likelihood: 60,
      impact: 50,
      severity: 30,
      title: 'Poor Visual Hierarchy in Lists',
      description: 'Important information doesn\'t stand out in list items',
      scenarios: [
        'Users can\'t quickly scan and find information',
        'Primary and secondary content look similar',
        'Actions are hard to discover',
        'Information overload in complex list items'
      ],
      warningSigns: [
        'All text has same weight and size',
        'Actions are hard to find',
        'Users take longer to complete tasks',
        'Eye-tracking shows scattered attention'
      ],
      prevention: [
        'Use consistent typography scale',
        'Create clear visual hierarchy',
        'Group related information',
        'Make primary actions prominent'
      ],
      codeExample: `
❌ PROBLEMATIC:
<div class="item">
  <span>Name</span>
  <span>Email</span>
  <span>Role</span>
  <button>Edit</button>
</div>

✅ SOLUTION:
<div class="item">
  <h4 class="item-title">Name</h4>
  <p class="item-subtitle">Email</p>
  <span class="item-meta">Role</span>
  <button class="item-action">Edit</button>
</div>
      `,
      fixComplexity: 'simple'
    },

    {
      id: 'interaction-feedback',
      category: 'minor',
      likelihood: 55,
      impact: 45,
      severity: 24.75,
      title: 'Insufficient Interaction Feedback',
      description: 'Users don\'t receive clear feedback when interacting with lists',
      scenarios: [
        'Users unsure if items are clickable',
        'No indication of selected state',
        'Loading states are missing',
        'Error states are unclear'
      ],
      warningSigns: [
        'No hover or focus states',
        'Selected items don\'t stand out',
        'Users click multiple times',
        'Confusion about interaction results'
      ],
      prevention: [
        'Add hover and focus states',
        'Clear selected/active indicators',
        'Loading and error states',
        'Consistent interaction patterns'
      ],
      codeExample: `
❌ PROBLEMATIC:
.item { cursor: pointer; }

✅ SOLUTION:
.item {
  cursor: pointer;
  transition: all 0.2s ease;
}
.item:hover { background-color: #f5f5f5; }
.item:focus { outline: 2px solid #007aff; }
.item.selected { background-color: #e3f2fd; }
      `,
      fixComplexity: 'simple'
    }
  ];

  /**
   * Predict problems based on list configuration
   */
  predictProblems(config: ListConfiguration): ListProblem[] {
    const predictedProblems: ListProblem[] = [];

    this.commonProblems.forEach(problem => {
      const likelihood = this.calculateLikelihood(problem, config);
      if (likelihood > 30) { // Only include likely problems
        predictedProblems.push({
          ...problem,
          likelihood
        });
      }
    });

    return predictedProblems.sort((a, b) => b.severity - a.severity);
  }

  /**
   * Calculate likelihood of a specific problem
   */
  private calculateLikelihood(problem: ListProblem, config: ListConfiguration): number {
    let likelihood = 0;

    switch (problem.id) {
      case 'mobile-touch-failure':
        if (config.targetDevices.includes('mobile')) {
          likelihood += 60;
          if (config.contentTypes.includes('actions')) likelihood += 25;
        }
        break;

      case 'horizontal-scroll-mobile':
        if (config.targetDevices.includes('mobile')) {
          likelihood += 50;
          if (config.dataComplexity === 'complex') likelihood += 30;
          if (config.contentTypes.includes('text')) likelihood += 10;
        }
        break;

      case 'large-list-performance':
        if (config.itemCount > 500) likelihood += 70;
        else if (config.itemCount > 100) likelihood += 40;
        else if (config.itemCount > 50) likelihood += 20;

        if (config.scrollBehavior === 'infinite') likelihood += 20;
        if (config.dataComplexity === 'complex') likelihood += 15;
        break;

      case 'accessibility-navigation':
        // High likelihood for custom implementations
        likelihood += 40;
        if (config.interactionType !== 'display') likelihood += 25;
        if (config.targetDevices.includes('mobile')) likelihood += 15;
        break;

      case 'inconsistent-responsive-behavior':
        if (config.targetDevices.length > 2) likelihood += 30;
        if (config.dataComplexity === 'complex') likelihood += 25;
        if (config.contentTypes.length > 2) likelihood += 20;
        break;

      case 'visual-hierarchy-issues':
        if (config.dataComplexity === 'complex') likelihood += 40;
        if (config.contentTypes.length > 2) likelihood += 20;
        if (config.interactionType !== 'display') likelihood += 15;
        break;

      case 'interaction-feedback':
        if (config.interactionType !== 'display') likelihood += 35;
        if (config.contentTypes.includes('actions')) likelihood += 20;
        break;
    }

    return Math.min(likelihood, 100);
  }

  /**
   * Get risk assessment for a configuration
   */
  getRiskAssessment(config: ListConfiguration): {
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    totalProblems: number;
    criticalProblems: number;
    majorProblems: number;
    recommendations: string[];
  } {
    const problems = this.predictProblems(config);
    const criticalProblems = problems.filter(p => p.category === 'critical').length;
    const majorProblems = problems.filter(p => p.category === 'major').length;

    let riskLevel: 'low' | 'medium' | 'high' | 'critical' = 'low';
    if (criticalProblems >= 2) riskLevel = 'critical';
    else if (criticalProblems >= 1 || majorProblems >= 3) riskLevel = 'high';
    else if (majorProblems >= 1 || problems.length >= 3) riskLevel = 'medium';

    const recommendations = problems
      .slice(0, 5)
      .map(p => `Address: ${p.title} (${p.fixComplexity} complexity)`);

    return {
      riskLevel,
      totalProblems: problems.length,
      criticalProblems,
      majorProblems,
      recommendations
    };
  }

  /**
   * Generate implementation recommendations
   */
  generateImplementationPlan(config: ListConfiguration): {
    phase: string;
    steps: string[];
    estimatedTime: string;
    priority: 'high' | 'medium' | 'low';
  } {
    const problems = this.predictProblems(config);
    const criticalProblems = problems.filter(p => p.category === 'critical');
    const majorProblems = problems.filter(p => p.category === 'major');

    if (criticalProblems.length > 0) {
      return {
        phase: 'Critical Fixes Required',
        steps: [
          'Implement minimum 44px touch targets',
          'Fix horizontal scrolling issues',
          'Add proper semantic HTML and ARIA labels',
          'Test on actual mobile devices'
        ],
        estimatedTime: '2-3 days',
        priority: 'high'
      };
    }

    if (majorProblems.length > 2) {
      return {
        phase: 'Performance Optimization',
        steps: [
          'Implement virtual scrolling for large lists',
          'Add keyboard navigation support',
          'Optimize responsive breakpoints',
          'Add proper interaction feedback'
        ],
        estimatedTime: '1-2 weeks',
        priority: 'high'
      };
    }

    return {
      phase: 'Enhancement & Polish',
      steps: [
        'Improve visual hierarchy',
        'Add loading states',
        'Enhance interaction feedback',
        'Optimize for accessibility'
      ],
      estimatedTime: '3-5 days',
      priority: 'medium'
    };
  }

  /**
   * Test a specific implementation for problems
   */
  validateImplementation(
    config: ListConfiguration,
    implementationCode: string
  ): {
    passed: boolean;
    issues: string[];
    suggestions: string[];
  } {
    const issues: string[] = [];
    const suggestions: string[] = [];

    // Check for common anti-patterns in implementation
    if (!implementationCode.includes('min-height')) {
      issues.push('Missing minimum height for touch targets');
      suggestions.push('Add min-height: 44px to interactive elements');
    }

    if (!implementationCode.includes('aria-')) {
      issues.push('Missing ARIA attributes for accessibility');
      suggestions.push('Add appropriate ARIA labels and roles');
    }

    if (config.itemCount > 100 && !implementationCode.includes('memo')) {
      issues.push('Large list without performance optimization');
      suggestions.push('Consider React.memo or virtualization');
    }

    if (config.targetDevices.includes('mobile') && !implementationCode.includes('rem')) {
      issues.push('Fixed pixel units may not scale well on mobile');
      suggestions.push('Use relative units (rem, em) for better scaling');
    }

    const passed = issues.length === 0;

    return { passed, issues, suggestions };
  }
}

// Export singleton instance
export const listProblemPredictor = new ListRenderingProblemPredictor();
