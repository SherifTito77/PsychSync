/**
 * 🔍 UX Usability Defect Detection System
 *
 * Automated analysis tool for identifying confusing screen layouts,
 * UX issues, and usability violations based on established UX heuristics
 * and best practices.
 */

export interface UXDefect {
  /** Unique identifier for the defect */
  id: string;
  /** Type of UX issue */
  type: UXDefectType;
  /** Severity level */
  severity: 'critical' | 'high' | 'medium' | 'low';
  /** Human-readable description */
  description: string;
  /** Component or element affected */
  element: string;
  /** Recommended fix */
  recommendation: string;
  /** WCAG guideline reference if applicable */
  wcagGuideline?: string;
  /** Specific heuristic violated */
  heuristic: string;
  /** Detection confidence (0-100) */
  confidence: number;
  /** Position/location of the issue */
  location?: {
    selector: string;
    coordinates: { x: number; y: number };
  };
}

export type UXDefectType =
  | 'visual_hierarchy'
  | 'cognitive_overload'
  | 'navigation_issue'
  | 'accessibility_violation'
  | 'touch_target_size'
  | 'color_contrast'
  | 'text_readability'
  | 'spacing_alignment'
  | 'consistency_issue'
  | 'response_feedback'
  | 'mobile_usability'
  | 'form_usability'
  | 'error_handling'
  | 'information_architecture';

export interface LayoutAnalysis {
  /** Component being analyzed */
  component: string;
  /** Overall usability score (0-100) */
  usabilityScore: number;
  /** Total number of defects found */
  totalDefects: number;
  /** Breakdown by severity */
  severityBreakdown: Record<string, number>;
  /** Detected defects */
  defects: UXDefect[];
  /** Layout metrics */
  metrics: LayoutMetrics;
}

export interface LayoutMetrics {
  /** Number of interactive elements */
  interactiveElements: number;
  /** Information density score */
  informationDensity: number;
  /** Visual hierarchy score */
  hierarchyScore: number;
  /** Touch accessibility score */
  touchScore: number;
  /** Color contrast compliance */
  contrastCompliance: number;
  /** Text readability score */
  readabilityScore: number;
  /** Consistency score */
  consistencyScore: number;
}

export class UXUsabilityDefectDetector {
  private heuristics = {
    visibility: 'System status should always be visible',
    match: 'System should match real world',
    userControl: 'User control and freedom',
    consistency: 'Consistency and standards',
    errorPrevention: 'Error prevention',
    recognition: 'Recognition rather than recall',
    flexibility: 'Flexibility and efficiency of use',
    aesthetic: 'Aesthetic and minimalist design',
    errorRecovery: 'Help users recognize, diagnose, and recover from errors',
    help: 'Help and documentation',
  };

  private colorContrastRatios = {
    normalText: 4.5,
    largeText: 3.0,
    nonText: 3.0,
  };

  private touchTargetSizes = {
    minimum: 44, // 44px minimum for WCAG
    recommended: 48, // 48px recommended
    spacing: 8, // 8px minimum spacing between targets
  };

  /**
   * Analyze a React component for UX defects
   */
  async analyzeLayout(componentName: string, container: HTMLElement): Promise<LayoutAnalysis> {
    const defects: UXDefect[] = [];
    const metrics = await this.calculateLayoutMetrics(container);

    // Run all defect detection algorithms
    defects.push(...this.detectVisualHierarchyIssues(container, componentName));
    defects.push(...this.detectCognitiveOverload(container, componentName));
    defects.push(...this.detectNavigationIssues(container, componentName));
    defects.push(...this.detectAccessibilityViolations(container, componentName));
    defects.push(...this.detectTouchTargetIssues(container, componentName));
    defects.push(...this.detectColorContrastIssues(container, componentName));
    defects.push(...this.detectTextReadabilityIssues(container, componentName));
    defects.push(...this.detectSpacingAlignmentIssues(container, componentName));
    defects.push(...this.detectConsistencyIssues(container, componentName));
    defects.push(...this.detectResponseFeedbackIssues(container, componentName));
    defects.push(...this.detectMobileUsabilityIssues(container, componentName));
    defects.push(...this.detectFormUsabilityIssues(container, componentName));
    defects.push(...this.detectErrorHandlingIssues(container, componentName));
    defects.push(...this.detectInformationArchitectureIssues(container, componentName));

    const severityBreakdown = this.calculateSeverityBreakdown(defects);
    const usabilityScore = this.calculateUsabilityScore(defects, metrics);

    return {
      component: componentName,
      usabilityScore,
      totalDefects: defects.length,
      severityBreakdown,
      defects,
      metrics,
    };
  }

