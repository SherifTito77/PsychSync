/**
 * iOS Safari vs Android Chrome Compatibility Analysis
 * Detects and resolves platform-specific list rendering differences
 */

export interface BrowserInfo {
  userAgent: string;
  platform: 'ios' | 'android' | 'desktop' | 'unknown';
  browser: 'safari' | 'chrome' | 'firefox' | 'edge' | 'unknown';
  version: string;
  engine: 'webkit' | 'blink' | 'gecko' | 'unknown';
  capabilities: {
    scrollBehavior: 'smooth' | 'standard' | 'jerky';
    touchEvents: 'native' | 'emulated' | 'hybrid';
    cssSupport: Record<string, boolean>;
    performance: 'excellent' | 'good' | 'fair' | 'poor';
  };
}

export interface CompatibilityIssue {
  id: string;
  platform: 'ios' | 'android' | 'both';
  severity: 'critical' | 'major' | 'minor';
  category: 'scrolling' | 'touch' | 'css' | 'performance' | 'interaction';
  title: string;
  description: string;
  symptoms: string[];
  solution: string;
  cssFix?: string;
  javascriptFix?: string;
  workaround?: string;
}

export class MobileBrowserCompatibility {
  private issues: CompatibilityIssue[] = [];
  private browserInfo: BrowserInfo;

  constructor() {
    this.browserInfo = this.detectBrowser();
    this.issues = this.identifyCompatibilityIssues();
  }

  /**
   * Detect current browser and platform
   */
  private detectBrowser(): BrowserInfo {
    const userAgent = navigator.userAgent;
    const platform = this.detectPlatform(userAgent);
    const browser = this.detectBrowserName(userAgent);
    const version = this.detectVersion(userAgent, browser);
    const engine = this.detectEngine(browser, userAgent);

    return {
      userAgent,
      platform,
      browser,
      version,
      engine,
      capabilities: this.assessCapabilities(platform, browser, version)
    };
  }

  private detectPlatform(userAgent: string): 'ios' | 'android' | 'desktop' | 'unknown' {
    if (/iPad|iPhone|iPod/.test(userAgent)) return 'ios';
    if (/Android/.test(userAgent)) return 'android';
    if (/Win|Mac|Linux/.test(userAgent) && !/Mobile/.test(userAgent)) return 'desktop';
    return 'unknown';
  }

  private detectBrowserName(userAgent: string): 'safari' | 'chrome' | 'firefox' | 'edge' | 'unknown' {
    if (/CriOS/i.test(userAgent) || /Chrome/.test(userAgent)) return 'chrome';
    if (/Safari/i.test(userAgent) && !/Chrome/.test(userAgent)) return 'safari';
    if (/Firefox/i.test(userAgent)) return 'firefox';
    if (/Edg/i.test(userAgent)) return 'edge';
    return 'unknown';
  }

  private detectVersion(userAgent: string, browser: string): string {
    const patterns = {
      safari: /Version\/(\d+(?:\.\d+)?)/i,
      chrome: /Chrome\/(\d+(?:\.\d+)?)/i,
      firefox: /Firefox\/(\d+(?:\.\d+)?)/i,
      edge: /Edg\/(\d+(?:\.\d+)?)/i
    };

    const match = userAgent.match(patterns[browser as keyof typeof patterns]);
    return match ? match[1] : 'unknown';
  }

  private detectEngine(browser: string, userAgent: string): 'webkit' | 'blink' | 'gecko' | 'unknown' {
    if (browser === 'safari') return 'webkit';
    if (browser === 'chrome' || browser === 'edge') return 'blink';
    if (browser === 'firefox') return 'gecko';
    return 'unknown';
  }

  private assessCapabilities(
    platform: string,
    browser: string,
    version: string
  ): BrowserInfo['capabilities'] {
    const isModern = this.isModernVersion(version);

    return {
      scrollBehavior: platform === 'ios' ? (isModern ? 'smooth' : 'jerky') : 'standard',
      touchEvents: platform === 'ios' ? 'native' : 'hybrid',
      cssSupport: this.getCSSSupport(platform, browser, version),
      performance: this.assessPerformance(platform, browser, version)
    };
  }

  private isModernVersion(version: string): boolean {
    if (version === 'unknown') return false;
    const [major] = version.split('.').map(Number);
    return major >= 14; // iOS 14+ and Chrome 90+
  }

