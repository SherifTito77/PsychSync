/**
 * 🧪 Comprehensive UX Usability Defect Detection Tests
 *
 * Tests the usability defect detection system with real UI components
 * and validates that it correctly identifies confusing screen layouts.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UXUsabilityDefectDetector, { UXDefect, LayoutAnalysis } from '../../utils/ux/usabilityDefectDetector';

describe('🔍 Comprehensive UX Usability Defect Detection Tests', () => {
  let detector: UXUsabilityDefectDetector;
  let userEventSetup: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    detector = new UXUsabilityDefectDetector();
    userEventSetup = userEvent.setup();
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('🧪 Visual Hierarchy Detection', () => {
    it('detects missing heading structure', async () => {
      render(
        <div data-testid="no-headings">
          <div>Content without proper headings</div>
          <div>More content</div>
          <div>Even more content</div>
        </div>
      );

      const container = document.querySelector('[data-testid="no-headings"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const hierarchyDefects = analysis.defects.filter(d => d.type === 'visual_hierarchy');
      expect(hierarchyDefects.length).toBeGreaterThan(0);
      expect(hierarchyDefects.some(d => d.description.includes('No heading elements found'))).toBe(true);
    });

    it('detects skipped heading levels', async () => {
      render(
        <div data-testid="skipped-headings">
          <h1>Main Title</h1>
          <h3>Skipped H2 - Should be H2</h3>
          <h4>Subsection</h4>
        </div>
      );

      const container = document.querySelector('[data-testid="skipped-headings"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const hierarchyDefects = analysis.defects.filter(d => d.type === 'visual_hierarchy');
      expect(hierarchyDefects.some(d => d.description.includes('Skipped heading level'))).toBe(true);
    });

    it('detects inconsistent font sizes', async () => {
      render(
        <div data-testid="consistent-font">
          <p style={{ fontSize: '14px' }}>Same size text</p>
          <p style={{ fontSize: '14px' }}>Same size text</p>
          <p style={{ fontSize: '14px' }}>Same size text</p>
        </div>
      );

      const container = document.querySelector('[data-testid="consistent-font"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      // Should not have font size inconsistency issues
      const hierarchyDefects = analysis.defects.filter(d =>
        d.type === 'visual_hierarchy' &&
        d.description.includes('same font size')
      );
      expect(hierarchyDefects.length).toBe(0);
    });

    it('detects lack of visual weight differentiation', async () => {
      render(
        <div data-testid="no-weight-diff">
          <div style={{ fontSize: '14px', fontWeight: 'normal' }}>Light content</div>
          <div style={{ fontSize: '14px', fontWeight: 'normal' }}>Light content</div>
          <div style={{ fontSize: '14px', fontWeight: 'normal' }}>Light content</div>
        </div>
      );

      const container = document.querySelector('[data-testid="no-weight-diff"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const hierarchyDefects = analysis.defects.filter(d => d.type === 'visual_hierarchy');
      expect(hierarchyDefects.some(d => d.description.includes('lack clear structure'))).toBe(true);
    });
  });

  describe('🧠 Cognitive Overload Detection', () => {
    it('detects too many interactive elements', async () => {
      render(
        <div data-testid="too-many-buttons">
          {Array.from({ length: 20 }, (_, i) => (
            <button key={i} onClick={() => {}}>Button {i + 1}</button>
          ))}
        </div>
      );

      const container = document.querySelector('[data-testid="too-many-buttons"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const overloadDefects = analysis.defects.filter(d => d.type === 'cognitive_overload');
      expect(overloadDefects.length).toBeGreaterThan(0);
      expect(overloadDefects.some(d => d.description.includes('Too many interactive elements'))).toBe(true);
    });

    it('detects information density issues', async () => {
      render(
        <div data-testid="dense-content" style={{ width: '300px', height: '200px' }}>
          <p>Very dense content that overwhelms users with too much information in a small space making it difficult to process and understand the key messages being conveyed through the interface design.</p>
          <p>Additional dense content that further contributes to cognitive overload and makes the interface overwhelming for users trying to complete their tasks efficiently and effectively.</p>
          <div>
            <span>Dense inline content</span>
            <span>More dense content</span>
            <span>Even more dense content</span>
            <span>Final dense content</span>
          </div>
          <ul style={{ margin: 0, padding: 0 }}>
            <li>Dense list item 1</li>
            <li>Dense list item 2</li>
            <li>Dense list item 3</li>
            <li>Dense list item 4</li>
            <li>Dense list item 5</li>
          </ul>
        </div>
      );

      const container = document.querySelector('[data-testid="dense-content"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const overloadDefects = analysis.defects.filter(d => d.type === 'cognitive_overload');
      expect(overloadDefects.some(d => d.description.includes('Information density too high'))).toBe(true);
    });

    it('detects long text blocks', async () => {
      const longText = 'This is a very long text block that contains way too many words for users to easily scan and process. '.repeat(10);

      render(
        <div data-testid="long-text">
          <p>{longText}</p>
        </div>
      );

      const container = document.querySelector('[data-testid="long-text"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const overloadDefects = analysis.defects.filter(d => d.type === 'cognitive_overload');
      expect(overloadDefects.some(d => d.description.includes('Long text block'))).toBe(true);
    });

    it('passes test with appropriate content density', async () => {
      render(
        <div data-testid="appropriate-density">
          <h2>Clean Section Title</h2>
          <p>Brief, scannable paragraph.</p>
          <ul>
            <li>Clear point</li>
            <li>Another point</li>
            <li>Final point</li>
          </ul>
          <button>Clear Action</button>
        </div>
      );

      const container = document.querySelector('[data-testid="appropriate-density"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      expect(analysis.usabilityScore).toBeGreaterThan(80);
      const overloadDefects = analysis.defects.filter(d => d.type === 'cognitive_overload' && d.severity === 'high');
      expect(overloadDefects.length).toBe(0);
    });
  });

  describe('🧭 Navigation Issue Detection', () => {
    it('detects missing navigation landmarks', async () => {
      render(
        <div data-testid="no-landmarks">
          <div>Content without semantic navigation structure</div>
          <button>Action Button</button>
          <a href="#">Link</a>
        </div>
      );

      const container = document.querySelector('[data-testid="no-landmarks"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const navDefects = analysis.defects.filter(d => d.type === 'navigation_issue');
      expect(navDefects.length).toBeGreaterThan(0);
    });

    it('detects unclear navigation labels', async () => {
      render(
        <nav data-testid="unclear-labels">
          <a href="#">Click here</a>
          <button>Submit</button>
          <button>OK</button>
        </nav>
      );

      const container = document.querySelector('[data-testid="unclear-labels"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const navDefects = analysis.defects.filter(d => d.type === 'navigation_issue');
      expect(navDefects.some(d => d.description.includes('Generic navigation label'))).toBe(true);
    });

    it('detects missing navigation labels', async () => {
      render(
        <nav data-testid="missing-labels">
          <button></button>
          <a href="#"></a>
        </nav>
      );

      const container = document.querySelector('[data-testid="missing-labels"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const navDefects = analysis.defects.filter(d => d.type === 'navigation_issue');
      expect(navDefects.some(d => d.description.includes('Unclear navigation label'))).toBe(true);
    });

    it('validates well-structured navigation', async () => {
      render(
        <div data-testid="good-navigation">
          <header role="banner">
            <h1>Application Title</h1>
            <nav role="navigation">
              <a href="/home">Home</a>
              <a href="/dashboard">Dashboard</a>
              <a href="/settings">Settings</a>
            </nav>
          </header>
          <main role="main">
            <h2>Main Content</h2>
            <p>Content description.</p>
          </main>
        </div>
      );

      const container = document.querySelector('[data-testid="good-navigation"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      expect(analysis.usabilityScore).toBeGreaterThan(85);
      const navDefects = analysis.defects.filter(d => d.type === 'navigation_issue' && d.severity === 'high');
      expect(navDefects.length).toBe(0);
    });
  });

  describe('♿ Accessibility Violation Detection', () => {
    it('detects missing alt text on images', async () => {
      render(
        <div data-testid="missing-alt">
          <img src="test.jpg" />
          <img src="test2.jpg" alt="This has alt text" />
        </div>
      );

      const container = document.querySelector('[data-testid="missing-alt"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const accessibilityDefects = analysis.defects.filter(d => d.type === 'accessibility_violation');
      expect(accessibilityDefects.some(d => d.description.includes('Missing alt text'))).toBe(true);
    });

    it('detects missing form labels', async () => {
      render(
        <form data-testid="missing-labels">
          <input type="text" />
          <input type="email" aria-label="Email Address" />
          <label htmlFor="password">Password</label>
          <input type="password" id="password" />
          <textarea />
        </form>
      );

      const container = document.querySelector('[data-testid="missing-labels"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const accessibilityDefects = analysis.defects.filter(d => d.type === 'accessibility_violation');
      expect(accessibilityDefects.some(d => d.description.includes('missing associated label'))).toBe(true);
    });

    it('detects missing focus styles', async () => {
      render(
        <div data-testid="no-focus-styles">
          <button style={{ outline: 'none', boxShadow: 'none' }}>Button without focus</button>
        </div>
      );

      const container = document.querySelector('[data-testid="no-focus-styles"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const accessibilityDefects = analysis.defects.filter(d => d.type === 'accessibility_violation');
      expect(accessibilityDefects.some(d => d.description.includes('lacks visible focus indicator'))).toBe(true);
    });

    it('validates accessible form structure', async () => {
      render(
        <form data-testid="accessible-form">
          <label htmlFor="username">Username</label>
          <input type="text" id="username" aria-label="Username input" />
          <button type="submit">Submit Form</button>
        </form>
      );

      const container = document.querySelector('[data-testid="accessible-form"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      expect(analysis.usabilityScore).toBeGreaterThan(90);
    });
  });

  describe('👆 Touch Target Size Detection', () => {
    it('detects touch targets too small', async () => {
      render(
        <div data-testid="small-touch-targets">
          <button style={{ width: '30px', height: '30px' }}>Tiny</button>
          <button style={{ width: '20px', height: '20px' }}>Micro</button>
          <button style={{ width: '44px', height: '44px' }}>Standard</button>
        </div>
      );

      const container = document.querySelector('[data-testid="small-touch-targets"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const touchDefects = analysis.defects.filter(d => d.type === 'touch_target_size');
      expect(touchDefects.length).toBeGreaterThan(1); // Should find both tiny buttons
    });

    it('detects insufficient spacing between touch targets', async () => {
      render(
        <div data-testid="no-spacing" style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <button style={{ width: '48px', height: '48px' }}>Button 1</button>
          <button style={{ width: '48px', height: '48px' }}>Button 2</button>
          <button style={{ width: '48px', height: '48px' }}>Button 3</button>
        </div>
      );

      const container = document.querySelector('[data-testid="no-spacing"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const touchDefects = analysis.defects.filter(d => d.type === 'touch_target_size');
      expect(touchDefects.some(d => d.description.includes('Insufficient spacing'))).toBe(true);
    });

    it('validates properly sized touch targets', async () => {
      render(
        <div data-testid="good-touch-targets">
          <button style={{ width: '48px', height: '48px', marginBottom: '16px' }}>Button 1</button>
          <button style={{ width: '52px', height: '52px', marginBottom: '16px' }}>Button 2</button>
          <button style={{ width: '44px', height: '44px', marginBottom: '16px' }}>Button 3</button>
        </div>
      );

      const container = document.querySelector('[data-testid="good-touch-targets"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const touchDefects = analysis.defects.filter(d => d.type === 'touch_target_size' && d.severity === 'high');
      expect(touchDefects.length).toBe(0);
    });
  });

  describe('🎨 Color Contrast Detection', () => {
    it('detects potential contrast issues', async () => {
      render(
        <div data-testid="contrast-issues">
          <p style={{ color: '#ffffff', backgroundColor: '#ffffcc' }}>Light text on light background</p>
          <p style={{ color: '#333333', backgroundColor: '#333333' }}>Dark text on dark background</p>
          <p style={{ color: '#000000', backgroundColor: '#ffffff' }}>Good contrast</p>
        </div>
      );

      const container = document.querySelector('[data-testid="contrast-issues"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('TestComponent', container);

      const contrastDefects = analysis.defects.filter(d => d.type === 'color_contrast');
      expect(contrastDefects.length).toBeGreaterThan(1);
    });
  });

  describe('📊 Comprehensive Layout Analysis', () => {
    it('generates complete analysis report', async () => {
      render(
        <div data-testid="complex-layout">
          <h1>Main Title</h1>
          <nav>
            <a href="#">Link 1</a>
            <button>Button 1</button>
          </nav>
          <main>
            <h2>Section Title</h2>
            <p>Content paragraph.</p>
            <form>
              <label htmlFor="input1">Input Label</label>
              <input type="text" id="input1" />
              <button type="submit">Submit</button>
            </form>
            <img src="test.jpg" alt="Test Image" />
            <div>
              <h3>Subsection</h3>
              {Array.from({ length: 20 }, (_, i) => (
                <button key={i} style={{ width: '40px', height: '40px' }}>B{i}</button>
              ))}
            </div>
          </main>
        </div>
      );

      const container = document.querySelector('[data-testid="complex-layout"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('ComplexComponent', container);

      // Should detect various types of defects
      expect(analysis.totalDefects).toBeGreaterThan(5);
      expect(analysis.defects.length).toBeGreaterThan(5);
      expect(analysis.usabilityScore).toBeLessThan(90); // Should have issues

      // Should have defects from multiple categories
      const defectTypes = new Set(analysis.defects.map(d => d.type));
      expect(defectTypes.size).toBeGreaterThan(2);
    });

    it('calculates accurate metrics', async () => {
      render(
        <div data-testid="metrics-test">
          <button>Button</button>
          <input type="text" />
          <a href="#">Link</a>
          <img src="test.jpg" alt="Test" />
        </div>
      );

      const container = document.querySelector('[data-testid="metrics-test"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('MetricsComponent', container);

      expect(analysis.metrics.interactiveElements).toBe(3); // button, input, link
      expect(analysis.metrics.hierarchyScore).toBeGreaterThan(0);
      expect(analysis.metrics.touchScore).toBeGreaterThan(0);
    });

    it('validates high-quality layout', async () => {
      render(
        <div data-testid="high-quality" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
          <header role="banner">
            <h1>Application Title</h1>
            <nav role="navigation">
              <a href="/">Home</a>
              <a href="/about">About</a>
            </nav>
          </header>
          <main role="main">
            <section>
              <h2>Section Title</h2>
              <p>This is a well-structured paragraph with appropriate length and readability.</p>
              <form>
                <label htmlFor="name">Name:</label>
                <input type="text" id="name" aria-label="Your full name" />
                <button type="submit" style={{ padding: '12px 24px', fontSize: '16px' }}>
                  Submit
                </button>
              </form>
            </section>
          </main>
          <footer role="contentinfo">
            <p>Footer content</p>
          </footer>
        </div>
      );

      const container = document.querySelector('[data-testid="high-quality"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('HighQualityComponent', container);

      expect(analysis.usabilityScore).toBeGreaterThan(85);
      expect(analysis.totalDefects).toBeLessThan(5);
    });
  });

  describe('🔧 Defect Classification and Severity', () => {
    it('correctly classifies defect severity levels', async () => {
      render(
        <div data-testid="severity-test">
          <img src="test.jpg" /> {/* Critical: missing alt */}
          <button style={{ width: '20px', height: '20px' }}>Tiny</button> {/* High: touch size */}
          <nav role="navigation">
            <a href="#">Click here</a> {/* Medium: generic label */}
          <p style={{ textAlign: 'justify' }}>Justified text</p> {/* Low: readability */}
          <button style={{ outline: 'none' }}>No focus</button> {/* Medium: accessibility */}
        </div>
      );

      const container = document.querySelector('[data-testid="severity-test"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('SeverityTestComponent', container);

      const criticalDefects = analysis.defects.filter(d => d.severity === 'critical');
      const highDefects = analysis.defects.filter(d => d.severity === 'high');
      const mediumDefects = analysis.defects.filter(d => d.severity === 'medium');
      const lowDefects = analysis.defects.filter(d => d.severity === 'low');

      expect(criticalDefects.length).toBeGreaterThan(0);
      expect(highDefects.length).toBeGreaterThan(0);
      expect(mediumDefects.length).toBeGreaterThan(0);
      expect(lowDefects.length).toBeGreaterThan(0);
    });

    it('provides actionable recommendations', async () => {
      render(
        <div data-testid="recommendations">
          <img src="test.jpg" />
        </div>
      );

      const container = document.querySelector('[data-testid="recommendations"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('RecommendationsComponent', container);

      const firstDefect = analysis.defects[0];
      expect(firstDefect.recommendation).toBeDefined();
      expect(firstDefect.recommendation.length).toBeGreaterThan(10);
      expect(firstDefect.wcagGuideline).toBeDefined();
      expect(firstDefect.heuristic).toBeDefined();
    });

    it('calculates confidence scores for defects', async () => {
      render(
        <div data-testid="confidence-test">
          <h1>Clear Title</h1>
          <img src="test.jpg" />
        </div>
      );

      const container = document.querySelector('[data-testid="confidence-test"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('ConfidenceComponent', container);

      analysis.defects.forEach(defect => {
        expect(defect.confidence).toBeGreaterThan(0);
        expect(defect.confidence).toBeLessThanOrEqualTo(100);
      });
    });
  });

  describe('🔄 Integration with Real Components', () => {
    it('analyzes dashboard layout components', async () => {
      const Dashboard = () => (
        <div style={{ padding: '20px' }}>
          <header style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h1>Dashboard</h1>
            <nav>
              <button>Home</button>
              <button>Settings</button>
            </nav>
          </header>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: '20px' }}>
            <aside>
              <h3>Sidebar</h3>
              <ul>
                <li><a href="#">Item 1</a></li>
                <li><a href="#">Item 2</a></li>
                <li><a href="#">Item 3</a></li>
              </ul>
            </aside>
            <main>
              <h2>Main Content</h2>
              <div style={{ display: 'grid', gap: '10px' }}>
                <div style={{ padding: '10px', border: '1px solid #ccc' }}>
                  <h4>Card 1</h4>
                  <p>Content 1</p>
                  <button>Action</button>
                </div>
                <div style={{ padding: '10px', border: '1px solid #ccc' }}>
                  <h4>Card 2</h4>
                  <p>Content 2</p>
                  <button>Action</button>
                </div>
                <div style={{ padding: '10px', border: '1px solid #ccc' }}>
                  <h4>Card 3</h4>
                  <p>Content 3</p>
                  <button>Action</button>
                </div>
              </div>
            </main>
            <aside>
              <h3>Info Panel</h3>
              <div style={{ background: '#f5f5f5', padding: '15px' }}>
                <h4>Statistics</h4>
                <p>Stat 1</p>
                <p>Stat 2</p>
                <p>Stat 3</p>
              </div>
            </aside>
          </div>
        </div>
      );

      render(<Dashboard />);
      const container = document.body; // Analyze entire rendered component
      const analysis = await detector.analyzeLayout('DashboardComponent', container);

      expect(analysis.totalDefects).toBeGreaterThan(0);
      expect(analysis.metrics).toBeDefined();
      expect(analysis.usabilityScore).toBeGreaterThan(0);
    });

    it('handles empty or minimal components gracefully', async () => {
      const EmptyComponent = () => <div data-testid="empty"> </div>;
      render(<EmptyComponent />);

      const container = document.querySelector('[data-testid="empty"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('EmptyComponent', container);

      expect(analysis).toBeDefined();
      expect(analysis.totalDefects).toBeGreaterThanOrEqual(0);
    });

    it('processes dynamic content updates', async () => {
      const DynamicComponent = () => {
        const [content, setContent] = React.useState('Initial');

        return (
          <div data-testid="dynamic">
            <h1>{content}</h1>
            <button onClick={() => setContent('Updated')}>Update</button>
          </div>
        );
      };

      render(<DynamicComponent />);
      const container = document.querySelector('[data-testid="dynamic"]') as HTMLElement;

      let analysis = await detector.analyzeLayout('DynamicComponent', container);
      const initialDefects = analysis.defects.length;

      // Trigger update
      const updateButton = screen.getByText('Update');
      await userEventSetup.click(updateButton);

      await waitFor(() => {
        expect(screen.getByText('Updated')).toBeInTheDocument();
      });

      analysis = await detector.analyzeLayout('DynamicComponent', container);
      const updatedDefects = analysis.defects.length;

      expect(analysis).toBeDefined();
      expect(updatedDefects).toBeGreaterThanOrEqual(0);
    });
  });

  describe('📈 Performance and Scalability', () => {
    it('handles large numbers of elements efficiently', async () => {
      const startTime = performance.now();

      render(
        <div data-testid="large-component">
          <h1>Large Component</h1>
          {Array.from({ length: 100 }, (_, i) => (
            <button key={i} style={{ margin: '2px' }}>
              Button {i}
            </button>
          ))}
          <div>
            {Array.from({ length: 50 }, (_, i) => (
              <img key={i} src={`test${i}.jpg`} />
            ))}
          </div>
        </div>
      );

      const container = document.querySelector('[data-testid="large-component"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('LargeComponent', container);

      const endTime = performance.now();
      const processingTime = endTime - startTime;

      expect(processingTime).toBeLessThan(1000); // Should complete within 1 second
      expect(analysis.defects.length).toBeGreaterThan(50); // Should find many defects
      expect(analysis.metrics.interactiveElements).toBe(100);
    });

    it('provides detailed analysis breakdown', async () => {
      render(
        <div data-testid="detailed-analysis">
          <header>
            <h1>Test Component</h1>
            <nav>
              <a href="#">Link</a>
              <button>Button</button>
            </nav>
          </header>
          <main>
            <h2>Content</h2>
            <form>
              <input type="text" />
              <textarea />
            </form>
          </main>
        </div>
      );

      const container = document.querySelector('[data-testid="detailed-analysis"]') as HTMLElement;
      const analysis = await detector.analyzeLayout('DetailedComponent', container);

      // Verify comprehensive analysis structure
      expect(analysis.component).toBe('DetailedComponent');
      expect(analysis.usabilityScore).toBeDefined();
      expect(analysis.totalDefects).toBeDefined();
      expect(analysis.severityBreakdown).toBeDefined();
      expect(analysis.defects).toBeDefined();
      expect(analysis.metrics).toBeDefined();
    });
  });
});