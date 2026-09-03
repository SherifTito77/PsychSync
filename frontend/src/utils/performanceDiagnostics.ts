/**
 * Performance Diagnostics Utility
 *
 * Helps identify performance bottlenecks in the React app
 * Run in browser console to diagnose slowness
 */

export const performanceDiagnostics = {
  /**
   * Measure component render performance
   * Usage: Call before and after component mount
   */
  measureRender(componentName: string) {
    performance.mark(`${componentName}-render-start`);
    return () => {
      performance.mark(`${componentName}-render-end`);
      performance.measure(
        `${componentName}-render`,
        `${componentName}-render-start`,
        `${componentName}-render-end`
      );

      const measure = performance.getEntriesByName(`${componentName}-render`)[0];
      console.log(`🎨 [Perf] ${componentName} rendered in ${measure.duration.toFixed(2)}ms`);

      // Clean up
      performance.clearMarks(`${componentName}-render-start`);
      performance.clearMarks(`${componentName}-render-end`);
      performance.clearMeasures(`${componentName}-render`);
    };
  },

  /**
   * Monitor React render count
   * Usage: Add to component's useEffect
   */
  trackRenderCount(componentName: string) {
    const key = `render-count-${componentName}`;
    const count = parseInt(sessionStorage.getItem(key) || '0') + 1;
    sessionStorage.setItem(key, count.toString());

    if (count % 10 === 0) {
      console.warn(`⚠️ [Perf] ${componentName} has rendered ${count} times`);
    }

    return count;
  },

  /**
   * Find all useEffect hooks and check their dependencies
   * Usage: Run in browser console
   */
  analyzeUseEffects() {
    const warnings: string[] = [];

    // Check for long tasks
    performance.getEntriesByType('measure').forEach((entry) => {
      if (entry.duration > 16) { // Longer than one frame at 60fps
        warnings.push(
          `⚠️ Long task detected: ${entry.name} took ${entry.duration.toFixed(2)}ms`
        );
      }
    });

    return warnings;
  },

  /**
   * Check for memory leaks
   */
  checkMemoryLeaks() {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const usedMB = (memory.usedJSHeapSize / 1048576).toFixed(2);
      const totalMB = (memory.totalJSHeapSize / 1048576).toFixed(2);
      const limitMB = (memory.jsHeapSizeLimit / 1048576).toFixed(2);

      console.log(`💾 [Memory] Used: ${usedMB}MB / Total: ${totalMB}MB / Limit: ${limitMB}MB`);

      if (parseFloat(usedMB) > 100) {
        console.warn('⚠️ High memory usage detected - possible memory leak');
      }

      return {
        used: parseFloat(usedMB),
        total: parseFloat(totalMB),
        limit: parseFloat(limitMB),
      };
    }

    console.warn('Memory API not available in this browser');
    return null;
  },

  /**
   * Get comprehensive performance report
   */
  generateReport() {
    console.group('📊 Performance Diagnostics Report');

    // Check render counts
    const renderCounts: Record<string, number> = {};
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key?.startsWith('render-count-')) {
        const componentName = key.replace('render-count-', '');
        renderCounts[componentName] = parseInt(sessionStorage.getItem(key) || '0');
      }
    }

    console.table(renderCounts);

    // Check for long tasks
    const warnings = this.analyzeUseEffects();
    if (warnings.length > 0) {
      console.warn('Performance warnings detected:');
      warnings.forEach((warning) => console.warn(warning));
    } else {
      console.log('✅ No long tasks detected');
    }

    // Check memory
    this.checkMemoryLeaks();

    // Check for blocked main thread
    const longTasks = performance.getEntriesByType('longtask');
    if (longTasks.length > 0) {
      console.warn(`⚠️ ${longTasks.length} long tasks detected (blocking main thread)`);
      longTasks.forEach((task) => {
        console.warn(`  - Duration: ${task.duration.toFixed(2)}ms`);
      });
    } else {
      console.log('✅ No long tasks detected');
    }

    console.groupEnd();

    return {
      renderCounts,
      warnings,
      longTasks: longTasks.length,
    };
  },

  /**
   * Clear all diagnostic data
   */
  clear() {
    // Clear render counts
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key?.startsWith('render-count-')) {
        sessionStorage.removeItem(key);
      }
    }

    // Clear performance marks
    performance.clearMarks();
    performance.clearMeasures();

    console.log('✅ Diagnostic data cleared');
  },
};

// Make available globally for easy console access
if (typeof window !== 'undefined') {
  (window as any).perfDiagnostics = performanceDiagnostics;
  console.log('✅ Performance diagnostics available as `perfDiagnostics` in console');
  console.log('  - Run `perfDiagnostics.generateReport()` for full report');
  console.log('  - Run `perfDiagnostics.checkMemoryLeaks()` for memory info');
  console.log('  - Run `perfDiagnostics.clear()` to reset data');
}
