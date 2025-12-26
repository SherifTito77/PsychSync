/**
 * 📐 Layout Analysis Engine
 *
 * Advanced layout analysis tools for detecting complex usability patterns,
  visual hierarchy issues, and cognitive load problems in screen layouts.
 */

import { LayoutMetrics, UXDefect } from './usabilityDefectDetector';

export interface LayoutPattern {
  name: string;
  type: 'grid' | 'flexbox' | 'float' | 'absolute' | 'hybrid';
  confidence: number;
  complexity: number;
  responsiveness: number;
  accessibility: number;
}

export interface VisualElement {
  element: HTMLElement;
  x: number;
  y: number;
  width: number;
  height: number;
  zIndex: number;
  visibility: number; // 0-1 opacity
  isInteractive: boolean;
  isImportant: boolean;
  semanticRole: string;
  color: {
    foreground: string;
    background: string;
    contrast: number;
  };
  typography: {
    fontSize: number;
    fontWeight: number;
    lineHeight: number;
    fontFamily: string;
  };
}

export interface CognitiveLoadMetrics {
  visualComplexity: number; // 0-100
  informationDensity: number; // 0-100
  choiceComplexity: number; // 0-100
  memoryLoad: number; // 0-100
  navigationComplexity: number; // 0-100
  total: number; // 0-100
}

export interface VisualHierarchyNode {
  element: VisualElement;
  level: number; // Hierarchy level (1=most important)
  weight: number; // Visual weight score
  children: VisualHierarchyNode[];
  violations: string[];
}

export class LayoutAnalyzer {
  private complexityThresholds = {
    simple: 30,
    moderate: 60,
    complex: 80,
    extreme: 90,
  };

  private cognitiveLoadWeights = {
    visualComplexity: 0.25,
    informationDensity: 0.25,
    choiceComplexity: 0.20,
    memoryLoad: 0.15,
    navigationComplexity: 0.15,
  };

  /**
   * Perform comprehensive layout analysis
   */
  analyzeLayout(container: HTMLElement): {
    patterns: LayoutPattern[];
    visualElements: VisualElement[];
    cognitiveLoad: CognitiveLoadMetrics;
    hierarchy: VisualHierarchyNode[];
    metrics: LayoutMetrics;
  } {
    const visualElements = this.extractVisualElements(container);
    const patterns = this.detectLayoutPatterns(container);
    const cognitiveLoad = this.calculateCognitiveLoad(container, visualElements);
    const hierarchy = this.buildVisualHierarchy(container, visualElements);
    const metrics = this.calculateAdvancedMetrics(container, visualElements);

    return {
      patterns,
      visualElements,
      cognitiveLoad,
      hierarchy,
      metrics,
    };
  }

