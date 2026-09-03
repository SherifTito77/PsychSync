/**
 * Browser Compatibility Matrix for PsychSync
 * Defines expected behavior and browser-specific considerations
 */

export interface BrowserCapability {
  supported: boolean;
  version?: string;
  workarounds?: string[];
  notes?: string;
}

export interface FeatureMatrix {
  [feature: string]: {
    Chrome: BrowserCapability;
    Edge: BrowserCapability;
    Safari: BrowserCapability;
    Firefox: BrowserCapability;
  };
}

export interface TestCase {
  id: string;
  name: string;
  description: string;
  category: 'css' | 'javascript' | 'accessibility' | 'performance' | 'pwa' | 'forms';
  priority: 'critical' | 'high' | 'medium' | 'low';
  browsers: {
    Chrome: BrowserCapability;
    Edge: BrowserCapability;
    Safari: BrowserCapability;
    Firefox: BrowserCapability;
  };
  testSteps: string[];
  expectedResult: string;
  knownIssues: string[];
}

export const BROWSER_COMPATIBILITY_MATRIX: FeatureMatrix = {
  // CSS Features
  'css-grid': {
    Chrome: { supported: true, version: '57+' },
    Edge: { supported: true, version: '16+' },
    Safari: { supported: true, version: '10.1+' },
    Firefox: { supported: true, version: '52+' }
  },
  'css-flexbox': {
    Chrome: { supported: true, version: '29+' },
    Edge: { supported: true, version: '12+' },
    Safari: { supported: true, version: '9+' },
    Firefox: { supported: true, version: '28+' }
  },
  'css-variables': {
    Chrome: { supported: true, version: '49+' },
    Edge: { supported: true, version: '16+' },
    Safari: { supported: true, version: '10.1+' },
    Firefox: { supported: true, version: '31+' }
  },
  'css-custom-properties': {
    Chrome: { supported: true, version: '49+' },
    Edge: { supported: true, version: '16+' },
    Safari: { supported: true, version: '10.1+' },
    Firefox: { supported: true, version: '31+' }
  },
  'backdrop-filter': {
    Chrome: { supported: true, version: '76+' },
    Edge: { supported: true, version: '79+' },
    Safari: { supported: true, version: '14+' },
    Firefox: {
      supported: false,
      workarounds: ['Use SVG filters or box-shadow as fallback'],
      notes: 'Firefox support is behind flag'
    }
  },
  'focus-visible': {
    Chrome: { supported: true, version: '86+' },
    Edge: { supported: true, version: '86+' },
    Safari: { supported: true, version: '15.4+' },
    Firefox: { supported: true, version: '85+' }
  },
  'scroll-behavior': {
    Chrome: { supported: true, version: '61+' },
    Edge: { supported: true, version: '79+' },
    Safari: { supported: false, workarounds: ['Use JavaScript smooth scroll libraries'] },
    Firefox: { supported: true, version: '36+' }
  },
  'container-queries': {
    Chrome: { supported: true, version: '105+' },
    Edge: { supported: true, version: '105+' },
    Safari: { supported: true, version: '16+' },
    Firefox: { supported: false, workarounds: ['Use JavaScript-based responsive solutions'] }
  },

  // JavaScript Features
  'intersection-observer': {
    Chrome: { supported: true, version: '51+' },
    Edge: { supported: true, version: '15+' },
    Safari: { supported: true, version: '12.1+' },
    Firefox: { supported: true, version: '55+' }
  },
  'resize-observer': {
    Chrome: { supported: true, version: '64+' },
    Edge: { supported: true, version: '79+' },
    Safari: { supported: true, version: '13.1+' },
    Firefox: { supported: true, version: '69+' }
  },
  'web-share': {
    Chrome: { supported: true, version: '89+' },
    Edge: { supported: true, version: '89+' },
    Safari: { supported: true, version: '12.3+' },
    Firefox: {
      supported: false,
      workarounds: ['Use custom share dialogs or third-party libraries'],
      notes: 'Firefox implementation is in progress'
    }
  },
  'clipboard': {
    Chrome: { supported: true, version: '66+' },
    Edge: { supported: true, version: '79+' },
    Safari: { supported: true, version: '13.1+' },
    Firefox: { supported: true, version: '63+' }
  },

  // Web APIs
  'service-worker': {
    Chrome: { supported: true, version: '40+' },
    Edge: { supported: true, version: '17+' },
    Safari: { supported: true, version: '11.1+' },
    Firefox: { supported: true, version: '44+' }
  },
  'push-notifications': {
    Chrome: { supported: true, version: '50+' },
    Edge: { supported: true, version: '17+' },
    Safari: { supported: true, version: '16+' },
    Firefox: { supported: true, version: '44+' }
  },
  'web-bluetooth': {
    Chrome: { supported: true, version: '56+' },
    Edge: { supported: true, version: '79+' },
    Safari: { supported: false, workarounds: ['Use native app or WebUSB'] },
    Firefox: {
      supported: false,
      workarounds: ['Use WebUSB or native app'],
      notes: 'Firefox has no plans to support Web Bluetooth'
    }
  },
  'web-assembly': {
    Chrome: { supported: true, version: '57+' },
    Edge: { supported: true, version: '16+' },
    Safari: { supported: true, version: '14+' },
    Firefox: { supported: true, version: '52+' }
  },

  // PWA Features
  'offline-support': {
    Chrome: { supported: true, version: '40+' },
    Edge: { supported: true, version: '17+' },
    Safari: { supported: true, version: '11.1+' },
    Firefox: { supported: true, version: '44+' }
  },
  'installable-pwa': {
    Chrome: { supported: true, version: '70+' },
    Edge: { supported: true, version: '79+' },
    Safari: { supported: true, version: '11.3+' },
    Firefox: { supported: false, workarounds: ['Use Firefox extension for PWA support'] }
  },
  'background-sync': {
    Chrome: { supported: true, version: '49+' },
    Edge: { supported: true, version: '79+' },
    Safari: { supported: false, workarounds: ['Use manual sync or Service Worker message'] },
    Firefox: { supported: false, workarounds: ['Use Service Worker events'] }
  },

  // Accessibility Features
  'aria-live-regions': {
    Chrome: { supported: true, version: '4+' },
    Edge: { supported: true, version: '12+' },
    Safari: { supported: true, version: '4+' },
    Firefox: { supported: true, version: '4+' }
  },
  'screen-reader-support': {
    Chrome: { supported: true, version: '4+' },
    Edge: { supported: true, version: '12+' },
    Safari: { supported: true, version: '4+', notes: 'VoiceOptimized for VoiceOver' },
    Firefox: { supported: true, version: '4+', notes: 'Works well with NVDA and JAWS' }
  },
  'keyboard-navigation': {
    Chrome: { supported: true, version: '4+' },
    Edge: { supported: true, version: '12+' },
    Safari: { supported: true, version: '4+' },
    Firefox: { supported: true, version: '4+' }
  }
};

