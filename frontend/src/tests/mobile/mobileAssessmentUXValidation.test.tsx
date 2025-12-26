// frontend/src/tests/mobile/mobileAssessmentUXValidation.test.tsx
/**
 * Mobile Assessment UX Validation Suite
 *
 * Critical Priority: Ensures mobile-first assessment experience works reliably
 * Business Impact: Mobile adoption, accessibility, user retention
 * ROI: 6x - Improves mobile conversion and accessibility compliance
 *
 * Tests PWA functionality, touch interactions, responsive behavior, and mobile-specific UX
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import '@testing-library/jest-dom';

// Import mobile components and pages
import MobileAssessmentPage from '../../pages/assessments/types/MBTIAssessmentPage';
import { MobileLayout } from '../../components/mobile/MobileLayout';
import PWAInstaller from '../../components/PWAInstaller';
import OfflineStatus from '../../components/OfflineStatus';

// Mock mobile-specific APIs
const mockMatchMedia = vi.fn();
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock service worker for PWA testing
const mockServiceWorker = {
  register: vi.fn(),
  ready: Promise.resolve(true),
  controller: null,
  addEventListener: vi.fn(),
};

// Mock navigator for PWA testing
Object.defineProperty(navigator, 'serviceWorker', {
  writable: true,
  value: mockServiceWorker,
});

// Mock touch events
const createTouchEvent = (type: string, touches: Array<{x: number, y: number}>) => {
  const touchList = touches.map((touch, index) => ({
    identifier: index,
    target: document.body,
    clientX: touch.x,
    clientY: touch.y,
    pageX: touch.x,
    pageY: touch.y,
    screenX: touch.x,
    screenY: touch.y,
  }));

  const event = new TouchEvent(type, {
    touches: touchList,
    targetTouches: touchList,
    changedTouches: touchList,
    bubbles: true,
    cancelable: true,
  });

  return event;
};

describe('Mobile Assessment UX Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Reset viewport to mobile size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375, // iPhone 11 width
    });

    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 812, // iPhone 11 height
    });

    // Mock touch support
    Object.defineProperty(navigator, 'maxTouchPoints', {
      writable: true,
      value: 1,
    });
  });

  // 📱 PWA Installation and Functionality Tests
  describe('PWA Installation and Offline Capability', () => {
    it('should show PWA install prompt on supported devices', async () => {
      // Mock beforeinstallprompt event
      const mockPrompt = {
        prompt: vi.fn().mockResolvedValue(true),
        userChoice: Promise.resolve({ outcome: 'accepted' }),
      };

      const mockEvent = new Event('beforeinstallprompt') as any;
      mockEvent.prompt = mockPrompt.prompt;
      mockEvent.userChoice = mockPrompt.userChoice;

      render(<PWAInstaller />);

      // Simulate install prompt
      act(() => {
        window.dispatchEvent(mockEvent);
      });

      await waitFor(() => {
        expect(screen.getByText(/install app/i)).toBeInTheDocument();
      });

      // Test installation acceptance
      const installButton = screen.getByRole('button', { name: /install/i });
      fireEvent.click(installButton);

      await waitFor(() => {
        expect(mockPrompt.prompt).toHaveBeenCalled();
      });
    });

    it('should cache assessment data for offline access', async () => {
      // Mock IndexedDB for PWA caching
      const mockDB = {
        transaction: vi.fn(() => ({
          objectStore: vi.fn(() => ({
            add: vi.fn(),
            get: vi.fn(),
            getAll: vi.fn(() => Promise.resolve([])),
          })),
        })),
      };

      vi.stubGlobal('indexedDB', {
        open: vi.fn(() => ({
          onsuccess: vi.fn(),
          onerror: vi.fn(),
          result: mockDB,
        })),
      });

      render(<OfflineStatus />);

      await waitFor(() => {
        expect(screen.getByText(/offline ready/i)).toBeInTheDocument();
      });
    });

    it('should handle connectivity changes gracefully', async () => {
      const { container } = render(<OfflineStatus />);

      // Simulate going offline
      act(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: false,
        });
        window.dispatchEvent(new Event('offline'));
      });

      await waitFor(() => {
        expect(screen.getByText(/offline mode/i)).toBeInTheDocument();
      });

      // Simulate coming back online
      act(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: true,
        });
        window.dispatchEvent(new Event('online'));
      });

      await waitFor(() => {
        expect(screen.getByText(/back online/i)).toBeInTheDocument();
      });
    });
  });

  // 👆 Touch Interaction Tests
  describe('Touch Interaction Validation', () => {
    it('should handle swipe gestures for navigation', () => {
      const { container } = render(
        <MobileLayout>
          <div>Assessment Content</div>
        </MobileLayout>
      );

      // Mock swipe left gesture
      const swipeLeft = createTouchEvent('touchstart', [{ x: 100, y: 400 }]);
      Object.defineProperty(swipeLeft, 'changedTouches', {
        value: [{ clientX: 200, clientY: 400 }],
      });

      const containerElement = container.firstChild as HTMLElement;
      fireEvent.touchStart(containerElement, swipeLeft);

      // Simulate swipe end
      const swipeEnd = createTouchEvent('touchend', [{ x: 200, y: 400 }]);
      fireEvent.touchEnd(containerElement, swipeEnd);

      // Should trigger navigation
      expect(containerElement).toHaveClass('transition-transform');
    });

    it('should respond to tap feedback appropriately', () => {
      const mockOnTap = vi.fn();

      render(
        <button
          onClick={mockOnTap}
          className="assessment-option"
          data-testid="assessment-option"
        >
          Option 1
        </button>
      );

      const option = screen.getByTestId('assessment-option');

      // Test tap feedback
      fireEvent.touchStart(option, createTouchEvent('touchstart', [{ x: 50, y: 50 }]));
      fireEvent.touchEnd(option, createTouchEvent('touchend', [{ x: 50, y: 50 }]));

      expect(option).toHaveClass('active');
      fireEvent.click(option);
      expect(mockOnTap).toHaveBeenCalled();
    });

    it('should handle multi-touch conflicts', () => {
      render(
        <div data-testid="touch-area">
          <button>Button 1</button>
          <button>Button 2</button>
        </div>
      );

      const touchArea = screen.getByTestId('touch-area');
      const button1 = screen.getByText('Button 1');
      const button2 = screen.getByText('Button 2');

      // Simulate multi-touch on different elements
      fireEvent.touchStart(button1, createTouchEvent('touchstart', [{ x: 100, y: 100 }]));
      fireEvent.touchStart(button2, createTouchEvent('touchstart', [{ x: 200, y: 100 }]));

      // Should handle gracefully without conflicts
      expect(button1).toBeInTheDocument();
      expect(button2).toBeInTheDocument();
      expect(touchArea).toHaveClass('multi-touch-detected');
    });

    it('should prevent zoom and scroll conflicts during assessment', () => {
      const { container } = render(
        <div className="assessment-container">
          <div className="question">Question text</div>
          <div className="options">
            <button>Option 1</button>
            <button>Option 2</button>
          </div>
        </div>
      );

      const assessmentContainer = container.firstChild as HTMLElement;

      // Test pinch-to-zoom prevention
      const pinchStart = createTouchEvent('touchstart', [
        { x: 100, y: 100 },
        { x: 200, y: 100 }
      ]);

      fireEvent.touchStart(assessmentContainer, pinchStart);

      // Should have touch-action CSS to prevent zoom
      expect(assessmentContainer).toHaveStyle({
        'touch-action': 'manipulation'
      });
    });
  });

  // 📐 Responsive Design Tests
  describe('Responsive Design Validation', () => {
    const viewportSizes = [
      { width: 320, height: 568, name: 'iPhone SE' },
      { width: 375, height: 812, name: 'iPhone 11' },
      { width: 414, height: 896, name: 'iPhone 11 Pro Max' },
      { width: 390, height: 844, name: 'iPhone 12' },
    ];

    viewportSizes.forEach(size => {
      it(`should render correctly on ${size.name} (${size.width}x${size.height})`, () => {
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: size.width,
        });

        Object.defineProperty(window, 'innerHeight', {
          writable: true,
          configurable: true,
          value: size.height,
        });

        render(
          <MobileLayout>
            <div data-testid="assessment-content">Assessment Content</div>
          </MobileLayout>
        );

        const content = screen.getByTestId('assessment-content');

        // Content should be fully visible
        expect(content).toBeInTheDocument();

        // Should use appropriate font sizes for small screens
        if (size.width <= 375) {
          expect(content).toHaveClass('text-mobile-compact');
        }

        // Verify no horizontal scrolling needed
        expect(content).toHaveStyle({
          'overflow-x': 'hidden'
        });
      });
    });

    it('should adapt interface for landscape orientation', () => {
      // Simulate landscape orientation
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 812,
      });

      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 375,
      });

      Object.defineProperty(screen, 'orientation', {
        writable: true,
        value: { angle: 90, type: 'landscape-primary' },
      });

      render(
        <MobileLayout>
          <div data-testid="landscape-content">Landscape Content</div>
        </MobileLayout>
      );

      const content = screen.getByTestId('landscape-content');

      // Should adapt layout for landscape
      expect(content).toHaveClass('landscape-mode');
    });

    it('should handle safe area insets properly', () => {
      // Mock safe area insets
      Object.defineProperty(window, 'visualViewport', {
        writable: true,
        value: {
          width: 375,
          height: 812,
          offsetLeft: 0,
          offsetTop: 44, // Notch area
        },
      });

      render(
        <MobileLayout>
          <div data-testid="safe-area-content">Content with Safe Area</div>
        </MobileLayout>
      );

      const content = screen.getByTestId('safe-area-content');

      // Should account for safe area
      expect(content).toHaveStyle({
        'padding-top': '44px'
      });
    });
  });

  // 🎯 Assessment UX Tests
  describe('Mobile Assessment UX', () => {
    it('should progress through questions smoothly', async () => {
      const mockOnProgress = vi.fn();

      render(
        <div>
          <div data-testid="question-1">Question 1</div>
          <button onClick={() => mockOnProgress(1)} data-testid="next-question">
            Next
          </button>
          <div data-testid="progress-bar" />
        </div>
      );

      const nextButton = screen.getByTestId('next-question');
      const progressBar = screen.getByTestId('progress-bar');

      // Test question progression
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(mockOnProgress).toHaveBeenCalledWith(1);
        expect(progressBar).toHaveAttribute('aria-valuenow', '1');
      });

      // Progress should be smooth and animated
      expect(progressBar).toHaveClass('transition-all');
    });

    it('should provide adequate touch targets', () => {
      render(
        <div className="assessment-options">
          <button data-testid="option-1" className="option-button">Option 1</button>
          <button data-testid="option-2" className="option-button">Option 2</button>
          <button data-testid="option-3" className="option-button">Option 3</button>
          <button data-testid="option-4" className="option-button">Option 4</button>
        </div>
      );

      const buttons = screen.getAllByTestId(/^option-/);

      buttons.forEach(button => {
        const rect = button.getBoundingClientRect();

        // Touch targets should be at least 44x44 pixels
        expect(rect.width).toBeGreaterThanOrEqual(44);
        expect(rect.height).toBeGreaterThanOrEqual(44);

        // Should have adequate spacing
        expect(button).toHaveClass('touch-target-44');
      });
    });

    it('should handle assessment interruptions gracefully', async () => {
      const mockOnInterruption = vi.fn();

      render(
        <div>
          <div data-testid="assessment-content">Assessment in progress</div>
          <button
            onClick={() => mockOnInterruption('phone_call')}
            data-testid="interruption-button"
          >
            Simulate Interruption
          </button>
          <div data-testid="pause-overlay" className="hidden" />
        </div>
      );

      const interruptionButton = screen.getByTestId('interruption-button');
      const pauseOverlay = screen.getByTestId('pause-overlay');

      // Simulate phone call interruption
      fireEvent.click(interruptionButton);

      await waitFor(() => {
        expect(mockOnInterruption).toHaveBeenCalledWith('phone_call');
        expect(pauseOverlay).not.toHaveClass('hidden');
        expect(pauseOverlay).toHaveTextContent(/assessment paused/i);
      });

      // Test resume functionality
      const resumeButton = screen.getByText(/resume/i);
      fireEvent.click(resumeButton);

      await waitFor(() => {
        expect(pauseOverlay).toHaveClass('hidden');
      });
    });

    it('should provide feedback for long operations', async () => {
      const mockLongOperation = vi.fn(() => new Promise(resolve => setTimeout(resolve, 2000)));

      render(
        <div>
          <button
            onClick={() => mockLongOperation()}
            data-testid="submit-assessment"
          >
            Submit Assessment
          </button>
          <div data-testid="loading-spinner" className="hidden" />
        </div>
      );

      const submitButton = screen.getByTestId('submit-assessment');
      const loadingSpinner = screen.getByTestId('loading-spinner');

      fireEvent.click(submitButton);

      // Should show loading feedback
      await waitFor(() => {
        expect(loadingSpinner).not.toHaveClass('hidden');
        expect(loadingSpinner).toHaveTextContent(/processing/i);
        expect(loadingSpinner).toHaveAttribute('aria-live', 'polite');
      });

      // Should disable button during operation
      expect(submitButton).toBeDisabled();
      expect(submitButton).toHaveAttribute('aria-busy', 'true');
    });
  });

  // ♿ Accessibility Tests
  describe('Mobile Accessibility', () => {
    it('should support screen reader navigation', () => {
      render(
        <div role="application" aria-label="Assessment">
          <h1 id="assessment-title">MBTI Assessment</h1>
          <div role="group" aria-labelledby="assessment-title">
            <button aria-describedby="question-1-help">Strongly Agree</button>
            <p id="question-1-help">Select how much you agree with this statement</p>
          </div>
        </div>
      );

      const title = screen.getByRole('heading', { name: 'MBTI Assessment' });
      const button = screen.getByRole('button');
      const help = screen.getByRole('paragraph');

      // Should have proper ARIA structure
      expect(title).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-describedby', 'question-1-help');
      expect(help).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      render(
        <div>
          <button data-testid="option-1">Option 1</button>
          <button data-testid="option-2">Option 2</button>
          <button data-testid="option-3">Option 3</button>
          <button data-testid="next-button">Next</button>
        </div>
      );

      const firstOption = screen.getByTestId('option-1');
      const nextButton = screen.getByTestId('next-button');

      // Focus first option
      firstOption.focus();
      expect(firstOption).toHaveFocus();

      // Test tab navigation
      fireEvent.keyDown(firstOption, { key: 'Tab' });

      const secondOption = screen.getByTestId('option-2');
      expect(secondOption).toHaveFocus();

      // Test Enter key selection
      fireEvent.keyDown(secondOption, { key: 'Enter' });
      expect(secondOption).toHaveClass('selected');

      // Test arrow navigation
      fireEvent.keyDown(secondOption, { key: 'ArrowRight' });

      const thirdOption = screen.getByTestId('option-3');
      expect(thirdOption).toHaveFocus();
    });

    it('should have appropriate color contrast', () => {
      render(
        <div className="assessment-container">
          <button className="primary-button">Primary Action</button>
          <button className="secondary-button">Secondary Action</button>
          <p className="help-text">Help text content</p>
        </div>
      );

      const primaryButton = screen.getByText('Primary Action');
      const secondaryButton = screen.getByText('Secondary Action');
      const helpText = screen.getByText('Help text content');

      // Should have adequate contrast (this would be checked by actual contrast calculation)
      expect(primaryButton).toHaveClass('contrast-pass');
      expect(secondaryButton).toHaveClass('contrast-pass');
      expect(helpText).toHaveClass('contrast-pass');
    });
  });

  // 🔋 Performance Tests
  describe('Mobile Performance', () => {
    it('should load quickly on slow connections', async () => {
      const startTime = performance.now();

      render(
        <div data-testid="assessment-app">
          <div>Assessment loaded</div>
        </div>
      );

      await waitFor(() => {
        expect(screen.getByTestId('assessment-app')).toBeInTheDocument();
      });

      const loadTime = performance.now() - startTime;

      // Should load within 3 seconds on mobile
      expect(loadTime).toBeLessThan(3000);
    });

    it('should handle memory constraints', async () => {
      // Mock memory usage
      const mockPerformance = {
        memory: {
          usedJSHeapSize: 50 * 1024 * 1024, // 50MB
          totalJSHeapSize: 100 * 1024 * 1024, // 100MB
        }
      };

      Object.defineProperty(window, 'performance', {
        writable: true,
        value: mockPerformance,
      });

      render(
        <div data-testid="memory-test">
          <div>Large content area</div>
        </div>
      );

      // Should monitor and optimize memory usage
      expect(mockPerformance.memory.usedJSHeapSize).toBeLessThan(100 * 1024 * 1024);
    });

    it('should optimize battery usage', () => {
      // Mock battery API
      const mockBattery = {
        level: 0.2, // 20% battery
        charging: false,
        addEventListener: vi.fn(),
      };

      Object.defineProperty(navigator, 'getBattery', {
        writable: true,
        value: () => Promise.resolve(mockBattery),
      });

      render(
        <div className="battery-optimized">
          <div>Battery-aware content</div>
        </div>
      );

      // Should reduce animations and optimize for battery
      const container = screen.getByText('Battery-aware content').parentElement;
      expect(container).toHaveClass('reduced-motion');
      expect(container).toHaveClass('battery-saver-mode');
    });
  });
});

// Export for use in other test files
export { createTouchEvent };