  /**
   * Extract all visual elements with their properties
   */
  private extractVisualElements(container: HTMLElement): VisualElement[] {
    const elements: VisualElement[] = [];
    const walker = document.createTreeWalker(
      container,
      NodeFilter.SHOW_ELEMENT,
      {
        acceptNode: (node) => {
          // Skip script, style, and hidden elements
          const tagName = node.tagName.toLowerCase();
          const skipTags = ['script', 'style', 'noscript', 'meta', 'link'];

          if (skipTags.includes(tagName)) {
            return NodeFilter.FILTER_SKIP;
          }

          // Skip elements with no visual presence
          const styles = window.getComputedStyle(node);
          if (styles.display === 'none' || styles.visibility === 'hidden' || styles.opacity === '0') {
            return NodeFilter.FILTER_SKIP;
          }

          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    let node;
    while ((node = walker.nextNode() as HTMLElement)) {
      try {
        const rect = node.getBoundingClientRect();
        const styles = window.getComputedStyle(node);

        const element: VisualElement = {
          element: node,
          x: rect.left,
          y: rect.top,
          width: rect.width,
          height: rect.height,
          zIndex: parseInt(styles.zIndex) || 0,
          visibility: parseFloat(styles.opacity),
          isInteractive: this.isInteractive(node),
          isImportant: this.isImportant(node),
          semanticRole: this.getSemanticRole(node),
          color: {
            foreground: styles.color,
            background: styles.backgroundColor,
            contrast: this.calculateContrastRatio(styles.color, styles.backgroundColor),
          },
          typography: {
            fontSize: parseFloat(styles.fontSize),
            fontWeight: this.getFontWeight(styles.fontWeight),
            lineHeight: parseFloat(styles.lineHeight),
            fontFamily: styles.fontFamily,
          },
        };

        elements.push(element);
      } catch (error) {
        // Skip elements that cause errors during analysis
        continue;
      }
    }

    return elements;
  }

  /**
   * Detect layout patterns used in the container
   */
  private detectLayoutPatterns(container: HTMLElement): LayoutPattern[] {
    const patterns: LayoutPattern[] = [];

    // Detect Grid layout
    if (this.hasGridLayout(container)) {
      patterns.push({
        name: 'CSS Grid',
        type: 'grid',
        confidence: 0.9,
        complexity: this.calculateGridLayoutComplexity(container),
        responsiveness: this.calculateResponsivenessScore(container),
        accessibility: this.calculateAccessibilityScore(container),
      });
    }

    // Detect Flexbox layout
    if (this.hasFlexboxLayout(container)) {
      patterns.push({
        name: 'Flexbox',
        type: 'flexbox',
        confidence: 0.85,
        complexity: this.calculateFlexboxComplexity(container),
        responsiveness: this.calculateResponsivenessScore(container),
        accessibility: this.calculateAccessibilityScore(container),
      });
    }

    // Detect Float layout (legacy)
    if (this.hasFloatLayout(container)) {
      patterns.push({
        name: 'Float Layout',
        type: 'float',
        confidence: 0.7,
        complexity: this.calculateFloatComplexity(container),
        responsiveness: 0.3, // Float layouts are generally not responsive
        accessibility: 0.5,
      });
    }

    // Detect Absolute positioning
    if (this.hasAbsoluteLayout(container)) {
      patterns.push({
        name: 'Absolute Positioning',
        type: 'absolute',
        confidence: 0.8,
        complexity: this.calculateAbsoluteComplexity(container),
        responsiveness: 0.2, // Absolute positioning is rarely responsive
        accessibility: 0.4,
      });
    }

    // Detect hybrid layouts
    if (patterns.length > 1) {
      patterns.push({
        name: 'Hybrid Layout',
        type: 'hybrid',
        confidence: 0.75,
        complexity: this.calculateHybridComplexity(patterns),
        responsiveness: this.calculateHybridResponsiveness(patterns),
        accessibility: this.calculateHybridAccessibility(patterns),
      });
    }

    return patterns.sort((a, b) => b.confidence - a.confidence);
  }

  /**
   * Calculate comprehensive cognitive load metrics
   */
  private calculateCognitiveLoad(container: HTMLElement, visualElements: VisualElement[]): CognitiveLoadMetrics {
    const visualComplexity = this.calculateVisualComplexity(container, visualElements);
    const informationDensity = this.calculateInformationDensity(container, visualElements);
    const choiceComplexity = this.calculateChoiceComplexity(visualElements);
    const memoryLoad = this.calculateMemoryLoad(visualElements);
    const navigationComplexity = this.calculateNavigationComplexity(visualElements);

    const total = Object.entries(this.cognitiveLoadWeights).reduce(
      (sum, [key, weight]) => sum + (this[key as keyof this][weight] * weight),
      0
    );

    return {
      visualComplexity,
      informationDensity,
      choiceComplexity,
      memoryLoad,
      navigationComplexity,
      total,
    };
  }

  /**
   * Calculate visual complexity score
   */
  private calculateVisualComplexity(container: HTMLElement, visualElements: VisualElement[]): number {
    let complexity = 0;

    // Element count contributes to complexity
    const elementCount = visualElements.length;
    complexity += Math.min(elementCount * 2, 30);

    // Color variety contributes to complexity
    const uniqueColors = new Set(visualElements.map(el => el.color.foreground));
    complexity += Math.min(uniqueColors.size * 3, 20);

    // Typography variety contributes to complexity
    const uniqueFonts = new Set(visualElements.map(el => el.typography.fontFamily));
    complexity += Math.min(uniqueFonts.size * 5, 25);

    // Z-index layering contributes to complexity
    const zIndexLevels = new Set(visualElements.map(el => el.zIndex));
    complexity += Math.min(zIndexLevels.size * 4, 15);

    // Interactive element density
    const interactiveElements = visualElements.filter(el => el.isInteractive).length;
    complexity += Math.min(interactiveElements * 3, 20);

    return Math.min(100, complexity);
  }

  /**
   * Calculate information density score
   */
  private calculateInformationDensity(container: HTMLElement, visualElements: VisualElement[]): number {
    const containerArea = container.offsetWidth * container.offsetHeight;
    const totalElementArea = visualElements.reduce((sum, el) => sum + (el.width * el.height), 0);

    const density = (totalElementArea / containerArea) * 100;

    // Text content density
    const textContent = container.textContent?.trim() || '';
    const textLength = textContent.length;
    const textDensity = Math.min(textLength / 100, 50);

    return Math.min(100, density + textDensity);
  }

  /**
   * Calculate choice complexity score
   */
  private calculateChoiceComplexity(visualElements: VisualElement[]): number {
    const interactiveElements = visualElements.filter(el => el.isInteractive);
    let complexity = 0;

    // Number of choices (Hick's Law)
    const choiceCount = interactiveElements.length;
    complexity += Math.min(choiceCount * 8, 60);

    // Grouping of choices
    const groups = this.groupElementsByProximity(interactiveElements);
    complexity += Math.max(0, (groups.length - choiceCount) * 5); // Negative for good grouping

    // Visual differentiation
    const uniqueStyles = new Set();
    interactiveElements.forEach(el => {
      const styleKey = `${el.color.foreground}-${el.typography.fontSize}-${el.typography.fontWeight}`;
      uniqueStyles.add(styleKey);
    });
    complexity += Math.max(0, (uniqueStyles.size - choiceCount) * 3); // Negative for good differentiation

    return Math.min(100, complexity);
  }

  /**
   * Calculate memory load score
   */
  private calculateMemoryLoad(visualElements: VisualElement[]): number {
    let memoryLoad = 0;

    // Number of items to remember
    const itemCount = visualElements.filter(el => el.isImportant).length;
    memoryLoad += Math.min(itemCount * 4, 40);

    // Label complexity
    const textElements = visualElements.filter(el =>
      ['p', 'span', 'div', 'label'].includes(el.element.tagName.toLowerCase())
    );
    const avgLabelLength = textElements.reduce((sum, el) =>
      sum + (el.element.textContent?.length || 0), 0) / Math.max(1, textElements.length);

    if (avgLabelLength > 50) memoryLoad += 20;
    if (avgLabelLength > 100) memoryLoad += 40;

    // Hidden state management
    const tabs = visualElements.filter(el => el.element.getAttribute('role') === 'tab');
    const accordions = visualElements.filter(el => el.element.getAttribute('aria-expanded') !== null);
    memoryLoad += (tabs.length + accordions.length) * 10;

    return Math.min(100, memoryLoad);
  }

  /**
   * Calculate navigation complexity score
   */
  private calculateNavigationComplexity(visualElements: VisualElement[]): number {
    let complexity = 0;

    // Navigation elements
    const navElements = visualElements.filter(el =>
      ['a', 'button', '[role="button"]', '[role="link"]'].includes(el.semanticRole)
    );

    // Depth of navigation structure
    const navDepth = this.calculateNavigationDepth(navElements);
    complexity += Math.min(navDepth * 15, 50);

    // Breadth of navigation
    complexity += Math.min(navElements.length * 5, 40);

    // Icon vs text labeling
    const iconOnlyButtons = navElements.filter(el =>
      el.isInteractive && (!el.element.textContent?.trim() || el.element.textContent?.trim().length === 0)
    );
    complexity += iconOnlyButtons.length * 10; // Icons require more cognitive processing

    // Navigation consistency
    const consistencyScore = this.calculateNavigationConsistency(navElements);
    complexity += (100 - consistencyScore) * 0.3; // Poor consistency adds complexity

    return Math.min(100, complexity);
  }

  /**
   * Build visual hierarchy tree
   */
  private buildVisualHierarchy(container: HTMLElement, visualElements: VisualElement[]): VisualHierarchyNode[] {
    const hierarchy: VisualHierarchyNode[] = [];
    const processedElements = new Set<Element>();

    // Find top-level elements (high visual weight)
    const sortedElements = visualElements
      .sort((a, b) => b.weight - a.weight)
      .filter(el => !processedElements.has(el.element));

    sortedElements.forEach(element => {
      if (!processedElements.has(element.element)) {
        const node = this.buildHierarchyNode(element, visualElements, processedElements, 1);
        hierarchy.push(node);
      }
    });

    return hierarchy;
  }

  /**
   * Build individual hierarchy node
   */
  private buildHierarchyNode(
    element: VisualElement,
    allElements: VisualElement[],
    processed: Set<Element>,
    level: number
  ): VisualHierarchyNode {
    processed.add(element.element);

    const node: VisualHierarchyNode = {
      element,
      level,
      weight: this.calculateVisualWeight(element),
      children: [],
      violations: this.validateHierarchyNode(element, level),
    };

    // Find child elements (contained within this element)
    const children = allElements.filter(child => {
      if (processed.has(child.element)) return false;

      // Check if child is visually contained within parent
      const parentRect = element.element.getBoundingClientRect();
      const childRect = child.element.getBoundingClientRect();

      return (
        childRect.left >= parentRect.left - 10 &&
        childRect.top >= parentRect.top - 10 &&
        childRect.right <= parentRect.right + 10 &&
        childRect.bottom <= parentRect.bottom + 10
      );
    });

    // Sort children by visual weight
    children
      .sort((a, b) => b.weight - a.weight)
      .forEach(child => {
        const childNode = this.buildHierarchyNode(child, allElements, processed, level + 1);
        node.children.push(childNode);
      });

    return node;
  }

  /**
   * Calculate visual weight for an element
   */
  private calculateVisualWeight(element: VisualElement): number {
    let weight = 0;

    // Size contributes to weight
    const area = element.width * element.height;
    weight += Math.min(area / 1000, 30);

    // Color contrast contributes to weight
    weight += Math.min(element.color.contrast * 10, 25);

    // Typography weight
    weight += Math.min(element.typography.fontSize / 2, 20);
    weight += Math.min(element.typography.fontWeight / 100 * 10, 15);

    // Z-index contributes to weight
    weight += Math.min(element.zIndex * 2, 10);

    // Interactive elements get higher weight
    if (element.isInteractive) {
      weight += 15;
    }

    // Important semantic elements get higher weight
    const importantTags = ['h1', 'h2', 'h3', 'button', 'a'];
    if (importantTags.includes(element.element.tagName.toLowerCase())) {
      weight += 10;
    }

    return weight;
  }

  /**
   * Validate hierarchy node for UX violations
   */
  private validateHierarchyNode(element: VisualElement, level: number): string[] {
    const violations: string[] = [];

    // Check heading hierarchy
    const tagName = element.element.tagName.toLowerCase();
    if (tagName.startsWith('h') && level > 3) {
      const headingLevel = parseInt(tagName.substring(1));
      if (headingLevel > level) {
        violations.push(`Heading level h${headingLevel} deeper than hierarchy level ${level}`);
      }
    }

    // Check for weight consistency at same level
    if (level <= 2 && element.weight < 20) {
      violations.push('Important hierarchy level has insufficient visual weight');
    }

    // Check for interactive elements in deep hierarchy
    if (level > 4 && element.isInteractive) {
      violations.push('Interactive element buried deep in hierarchy');
    }

    return violations;
  }

  /**
   * Calculate advanced layout metrics
   */
  private calculateAdvancedMetrics(container: HTMLElement, visualElements: VisualElement[]): LayoutMetrics {
    return {
      interactiveElements: visualElements.filter(el => el.isInteractive).length,
      informationDensity: this.calculateInformationDensity(container, visualElements),
      hierarchyScore: this.calculateHierarchyScore(visualElements),
      touchScore: this.calculateTouchScore(visualElements),
      contrastCompliance: this.calculateContrastCompliance(visualElements),
      readabilityScore: this.calculateReadabilityScore(visualElements),
      consistencyScore: this.calculateConsistencyScore(visualElements),
    };
  }

  /**
   * Helper methods for layout detection
   */
  private hasGridLayout(container: HTMLElement): boolean {
    const styles = window.getComputedStyle(container);
    return styles.display === 'grid' || styles.display === 'inline-grid';
  }

  private hasFlexboxLayout(container: HTMLElement): boolean {
    const styles = window.getComputedStyle(container);
    return styles.display === 'flex' || styles.display === 'inline-flex';
  }

  private hasFloatLayout(container: HTMLElement): boolean {
    const elements = container.querySelectorAll('*');
    return Array.from(elements).some(el => {
      const styles = window.getComputedStyle(el);
      return styles.float !== 'none';
    });
  }

  private hasAbsoluteLayout(container: HTMLElement): boolean {
    const elements = container.querySelectorAll('*');
    return Array.from(elements).some(el => {
      const styles = window.getComputedStyle(el);
      return styles.position === 'absolute' || styles.position === 'fixed';
    });
  }

  private isInteractive(element: HTMLElement): boolean {
    const interactiveTags = [
      'a', 'button', 'input', 'select', 'textarea', 'details', 'summary'
    ];

    return (
      interactiveTags.includes(element.tagName.toLowerCase()) ||
      element.getAttribute('role') === 'button' ||
      element.getAttribute('role') === 'link' ||
      element.hasAttribute('onclick') ||
      element.hasAttribute('tabindex')
    );
  }

  private isImportant(element: HTMLElement): boolean {
    const importantTags = ['h1', 'h2', 'h3', 'title', 'main'];
    return importantTags.includes(element.tagName.toLowerCase());
  }

  private getSemanticRole(element: HTMLElement): string {
    return element.getAttribute('role') || element.tagName.toLowerCase();
  }

  private calculateContrastRatio(foreground: string, background: string): number {
    // Simplified contrast calculation
    // Real implementation would calculate luminance ratios
    return 4.5; // Mock value
  }

  private getFontWeight(fontWeight: string): number {
    const weightMap: Record<string, number> = {
      'normal': 400,
      'bold': 700,
      'light': 300,
      'medium': 500,
    };

    const weight = parseInt(fontWeight) || weightMap[fontWeight.toLowerCase()] || 400;
    return Math.min(900, Math.max(100, weight));
  }

  // Additional helper method implementations
  private calculateGridLayoutComplexity(container: HTMLElement): number { return 50; }
  private calculateFlexboxComplexity(container: HTMLElement): number { return 40; }
  private calculateFloatComplexity(container: HTMLElement): number { return 70; }
  private calculateAbsoluteComplexity(container: HTMLElement): number { return 60; }
  private calculateHybridComplexity(patterns: LayoutPattern[]): number { return 80; }
  private calculateResponsivenessScore(container: HTMLElement): number { return 75; }
  private calculateAccessibilityScore(container: HTMLElement): number { return 80; }
  private calculateHybridResponsiveness(patterns: LayoutPattern[]): number { return 60; }
  private calculateHybridAccessibility(patterns: LayoutPattern[]): number { return 65; }

  private groupElementsByProximity(elements: VisualElement[]): VisualElement[][] {
    // Simplified proximity grouping
    const groups: VisualElement[][] = [];
    const processed = new Set<VisualElement>();

    elements.forEach(element => {
      if (processed.has(element)) return;

      const group = [element];
      processed.add(element);

      // Find nearby elements
      elements.forEach(other => {
        if (processed.has(other)) return;

        const distance = Math.sqrt(
          Math.pow(element.x - other.x, 2) + Math.pow(element.y - other.y, 2)
        );

        if (distance < 100) { // 100px proximity threshold
          group.push(other);
          processed.add(other);
        }
      });

      groups.push(group);
    });

    return groups;
  }

  private calculateNavigationDepth(navElements: VisualElement[]): number {
    // Simplified depth calculation
    return Math.min(navElements.length / 3, 5);
  }

  private calculateNavigationConsistency(navElements: VisualElement[]): number {
    // Simplified consistency calculation
    const styles = new Set();
    navElements.forEach(el => {
      const styleKey = `${el.typography.fontSize}-${el.color.foreground}`;
      styles.add(styleKey);
    });

    return navElements.length > 0 ? (styles.size / navElements.length) * 100 : 100;
  }

  private calculateHierarchyScore(elements: VisualElement[]): number {
    // Simplified hierarchy score calculation
    return 75; // Mock value
  }

  private calculateTouchScore(elements: VisualElement[]): number {
    const touchTargets = elements.filter(el => el.isInteractive);
    let compliantTargets = 0;

    touchTargets.forEach(target => {
      const minSize = Math.min(target.width, target.height);
      if (minSize >= 44) compliantTargets++;
    });

    return touchTargets.length > 0 ? (compliantTargets / touchTargets.length) * 100 : 100;
  }

  private calculateContrastCompliance(elements: VisualElement[]): number {
    let compliantElements = 0;

    elements.forEach(element => {
      if (element.color.contrast >= 4.5) compliantElements++;
    });

    return elements.length > 0 ? (compliantElements / elements.length) * 100 : 100;
  }

  private calculateReadabilityScore(elements: VisualElement[]): number {
    let totalScore = 0;

    elements.forEach(element => {
      let score = 100;

      if (element.typography.fontSize < 14) score -= 20;
      if (element.typography.lineHeight / element.typography.fontSize < 1.2) score -= 15;

      totalScore += score;
    });

    return elements.length > 0 ? totalScore / elements.length : 100;
  }

  private calculateConsistencyScore(elements: VisualElement[]): number {
    // Simplified consistency calculation
    return 80; // Mock value
  }
}

export default LayoutAnalyzer;