  private getCSSSupport(
    platform: string,
    browser: string,
    version: string
  ): Record<string, boolean> {
    const isModern = this.isModernVersion(version);

    return {
      // Modern CSS features
      'scroll-behavior': browser === 'chrome' || (browser === 'safari' && isModern),
      'backdrop-filter': browser === 'safari' || (browser === 'chrome' && isModern),
      'css-grid': isModern,
      'flexbox-gap': browser === 'safari' ? isModern : true,
      'position-sticky': isModern,
      'overscroll-behavior': browser === 'chrome',
      'webkit-overflow-scrolling': browser === 'safari',
      'touch-action': browser === 'chrome' || (browser === 'safari' && isModern),
      // iOS specific
      '-webkit-appearance': browser === 'safari',
      '-webkit-tap-highlight-color': browser === 'safari',
      '-webkit-overflow-scrolling': browser === 'safari'
    };
  }

  private assessPerformance(
    platform: string,
    browser: string,
    version: string
  ): 'excellent' | 'good' | 'fair' | 'poor' {
    const isModern = this.isModernVersion(version);

    if (platform === 'ios' && browser === 'safari') {
      return isModern ? 'excellent' : 'good';
    }

    if (platform === 'android' && browser === 'chrome') {
      return 'excellent';
    }

    return isModern ? 'good' : 'fair';
  }

