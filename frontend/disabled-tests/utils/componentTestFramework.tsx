/**
 * 🧪 Comprehensive Component Testing Framework
 *
 * Enterprise-grade testing utilities and patterns for consistent
 * component testing across the entire PsychSync platform.
 */

import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { ReactElement } from 'react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { vi } from 'vitest';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

export interface ComponentTestConfig {
  /** Component name for test identification */
  componentName: string;
  /** Default props for the component */
  defaultProps?: Record<string, any>;
  /** Accessibility testing configuration */
  accessibilityConfig?: {
    skipAxeTesting?: boolean;
    axeRules?: Record<string, any>;
  };
  /** Interaction testing configuration */
  interactionConfig?: {
    skipMouseTesting?: boolean;
    skipKeyboardTesting?: boolean;
    skipTouchTesting?: boolean;
  };
  /** Custom render options */
  renderOptions?: RenderOptions;
}

export interface ComponentTestCase {
  /** Test case name */
  name: string;
  /** Component props for this test */
  props?: Record<string, any>;
  /** Expected results */
  expectations?: {
    shouldHaveClass?: string[];
    shouldHaveAttribute?: Record<string, string>;
    shouldNotHaveAttribute?: string[];
    shouldBeDisabled?: boolean;
    shouldBeVisible?: boolean;
    ariaLabel?: string;
    role?: string;
  };
  /** Custom test function */
  customTest?: (result: RenderResult) => void | Promise<void>;
}

export interface InteractionTestCase {
  /** Test name */
  name: string;
  /** Type of interaction */
  interactionType: 'hover' | 'click' | 'focus' | 'blur' | 'keydown' | 'keyup' | 'input';
  /** Target element selector (if not the root element) */
  targetSelector?: string;
  /** Interaction parameters */
  interactionParams?: {
    key?: string;
    text?: string;
    times?: number;
  };
  /** Expected outcome */
  expectedOutcome?: {
    shouldHaveBeenCalled?: string;
    shouldHaveClass?: string;
    shouldHaveAttribute?: Record<string, string>;
  };
}

/**
 * Enhanced render function with common providers and configurations
 */
export function renderWithProviders(
  ui: ReactElement,
  options: RenderOptions = {}
): RenderResult {
  // Add any global providers here (ThemeProvider, etc.)
  return render(ui, {
    wrapper: ({ children }) => <>{children}</>,
    ...options,
  });
}

/**
 * Base component testing class with common functionality
 */
export abstract class ComponentTestSuite<TProps = any> {
  protected config: ComponentTestConfig;
  protected userEvent = userEvent.setup();

  constructor(config: ComponentTestConfig) {
    this.config = config;
  }

  /**
   * Render the component with test configuration
   */
  protected renderComponent(props: TProps = {} as TProps): RenderResult {
    const finalProps = { ...this.config.defaultProps, ...props };
    const component = this.createComponent(finalProps);

    return renderWithProviders(component, this.config.renderOptions);
  }

  /**
   * Abstract method to create the component instance
   */
  protected abstract createComponent(props: TProps): ReactElement;

  /**
   * Run accessibility testing using axe
   */
  async testAccessibility(
    renderResult: RenderResult,
    customRules?: Record<string, any>
  ): Promise<{ passed: boolean; violations: any[] }> {
    if (this.config.accessibilityConfig?.skipAxeTesting) {
      return { passed: true, violations: [] };
    }

    const rules = { ...this.config.accessibilityConfig?.axeRules, ...customRules };
    const results = await axe(renderResult.container, { rules });

    return {
      passed: results.violations.length === 0,
      violations: results.violations,
    };
  }

  /**
   * Test basic component rendering
   */
  testBasicRendering(testCases: ComponentTestCase[]): void {
    describe(`✅ Basic Rendering - ${this.config.componentName}`, () => {
      test.each(testCases)('$name', async (testCase) => {
        const renderResult = this.renderComponent(testCase.props);

        // Test basic presence
        expect(renderResult.container).toBeInTheDocument();

        // Test custom expectations
        if (testCase.expectations) {
          const element = renderResult.getByRole('button') || renderResult.container.firstChild;

          // Test classes
          if (testCase.expectations.shouldHaveClass) {
            testCase.expectations.shouldHaveClass.forEach(className => {
              expect(element).toHaveClass(className);
            });
          }

          // Test attributes
          if (testCase.expectations.shouldHaveAttribute) {
            Object.entries(testCase.expectations.shouldHaveAttribute).forEach(([attr, value]) => {
              expect(element).toHaveAttribute(attr, value);
            });
          }

          if (testCase.expectations.shouldNotHaveAttribute) {
            testCase.expectations.shouldNotHaveAttribute.forEach(attr => {
              expect(element).not.toHaveAttribute(attr);
            });
          }

          // Test disabled state
          if (testCase.expectations.shouldBeDisabled !== undefined) {
            const interactiveElement = renderResult.getByRole('button') ||
                                      renderResult.getByRole('input') ||
                                      renderResult.getByRole('textbox') ||
                                      element;

            if (testCase.expectations.shouldBeDisabled) {
              expect(interactiveElement).toBeDisabled();
            } else {
              expect(interactiveElement).not.toBeDisabled();
            }
          }

          // Test visibility
          if (testCase.expectations.shouldBeVisible !== undefined) {
            if (testCase.expectations.shouldBeVisible) {
              expect(element).toBeVisible();
            } else {
              expect(element).not.toBeVisible();
            }
          }
        }

        // Run custom test if provided
        if (testCase.customTest) {
          await testCase.customTest(renderResult);
        }

        // Test accessibility
        if (!this.config.accessibilityConfig?.skipAxeTesting) {
          const accessibilityResults = await this.testAccessibility(renderResult);
          expect(accessibilityResults.passed).toBe(true);

          if (!accessibilityResults.passed) {
            console.warn('Accessibility violations:', accessibilityResults.violations);
          }
        }
      });
    });
  }