  /**
   * Calculate comprehensive layout metrics
   */
  private async calculateLayoutMetrics(container: HTMLElement): Promise<LayoutMetrics> {
    const interactiveElements = container.querySelectorAll(
      'button, a, input, select, textarea, [role="button"], [onclick]'
    ).length;

    const allElements = container.querySelectorAll('*').length;
    const textNodes = this.getTextNodes(container).length;

    return {
      interactiveElements,
      informationDensity: this.calculateInformationDensity(allElements, textNodes),
      hierarchyScore: this.calculateHierarchyScore(container),
      touchScore: this.calculateTouchScore(container),
      contrastCompliance: this.calculateContrastCompliance(container),
      readabilityScore: this.calculateReadabilityScore(container),
      consistencyScore: this.calculateConsistencyScore(container),
    };
  }

  /**
   * Detect visual hierarchy issues
   */
  private detectVisualHierarchyIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for proper heading structure
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
    if (headings.length === 0) {
      defects.push(this.createDefect(
        'visual_hierarchy',
        'high',
        'No heading elements found - content lacks clear structure',
        'page',
        'Add appropriate heading elements (h1-h6) to establish content hierarchy',
        '1.3.1',
        'Information and relationships',
        85
      ));
    }

    // Check heading order
    let previousLevel = 0;
    headings.forEach((heading, index) => {
      const currentLevel = parseInt(heading.tagName.substring(1));
      if (currentLevel > previousLevel + 1) {
        defects.push(this.createDefect(
          'visual_hierarchy',
          'medium',
          `Skipped heading level: h${previousLevel} to h${currentLevel}`,
          `h${currentLevel}`,
          'Use proper heading hierarchy without skipping levels',
          '1.3.1',
          'Information and relationships',
          75
        ));
      }
      previousLevel = currentLevel;
    });

    // Check for insufficient visual weight differentiation
    const textElements = container.querySelectorAll('p, span, div');
    const fontSizes = new Set<number>();

    textElements.forEach(element => {
      const fontSize = parseFloat(window.getComputedStyle(element).fontSize);
      if (fontSize > 0) fontSizes.add(Math.round(fontSize));
    });

    if (fontSizes.size === 1 && textElements.length > 3) {
      defects.push(this.createDefect(
        'visual_hierarchy',
        'medium',
        'All text elements have the same font size - lacks visual hierarchy',
        'content',
        'Use different font sizes or weights to establish visual hierarchy',
        '1.4.8',
        'Visual presentation',
        70
      ));
    }

