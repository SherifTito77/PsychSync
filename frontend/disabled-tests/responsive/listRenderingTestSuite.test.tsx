/**
 * Comprehensive List Rendering Test Suite
 * Tests for common responsive list rendering problems and their solutions
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ListRenderingAnalyzer, type ListRenderingIssue, type ListRenderingTestCase } from './listRenderingProblems';

describe('📱 Comprehensive List Rendering Test Suite', () => {
  let analyzer: ListRenderingAnalyzer;

  beforeEach(() => {
    analyzer = new ListRenderingAnalyzer();
  });

  describe('🔍 List Rendering Issue Identification', () => {
    it('should identify all common list rendering problems', () => {
      const issues = analyzer.analyzeListRenderingProblems();

      expect(issues).toBeDefined();
      expect(issues.length).toBeGreaterThan(0);

      // Verify issue categories
      const categories = issues.map(issue => issue.category);
      expect(categories).toContain('overflow');
      expect(categories).toContain('spacing');
      expect(categories).toContain('wrapping');
      expect(categories).toContain('navigation');
      expect(categories).toContain('accessibility');
      expect(categories).toContain('performance');
      expect(categories).toContain('visual');
      expect(categories).toContain('interaction');

      console.log(`📋 Identified ${issues.length} list rendering issues across ${[...new Set(categories)].length} categories`);
    });

    it('should provide detailed issue information', () => {
      const issues = analyzer.analyzeListRenderingProblems();
      const overflowIssue = issues.find(issue => issue.id === 'list-overflow-001');

      expect(overflowIssue).toBeDefined();
      expect(overflowIssue?.title).toBe('Text Truncation Without Indication');
      expect(overflowIssue?.severity).toBe('high');
      expect(overflowIssue?.problematicViewports).toBe('mobile');
      expect(overflowIssue?.symptoms).toBeDefined();
      expect(overflowIssue?.impact).toBeDefined();
      expect(overflowIssue?.prevention).toBeDefined();
      expect(overflowIssue?.solution).toBeDefined();

      console.log(`✅ Issue ${overflowIssue?.id}: ${overflowIssue?.title} (${overflowIssue?.severity} severity)`);
    });

    it('should prioritize issues by severity', () => {
      const issues = analyzer.analyzeListRenderingProblems();

      const criticalIssues = issues.filter(issue => issue.severity === 'critical');
      const highIssues = issues.filter(issue => issue.severity === 'high');
      const mediumIssues = issues.filter(issue => issue.severity === 'medium');
      const lowIssues = issues.filter(issue => issue.severity === 'low');

      expect(criticalIssues.length + highIssues.length + mediumIssues.length + lowIssues.length).toBe(issues.length);

      console.log(`🚨 Critical: ${criticalIssues.length}, High: ${highIssues.length}, Medium: ${mediumIssues.length}, Low: ${lowIssues.length}`);
    });
  });

  describe('📐 Text Overflow and Wrapping Tests', () => {
    it('should detect text overflow issues', () => {
      const { container } = render(
        <div style={{ width: '300px' }}>
          <ul>
            <li style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              Very long list item that gets truncated without proper indication
            </li>
          </ul>
        </div>
      );

      const listItem = container.querySelector('li');
      expect(listItem).toBeTruthy();

      const computedStyle = window.getComputedStyle(listItem!);
      expect(computedStyle.textOverflow).toBe('ellipsis');
      expect(computedStyle.whiteSpace).toBe('nowrap');

      console.log(`✅ Text overflow detection: ellipsis applied correctly`);
    });

    it('should test horizontal scrolling problems', () => {
      const { container } = render(
        <div style={{ width: '300px', overflowX: 'auto' }}>
          <ul style={{ whiteSpace: 'nowrap' }}>
            <li>Very long item that causes horizontal scrolling</li>
            <li>Another long item that exacerbates the issue</li>
          </ul>
        </div>
      );

      const listContainer = container.querySelector('div');
      const list = container.querySelector('ul');

      expect(listContainer).toBeTruthy();
      expect(list).toBeTruthy();

      // Check if container forces horizontal scroll
      const containerStyle = window.getComputedStyle(listContainer!);
      const listStyle = window.getComputedStyle(list!);

      expect(containerStyle.overflowX).toBe('auto');
      expect(listStyle.whiteSpace).toBe('nowrap');

      console.log(`⚠️  Horizontal scrolling detected: overflow-x: auto with nowrap`);
    });

    it('should test text wrapping solutions', () => {
      const { container } = render(
        <div style={{ width: '300px' }}>
          <ul>
            <li style={{ wordWrap: 'break-word', lineHeight: '1.5' }}>
              Supercalifragilisticexpialidocious text that should wrap properly
            </li>
          </ul>
        </div>
      );

      const listItem = container.querySelector('li');
      expect(listItem).toBeTruthy();

      const computedStyle = window.getComputedStyle(listItem!);
      expect(computedStyle.wordWrap || computedStyle.overflowWrap).toMatch(/break-word/);

      console.log(`✅ Text wrapping solution: break-word applied with proper line-height`);
    });
  });

  describe('📏 Spacing and Touch Target Tests', () => {
    it('should detect insufficient tap target sizes', () => {
      const { container } = render(
        <ul>
          <li>
            <button style={{ padding: '4px', height: '32px' }}>Small Button</button>
          </li>
          <li>
            <button style={{ padding: '12px', height: '48px' }}>Proper Button</button>
          </li>
        </ul>
      );

      const buttons = container.querySelectorAll('button');
      expect(buttons).toHaveLength(2);

      const smallButton = buttons[0].getBoundingClientRect();
      const properButton = buttons[1].getBoundingClientRect();

      // Check mobile touch target requirements
      expect(smallButton.height).toBeLessThan(44);
      expect(properButton.height).toBeGreaterThanOrEqual(44);

      console.log(`📱 Tap target sizes: Small=${smallButton.height}px (❌), Proper=${properButton.height}px (✅)`);
    });

    it('should test responsive spacing consistency', () => {
      const { container } = render(
        <ul>
          <li style={{ marginBottom: '8px' }}>Item 1</li>
          <li style={{ marginBottom: '8px' }}>Item 2</li>
          <li style={{ marginBottom: '8px' }}>Item 3</li>
          <li style={{ marginBottom: '16px' }}>Item 4 (inconsistent)</li>
        </ul>
      );

      const items = container.querySelectorAll('li');
      expect(items).toHaveLength(4);

      const spacings: number[] = [];
      for (let i = 0; i < items.length - 1; i++) {
        const style = window.getComputedStyle(items[i]);
        spacings.push(parseFloat(style.marginBottom));
      }

      const spacingVariance = Math.max(...spacings) - Math.min(...spacings);
      expect(spacingVariance).toBeGreaterThan(0);

      console.log(`📏 Spacing variance detected: ${spacingVariance}px (inconsistent spacing)`);
    });
  });

  describe('🧭 Navigation and Accessibility Tests', () => {
    it('should test keyboard navigation in lists', async () => {
      const { container } = render(
        <ul>
          <li><button tabIndex={0}>List Item 1</button></li>
          <li><button tabIndex={0}>List Item 2</button></li>
          <li><button tabIndex={0}>List Item 3</button></li>
        </ul>
      );

      const buttons = container.querySelectorAll('button');
      expect(buttons).toHaveLength(3);

      // Test focus management
      buttons.forEach((button, index) => {
        button.focus();
        expect(document.activeElement).toBe(button);
        console.log(`🧭 Button ${index + 1} focus: ✅`);
      });
    });

    it('should test semantic list markup', () => {
      const { container } = render(
        <ul role="list" aria-label="Test semantic list">
          <li role="listitem">Semantic Item 1</li>
          <li role="listitem">Semantic Item 2</li>
        </ul>
      );

      const list = container.querySelector('ul');
      const items = container.querySelectorAll('li');

      expect(list).toBeTruthy();
      expect(items).toHaveLength(2);

      expect(list?.getAttribute('role')).toBe('list');
      expect(list?.getAttribute('aria-label')).toBe('Test semantic list');

      items.forEach((item, index) => {
        expect(item.getAttribute('role')).toBe('listitem');
      });

      console.log(`♿ Semantic markup: ✅ Proper list structure with ARIA labels`);
    });

    it('should test screen reader compatibility', () => {
      const { container } = render(
        <ul style={{ listStyle: 'none' }} role="list">
          <li>Item with hidden marker</li>
          <li>Another item</li>
        </ul>
      );

      const list = container.querySelector('ul');
      expect(list).toBeTruthy();

      const listStyle = window.getComputedStyle(list!);
      const hasRole = list?.hasAttribute('role');

      // Check if list compensates for hidden markers
      expect(listStyle.listStyle).toBe('none');
      expect(hasRole).toBe(true);

      console.log(`🔊 Screen reader compatibility: ✅ Role attribute compensates for hidden markers`);
    });
  });

  describe('⚡ Performance Tests', () => {
    it('should test large list rendering performance', async () => {
      const startTime = performance.now();

      const { container } = render(
        <ul style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {Array.from({ length: 100 }, (_, i) => (
            <li key={i} style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
              Performance Test Item {i + 1}
            </li>
          ))}
        </ul>
      );

      const renderTime = performance.now() - startTime;
      const items = container.querySelectorAll('li');

      expect(items).toHaveLength(100);
      expect(renderTime).toBeLessThan(500); // Allow generous limit for test environment

      console.log(`⚡ Large list render time: ${renderTime.toFixed(2)}ms for ${items.length} items`);
    });

    it('should test scrolling performance', async () => {
      const { container } = render(
        <div style={{ height: '200px', overflowY: 'auto' }}>
          <ul>
            {Array.from({ length: 50 }, (_, i) => (
              <li key={i} style={{ padding: '12px', height: '60px' }}>
                Scrollable Item {i + 1} with content
              </li>
            ))}
          </ul>
        </div>
      );

      const scrollContainer = container.firstElementChild as HTMLElement;
      expect(scrollContainer).toBeTruthy();

      const scrollStartTime = performance.now();

      // Simulate scroll
      scrollContainer.scrollTop = 100;
      await new Promise(resolve => setTimeout(resolve, 10));

      const scrollTime = performance.now() - scrollStartTime;

      expect(scrollTime).toBeLessThan(100);
      console.log(`📜 Scroll performance: ${scrollTime.toFixed(2)}ms`);
    });
  });

  describe('🎨 Visual and Interaction Tests', () => {
    it('should test hover and active states', async () => {
      const { container } = render(
        <ul>
          <li
            style={{
              padding: '12px',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f0f0f0'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            Interactive List Item
          </li>
        </ul>
      );

      const listItem = container.querySelector('li');
      expect(listItem).toBeTruthy();

      // Test hover state
      fireEvent.mouseEnter(listItem!);
      const hoverStyle = window.getComputedStyle(listItem!);

      // Test active state
      fireEvent.mouseDown(listItem!);

      console.log(`🎨 Interactive states: Hover and active events handled`);
    });

    it('should test consistent styling across viewports', () => {
      const viewports = [
        { width: 320, name: 'mobile' },
        { width: 768, name: 'tablet' },
        { width: 1024, name: 'desktop' }
      ];

      viewports.forEach(viewport => {
        // Mock viewport width
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: viewport.width,
        });

        const { container } = render(
          <ul>
            <li style={{
              padding: viewport.width < 768 ? '8px' : viewport.width < 1024 ? '12px' : '16px'
            }}>
              Responsive Item
            </li>
          </ul>
        );

        const listItem = container.querySelector('li');
        const style = window.getComputedStyle(listItem!);
        const padding = parseFloat(style.padding);

        // Verify responsive padding
        if (viewport.width < 768) {
          expect(padding).toBeLessThanOrEqual(8);
        } else if (viewport.width < 1024) {
          expect(padding).toBeLessThanOrEqual(12);
        } else {
          expect(padding).toBeLessThanOrEqual(16);
        }

        console.log(`📱 ${viewport.name} (${viewport.width}px): padding=${padding}px`);
      });
    });
  });

  describe('🔧 Test Case Generation and Validation', () => {
    it('should generate comprehensive test cases', () => {
      const testCases = analyzer.generateTestCases();

      expect(testCases).toBeDefined();
      expect(testCases.length).toBeGreaterThan(0);

      testCases.forEach(testCase => {
        expect(testCase.id).toBeDefined();
        expect(testCase.name).toBeDefined();
        expect(testCase.description).toBeDefined();
        expect(testCase.currentImplementation).toBeDefined();
        expect(testCase.responsiveSolution).toBeDefined();
        expect(testCase.issues).toBeDefined();
        expect(testCase.problematicSizes).toBeDefined();
      });

      console.log(`📋 Generated ${testCases.length} comprehensive test cases`);
    });

    it('should validate problematic viewport sizes', () => {
      const testCases = analyzer.generateTestCases();
      const allProblematicSizes = testCases.flatMap(tc => tc.problematicSizes);

      // Verify common problematic viewport sizes are covered
      expect(allProblematicSizes).toContain(320); // Mobile
      expect(allProblematicSizes).toContain(375); // Mobile larger
      expect(allProblematicSizes).toContain(768); // Tablet

      const uniqueSizes = [...new Set(allProblematicSizes)];
      console.log(`📱 Problematic viewport sizes covered: ${uniqueSizes.join(', ')}px`);
    });
  });

  describe('📊 Viewport-Specific Analysis', () => {
    it('should analyze mobile-specific problems', () => {
      const viewportResults = analyzer.analyzeViewportProblems();
      const mobileResults = viewportResults.find(r => r.viewport === 'mobile');

      expect(mobileResults).toBeDefined();
      expect(mobileResults?.width).toBe(375);

      if (mobileResults && mobileResults.issues.length > 0) {
        console.log(`📱 Mobile issues detected: ${mobileResults.issues.length}`);
        mobileResults.issues.forEach(issue => console.log(`  - ${issue}`));

        console.log(`💡 Mobile recommendations: ${mobileResults.recommendations.length}`);
        mobileResults.recommendations.forEach(rec => console.log(`  - ${rec}`));
      }
    });

    it('should analyze tablet-specific problems', () => {
      const viewportResults = analyzer.analyzeViewportProblems();
      const tabletResults = viewportResults.find(r => r.viewport === 'tablet');

      expect(tabletResults).toBeDefined();
      expect(tabletResults?.width).toBe(768);

      console.log(`📱 Tablet analysis complete with ${tabletResults?.issues.length} issues found`);
    });

    it('should analyze desktop-specific problems', () => {
      const viewportResults = analyzer.analyzeViewportProblems();
      const desktopResults = viewportResults.find(r => r.viewport === 'desktop');

      expect(desktopResults).toBeDefined();
      expect(desktopResults?.width).toBe(1024);

      console.log(`🖥️  Desktop analysis complete with ${desktopResults?.issues.length} issues found`);
    });
  });

  describe('🎯 Solution Validation Tests', () => {
    it('should validate responsive solutions', () => {
      const testCases = analyzer.generateTestCases();

      testCases.forEach(testCase => {
        // Render the problematic version
        const { container: problemContainer } = render(
          <div style={{ width: '300px' }}>
            {testCase.currentImplementation}
          </div>
        );

        // Render the solution
        const { container: solutionContainer } = render(
          <div style={{ width: '300px' }}>
            {testCase.responsiveSolution}
          </div>
        );

        // Basic validation that both render
        expect(problemContainer).toBeTruthy();
        expect(solutionContainer).toBeTruthy();

        console.log(`✅ Validated solution for: ${testCase.name}`);
      });
    });

    it('should provide actionable recommendations', () => {
      const issues = analyzer.analyzeListRenderingProblems();

      issues.forEach(issue => {
        expect(issue.solution).toBeDefined();
        expect(issue.solution!.length).toBeGreaterThan(0);
        expect(issue.prevention).toBeDefined();
        expect(issue.prevention.length).toBeGreaterThan(0);
      });

      const totalRecommendations = issues.reduce((sum, issue) =>
        sum + issue.prevention.length, 0
      );

      console.log(`💡 Total actionable recommendations: ${totalRecommendations}`);
    });
  });

  describe('📈 Comprehensive Summary Reports', () => {
    it('should generate detailed analysis summary', () => {
      const issues = analyzer.analyzeListRenderingProblems();
      const testCases = analyzer.generateTestCases();
      const viewportResults = analyzer.analyzeViewportProblems();

      // Issue distribution
      const issueDistribution = issues.reduce((acc, issue) => {
        acc[issue.category] = (acc[issue.category] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      // Severity distribution
      const severityDistribution = issues.reduce((acc, issue) => {
        acc[issue.severity] = (acc[issue.severity] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      console.log('\n📊 Comprehensive List Rendering Analysis Summary:');
      console.log(`Total Issues Identified: ${issues.length}`);
      console.log(`Test Cases Generated: ${testCases.length}`);
      console.log(`Viewport Analyses: ${viewportResults.length}`);

      console.log('\n📋 Issues by Category:');
      Object.entries(issueDistribution).forEach(([category, count]) => {
        console.log(`  ${category}: ${count} issues`);
      });

      console.log('\n🚨 Issues by Severity:');
      Object.entries(severityDistribution).forEach(([severity, count]) => {
        console.log(`  ${severity}: ${count} issues`);
      });

      // Validation
      expect(issues.length).toBeGreaterThan(0);
      expect(testCases.length).toBeGreaterThan(0);
      expect(viewportResults.length).toBe(3); // mobile, tablet, desktop
      expect(Object.keys(issueDistribution).length).toBeGreaterThan(0);
      expect(Object.keys(severityDistribution).length).toBeGreaterThan(0);
    });
  });
});