  /**
   * Test mouse interactions
   */
  testMouseInteractions(testCases: InteractionTestCase[]): void {
    if (this.config.interactionConfig?.skipMouseTesting) {
      return;
    }

    describe(`🖱️ Mouse Interactions - ${this.config.componentName}`, () => {
      test.each(testCases)('$name', async (testCase) => {
        const mockCallback = vi.fn();
        const propsWithCallback = {
          ...testCase.props,
          onClick: mockCallback,
          onMouseEnter: mockCallback,
          onMouseLeave: mockCallback,
        };

        const renderResult = this.renderComponent(propsWithCallback);
        const target = testCase.targetSelector
          ? renderResult.container.querySelector(testCase.targetSelector)
          : renderResult.container.firstChild as Element;

        expect(target).toBeInTheDocument();

        switch (testCase.interactionType) {
          case 'hover':
            await this.userEvent.hover(target);
            break;
          case 'click':
            await this.userEvent.click(target);
            break;
          case 'input':
            if (testCase.interactionParams?.text) {
              await this.userEvent.type(target, testCase.interactionParams.text);
            }
            break;
        }

        // Test expected outcomes
        if (testCase.expectedOutcome) {
          if (testCase.expectedOutcome.shouldHaveBeenCalled) {
            expect(mockCallback).toHaveBeenCalled();
          }

          if (testCase.expectedOutcome.shouldHaveClass) {
            expect(target).toHaveClass(testCase.expectedOutcome.shouldHaveClass);
          }

          if (testCase.expectedOutcome.shouldHaveAttribute) {
            Object.entries(testCase.expectedOutcome.shouldHaveAttribute).forEach(([attr, value]) => {
              expect(target).toHaveAttribute(attr, value);
            });
          }
        }
      });
    });
  }

  /**
   * Test keyboard interactions
   */
  testKeyboardInteractions(testCases: InteractionTestCase[]): void {
    if (this.config.interactionConfig?.skipKeyboardTesting) {
      return;
    }

    describe(`⌨️ Keyboard Interactions - ${this.config.componentName}`, () => {
      test.each(testCases)('$name', async (testCase) => {
        const mockCallback = vi.fn();
        const propsWithCallback = {
          ...testCase.props,
          onKeyDown: mockCallback,
          onKeyUp: mockCallback,
          onFocus: mockCallback,
          onBlur: mockCallback,
        };

        const renderResult = this.renderComponent(propsWithCallback);
        const target = testCase.targetSelector
          ? renderResult.container.querySelector(testCase.targetSelector)
          : renderResult.container.firstChild as Element;

        expect(target).toBeInTheDocument();

        // Focus the element first
        target.focus();
        expect(target).toHaveFocus();

        // Perform keyboard interaction
        switch (testCase.interactionType) {
          case 'focus':
            // Already focused above
            break;
          case 'blur':
            target.blur();
            break;
          case 'keydown':
          case 'keyup':
            if (testCase.interactionParams?.key) {
              await this.userEvent.keyboard(`{${testCase.interactionParams.key}}`);
            }
            break;
        }

        // Test expected outcomes
        if (testCase.expectedOutcome) {
          if (testCase.expectedOutcome.shouldHaveBeenCalled) {
            expect(mockCallback).toHaveBeenCalled();
          }

          if (testCase.expectedOutcome.shouldHaveClass) {
            expect(target).toHaveClass(testCase.expectedOutcome.shouldHaveClass);
          }
        }
      });
    });
  }