export const CROSS_BROWSER_TEST_CASES: TestCase[] = [
  // CSS Tests
  {
    id: 'css-001',
    name: 'Grid Layout Rendering',
    description: 'Test CSS Grid layout functionality across browsers',
    category: 'css',
    priority: 'critical',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: true }
    },
    testSteps: [
      'Navigate to a page with CSS Grid layout',
      'Verify grid items align properly',
      'Test responsive grid behavior',
      'Check grid gaps and alignment'
    ],
    expectedResult: 'Grid layout renders correctly with proper item positioning',
    knownIssues: ['Older Safari versions may need -webkit-grid prefix']
  },
  {
    id: 'css-002',
    name: 'Flexbox Layout Consistency',
    description: 'Test Flexbox layout consistency across browsers',
    category: 'css',
    priority: 'critical',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: true }
    },
    testSteps: [
      'Navigate to page with flexbox layouts',
      'Test flex-direction variations',
      'Test justify-content and align-items',
      'Test flex-wrap behavior'
    ],
    expectedResult: 'Flexbox layouts behave consistently across browsers',
    knownIssues: ['Legacy Edge may need -ms-flexbox prefix']
  },
  {
    id: 'css-003',
    name: 'CSS Custom Properties',
    description: 'Test CSS custom properties (variables) support',
    category: 'css',
    priority: 'high',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: true }
    },
    testSteps: [
      'Define CSS custom properties',
      'Use variables in styles',
      'Test dynamic variable updates',
      'Test fallback values'
    ],
    expectedResult: 'CSS variables work consistently across browsers',
    knownIssues: []
  },
  {
    id: 'css-004',
    name: 'Backdrop Filter Effects',
    description: 'Test backdrop-filter CSS property',
    category: 'css',
    priority: 'medium',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: false, workarounds: ['Use SVG filters'] }
    },
    testSteps: [
      'Apply backdrop-filter to elements',
      'Test blur effects',
      'Test other filter functions',
      'Check performance impact'
    ],
    expectedResult: 'Backdrop effects work where supported',
    knownIssues: ['Firefox lacks support', 'Safari requires prefix for some effects']
  },

  // JavaScript Tests
  {
    id: 'js-001',
    name: 'Intersection Observer Performance',
    description: 'Test Intersection Observer API functionality',
    category: 'javascript',
    priority: 'high',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: true }
    },
    testSteps: [
      'Create Intersection Observer instance',
      'Observe multiple elements',
      'Test threshold callbacks',
      'Test performance with many elements'
    ],
    expectedResult: 'Intersection Observer works efficiently',
    knownIssues: []
  },
  {
    id: 'js-002',
    name: 'Web Share API',
    description: 'Test Web Share API functionality',
    category: 'javascript',
    priority: 'medium',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: false, workarounds: ['Use custom share dialog'] }
    },
    testSteps: [
      'Check Web Share API availability',
      'Test sharing text content',
      'Test sharing URLs',
      'Test share dialog cancellation'
    ],
    expectedResult: 'Web Share works where supported',
    knownIssues: ['Firefox lacks support', 'Desktop Safari requires user gesture']
  },

  // Accessibility Tests
  {
    id: 'a11y-001',
    name: 'ARIA Live Regions',
    description: 'Test ARIA live region announcements',
    category: 'accessibility',
    priority: 'critical',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: true }
    },
    testSteps: [
      'Create element with aria-live="polite"',
      'Add content dynamically',
      'Test screen reader announcements',
      'Test aria-live="assertive" behavior'
    ],
    expectedResult: 'Live regions announce content to screen readers',
    knownIssues: ['VoiceOver may have slight delay in announcements']
  },
  {
    id: 'a11y-002',
    name: 'Focus Management',
    description: 'Test focus management and keyboard navigation',
    category: 'accessibility',
    priority: 'critical',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: true }
    },
    testSteps: [
      'Test tab order through interactive elements',
      'Test focus trapping in modals',
      'Test skip links',
      'Test focus indicators'
    ],
    expectedResult: 'Focus management works correctly',
    knownIssues: ['Safari may show different focus indicator styles']
  },

  // PWA Tests
  {
    id: 'pwa-001',
    name: 'Service Worker Registration',
    description: 'Test service worker registration and functionality',
    category: 'pwa',
    priority: 'critical',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: true }
    },
    testSteps: [
      'Register service worker',
      'Test offline functionality',
      'Test cache management',
      'Test background sync'
    ],
    expectedResult: 'Service worker works across browsers',
    knownIssues: ['Safari has stricter offline requirements']
  },
  {
    id: 'pwa-002',
    name: 'PWA Installation',
    description: 'Test PWA installation prompts and behavior',
    category: 'pwa',
    priority: 'high',
    browsers: {
      Chrome: { supported: true },
      Edge: { supported: true },
      Safari: { supported: true },
      Firefox: { supported: false, workarounds: ['Use Firefox extension'] }
    },
    testSteps: [
      'Check install prompt availability',
      'Test installation flow',
      'Test installed app behavior',
      'Test app shortcuts'
    ],
    expectedResult: 'PWA installs successfully where supported',
    knownIssues: ['Firefox lacks native PWA install support']
  }
];

export const BROWSER_SPECIFIC_CONFIG = {
  Chrome: {
    preferredDevTools: true,
    debuggingShortcuts: ['F12', 'Ctrl+Shift+I'],
    testConsiderations: [
      'Most feature-complete testing environment',
      'Good performance profiling tools',
      'Excellent CSS Grid support'
    ]
  },
  Edge: {
    preferredDevTools: true,
    debuggingShortcuts: ['F12', 'Ctrl+Shift+I'],
    testConsiderations: [
      'Same engine as Chrome (Blink)',
      'Similar feature support',
      'Built-in accessibility testing tools'
    ]
  },
  Safari: {
    preferredDevTools: true,
    debuggingShortcuts: ['Option+Cmd+I'],
    testConsiderations: [
      'WebKit engine may have rendering differences',
      'Touch gesture support testing needed',
      'VoiceOver accessibility testing essential',
      'Progressive Web App limitations'
    ]
  },
  Firefox: {
    preferredDevTools: true,
    debuggingShortcuts: ['F12', 'Ctrl+Shift+I'],
    testConsiderations: [
      'Gecko engine rendering differences',
      'Enhanced privacy features may affect testing',
      'Excellent accessibility developer tools',
      'Some modern CSS features behind flags'
    ]
  }
};