  /**
   * Identify platform-specific compatibility issues
   */
  private identifyCompatibilityIssues(): CompatibilityIssue[] {
    const issues: CompatibilityIssue[] = [];

    // iOS Safari specific issues
    if (this.browserInfo.platform === 'ios' && this.browserInfo.browser === 'safari') {
      issues.push(
        {
          id: 'ios-safari-scroll-jump',
          platform: 'ios',
          severity: 'critical',
          category: 'scrolling',
          title: 'iOS Safari Scroll Position Jump',
          description: 'Fixed positioning elements jump during scroll on iOS Safari',
          symptoms: [
            'Headers/footers jump during scroll',
            'Fixed navigation elements reposition',
            'Unsmooth scroll behavior',
            'Elements flash during scroll'
          ],
          solution: 'Use position: sticky with proper webkit prefixes and scroll anchoring',
          cssFix: `
/* iOS Safari scroll fix */
.sticky-header {
  position: -webkit-sticky;
  position: sticky;
  top: 0;
  z-index: 100;
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
}

/* Prevent scroll jumping */
.list-container {
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

/* Scroll anchoring for iOS */
html {
  scroll-behavior: smooth;
  scroll-padding-top: 60px; /* Account for sticky header */
}
          `,
          workaround: 'Add scroll-behavior: smooth to html and use CSS scroll-padding-top'
        },

        {
          id: 'ios-safari-overscroll-bounce',
          platform: 'ios',
          severity: 'major',
          category: 'scrolling',
          title: 'iOS Safari Overscroll Bounce Effect',
          description: 'iOS特有的弹性滚动效果影响列表滚动体验',
          symptoms: [
            'Lists bounce beyond boundaries',
            'Rubber band effect on scroll',
            'Unexpected scroll behavior',
            'Visual confusion for users'
          ],
          solution: 'Control overscroll behavior with CSS properties',
          cssFix: `
/* iOS overscroll control */
.list-container {
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  height: 100vh;
}

/* Prevent bounce for fixed lists */
.list-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
          `
        },

        {
          id: 'ios-safari-touch-highlight',
          platform: 'ios',
          severity: 'minor',
          category: 'touch',
          title: 'iOS Safari Default Tap Highlight',
          description: 'iOS Safari shows default gray tap highlight on interactive elements',
          symptoms: [
            'Gray overlay on tap',
            'Inconsistent with design',
            'Visual feedback conflicts',
            'Poor touch interaction experience'
          ],
          solution: 'Disable default tap highlight and use custom feedback',
          cssFix: `
/* Remove iOS tap highlight */
.list-item {
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
}

/* Add custom touch feedback */
.list-item:active {
  background-color: #f0f0f0;
  transform: scale(0.98);
  transition: all 0.1s ease;
}
          `
        },

        {
          id: 'ios-safari-backdrop-filter',
          platform: 'ios',
          severity: 'major',
          category: 'css',
          title: 'iOS Safari Backdrop Filter Performance',
          description: 'Backdrop filter effects can cause performance issues on iOS Safari',
          symptoms: [
            'Scrolling becomes slow with blur effects',
            'Janky animations with backdrop filters',
            'High CPU usage during scroll',
            'Battery drain on mobile devices'
          ],
          solution: 'Use performance-optimized backdrop filters with hardware acceleration',
          cssFix: `
/* Optimized backdrop filter for iOS */
.blur-overlay {
  -webkit-backdrop-filter: blur(10px) saturate(180%);
  backdrop-filter: blur(10px) saturate(180%);
  -webkit-transform: translateZ(0);
  transform: translateZ(0);
  will-change: transform;
}

/* Alternative without performance hit */
.blur-overlay-fallback {
  background: rgba(255, 255, 255, 0.8);
}
          `
        }
      );
    }

    // Android Chrome specific issues
    if (this.browserInfo.platform === 'android' && this.browserInfo.browser === 'chrome') {
      issues.push(
        {
          id: 'android-chrome-scroll-smoothness',
          platform: 'android',
          severity: 'minor',
          category: 'scrolling',
          title: 'Android Chrome Scroll Smoothness Variations',
          description: 'Chrome scroll smoothness varies across Android versions and devices',
          symptoms: [
            'Inconsistent scroll smoothness',
            'Choppy scrolling on older devices',
            'Variable scroll performance',
            'Inconsistent animation frame rates'
          ],
          solution: 'Use scroll-behavior smooth with performance optimizations',
          cssFix: `
/* Optimized scrolling for Android Chrome */
.list-container {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  will-change: scroll-position;
  contain: layout style paint;
}

/* Performance optimization */
.list-item {
  contain: layout style paint;
  will-change: auto;
}

/* Disable animations on low-end devices */
@media (prefers-reduced-motion: reduce) {
  .list-container {
    scroll-behavior: auto;
  }
}
          `
        },

        {
          id: 'android-chrome-touch-feedback',
          platform: 'android',
          severity: 'minor',
          category: 'touch',
          title: 'Android Chrome Touch Response Time',
          description: 'Touch feedback may be delayed on certain Android devices with Chrome',
          symptoms: [
            'Delayed touch response',
            'Inconsistent touch feedback timing',
            'Touch lag on older devices',
            'Variable interaction performance'
          ],
          solution: 'Add immediate visual feedback and optimize touch event handling',
          javascriptFix: `
// Optimized touch handling for Android Chrome
const handleTouchStart = (e) => {
  // Immediate visual feedback
  e.target.classList.add('touch-active');

  // Prevent default behavior if needed
  if (needsPreventDefault(e)) {
    e.preventDefault();
  }
};

const handleTouchEnd = (e) => {
  // Remove visual feedback immediately
  e.target.classList.remove('touch-active');

  // Handle the interaction
  handleInteraction(e);
};

// CSS for immediate feedback
.touch-active {
  background-color: #f0f0f0 !important;
  transform: scale(0.98) !important;
}
          `
        }
      );
    }

    // Cross-platform issues
    issues.push(
      {
        id: 'cross-platform-scroll-position',
        platform: 'both',
        severity: 'major',
        category: 'scrolling',
        title: 'Cross-Platform Scroll Position Differences',
        description: 'Scroll position restoration varies between iOS Safari and Android Chrome',
        symptoms: [
          'Different scroll restoration behavior',
          'Inconsistent scroll position after navigation',
          'Variable scroll animation timing',
          'Platform-specific scroll quirks'
        ],
        solution: 'Implement platform-agnostic scroll position management',
        javascriptFix: `
// Cross-platform scroll position management
const saveScrollPosition = () => {
  sessionStorage.setItem('listScrollPosition', window.scrollY.toString());
};

const restoreScrollPosition = () => {
  const savedPosition = sessionStorage.getItem('listScrollPosition');
  if (savedPosition) {
    // Use requestAnimationFrame for smooth restoration
    requestAnimationFrame(() => {
      window.scrollTo(0, parseInt(savedPosition, 10));
    });
  }
};

// Platform-specific optimizations
const optimizeScrollForPlatform = () => {
  if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
    // iOS Safari optimizations
    document.body.style.webkitOverflowScrolling = 'touch';
  } else if (/Android/.test(navigator.userAgent)) {
    // Android Chrome optimizations
    document.body.style.overscrollBehavior = 'contain';
  }
};
        `
      },

      {
        id: 'cross-platform-list-performance',
        platform: 'both',
        severity: 'major',
        category: 'performance',
        title: 'List Performance Variations Across Platforms',
        description: 'List rendering performance differs significantly between platforms',
        symptoms: [
          'iOS Safari faster/slower than expected',
          'Android Chrome performance variations',
          'Inconsistent animation smoothness',
          'Variable memory usage patterns'
        ],
        solution: 'Implement platform-specific performance optimizations',
        javascriptFix: `
// Platform-specific performance optimizations
const optimizeListPerformance = () => {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isAndroid = /Android/.test(navigator.userAgent);

  if (isIOS) {
    // iOS Safari optimizations
    return {
      itemHeight: 44, // Optimal for iOS touch
      bufferSize: 20,
      useTransform3d: true,
      enableHardwareAcceleration: true
    };
  } else if (isAndroid) {
    // Android Chrome optimizations
    return {
      itemHeight: 48, // Optimal for Android touch
      bufferSize: 30,
      useTransform3d: true,
      enableHardwareAcceleration: true
    };
  }

  // Desktop defaults
  return {
    itemHeight: 40,
    bufferSize: 50,
    useTransform3d: false,
    enableHardwareAcceleration: true
  };
};
        `
      },

      {
        id: 'cross-platform-css-grid-support',
        platform: 'both',
        severity: 'minor',
        category: 'css',
        title: 'CSS Grid Support Variations',
        description: 'CSS Grid support and behavior differs between Safari and Chrome',
        symptoms: [
          'Grid layout differences',
          'Gap property support variations',
          'Inconsistent grid behavior',
          'Fallback layout issues'
        ],
        solution: 'Use progressive enhancement with proper CSS fallbacks',
        cssFix: `
/* Progressive enhancement for CSS Grid */
.list-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

/* Safari fallback */
@supports not (gap: 1px) {
  .list-grid {
    display: flex;
    flex-wrap: wrap;
    margin: -8px;
  }

  .list-grid > * {
    flex: 1 1 250px;
    margin: 8px;
  }
}

/* iOS Safari specific fixes */
@supports (-webkit-backdrop-filter: blur(1px)) {
  .list-grid {
    -webkit-transform: translateZ(0);
    transform: translateZ(0);
  }
}
        `
      }
    );

    return issues;
  }