  /**
   * Test component states and prop variations
   */
  testComponentStates(stateTestCases: Array<{
    name: string;
    props: Partial<TProps>;
    expectedState: string;
    expectedClasses?: string[];
    expectedAttributes?: Record<string, string>;
  }>): void {
    describe(`🔄 Component States - ${this.config.componentName}`, () => {
      test.each(stateTestCases)('$name', async ({ props, expectedState, expectedClasses, expectedAttributes }) => {
        const renderResult = this.renderComponent(props as TProps);
        const element = renderResult.container.firstChild as Element;

        expect(element).toBeInTheDocument();

        if (expectedClasses) {
          expectedClasses.forEach(className => {
            expect(element).toHaveClass(className);
          });
        }

        if (expectedAttributes) {
          Object.entries(expectedAttributes).forEach(([attr, value]) => {
            expect(element).toHaveAttribute(attr, value);
          });
        }
      });
    });
  }

  /**
   * Test edge cases and error handling
   */
  testEdgeCases(edgeCases: Array<{
    name: string;
    props: Partial<TProps>;
    shouldHandleGracefully: boolean;
    expectedBehavior?: string;
  }>): void {
    describe(`🎯 Edge Cases - ${this.config.componentName}`, () => {
      test.each(edgeCases)('$name', async ({ props, shouldHandleGracefully, expectedBehavior }) => {
        expect(() => {
          const renderResult = this.renderComponent(props as TProps);

          if (shouldHandleGracefully) {
            expect(renderResult.container).toBeInTheDocument();
          }
        }).not.toThrow();
      });
    });
  }

  /**
   * Run all tests for the component
   */
  runFullTestSuite({
    renderingTests = [],
    mouseTests = [],
    keyboardTests = [],
    stateTests = [],
    edgeCases = [],
  }: {
    renderingTests?: ComponentTestCase[];
    mouseTests?: InteractionTestCase[];
    keyboardTests?: InteractionTestCase[];
    stateTests?: Array<{
      name: string;
      props: Partial<TProps>;
      expectedState: string;
      expectedClasses?: string[];
      expectedAttributes?: Record<string, string>;
    }>;
    edgeCases?: Array<{
      name: string;
      props: Partial<TProps>;
      shouldHandleGracefully: boolean;
      expectedBehavior?: string;
    }>;
  } = {}): void {
    // Run all test categories
    if (renderingTests.length > 0) {
      this.testBasicRendering(renderingTests);
    }

    if (mouseTests.length > 0) {
      this.testMouseInteractions(mouseTests);
    }

    if (keyboardTests.length > 0) {
      this.testKeyboardInteractions(keyboardTests);
    }

    if (stateTests.length > 0) {
      this.testComponentStates(stateTests);
    }

    if (edgeCases.length > 0) {
      this.testEdgeCases(edgeCases);
    }
  }
}

/**
 * Utility functions for common testing patterns
 */
export const TestUtils = {
  /**
   * Create mock props for testing
   */
  createMockProps<T extends Record<string, any>>(defaults: T, overrides: Partial<T> = {}): T {
    return { ...defaults, ...overrides };
  },

  /**
   * Test accessibility for any rendered component
   */
  async testAccessibility(renderResult: RenderResult, rules?: Record<string, any>) {
    const results = await axe(renderResult.container, { rules });
    expect(results).toHaveNoViolations();
    return results;
  },

  /**
   * Generate test cases for all variants of a component
   */
  generateVariantTests<T extends Record<string, any>>(
    variants: Array<{ name: string; props: T }>,
    componentClass: new (props: T) => any
  ): ComponentTestCase[] {
    return variants.map(variant => ({
      name: `renders ${variant.name} variant correctly`,
      props: variant.props,
      expectations: {
        shouldBeVisible: true,
      },
    }));
  },

  /**
   * Test component performance
   */
  async testPerformance(renderFunction: () => RenderResult, maxRenderTime = 100): Promise<number> {
    const startTime = performance.now();
    const renderResult = renderFunction();
    const endTime = performance.now();

    const renderTime = endTime - startTime;
    expect(renderTime).toBeLessThan(maxRenderTime);

    return renderTime;
  },
};

/**
 * Predefined accessibility rules for different component types
 */
export const AccessibilityRules = {
  interactive: {
    'button-name': { enabled: true },
    'focus-order-semantics': { enabled: true },
    'keyboard-navigation': { enabled: true },
    'color-contrast': { enabled: true },
  },
  informative: {
    'label-title-only': { enabled: false }, // Allow title-only for simple components
    'color-contrast': { enabled: true },
  },
  decorative: {
    'aria-hidden-body': { enabled: false }, // Allow decorative elements
  },
};

/**
 * Export default testing configuration
 */
export const DefaultTestConfig: Partial<ComponentTestConfig> = {
  accessibilityConfig: {
    skipAxeTesting: false,
  },
  interactionConfig: {
    skipMouseTesting: false,
    skipKeyboardTesting: false,
    skipTouchTesting: true, // Skip touch testing by default
  },
};

export default ComponentTestSuite;
