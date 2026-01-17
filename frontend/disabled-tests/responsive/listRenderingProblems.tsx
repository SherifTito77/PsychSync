/**
 * Responsive List Rendering Problems Analysis
 * Identifies and documents common list rendering issues across viewport sizes
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';

export interface ListRenderingIssue {
  id: string;
  title: string;
  category: 'overflow' | 'spacing' | 'wrapping' | 'navigation' | 'accessibility' | 'performance' | 'visual' | 'interaction';
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  problematicViewports: 'mobile' | 'tablet' | 'desktop' | 'all';
  htmlExample?: string;
  cssExample?: string;
  solution?: string;
  symptoms: string[];
  impact: string;
  prevention: string[];
}

export interface ListRenderingTestCase {
  id: string;
  name: string;
  description: string;
  problemScenario: string;
  currentImplementation: React.ReactNode;
  problematicSizes: number[];
  issues: ListRenderingIssue[];
  responsiveSolution: React.ReactNode;
}

export class ListRenderingAnalyzer {
  private issues: ListRenderingIssue[] = [];
  private testResults: Array<{
    viewport: string;
    width: number;
    issues: string[];
    recommendations: string[];
  }> = [];

  /**
   * Analyze common list rendering problems
   */
  analyzeListRenderingProblems(): ListRenderingIssue[] {
    this.issues = this.identifyCommonIssues();
    return this.issues;
  }

  /**
   * Identify common list rendering issues
   */
  private identifyCommonIssues(): ListRenderingIssue[] {
    return [
      // Text Overflow Issues
      {
        id: 'list-overflow-001',
        title: 'Text Truncation Without Indication',
        category: 'overflow',
        severity: 'high',
        description: 'List items are truncated without visual indication that content is cut off',
        problematicViewports: 'mobile',
        htmlExample: `
          <ul>
            <li>Very long list item that gets cut off without...</li>
            <li>Another item with insufficient space</li>
          </ul>
        `,
        cssExample: `
          .list-item {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        `,
        solution: 'Add text-overflow: ellipsis or allow text wrapping with proper spacing',
        symptoms: ['Content appears cut off', 'Users can\'t read full text', 'Inconsistent ellipsis behavior'],
        impact: 'Users miss important information in lists',
        prevention: [
          'Use text-overflow: ellipsis with proper container constraints',
          'Allow text wrapping where appropriate',
          'Implement tooltip on hover for full text'
        ]
      },
      {
        id: 'list-overflow-002',
        title: 'Horizontal Scrolling in Vertical Lists',
        category: 'overflow',
        severity: 'high',
        description: 'Lists scroll horizontally instead of wrapping content',
        problematicViewports: 'mobile',
        htmlExample: `
          <ul style="overflow-x: auto; white-space: nowrap;">
            <li>Very long item that causes horizontal scrolling</li>
            <li>Another long item that exacerbates the issue</li>
          </ul>
        `,
        solution: 'Allow natural text wrapping and proper list item sizing',
        symptoms: ['Horizontal scrollbar appears', 'Users can\'t read content without scrolling', 'Poor mobile experience'],
        impact: 'Poor readability and user frustration on mobile devices',
        prevention: [
          'Avoid overflow-x: auto on lists',
          'Use flexible list item widths',
          'Implement proper responsive sizing'
        ]
      },

      // Spacing Issues
      {
        id: 'list-spacing-001',
        title: 'Inconsistent List Item Spacing',
        category: 'spacing',
        severity: 'medium',
        description: 'Irregular spacing between list items across viewport sizes',
        problematicViewports: 'all',
        htmlExample: `
          <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
            <li>Item 4</li>
          </ul>
        `,
        cssExample: `
          .list-item {
            margin-bottom: 8px; /* Fixed spacing */
          }
          @media (min-width: 768px) {
            .list-item {
              margin-bottom: 12px; /* Different spacing on tablet */
            }
          }
        `,
        solution: 'Use consistent, responsive spacing with relative units',
        symptoms: ['Inconsistent gaps between items', 'Poor visual hierarchy', 'Cluttered appearance'],
        impact: 'List appears unprofessional and hard to scan',
        prevention: [
          'Use relative units for spacing (rem, em)',
          'Implement consistent margin/bottom patterns',
          'Test spacing across all viewport sizes'
        ]
      },
      {
        id: 'list-spacing-002',
        title: 'Insufficient Tap Targets on Mobile',
        category: 'spacing',
        severity: 'high',
        description: 'List items too small for touch interaction on mobile devices',
        problematicViewports: 'mobile',
        htmlExample: `
          <ul>
            <li style="padding: 8px; line-height: 1;">Small touch target</li>
            <li style="padding: 8px; line-height: 1;">Another small target</li>
          </ul>
        `,
        solution: 'Increase tap target size to 44px minimum for mobile',
        symptoms: ['Difficult to tap items accurately', 'Accidental taps on wrong items', 'Poor mobile UX'],
        impact: 'Users struggle with basic list interactions',
        prevention: [
          'Use minimum 44px height for touch targets',
          'Increase padding and margins for mobile',
          'Consider larger hit areas than visible bounds'
        ]
      },

      // Wrapping Issues
      {
        id: 'list-wrapping-001',
        title: 'Inconsistent Text Wrapping',
        category: 'wrapping',
        severity: 'medium',
        description: 'Text wraps unpredictably or breaks in awkward places',
        problematicViewports: 'all',
        htmlExample: `
          <ul style="width: 300px; word-break: break-all;">
            <li>Supercalifragilisticexpialidocious text</li>
            <li>AnotherExampleWithAwkwardWrapping</li>
          </ul>
        `,
        solution: 'Use appropriate word-breaking and hyphenation strategies',
        symptoms: ['Text breaks in awkward places', 'Unpredictable line breaks', 'Poor readability'],
        impact: 'Content becomes difficult to read and understand',
        prevention: [
          'Use word-wrap: break-word instead of break-all',
          'Implement proper hyphenation where appropriate',
          'Consider line-height for readability'
        ]
      },
      {
        id: 'list-wrapping-002',
        title: 'Multiline Content Breaking List Structure',
        category: 'wrapping',
        severity: 'medium',
        description: 'Multiline list items break visual list hierarchy',
        problematicViewports: 'all',
        htmlExample: `
          <ul>
            <li>Single line item</li>
            <li>Very long multiline
                content that breaks
                the visual list
                structure and makes
                it hard to scan
            </li>
            <li>Another single line</li>
          </ul>
        `,
        solution: 'Handle multiline content with proper styling and spacing',
        symptoms: ['List items have different heights', 'Visual hierarchy disrupted', 'Scanning difficulty'],
        impact: 'List becomes harder to read and understand',
        prevention: [
          'Consistent padding for multiline items',
          'Proper line-height for readability',
          'Test with various content lengths'
        ]
      },

      // Navigation Issues
      {
        id: 'list-navigation-001',
        title: 'Poor List Navigation on Mobile',
        category: 'navigation',
        severity: 'high',
        description: 'Long lists are difficult to navigate on mobile devices',
        problematicViewports: 'mobile',
        htmlExample: `
          <ul>
            ${Array.from({length: 50}, (_, i) =>
              `<li>List Item ${i + 1} with moderately long text</li>`
            ).join('')}
          </ul>
        `,
        solution: 'Implement pagination, sticky headers, or virtual scrolling',
        symptoms: ['Infinite scrolling required', 'No way to jump to specific items', 'Poor context awareness'],
        impact: 'Users cannot efficiently navigate long lists',
        prevention: [
          'Implement virtual scrolling for large lists',
          'Add alphabetical or category filtering',
          'Provide search functionality',
          'Use pagination with clear navigation'
        ]
      },
      {
        id: 'list-navigation-002',
        title: 'Missing Skip Links for Long Lists',
        category: 'navigation',
        severity: 'medium',
        description: 'No way to skip to specific list sections or items',
        problematicViewports: 'all',
        htmlExample: `
          <ul>
            <li id="section-a">Section A items...</li>
            <li id="section-b">Section B items...</li>
            <li id="section-c">Section C items...</li>
          </ul>
        `,
        solution: 'Add internal navigation with skip links',
        symptoms: ['Cannot jump to specific sections', 'Poor keyboard navigation', 'Accessibility issues'],
        impact: 'Reduced usability for long or categorized lists',
        prevention: [
          'Add sticky navigation for long lists',
          'Implement jump links with proper ARIA labeling',
          'Provide index or alphabetical sorting',
          'Test keyboard navigation thoroughly'
        ]
      },

      // Accessibility Issues
      {
        id: 'list-accessibility-001',
        title: 'Missing Semantic List Markup',
        category: 'accessibility',
        severity: 'high',
        description: 'Using div elements instead of proper list semantic HTML',
        problematicViewports: 'all',
        htmlExample: `
          <div class="list">
            <div class="list-item">Item 1</div>
            <div class="list-item">Item 2</div>
            <div class="list-item">Item 3</div>
          </div>
        `,
        cssExample: `
          .list {
            list-style: none;
            padding: 0;
          }
        `,
        solution: 'Use proper semantic list elements (ul, ol, li)',
        symptoms: ['Screen readers don\'t recognize as list', 'Keyboard navigation issues', 'SEO impact'],
        impact: 'Significant accessibility and usability problems',
        prevention: [
          'Always use ul/ol/li for lists',
          'Maintain proper list hierarchy',
          'Add appropriate ARIA labels',
          'Test with screen readers'
        ]
      },
      {
        id: 'list-accessibility-002',
        title: 'Poor List Marker Accessibility',
        category: 'accessibility',
        severity: 'medium',
        description: 'List bullets or numbers are not accessible to screen readers',
        problematicViewports: 'all',
        htmlExample: `
          <ul style="list-style: none;">
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
          </ul>
        `,
        solution: 'Ensure list markers are visible and accessible',
        symptoms: ['Screen readers can\'t count list items', 'Visual list markers missing', 'Context loss'],
        impact: 'Reduced accessibility for screen reader users',
        prevention: [
          'Keep default list styles or use accessible alternatives',
          'Add CSS counter for custom markers if needed',
          'Test with actual screen reading software',
          'Maintain list structure in DOM'
        ]
      },

      // Performance Issues
      {
        id: 'list-performance-001',
        title: 'Inefficient DOM Updates for Large Lists',
        category: 'performance',
        severity: 'medium',
        description: 'Re-rendering entire list for small changes causes performance issues',
        problematicViewports: 'all',
        htmlExample: `
          <ul id="list-container">
            ${Array.from({length: 1000}, (_, i) =>
              `<li id="item-${i}">Item ${i}</li>`
            ).join('')}
          </ul>
        `,
        solution: 'Implement virtual scrolling or optimized rendering',
        symptoms: ['Slow rendering for large lists', 'High CPU usage', 'Jank on scroll'],
        impact: 'Poor performance and user experience degradation',
        prevention: [
          'Use virtual scrolling for very large lists',
          'Implement efficient update patterns',
          'Use React.memo for list items',
          'Consider windowing techniques'
        ]
      },
      {
        id: 'list-performance-002',
        title: 'Excessive DOM Nodes in Lists',
        category: 'performance',
        severity: 'medium',
        description: 'Lists contain too many DOM elements causing performance issues',
        problematicViewports: 'all',
        htmlExample: `
          <ul>
            ${Array.from({length: 500}, (_, i) =>
              `<li>
                <div class="item-content">
                  <h3>Title ${i}</h3>
                  <p>Description ${i} with nested content</p>
                  <button>Action ${i}</button>
                  <span>Metadata ${i}</span>
                </div>
              </li>`
            ).join('')}
          </ul>
        `,
        solution: 'Simplify list item structure and use lazy loading',
        symptoms: ['Slow initial render', 'High memory usage', 'Poor scrolling performance'],
        impact: 'Page load times and interactivity suffer',
        prevention: [
          'Minimize DOM complexity in list items',
          'Use lazy loading for off-screen content',
          'Implement progressive loading strategies',
          'Consider virtualization for very large lists'
        ]
      },

      // Visual Issues
      {
        id: 'list-visual-001',
        title: 'Inconsistent List Styling',
        category: 'visual',
        severity: 'medium',
        description: 'List styling varies across viewport sizes causing visual inconsistency',
        problematicViewports: 'all',
        htmlExample: `
          <ul>
            <li style="padding: 8px;">Mobile Item</li>
            <li style="padding: 16px;">Tablet Item</li>
            <li style="padding: 24px;">Desktop Item</li>
          </ul>
        `,
        cssExample: `
          @media (max-width: 768px) {
            li { padding: 8px; }
          }
          @media (min-width: 769px) and (max-width: 1024px) {
            li { padding: 16px; }
          }
          @media (min-width: 1025px) {
            li { padding: 24px; }
          }
        `,
        solution: 'Create consistent responsive styling patterns',
        symptoms: ['Different spacing across devices', 'Inconsistent visual hierarchy', 'Poor design cohesion'],
        impact: 'Design appears unprofessional and inconsistent',
        prevention: [
          'Establish design system for list components',
          'Use relative units for responsive scaling',
          'Create consistent visual hierarchy',
          'Test across all viewport sizes'
        ]
      },

      // Interaction Issues
      {
        id: 'list-interaction-001',
        title: 'Poor Hover and Active States',
        category: 'interaction',
        severity: 'medium',
        description: 'List items lack clear hover or active states for user feedback',
        problematicViewports: 'all',
        htmlExample: `
          <ul>
            <li>Interactive Item 1</li>
            <li>Interactive Item 2</li>
            <li>Interactive Item 3</li>
          </ul>
        `,
        cssExample: `
          li:hover {
            background-color: #f0f0f0;
          }
          li:active {
            background-color: #e0e0e0;
          }
        `,
        solution: 'Implement clear interactive states with proper visual feedback',
        symptoms: ['No hover indication', 'Unclear interaction points', 'Poor user feedback'],
        impact: 'Users can easily miss interactive elements or feel uncertain about interactions',
        prevention: [
          'Add clear hover states with appropriate contrast',
          'Implement active/focus states for feedback',
          'Use consistent color schemes',
          'Test with various input methods'
        ]
      },
      {
        id: 'list-interaction-002',
        title: 'Drag and Drop Issues in Sortable Lists',
        category: 'interaction',
        severity: 'low',
        description: 'Sortable lists have poor drag and drop UX on mobile devices',
        problematicViewports: 'mobile',
        htmlExample: `
          <ul id="sortable-list">
            <li draggable="true">Item 1</li>
            <li draggable="true">Item 2</li>
            <li draggable="true">Item 3</li>
          </ul>
        `,
        solution: 'Implement touch-friendly drag and drop patterns',
        symptoms: ['Difficult to drag on mobile', 'Visual feedback unclear', 'Touch targets too small'],
        impact: 'Poor mobile user experience for sortable interfaces',
        prevention: [
          'Use touch-friendly drag handles',
          'Implement visual drag feedback',
          'Test with actual mobile devices',
          'Consider alternative sorting methods for mobile'
        ]
      }
    ];
  }

  /**
   * Generate test cases for problematic list rendering scenarios
   */
  generateTestCases(): ListRenderingTestCase[] {
    return [
      {
        id: 'responsive-list-001',
        name: 'Text Overflow in Mobile Lists',
        description: 'Lists with long text content that overflows on mobile devices',
        problemScenario: 'Mobile viewport (320px) with list items containing long text content',
        currentImplementation: (
          <ul style={{ width: '300px' }}>
            <li style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              padding: '8px'
            }}>
              Very long list item that gets truncated without proper ellipsis handling
            </li>
            <li style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              padding: '8px'
            }}>
              Another item with insufficient space for proper display
            </li>
          </ul>
        ),
        problematicSizes: [320, 375],
        issues: this.issues.filter(i => i.id.startsWith('list-overflow')),
        responsiveSolution: (
          <ul style={{ width: '100%', maxWidth: '300px' }}>
            <li style={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              padding: '12px',
              position: 'relative'
            }}>
              Very long list item with proper ellipsis and tooltip
              <span style={{
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                backgroundColor: '#007aff',
                color: 'white',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '12px'
              }}>
                ...
              </span>
            </li>
            <li style={{
              padding: '12px',
              whiteSpace: 'normal',
              wordWrap: 'break-word'
            }}>
              Another item with proper text wrapping for mobile devices
            </li>
          </ul>
        )
      },

      {
        id: 'responsive-list-002',
        name: 'Navigation Issues in Long Lists',
        description: 'Long lists that are difficult to navigate on mobile devices',
        problemScenario: 'Mobile list with 50+ items requiring scrolling',
        currentImplementation: (
          <div>
            <h3>Long List Example</h3>
            <ul style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {Array.from({ length: 50 }, (_, i) => (
                <li key={i} style={{
                  padding: '8px',
                  borderBottom: '1px solid #eee'
                }}>
                  List Item {i + 1} - This is a moderately long list item that takes up space
                </li>
              ))}
            </ul>
          </div>
        ),
        problematicSizes: [320, 375, 768],
        issues: this.issues.filter(i => i.id.startsWith('list-navigation')),
        responsiveSolution: (
          <div>
            <div style={{
              position: 'sticky',
              top: 0,
              backgroundColor: 'white',
              zIndex: 10,
              padding: '12px',
              borderBottom: '2px solid #007aff',
              textAlign: 'center',
              fontWeight: 'bold'
            }}>
              Quick Navigation
            </div>
            <ul style={{ maxHeight: '60vh', overflowY: 'auto', paddingTop: '16px' }}>
              {Array.from({ length: 10 }, (_, i) => (
                <li key={i} style={{
                  padding: '12px',
                  borderBottom: '1px solid #eee',
                  scrollMarginTop: 0
                }}>
                  <a href={`#item-${i}`} style={{
                    color: '#007aff',
                    textDecoration: 'none',
                    fontWeight: '500',
                    display: 'block'
                  }}>
                    Item {i + 1} - Concise list item for mobile
                  </a>
                </li>
              ))}
            </ul>
            <div style={{
              textAlign: 'center',
              padding: '16px',
              backgroundColor: '#f8f9fa',
              borderTop: '1px solid #dee2e6'
            }}>
              <small>Showing 10 of 50 items</small>
            </div>
          </div>
        )
      },

      {
        id: 'responsive-list-003',
        name: 'Complex List Component with Mixed Content',
        description: 'Lists containing mixed content types (text, images, actions)',
        problemScenario: 'Mobile/tablet layout with complex list items',
        currentImplementation: (
          <ul style={{ width: '100%', padding: '0' }}>
            <li style={{
              padding: '8px',
              borderBottom: '1px solid #eee',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <div style={{
                width: '40px',
                height: '40px',
                backgroundColor: '#007aff',
                borderRadius: '4px'
              }}></div>
              <div style={{ flex: 1, minWidth: '0' }}>
                <strong>Avatar List Item</strong>
                <p style={{
                  margin: '4px 0 0',
                  fontSize: '14px',
                  color: '#666'
                }}>
                  This item contains an avatar, title, and description that may cause layout issues
                </p>
              </div>
            </li>
            <li style={{
              padding: '8px',
              borderBottom: '1px solid #eee',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px'
            }}>
              <button style={{
                width: '32px',
                height: '32px',
                backgroundColor: '#28a745',
                borderRadius: '4px',
                color: 'white',
                border: 'none',
                cursor: 'pointer'
              }}>
                  +
                </button>
              <div style={{ flex: 1, minWidth: '0' }}>
                <strong>Action List Item</strong>
                <p style={{
                  margin: '4px 0 0',
                  fontSize: '14px',
                  color: '#666'
                }}>
                  This item has an action button and may have complex interactive behavior
                </p>
              </div>
            </li>
          </ul>
        ),
        problematicSizes: [320, 375, 768],
        issues: this.issues.filter(i =>
          i.id.startsWith('list-spacing') ||
          i.id.startsWith('list-interaction')
        ),
        responsiveSolution: (
          <ul style={{
            width: '100%',
            padding: '0',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}>
            <li style={{
              padding: '12px 16px',
              borderBottom: '1px solid #eee',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                backgroundColor: '#007aff',
                borderRadius: '6px',
                flexShrink: 0
              }}></div>
              <div style={{ flex: 1, minWidth: '0' }}>
                <h4 style={{ margin: '0 0 4px 0' }}>Responsive Avatar Item</h4>
                <p style={{
                  margin: 0,
                  fontSize: '14px',
                  lineHeight: '1.4',
                  color: '#666'
                }}>
                  Properly spaced avatar with title and description
                </p>
              </div>
              <button style={{
                width: '40px',
                height: '40px',
                backgroundColor: '#28a745',
                borderRadius: '6px',
                color: 'white',
                border: 'none',
                cursor: 'pointer',
                flexShrink: 0
              }}>
                +
              </button>
            </li>
            <li style={{
              padding: '12px 16px',
              borderBottom: '1px solid #eee',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px'
            }}>
              <button style={{
                width: '40px',
                height: '40px',
                backgroundColor: '#dc3545',
                borderRadius: '6px',
                color: 'white',
                border: 'none',
                cursor: 'pointer',
                flexShrink: 0
              }}>
                  ×
                </button>
              <div style={{ flex: 1, minWidth: '0' }}>
                <h4 style={{ margin: '0 0 4px 0' }}>Interactive Item with Action</h4>
                <p style={{
                  margin: 0,
                  fontSize: '14px',
                  lineHeight: '1.4',
                  color: '#666'
                }}>
                  Action button with proper spacing and responsive behavior
                </p>
              </div>
            </li>
          </ul>
        )
      },

      {
        id: 'responsive-list-004',
        name: 'Nested List Structure Problems',
        description: 'Multi-level lists with complex nesting causing readability issues',
        problemScenario: 'Nested navigation or category lists on mobile',
        currentImplementation: (
          <ul style={{ width: '100%', padding: '0' }}>
            <li style={{ padding: '8px' }}>
              <strong>Category 1</strong>
              <ul style={{ marginLeft: '20px', padding: '4px 0' }}>
                <li>Nested item 1.1</li>
                <li>Nested item 1.2</li>
                <li>Nested item 1.3</li>
              </ul>
            </li>
            <li style={{ padding: '8px' }}>
              <strong>Category 2</strong>
              <ul style={{ marginLeft: '20px', padding: '4px 0' }}>
                <li>Nested item 2.1</li>
                <li>Nested item 2.2</li>
                <li>Nested item 2.3</li>
                <li>Nested item 2.4 with very long content that wraps</li>
              </ul>
            </li>
          </ul>
        ),
        problematicSizes: [320, 375],
        issues: this.issues.filter(i => i.id.startsWith('list-wrapping') || i.id.startsWith('list-spacing')),
        responsiveSolution: (
          <ul style={{
            width: '100%',
            padding: '0',
            counterReset: 'list-counter'
          }}>
            <li style={{
              padding: '12px 16px',
              counterIncrement: 'list-item',
              marginBottom: '8px',
              borderBottom: '1px solid #eee'
            }}>
              <div style={{
                fontWeight: 'bold',
                marginBottom: '4px'
              }}>
                <span style={{ color: '#007aff' }}>
                  {String.fromCharCode(0x2022)} {/* Bullet */}
                </span>
                Category 1
              </div>
              <ul style={{ marginLeft: '16px', paddingLeft: '0' }}>
                <li style={{
                  padding: '4px 0',
                  borderBottom: '1px solid #f0f0f0',
                  lineHeight: '1.5'
                }}>
                  <span style={{ color: '#666' }}>•</span> Nested item 1.1
                </li>
                <li style={{
                  padding: '4px 0',
                  borderBottom: '1px solid #f0f0f0',
                  lineHeight: '1.5'
                }}>
                  <span style={{ color: '#666' }}>•</span> Nested item 1.2
                </li>
                <li style={{
                  padding: '4px 0',
                  lineHeight: '1.5',
                  wordWrap: 'break-word'
                }}>
                  <span style={{ color: '#666' }}>•</span> Nested item 1.3 with
                  proper wrapping behavior for mobile viewing
                </li>
              </ul>
            </li>
            <li style={{
              padding: '12px 16px',
              counterIncrement: 'list-item',
              marginBottom: '8px',
              borderBottom: '1px solid #eee'
            }}>
              <div style={{
                fontWeight: 'bold',
                marginBottom: '4px'
              }}>
                <span style={{ color: '#007aff' }}>
                  {String.fromCharCode(0x2022)}
                </span>
                Category 2
              </div>
              <ul style={{ marginLeft: '16px', paddingLeft: '0' }}>
                <li style={{
                  padding: '4px 0',
                  borderBottom: '1px solid #f0f0f0',
                  lineHeight: '1.5'
                }}>
                  <span style={{ color: '#666' }}>•</span> Nested item 2.1
                </li>
                <li style={{
                  padding: '4px 0',
                  borderBottom: '1px solid #f0f0f0',
                  lineHeight: '1.5',
                  wordWrap: 'break-word'
                }}>
                  <span style={{ color: '#666' }}>•</span> Nested item 2.2 with
                  very long descriptive text that properly wraps and maintains readability
                  across different screen sizes
                </li>
              </ul>
            </li>
          </ul>
        )
      },

      {
        id: 'responsive-list-005',
        name: 'Horizontal List with Responsive Behavior',
        description: 'Horizontal scrolling lists that need to adapt to viewport',
        problemScenario: 'Horizontal lists that don't stack properly on mobile',
        currentImplementation: (
          <div style={{
            width: '100%',
            overflowX: 'auto',
            whiteSpace: 'nowrap'
          }}>
            <ul style={{
              display: 'inline-block',
              margin: '0',
              padding: '0'
            }}>
              <li style={{
                display: 'inline-block',
                padding: '8px 12px',
                marginRight: '4px',
                backgroundColor: '#007aff',
                color: 'white'
              }}>
                Tag 1
              </li>
              <li style={{
                display: 'inline-block',
                padding: '8px 12px',
                marginRight: '4px',
                backgroundColor: '#6c757d',
                color: 'white'
              }}>
                Tag 2
              </li>
              <li style={{
                display: 'inline-block',
                padding: '8px 12px',
                marginRight: '4px',
                backgroundColor: '#28a745',
                color: 'white'
              }}>
                Tag 3
              </li>
            </ul>
          </div>
        ),
        problematicSizes: [320, 375],
        issues: this.issues.filter(i => i.id.startsWith('list-overflow')),
        responsiveSolution: (
          <div style={{ width: '100%' }}>
            <div style={{
              marginBottom: '16px',
              padding: '12px',
              backgroundColor: '#f8f9fa',
              borderRadius: '6px'
            }}>
              <strong>Filter Tags:</strong>
              <input
                type="text"
                placeholder="Search tags..."
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  marginTop: '8px'
                }}
              />
            </div>
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
              padding: '0'
            }}>
              <span style={{
                padding: '8px 12px',
                backgroundColor: '#007aff',
                color: 'white',
                borderRadius: '20px',
                fontSize: '14px'
              }}>
                Tag 1
              </span>
              <span style={{
                padding: '8px 12px',
                backgroundColor: '#6c757d',
                color: 'white',
                borderRadius: '20px',
                fontSize: '14px'
              }}>
                Tag 2
              </span>
              <span style={{
                padding: '8px 12px',
                backgroundColor: '#28a745',
                color: 'white',
                borderRadius: '20px',
                fontSize: '14px'
              }}>
                Tag 3
              </span>
              <span style={{
                padding: '8px 12px',
                backgroundColor: '#dc3545',
                color: 'white',
                borderRadius: '20px',
                fontSize: '14px'
              }}>
                Tag 4
              </span>
              <span style={{
                padding: '8px 12px',
                backgroundColor: '#ffc107',
                color: '#212529',
                borderRadius: '20px',
                fontSize: '14px'
              }}>
                Tag 5
              </span>
            </div>
          </div>
        )
      }
    ];
  }

  /**
   * Analyze viewport-specific list rendering problems
   */
  analyzeViewportProblems(): typeof TestResults['testResults'] {
    const viewports = [
      { name: 'mobile', width: 375 },
      { name: 'tablet', width: 768 },
      { name: 'desktop', width: 1024 }
    ];

    viewports.forEach(viewport => {
      const issues: string[] = [];
      const recommendations: string[] = [];

      // Test common list scenarios at this viewport
      this.testBasicListRendering(viewport.width, issues, recommendations);
      this.testListNavigation(viewport.width, issues, recommendations);
      this.testListAccessibility(viewport.width, issues, recommendations);
      this.testListPerformance(viewport.width, issues, recommendations);

      this.testResults.push({
        viewport: viewport.name,
        width: viewport.width,
        issues,
        recommendations
      });
    });

    return this.testResults;
  }

  /**
   * Test basic list rendering at different viewport sizes
   */
  private testBasicListRendering(width: number, issues: string[], recommendations: string[]): void {
    // Create test container
    const container = document.createElement('div');
    container.style.width = `${width}px`;
    container.style.fontFamily = 'system-ui';
    container.style.fontSize = '16px';

    // Test basic ul list
    const ul = document.createElement('ul');
    ul.style.listStyle = 'none';
    ul.style.padding = '0';
    ul.style.margin = '0';

    // Add test list items
    for (let i = 0; i < 10; i++) {
      const li = document.createElement('li');
      li.textContent = `Test List Item ${i + 1} with some content to check wrapping behavior`;
      li.style.padding = '8px';
      li.style.marginBottom = '4px';
      li.style.borderBottom = '1px solid #eee';
      ul.appendChild(li);
    }

    container.appendChild(ul);
    document.body.appendChild(container);

    try {
      const computedStyle = window.getComputedStyle(ul);
      const firstItem = ul.querySelector('li');

      // Test for overflow issues
      if (container.scrollWidth > width) {
        issues.push('List container exceeds viewport width');
        recommendations.push('Implement horizontal scrolling or text wrapping');
      }

      // Check text wrapping
      if (firstItem) {
        const itemStyle = window.getComputedStyle(firstItem);
        const itemWidth = parseFloat(itemStyle.width);

        if (itemWidth > width * 0.9) {
          issues.push('List item too wide for viewport');
          recommendations.push('Implement responsive text sizing or wrapping');
        }

        const textHeight = parseFloat(itemStyle.lineHeight);
        if (textHeight < 1.2) {
          issues.push('Insufficient line height for readability');
          recommendations.push('Increase line-height to at least 1.4');
        }
      }

      // Check spacing consistency
      const items = ul.querySelectorAll('li');
      const itemSpacing = [];
      for (let i = 0; i < items.length - 1; i++) {
        const item1 = window.getComputedStyle(items[i]);
        const item2 = window.getComputedStyle(items[i + 1]);
        itemSpacing.push(
          parseFloat(item2.marginBottom) - parseFloat(item1.marginBottom)
        );
      }

      const spacingVariance = Math.max(...itemSpacing) - Math.min(...itemSpacing);
      if (spacingVariance > 2) {
        issues.push('Inconsistent list item spacing');
        recommendations.push('Use consistent spacing patterns with relative units');
      }

    } finally {
      document.body.removeChild(container);
    }
  }

  /**
   * Test list navigation functionality
   */
  private testListNavigation(width: number, issues: string[], recommendations: string[]): void {
    // Test keyboard navigation
    const container = document.createElement('div');
    container.style.width = `${width}px`;

    const ul = document.createElement('ul');
    ul.style.listStyle = 'none';
    ul.style.padding = '0';
    ul.style.margin = '0';

    // Create focusable list items
    for (let i = 0; i < 5; i++) {
      const li = document.createElement('li');
      const button = document.createElement('button');
      button.textContent = `List Item ${i + 1}`;
      button.style.width = '100%';
      button.style.padding = '8px';
      button.style.border = '1px solid #ccc';
      button.style.backgroundColor = 'white';
      button.style.cursor = 'pointer';
      li.appendChild(button);
      ul.appendChild(li);
    }

    container.appendChild(ul);
    document.body.appendChild(container);

    try {
      // Test focus navigation
      const buttons = container.querySelectorAll('button');

      buttons.forEach((button, index) => {
        button.focus();
        if (document.activeElement !== button) {
          issues.push(`List item ${index + 1} cannot receive focus`);
          recommendations.push('Ensure all interactive list items are focusable');
        }

        // Test tap target size (minimum 44px for mobile)
        const buttonRect = button.getBoundingClientRect();
        if (buttonRect.height < 44) {
          issues.push(`List item ${index + 1} tap target too small: ${buttonRect.height}px`);
          recommendations.push('Increase tap target size to minimum 44px height');
        }
      });

    } finally {
      document.body.removeChild(container);
    }
  }

  /**
   * Test list accessibility
   */
  private testListAccessibility(width: number, issues: string[], recommendations: string[]): void {
    const container = document.createElement('div');
    container.style.width = `${width}px`;

    const ul = document.createElement('ul');
    ul.setAttribute('role', 'list');
    ul.setAttribute('aria-label', 'Test list');

    // Create accessible list items
    for (let i = 0; i < 5; i++) {
      const li = document.createElement('li');
      li.setAttribute('role', 'listitem');
      li.setAttribute('aria-label', `List Item ${i + 1}`);
      li.textContent = `Accessible List Item ${i + 1}`;
      li.style.padding = '8px';
      li.style.marginBottom = '4px';
      ul.appendChild(li);
    }

    container.appendChild(ul);
    document.body.appendChild(container);

    try {
      // Check semantic structure
      if (ul.getAttribute('role') !== 'list') {
        issues.push('List lacks proper semantic role');
        recommendations.push('Use semantic ul element with role="list"');
      }

      // Check ARIA labels
      const items = container.querySelectorAll('[aria-label]');
      items.forEach((item, index) => {
        if (!item.getAttribute('aria-label') && item.textContent.trim().length === 0) {
          issues.push(`List item ${index + 1} missing ARIA label`);
          recommendations.push('Add aria-label to list items without text content');
        }
      });

      // Test screen reader compatibility
      const listStyle = window.getComputedStyle(ul);
      if (listStyle.listStyle === 'none' && !ul.hasAttribute('role')) {
        issues.push('List without visible markers for screen readers');
        recommendations.push('Add role="list" or restore visible list styles');
      }

    } finally {
      document.body.removeChild(container);
    }
  }

  /**
   * Test list performance
   */
  private testListPerformance(width: number, issues: string[], recommendations: string[]): void {
    const startTime = performance.now();

    const container = document.createElement('div');
    container.style.width = `${width}px`;

    const ul = document.createElement('ul');
    ul.style.listStyle = 'none';
    ul.style.padding = '0';
    ul.style.margin = '0';

    // Create large list for performance testing
    for (let i = 0; i < 100; i++) {
      const li = document.createElement('li');
      li.innerHTML = `
        <div class="list-content">
          <h4>Performance Test Item ${i + 1}</h4>
          <p>This is a list item with complex content that may impact rendering performance in large lists.</p>
          <button>Action Button ${i + 1}</button>
        </div>
      `;
      li.style.padding = '12px';
      li.style.marginBottom = '4px';
      ul.appendChild(li);
    }

    container.appendChild(ul);
    document.body.appendChild(container);

    try {
      const renderTime = performance.now() - startTime;

      // Test rendering performance
      if (renderTime > 100) {
        issues.push(`Slow list rendering: ${renderTime.toFixed(2)}ms`);
        recommendations.push('Consider virtual scrolling for large lists');
      }

      // Test scroll performance
      const scrollStartTime = performance.now();
      container.scrollTop = 100;
      const scrollTime = performance.now() - scrollStartTime;

      if (scrollTime > 50) {
        issues.push(`Slow list scrolling: ${scrollTime.toFixed(2)}ms`);
        recommendations.push('Optimize list scrolling performance');
      }

    } finally {
      document.body.removeChild(container);
    }
  }
}

export const listRenderingAnalyzer = new ListRenderingAnalyzer();