    return defects;
  }

  /**
   * Detect cognitive overload issues
   */
  private detectCognitiveOverload(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Count interactive elements
    const interactiveElements = container.querySelectorAll(
      'button, a, input, select, textarea, [role="button"]'
    ).length;

    // Too many choices can cause decision paralysis
    if (interactiveElements > 15) {
      defects.push(this.createDefect(
        'cognitive_overload',
        'high',
        `Too many interactive elements (${interactiveElements}) - may overwhelm users`,
        'navigation',
        'Group related actions or use progressive disclosure',
        '3.3.4',
        'Error prevention',
        90
      ));
    }

    // Check for dense information layout
    const allElements = container.querySelectorAll('*').length;
    const containerArea = container.offsetWidth * container.offsetHeight;
    const density = allElements / (containerArea / 10000); // elements per 100x100px

    if (density > 50) {
      defects.push(this.createDefect(
        'cognitive_overload',
        'high',
        'Information density too high - layout appears cluttered',
        'layout',
        'Increase whitespace and use progressive disclosure',
        '1.4.8',
        'Visual presentation',
        85
      ));
    }

    // Check for excessive text blocks
    const textBlocks = container.querySelectorAll('p, div');
    textBlocks.forEach(element => {
      const text = element.textContent?.trim() || '';
      const wordCount = text.split(/\s+/).length;

      if (wordCount > 100) {
        defects.push(this.createDefect(
          'cognitive_overload',
          'medium',
          `Long text block (${wordCount} words) - difficult to scan`,
          'content',
          'Break long text into shorter paragraphs or use bullet points',
          '1.4.8',
          'Visual presentation',
          80
        ));
      }
    });

    return defects;
  }

  /**
   * Detect navigation issues
   */
  private detectNavigationIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for missing navigation landmarks
    const hasNav = container.querySelector('nav, [role="navigation"]');
    const hasMain = container.querySelector('main, [role="main"]');
    const hasHeader = container.querySelector('header, [role="banner"]');
    const hasFooter = container.querySelector('footer, [role="contentinfo"]');

    if (!hasMain && componentName.toLowerCase().includes('dashboard')) {
      defects.push(this.createDefect(
        'navigation_issue',
        'high',
        'Missing main content landmark - poor navigation structure',
        'structure',
        'Add main landmark or role="main" to main content area',
        '1.3.6',
        'Identify purpose',
        95
      ));
    }

    // Check for unclear navigation labels
    const links = container.querySelectorAll('a, button');
    links.forEach(element => {
      const text = element.textContent?.trim();

      if (!text || text.length < 3) {
        defects.push(this.createDefect(
          'navigation_issue',
          'medium',
          'Unclear navigation label - poor usability',
          element.tagName.toLowerCase(),
          'Add descriptive text to navigation elements',
          '2.4.6',
          'Headings and labels',
          75
        ));
      }

      // Check for generic labels
      const genericLabels = ['click here', 'learn more', 'submit', 'ok', 'cancel'];
      if (genericLabels.some(label => text?.toLowerCase().includes(label))) {
        defects.push(this.createDefect(
          'navigation_issue',
          'low',
          `Generic navigation label: "${text}"`,
          element.tagName.toLowerCase(),
          'Use specific, descriptive action labels',
          '2.4.6',
          'Headings and labels',
          65
        ));
      }
    });

    return defects;
  }

  /**
   * Detect accessibility violations
   */
  private detectAccessibilityViolations(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for missing alt text on images
    const images = container.querySelectorAll('img');
    images.forEach((img, index) => {
      if (!img.alt && !img.getAttribute('aria-label')) {
        defects.push(this.createDefect(
          'accessibility_violation',
          'high',
          `Missing alt text on image ${index + 1}`,
          'img',
          'Add descriptive alt text or mark as decorative with alt=""',
          '1.1.1',
          'Non-text content',
          95
        ));
      }
    });

    // Check for form labels
    const inputs = container.querySelectorAll('input, select, textarea');
    inputs.forEach((input, index) => {
      const htmlInput = input as HTMLInputElement;
      const hasLabel = htmlInput.getAttribute('aria-label') ||
                      htmlInput.getAttribute('aria-labelledby') ||
                      container.querySelector(`label[for="${htmlInput.id}"]`);

      if (!hasLabel && htmlInput.type !== 'hidden') {
        defects.push(this.createDefect(
          'accessibility_violation',
          'high',
          `Form input ${index + 1} missing associated label`,
          'input',
          'Add label element or aria-label/aria-labelledby',
          '3.3.2',
          'Labels or instructions',
          90
        ));
      }
    });

    // Check for focus management
    const focusableElements = container.querySelectorAll(
      'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    focusableElements.forEach((element, index) => {
      const styles = window.getComputedStyle(element);
      const hasFocusStyles = styles.outline !== 'none' || styles.boxShadow !== 'none';

      if (!hasFocusStyles) {
        defects.push(this.createDefect(
          'accessibility_violation',
          'medium',
          `Focusable element ${index + 1} lacks visible focus indicator`,
          element.tagName.toLowerCase(),
          'Add visible focus styles (outline, box-shadow, etc.)',
          '2.4.7',
          'Focus visible',
          80
        ));
      }
    });

    return defects;
  }

  /**
   * Detect touch target size issues
   */
  private detectTouchTargetIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check touch target sizes for interactive elements
    const touchTargets = container.querySelectorAll(
      'button, a, input[type="checkbox"], input[type="radio"], [role="button"]'
    );

    touchTargets.forEach((element, index) => {
      const rect = element.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;
      const minSize = Math.min(width, height);

      if (minSize < this.touchTargetSizes.minimum) {
        defects.push(this.createDefect(
          'touch_target_size',
          'high',
          `Touch target ${index + 1} too small (${Math.round(minSize)}px < 44px)`,
          element.tagName.toLowerCase(),
          'Increase touch target size to minimum 44x44px',
          '2.5.5',
          'Target size',
          95
        ));
      } else if (minSize < this.touchTargetSizes.recommended) {
        defects.push(this.createDefect(
          'touch_target_size',
          'medium',
          `Touch target ${index + 1} smaller than recommended (${Math.round(minSize)}px < 48px)`,
          element.tagName.toLowerCase(),
          'Increase touch target to recommended 48x48px for better UX',
          '2.5.5',
          'Target size',
          70
        ));
      }
    });

    // Check spacing between touch targets
    for (let i = 0; i < touchTargets.length - 1; i++) {
      const element1 = touchTargets[i];
      const element2 = touchTargets[i + 1];

      const rect1 = element1.getBoundingClientRect();
      const rect2 = element2.getBoundingClientRect();

      const horizontalSpacing = Math.abs(rect1.left - rect2.left);
      const verticalSpacing = Math.abs(rect1.top - rect2.top);
      const minSpacing = Math.min(horizontalSpacing, verticalSpacing);

      if (minSpacing < this.touchTargetSizes.spacing) {
        defects.push(this.createDefect(
          'touch_target_size',
          'medium',
          `Insufficient spacing between touch targets (${Math.round(minSpacing)}px < 8px)`,
          'touch_targets',
          'Increase spacing between interactive elements to minimum 8px',
          '2.5.5',
          'Target size',
          75
        ));
      }
    }

    return defects;
  }

  /**
   * Detect color contrast issues
   */
  private detectColorContrastIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // This is a simplified check - in real implementation, you'd need
    // sophisticated color analysis tools
    const textElements = container.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, label');

    textElements.forEach((element, index) => {
      const styles = window.getComputedStyle(element);
      const fontSize = parseFloat(styles.fontSize);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;

      // Skip transparent backgrounds (they inherit from parent)
      if (backgroundColor === 'rgba(0, 0, 0, 0)' || backgroundColor === 'transparent') {
        return;
      }

      // Simple heuristic for potential contrast issues
      const isLightText = this.isLightColor(color);
      const isLightBackground = this.isLightColor(backgroundColor);

      if (isLightText && isLightBackground) {
        defects.push(this.createDefect(
          'color_contrast',
          'high',
          `Potential color contrast issue: light text on light background`,
          element.tagName.toLowerCase(),
          'Ensure sufficient color contrast (4.5:1 for normal text, 3:1 for large text)',
          '1.4.3',
          'Contrast',
          85
        ));
      } else if (!isLightText && !isLightBackground) {
        defects.push(this.createDefect(
          'color_contrast',
          'high',
          `Potential color contrast issue: dark text on dark background`,
          element.tagName.toLowerCase(),
          'Ensure sufficient color contrast (4.5:1 for normal text, 3:1 for large text)',
          '1.4.3',
          'Contrast',
          85
        ));
      }
    });

    return defects;
  }

  /**
   * Detect text readability issues
   */
  private detectTextReadabilityIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    const textElements = container.querySelectorAll('p, span, div, label');

    textElements.forEach((element, index) => {
      const styles = window.getComputedStyle(element);
      const fontSize = parseFloat(styles.fontSize);
      const lineHeight = parseFloat(styles.lineHeight);
      const letterSpacing = parseFloat(styles.letterSpacing);

      // Check font size
      if (fontSize < 14) {
        defects.push(this.createDefect(
          'text_readability',
          'medium',
          `Text too small (${Math.round(fontSize)}px < 14px)`,
          element.tagName.toLowerCase(),
          'Use minimum 14px font size for better readability',
          '1.4.4',
          'Resize text',
          75
        ));
      }

      // Check line height
      const lineHeightRatio = lineHeight / fontSize;
      if (lineHeightRatio < 1.2) {
        defects.push(this.createDefect(
          'text_readability',
          'low',
          `Line height too tight (${lineHeightRatio.toFixed(2)} < 1.2)`,
          element.tagName.toLowerCase(),
          'Increase line height to at least 1.2x font size',
          '1.4.8',
          'Visual presentation',
          65
        ));
      } else if (lineHeightRatio > 2) {
        defects.push(this.createDefect(
          'text_readability',
          'low',
          `Line height too loose (${lineHeightRatio.toFixed(2)} > 2.0)`,
          element.tagName.toLowerCase(),
          'Reduce line height to improve readability',
          '1.4.8',
          'Visual presentation',
          60
        ));
      }

      // Check for text justification (can cause readability issues)
      if (styles.textAlign === 'justify') {
        defects.push(this.createDefect(
          'text_readability',
          'low',
          'Text justification can create "rivers" and reduce readability',
          element.tagName.toLowerCase(),
          'Consider using left or right alignment instead of justified text',
          '1.4.8',
          'Visual presentation',
          55
        ));
      }
    });

    return defects;
  }

  /**
   * Detect spacing and alignment issues
   */
  private detectSpacingAlignmentIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for elements without proper spacing
    const elements = container.children;

    for (let i = 0; i < elements.length - 1; i++) {
      const element1 = elements[i];
      const element2 = elements[i + 1];

      const rect1 = element1.getBoundingClientRect();
      const rect2 = element2.getBoundingClientRect();

      // Check vertical spacing
      const verticalSpacing = rect2.top - (rect1.top + rect1.height);

      if (verticalSpacing < 8 && !this.isTextFlow(element1, element2)) {
        defects.push(this.createDefect(
          'spacing_alignment',
          'medium',
          `Insufficient vertical spacing (${Math.round(verticalSpacing)}px < 8px)`,
          'layout',
          'Increase spacing between elements for better visual separation',
          '1.4.8',
          'Visual presentation',
          70
        ));
      }
    }

    // Check for alignment inconsistencies
    const flexContainers = container.querySelectorAll('[style*="display: flex"], .flex');
    flexContainers.forEach((container, index) => {
      const styles = window.getComputedStyle(container);
      const justifyContent = styles.justifyContent;

      if (justifyContent === 'flex-start') {
        // Check if child elements are properly aligned
        const children = container.children;
        const firstChildLeft = children[0]?.getBoundingClientRect().left;

        for (let i = 1; i < children.length; i++) {
          const childLeft = children[i]?.getBoundingClientRect().left;
          if (Math.abs(childLeft - firstChildLeft) > 2) {
            defects.push(this.createDefect(
              'spacing_alignment',
              'low',
              'Inconsistent left alignment in flex container',
              'flex_container',
              'Use consistent alignment for flex container children',
              '1.4.10',
              'Reflow',
              60
            ));
            break;
          }
        }
      }
    });

    return defects;
  }

  /**
   * Detect consistency issues
   */
  private detectConsistencyIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for inconsistent button styles
    const buttons = container.querySelectorAll('button, [role="button"]');
    const buttonStyles = new Map<string, number>();

    buttons.forEach(button => {
      const styles = window.getComputedStyle(button);
      const styleKey = `${styles.backgroundColor}-${styles.color}-${styles.fontSize}-${styles.padding}`;
      buttonStyles.set(styleKey, (buttonStyles.get(styleKey) || 0) + 1);
    });

    if (buttonStyles.size > 3) {
      defects.push(this.createDefect(
        'consistency_issue',
        'medium',
        `Inconsistent button styling (${buttonStyles.size} different styles)`,
        'buttons',
        'Use consistent button styling across the interface',
        '3.2.4',
        'Consistency',
        75
      ));
    }

    // Check for inconsistent link styling
    const links = container.querySelectorAll('a[href]');
    const linkStyles = new Map<string, number>();

    links.forEach(link => {
      const styles = window.getComputedStyle(link);
      const styleKey = `${styles.color}-${styles.textDecoration}-${styles.fontSize}`;
      linkStyles.set(styleKey, (linkStyles.get(styleKey) || 0) + 1);
    });

    if (linkStyles.size > 2) {
      defects.push(this.createDefect(
        'consistency_issue',
        'low',
        `Inconsistent link styling (${linkStyles.size} different styles)`,
        'links',
        'Use consistent link styling (standard underlined blue links)',
        '3.2.4',
        'Consistency',
        60
      ));
    }

    return defects;
  }

  /**
   * Detect response and feedback issues
   */
  private detectResponseFeedbackIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for loading indicators
    const loadingElements = container.querySelectorAll('[loading], .loading, [aria-busy="true"]');
    if (loadingElements.length === 0 && componentName.toLowerCase().includes('form')) {
      defects.push(this.createDefect(
        'response_feedback',
        'medium',
        'No loading indicators found for form submissions',
        'forms',
        'Add loading states for async operations',
        '4.2.2',
        'Inputs',
        70
      ));
    }

    // Check for error message containers
    const errorElements = container.querySelectorAll('.error, [role="alert"]');
    if (errorElements.length === 0 && componentName.toLowerCase().includes('form')) {
      defects.push(this.createDefect(
        'response_feedback',
        'high',
        'No error message containers found for form validation',
        'forms',
        'Add error message display for form validation',
        '3.3.1',
        'Error identification',
        85
      ));
    }

    // Check for success feedback
    const successElements = container.querySelectorAll('.success, .confirmation');
    if (successElements.length === 0 && componentName.toLowerCase().includes('form')) {
      defects.push(this.createDefect(
        'response_feedback',
        'medium',
        'No success feedback found for completed actions',
        'actions',
        'Add success messages or confirmations for completed actions',
        '4.1.3',
        'Status messages',
        65
      ));
    }

    return defects;
  }

  /**
   * Detect mobile usability issues
   */
  private detectMobileUsabilityIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Simulate mobile viewport
    const originalWidth = container.style.width;
    container.style.width = '375px'; // iPhone width

    // Check for horizontal scrolling on mobile
    const containerWidth = container.scrollWidth;
    const viewportWidth = container.offsetWidth;

    if (containerWidth > viewportWidth) {
      defects.push(this.createDefect(
        'mobile_usability',
        'high',
        'Horizontal scrolling on mobile viewport (375px)',
        'layout',
        'Design responsive layout that fits within mobile viewport width',
        '1.4.10',
        'Reflow',
        95
      ));
    }

    // Check for viewport meta tag
    const hasViewportMeta = document.querySelector('meta[name="viewport"]');
    if (!hasViewportMeta) {
      defects.push(this.createDefect(
        'mobile_usability',
        'critical',
        'Missing viewport meta tag for mobile optimization',
        'head',
        'Add viewport meta tag: <meta name="viewport" content="width=device-width, initial-scale=1">',
        '1.4.10',
        'Reflow',
        100
      ));
    }

    container.style.width = originalWidth; // Restore original width

    return defects;
  }

  /**
   * Detect form usability issues
   */
  private detectFormUsabilityIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for form elements
    const forms = container.querySelectorAll('form');
    if (forms.length === 0 && componentName.toLowerCase().includes('form')) {
      return defects; // Skip if no forms found
    }

    forms.forEach((form, formIndex) => {
      // Check for clear submit buttons
      const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
      if (submitButtons.length === 0) {
        defects.push(this.createDefect(
          'form_usability',
          'high',
          `Form ${formIndex + 1} missing submit button`,
          'form',
          'Add clear submit button for form completion',
          '3.2.2',
          'On input',
          85
        ));
      }

      // Check for required field indicators
      const requiredFields = form.querySelectorAll('[required], [aria-required="true"]');
      const requiredIndicators = form.querySelectorAll('.required, [aria-label*="required"]');

      if (requiredFields.length > requiredIndicators.length) {
        defects.push(this.createDefect(
          'form_usability',
          'medium',
          `Required fields lack visual indicators in form ${formIndex + 1}`,
          'form',
          'Add visual indicators (asterisks) for required fields',
          '3.3.2',
          'Labels or instructions',
          75
        ));
      }

      // Check for input validation feedback
      const inputFields = form.querySelectorAll('input, select, textarea');
      inputFields.forEach((field, fieldIndex) => {
        const hasValidation = field.getAttribute('pattern') ||
                             field.getAttribute('minlength') ||
                             field.getAttribute('maxlength') ||
                             field.getAttribute('required');

        if (hasValidation) {
          const validationMessage = field.getAttribute('aria-describedby') ||
                                   form.querySelector(`[for="${field.id}"] + .error-message`);

          if (!validationMessage) {
            defects.push(this.createDefect(
              'form_usability',
              'medium',
              `Input field ${fieldIndex + 1} has validation but no error message container`,
              'form',
              'Add error message container for validation feedback',
              '3.3.1',
              'Error identification',
              70
            ));
          }
        }
      });
    });

    return defects;
  }

  /**
   * Detect error handling issues
   */
  private detectErrorHandlingIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for generic error messages
    const errorElements = container.querySelectorAll('.error, .alert-error');
    errorElements.forEach((element, index) => {
      const text = element.textContent?.trim();

      if (text && (
        text.toLowerCase().includes('an error occurred') ||
        text.toLowerCase().includes('something went wrong') ||
        text.toLowerCase().includes('error') && text.length < 20
      )) {
        defects.push(this.createDefect(
          'error_handling',
          'high',
          `Generic error message: "${text}"`,
          'error_message',
          'Provide specific, actionable error messages',
          '3.3.1',
          'Error identification',
          90
        ));
      }
    });

    // Check for missing recovery options
    const errorContainers = container.querySelectorAll('[role="alert"], .error');
    errorContainers.forEach((container, index) => {
      const hasRecoveryAction = container.querySelector('button, a') ||
                              container.nextElementSibling?.querySelector('button, a');

      if (!hasRecoveryAction && !container.textContent?.toLowerCase().includes('refresh')) {
        defects.push(this.createDefect(
          'error_handling',
          'medium',
          `Error container ${index + 1} lacks recovery action`,
          'error_container',
          'Provide action buttons or recovery options for errors',
          '3.3.3',
          'Error suggestion',
          75
        ));
      }
    });

    return defects;
  }

  /**
   * Detect information architecture issues
   */
  private detectInformationArchitectureIssues(container: HTMLElement, componentName: string): UXDefect[] {
    const defects: UXDefect[] = [];

    // Check for grouping of related content
    const relatedContentGroups = new Map<string, Element[]>();
    const allElements = container.querySelectorAll('div, section, article');

    // Simple heuristic: group by similar content patterns
    allElements.forEach(element => {
      const text = element.textContent?.trim().toLowerCase() || '';
      const keywords = text.split(/\s+/).filter(word => word.length > 3);

      keywords.forEach(keyword => {
        if (!relatedContentGroups.has(keyword)) {
          relatedContentGroups.set(keyword, []);
        }
        relatedContentGroups.get(keyword)!.push(element);
      });
    });

    // Look for potential grouping issues
    relatedContentGroups.forEach((elements, keyword) => {
      if (elements.length > 1) {
        // Check if related elements are visually grouped
        const firstParent = elements[0].parentElement;
        const allSameParent = elements.every(el => el.parentElement === firstParent);

        if (!allSameParent) {
          defects.push(this.createDefect(
            'information_architecture',
            'medium',
            `Related content not grouped: "${keyword}" appears in multiple sections`,
            'content',
            'Group related content in same container or section',
            '1.3.1',
            'Information and relationships',
            70
          ));
        }
      }
    });

    // Check for deep nesting
    const maxDepth = this.getMaxNestingDepth(container);
    if (maxDepth > 6) {
      defects.push(this.createDefect(
        'information_architecture',
        'low',
        `Deep nesting detected (depth ${maxDepth}) - may affect scannability`,
        'structure',
        'Reduce nesting depth to improve content scannability',
        '1.4.10',
        'Reflow',
        60
      ));
    }

    return defects;
  }

  /**
   * Helper methods for calculations and utilities
   */
  private createDefect(
    type: UXDefectType,
    severity: 'critical' | 'high' | 'medium' | 'low',
    description: string,
    element: string,
    recommendation: string,
    heuristic: string,
    wcagGuideline: string,
    confidence: number
  ): UXDefect {
    return {
      id: `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      severity,
      description,
      element,
      recommendation,
      wcagGuideline,
      heuristic,
      confidence,
    };
  }

  private getTextNodes(container: HTMLElement): Node[] {
    const textNodes: Node[] = [];
    const walker = document.createTreeWalker(
      container,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          // Skip empty text nodes and whitespace-only nodes
          return node.textContent?.trim().length ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
        }
      } as NodeFilter
    );

    let node;
    while ((node = walker.nextNode())) {
      if (node.textContent?.trim()) {
        textNodes.push(node);
      }
    }

    return textNodes;
  }

  private calculateInformationDensity(allElements: number, textNodes: number): number {
    return Math.min(100, (allElements / Math.max(1, textNodes)) * 10);
  }

  private calculateHierarchyScore(container: HTMLElement): number {
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6').length;
    const allElements = container.querySelectorAll('*').length;

    if (allElements === 0) return 0;
    return Math.min(100, (headings / allElements) * 100);
  }

  private calculateTouchScore(container: HTMLElement): number {
    const touchTargets = container.querySelectorAll(
      'button, a, input[type="checkbox"], input[type="radio"], [role="button"]'
    );

    let compliantTargets = 0;
    touchTargets.forEach(element => {
      const rect = element.getBoundingClientRect();
      const minSize = Math.min(rect.width, rect.height);
      if (minSize >= this.touchTargetSizes.minimum) {
        compliantTargets++;
      }
    });

    return touchTargets.length === 0 ? 100 : (compliantTargets / touchTargets.length) * 100;
  }

  private calculateContrastCompliance(container: HTMLElement): number {
    // Simplified implementation - real version would calculate actual contrast ratios
    return 85; // Mock value
  }

  private calculateReadabilityScore(container: HTMLElement): number {
    const textElements = container.querySelectorAll('p, span, div');
    let totalScore = 0;

    textElements.forEach(element => {
      const styles = window.getComputedStyle(element);
      const fontSize = parseFloat(styles.fontSize);
      const lineHeight = parseFloat(styles.lineHeight);

      let score = 100;
      if (fontSize < 14) score -= 20;
      if (lineHeight / fontSize < 1.2) score -= 15;
      if (lineHeight / fontSize > 2) score -= 10;

      totalScore += score;
    });

    return textElements.length === 0 ? 100 : totalScore / textElements.length;
  }

  private calculateConsistencyScore(container: HTMLElement): number {
    // Simplified implementation - real version would compare styling consistency
    return 80; // Mock value
  }

  private calculateSeverityBreakdown(defects: UXDefect[]): Record<string, number> {
    return defects.reduce((acc, defect) => {
      acc[defect.severity] = (acc[defect.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  private calculateUsabilityScore(defects: UXDefect[], metrics: LayoutMetrics): number {
    const severityWeights = { critical: 25, high: 15, medium: 8, low: 3 };
    const penalty = defects.reduce((total, defect) => {
      return total + (severityWeights[defect.severity] || 0);
    }, 0);

    const baseScore = 100;
    const metricBonus = (
      metrics.hierarchyScore * 0.2 +
      metrics.touchScore * 0.2 +
      metrics.contrastCompliance * 0.2 +
      metrics.readabilityScore * 0.2 +
      metrics.consistencyScore * 0.2
    ) / 100;

    return Math.max(0, baseScore - penalty + (metricBonus * 10));
  }

  private isLightColor(color: string): boolean {
    // Simplified color analysis - real implementation would convert RGB to luminance
    const isLight = color.includes('rgb(255') ||
                    color.includes('white') ||
                    color.includes('#fff') ||
                    color.includes('#ffff');
    return isLight;
  }

  private isTextFlow(element1: Element, element2: Element): boolean {
    // Check if elements are likely in text flow (paragraph, span, etc.)
    const textTags = ['p', 'span', 'div', 'strong', 'em', 'i', 'b'];
    return textTags.includes(element1.tagName.toLowerCase()) &&
           textTags.includes(element2.tagName.toLowerCase());
  }

  private getMaxNestingDepth(element: Element, currentDepth = 0): number {
    if (element.children.length === 0) {
      return currentDepth;
    }

    let maxDepth = currentDepth;
    for (const child of element.children) {
      const childDepth = this.getMaxNestingDepth(child, currentDepth + 1);
      maxDepth = Math.max(maxDepth, childDepth);
    }

    return maxDepth;
  }

  /**
   * Generate a comprehensive UX defect report
   */
  generateReport(analyses: LayoutAnalysis[]): string {
    const totalDefects = analyses.reduce((sum, analysis) => sum + analysis.totalDefects, 0);
    const averageScore = analyses.reduce((sum, analysis) => sum + analysis.usabilityScore, 0) / analyses.length;

    const allDefects = analyses.flatMap(analysis => analysis.defects);
    const severityCounts = allDefects.reduce((acc, defect) => {
      acc[defect.severity] = (acc[defect.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    let report = `# 🔍 UX Usability Defect Report\n\n`;
    report += `**Generated**: ${new Date().toLocaleString()}\n`;
    report += `**Components Analyzed**: ${analyses.length}\n`;
    report += `**Total Defects**: ${totalDefects}\n`;
    report += `**Average Usability Score**: ${averageScore.toFixed(1)}%\n\n`;

    report += `## 📊 Severity Breakdown\n\n`;
    Object.entries(severityCounts).forEach(([severity, count]) => {
      report += `- **${severity.charAt(0).toUpperCase() + severity.slice(1)}**: ${count} defects\n`;
    });

    report += `\n## 🎯 Component Analysis\n\n`;
    analyses.forEach(analysis => {
      report += `### ${analysis.component}\n`;
      report += `- **Usability Score**: ${analysis.usabilityScore.toFixed(1)}%\n`;
      report += `- **Defects**: ${analysis.totalDefects}\n`;

      if (analysis.defects.length > 0) {
        report += `\n**Top Issues**:\n`;
        analysis.defects
          .sort((a, b) => b.confidence - a.confidence)
          .slice(0, 3)
          .forEach(defect => {
            report += `- ${defect.description} (${defect.severity})\n`;
          });
      }
      report += '\n';
    });

    return report;
  }
}

export default UXUsabilityDefectDetector;
