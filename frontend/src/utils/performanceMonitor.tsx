/**
 * Performance Monitoring Utilities for React Components
 *
 * These hooks help detect unnecessary re-renders and effect re-runs
 * during development. Use them to identify performance bottlenecks.
 *
 * ✅ USAGE:
 * - Add useRenderCount to component to track render count
 * - Add useEffectWatch to effects to monitor dependency changes
 * - Add useWhyDidYouUpdate to understand why components re-render
 */

import React, { useEffect, useRef, DependencyList, useCallback, useState, useMemo } from 'react';

/**
 * Track and log component render counts
 *
 * Helps identify components that are rendering too frequently
 *
 * @example
 * function MyComponent() {
 *   useRenderCount('MyComponent');
 *   return <div>Hello</div>;
 * }
 */
export function useRenderCount(componentName: string) {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current += 1;

    if (process.env.NODE_ENV === 'development') {
      console.log(
        `🔄 [${componentName}] Render count: ${renderCount.current}`
      );

      // Warn if component renders more than 10 times
      if (renderCount.current > 10) {
        console.warn(
          `⚠️  [${componentName}] High render count detected: ${renderCount.current}`
        );
      }
    }
  });
}

/**
 * Monitor effect dependency changes
 *
 * Helps identify which dependencies are causing effect re-runs
 *
 * @param effectName - Name of the effect for logging
 * @param deps - Dependency array from useEffect
 *
 * @example
 * useEffect(() => {
 *   // effect logic
 * }, [dependency1, dependency2]);
 *
 * // Add useWhyDidYouUpdate to track which deps changed
 * useEffectWatch('MyEffect', [dependency1, dependency2]);
 */
export function useEffectWatch(effectName: string, deps: DependencyList) {
  const prevDeps = useRef<DependencyList>();

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    if (prevDeps.current) {
      const changedDeps: Array<{ index: number; prev: any; curr: any }> = [];

      deps.forEach((dep, i) => {
        if (dep !== prevDeps.current[i]) {
          changedDeps.push({
            index: i,
            prev: prevDeps.current[i],
            curr: dep,
          });
        }
      });

      if (changedDeps.length > 0) {
        console.log(
          `⚡ [${effectName}] Re-run. Changed dependencies:`,
          changedDeps.map((d) => ({
            index: d.index,
            prev: typeof d.prev === 'object' ? '[Object]' : d.prev,
            curr: typeof d.curr === 'object' ? '[Object]' : d.curr,
          }))
        );
      }
    }

    prevDeps.current = deps;
  }, deps);
}

/**
 * Track why a component re-rendered
 *
 * Helps understand which props or state changes caused re-render
 *
 * @param props - Current props
 * @param componentName - Name of the component
 *
 * @example
 * function MyComponent(props) {
 *   useWhyDidYouUpdate(props, 'MyComponent');
 *   return <div>{props.value}</div>;
 * }
 */
export function useWhyDidYouUpdate(props: Record<string, any>, componentName: string) {
  const prevProps = useRef<Record<string, any>>();

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    if (prevProps.current) {
      const allKeys = Object.keys({ ...prevProps.current, ...props });
      const changedProps: Record<string, { from: any; to: any }> = {};

      allKeys.forEach((key) => {
        if (prevProps.current[key] !== props[key]) {
          changedProps[key] = {
            from: prevProps.current[key],
            to: props[key],
          };
        }
      });

      if (Object.keys(changedProps).length > 0) {
        console.log(
          `🔍 [${componentName}] Why did it re-render?`,
          changedProps
        );
      }
    }

    prevProps.current = props;
  });
}

/**
 * Measure render performance
 *
 * Tracks how long renders take and logs warnings for slow renders
 *
 * @param componentName - Name of the component
 * @param thresholdMs - Threshold in ms for warning (default: 16ms for 60fps)
 *
 * @example
 * function MyComponent() {
 *   useRenderPerformance('MyComponent');
 *   return <div>Complex UI</div>;
 * }
 */
export function useRenderPerformance(
  componentName: string,
  thresholdMs: number = 16
) {
  const renderStartTime = useRef<number>();

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    if (renderStartTime.current) {
      const renderTime = performance.now() - renderStartTime.current;

      if (renderTime > thresholdMs) {
        console.warn(
          `⚠️  [${componentName}] Slow render detected: ${renderTime.toFixed(2)}ms (threshold: ${thresholdMs}ms)`
        );
      }
    }

    renderStartTime.current = performance.now();
  });
}

/**
 * Check if component is being rendered unnecessarily
 *
 * Compares current props/state with previous to detect changes
 *
 * @param componentName - Name of the component
 * @param props - Component props (optional)
 * @param state - Component state (optional)
 *
 * @example
 * function MyComponent(props) {
 *   const [count, setCount] = useState(0);
 *   useDetectUnnecessaryRenders('MyComponent', { props: props, state: { count } });
 *   return <div>{count}</div>;
 * }
 */