  /**
   * Get current browser information
   */
  getBrowserInfo(): BrowserInfo {
    return this.browserInfo;
  }

  /**
   * Get compatibility issues for current platform
   */
  getCompatibilityIssues(): CompatibilityIssue[] {
    const platformIssues = this.issues.filter(
      issue => issue.platform === this.browserInfo.platform ||
              issue.platform === 'both'
    );

    // Sort by severity
    return platformIssues.sort((a, b) => {
      const severityOrder = { critical: 4, major: 3, minor: 2 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }

  /**
   * Get platform-specific CSS fixes
   */
  getPlatformCSSFixes(): string {
    const issues = this.getCompatibilityIssues();
    const cssFixes = issues
      .filter(issue => issue.cssFix)
      .map(issue => `/* ${issue.title} */\n${issue.cssFix}`)
      .join('\n\n');

    return cssFixes;
  }

  /**
   * Generate cross-platform compatibility report
   */
  generateCompatibilityReport(): {
    browserInfo: BrowserInfo;
    issues: CompatibilityIssue[];
    recommendations: string[];
    severityBreakdown: Record<string, number>;
  } {
    const issues = this.getCompatibilityIssues();

    const severityBreakdown = issues.reduce((acc, issue) => {
      acc[issue.severity] = (acc[issue.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const recommendations = [
      this.browserInfo.platform === 'ios'
        ? 'Test thoroughly on iOS Safari for scroll behavior'
        : 'Test on Android Chrome for touch responsiveness',
      this.browserInfo.engine === 'webkit'
        ? 'Use -webkit- prefixes for Safari compatibility'
        : 'Use standard CSS properties for Chrome compatibility',
      'Implement platform-specific performance optimizations',
      'Test on actual devices, not just emulators',
      'Consider platform-specific UI patterns'
    ];

    return {
      browserInfo: this.browserInfo,
      issues,
      recommendations,
      severityBreakdown
    };
  }

  /**
   * Validate list implementation for cross-platform compatibility
   */
  validateListImplementation(element: HTMLElement): {
    passed: boolean;
    issues: string[];
    recommendations: string[];
    platformSpecific: Record<string, string>;
  } {
    const issues: string[] = [];
    const recommendations: string[] = [];
    const platformSpecific: Record<string, string> = {};

    // Check for common cross-platform issues
    const computedStyle = window.getComputedStyle(element);

    // iOS Safari checks
    if (this.browserInfo.platform === 'ios') {
      if (computedStyle.webkitOverflowScrolling !== 'touch') {
        issues.push('Missing -webkit-overflow-scrolling: touch for iOS Safari');
        recommendations.push('Add -webkit-overflow-scrolling: touch to scrollable containers');
      }

      if (computedStyle.webkitTapHighlightColor !== 'transparent') {
        issues.push('Default iOS tap highlight not disabled');
        recommendations.push('Add -webkit-tap-highlight-color: transparent');
      }
    }

    // Android Chrome checks
    if (this.browserInfo.platform === 'android') {
      if (computedStyle.touchAction === 'auto') {
        recommendations.push('Consider touch-action optimization for better Android performance');
      }
    }

    // Cross-platform checks
    if (!computedStyle.contain || computedStyle.contain === 'none') {
      recommendations.push('Add CSS contain property for better performance');
    }

    const passed = issues.length === 0;

    return {
      passed,
      issues,
      recommendations,
      platformSpecific
    };
  }
}

// Export singleton instance
export const mobileBrowserCompatibility = new MobileBrowserCompatibility();