export function useDetectUnnecessaryRenders(
  componentName: string,
  data: {
    props?: Record<string, any>;
    state?: Record<string, any>;
  } = {}
) {
  const prevData = useRef<{
    props?: Record<string, any>;
    state?: Record<string, any>;
  }>();

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development' || !prevData.current) {
      prevData.current = data;
      return;
    }

    const hasChanges =
      (data.props &&
        JSON.stringify(data.props) !== JSON.stringify(prevData.current.props)) ||
      (data.state &&
        JSON.stringify(data.state) !== JSON.stringify(prevData.current.state));

    if (!hasChanges) {
      console.warn(
        `❌ [${componentName}] Unnecessary render detected! No props or state changed.`
      );
    }

    prevData.current = data;
  });
}

/**
 * Performance marker for measuring specific operations
 *
 * @param label - Label for the measurement
 *
 * @example
 * function MyComponent() {
 *   useEffect(() => {
 *     performanceMark('data-fetch-start');
 *     fetchData().then(() => {
 *       performanceMark('data-fetch-end');
 *       performanceMeasure('data-fetch', 'data-fetch-start', 'data-fetch-end');
 *     });
 *   }, []);
 * }
 */
export function performanceMark(label: string) {
  if (process.env.NODE_ENV === 'development' && typeof performance !== 'undefined') {
    performance.mark(`${label}-mark`);
  }
}

/**
 * Measure time between two performance marks
 *
 * @param measureName - Name for the measurement
 * @param startMark - Starting mark label
 * @param endMark - Ending mark label
 *
 * @example
 * performanceMeasure('Operation', 'start-mark', 'end-mark');
 */
export function performanceMeasure(
  measureName: string,
  startMark: string,
  endMark: string
) {
  if (process.env.NODE_ENV === 'development' && typeof performance !== 'undefined') {
    try {
      performance.measure(
        measureName,
        `${startMark}-mark`,
        `${endMark}-mark`
      );

      const measures = performance.getEntriesByName(measureName, 'measure');
      const lastMeasure = measures[measures.length - 1];

      if (lastMeasure) {
        console.log(`⏱️  [${measureName}] Duration: ${lastMeasure.duration.toFixed(2)}ms`);
      }

      // Clean up marks
      performance.clearMarks(`${startMark}-mark`);
      performance.clearMarks(`${endMark}-mark`);
      performance.clearMeasures(measureName);
    } catch (e) {
      console.error('Performance measure error:', e);
    }
  }
}

/**
 * Hook to measure async operation performance
 *
 * @param operationName - Name of the async operation
 *
 * @example
 * function MyComponent() {
 *   const measureAsync = useAsyncOperation('Data Fetch');
 *
 *   useEffect(() => {
 *     measureAsync(async () => {
 *       await fetchData();
 *     });
 *   }, []);
 *
 *   return <div>Loading...</div>;
 * }
 */
export function useAsyncOperation(operationName: string) {
  return useCallback(
    async function <T>(asyncFn: () => Promise<T>): Promise<T> {
      if (process.env.NODE_ENV === 'development') {
        const startMark = `${operationName}-start`;
        const endMark = `${operationName}-end`;

        performanceMark(startMark);

        try {
          const result = await asyncFn();

          performanceMark(endMark);
          performanceMeasure(operationName, startMark, endMark);

          return result;
        } catch (error) {
          performanceMark(`${operationName}-error`);
          performanceMeasure(operationName, startMark, `${operationName}-error`);
          throw error;
        }
      } else {
        return asyncFn();
      }
    },
    [operationName]
  );
}

/**
 * Development-only performance logger
 *
 * Automatically logs render counts, effect runs, and prop changes
 * in development mode.
 *
 * @example
 * function MyComponent({ value }) {
 *   useDevModePerformance('MyComponent', { props: { value } });
 *   return <div>{value}</div>;
 * }
 */
export function useDevModePerformance(
  componentName: string,
  options?: {
    props?: Record<string, any>;
    state?: Record<string, any>;
    logRenders?: boolean;
    logEffects?: boolean;
  }
) {
  // Log renders
  if (options?.logRenders !== false) {
    useRenderCount(componentName);
  }

  // Track prop/state changes
  if (options?.props || options?.state) {
    useWhyDidYouUpdate(
      options.props || options.state || {},
      componentName
    );
  }
}

/**
 * Create a performance-optimized memoized component wrapper
 *
 * Wraps React.memo with additional logging in development
 *
 * @example
 * const OptimizedComponent = withPerformanceLogging(
 *   'MyComponent',
 *   React.memo(function MyComponent({ value }) {
 *     return <div>{value}</div>;
 *   })
 * );
 */
export function withPerformanceLogging<P extends object>(
  componentName: string,
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  if (process.env.NODE_ENV === 'development') {
    return function PerformanceLoggedComponent(props: P) {
      useRenderCount(componentName);
      useWhyDidYouUpdate(props, componentName);

      return <Component {...props} />;
    };
  }

  return Component;
}
