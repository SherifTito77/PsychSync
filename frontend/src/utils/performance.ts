// frontend/src/utils/performance.ts
/**
 * Performance monitoring and optimization utilities for the frontend
 */
import React from 'react';
// =============================================================================
// PERFORMANCE MONITORING
// =============================================================================
export interface PerformanceMetrics {
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  ttfb: number; // Time to First Byte
}
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: PerformanceObserver[] = [];
  private constructor() {
    this.initializeObservers();
  }
  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }
  private initializeObservers() {
    if (typeof window === 'undefined' || !window.performance) return;
    // First Contentful Paint
    this.observePerformanceEntry('paint', (entries) => {
      for (const entry of entries.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.fcp = entry.startTime;
          break;
        }
      }
    });
    // Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          if (lastEntry) {
            this.metrics.lcp = lastEntry.startTime;
          }
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);
      } catch (e) {
        console.warn('LCP observer not supported:', e);
      }
    }
    // First Input Delay
    try {
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (entry.processingStart) {
            this.metrics.fid = entry.processingStart - entry.startTime;
          }
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
      this.observers.push(fidObserver);
    } catch (e) {
      console.warn('FID observer not supported:', e);
    }
    // Cumulative Layout Shift
    try {
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            this.metrics.cls = clsValue;
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(clsObserver);
    } catch (e) {
      console.warn('CLS observer not supported:', e);
    }
    // Navigation Timing (for TTFB)
    this.observePerformanceEntry('navigation', (entries) => {
      const navEntry = entries[0] as PerformanceNavigationTiming;
      if (navEntry) {
        this.metrics.ttfb = navEntry.responseStart - navEntry.requestStart;
      }
    });
  }
  private observePerformanceEntry(type: string, callback: (entries: PerformanceObserverEntryList) => void) {
    try {
      const observer = new PerformanceObserver(callback);
      observer.observe({ entryTypes: [type] });
      this.observers.push(observer);
    } catch (e) {
      console.warn(`Performance observer for ${type} not supported:`, e);
    }
  }
  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }
  generateReport(): string {
    const metrics = this.metrics;
    const report = [
      '🚀 PsychSync Frontend Performance Report',
      '='.repeat(40),
      '',
    ];
    if (metrics.fcp !== undefined) {
      const fcpStatus = metrics.fcp < 1800 ? '✅ Good' : metrics.fcp < 3000 ? '⚠️ Needs Improvement' : '❌ Poor';
      report.push(`First Contentful Paint: ${metrics.fcp.toFixed(0)}ms ${fcpStatus}`);
    }
    if (metrics.lcp !== undefined) {
      const lcpStatus = metrics.lcp < 2500 ? '✅ Good' : metrics.lcp < 4000 ? '⚠️ Needs Improvement' : '❌ Poor';
      report.push(`Largest Contentful Paint: ${metrics.lcp.toFixed(0)}ms ${lcpStatus}`);
    }
    if (metrics.fid !== undefined) {
      const fidStatus = metrics.fid < 100 ? '✅ Good' : metrics.fid < 300 ? '⚠️ Needs Improvement' : '❌ Poor';
      report.push(`First Input Delay: ${metrics.fid.toFixed(0)}ms ${fidStatus}`);
    }
    if (metrics.cls !== undefined) {
      const clsStatus = metrics.cls < 0.1 ? '✅ Good' : metrics.cls < 0.25 ? '⚠️ Needs Improvement' : '❌ Poor';
      report.push(`Cumulative Layout Shift: ${metrics.cls.toFixed(3)} ${clsStatus}`);
    }
    if (metrics.ttfb !== undefined) {
      const ttfbStatus = metrics.ttfb < 600 ? '✅ Good' : metrics.ttfb < 1000 ? '⚠️ Needs Improvement' : '❌ Poor';
      report.push(`Time to First Byte: ${metrics.ttfb.toFixed(0)}ms ${ttfbStatus}`);
    }
    report.push('');
    report.push('💡 Tips for better performance:');
    report.push('- Use lazy loading for images and components');
    report.push('- Optimize bundle size with code splitting');
    report.push('- Implement service workers for caching');
    report.push('- Use CDNs for static assets');
    return report.join('\n');
  }
  disconnect() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}
// =============================================================================
// RESOURCE OPTIMIZATION
// =============================================================================
export class ResourceOptimizer {
  private static preloadedResources = new Set<string>();
  static preloadResource(url: string, type: 'image' | 'font' | 'script' | 'style' = 'script') {
    if (this.preloadedResources.has(url)) return;
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = url;
    link.as = type;
    if (type === 'font') {
      link.crossOrigin = 'anonymous';
    }
    document.head.appendChild(link);
    this.preloadedResources.add(url);
  }
  static preloadCriticalResources() {
    // Preload critical fonts
    this.preloadResource('/fonts/inter-var.woff2', 'font');
    // Preload critical images
    this.preloadResource('/images/logo.svg', 'image');
    // Preload critical stylesheets
    this.preloadResource('/css/critical.css', 'style');
  }
  static optimizeImages() {
    // Add loading="lazy" to all images that don't have it
    const images = document.querySelectorAll('img:not([loading])');
    images.forEach(img => {
      img.setAttribute('loading', 'lazy');
    });
  }
  static createServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('✅ Service Worker registered:', registration);
        })
        .catch(error => {
          console.log('❌ Service Worker registration failed:', error);
        });
    }
  }
}
// =============================================================================
// BUNDLE ANALYSIS
// =============================================================================
export interface BundleInfo {
  name: string;
  size: number;
  chunks: string[];
}
export class BundleAnalyzer {
  static getBundleInfo(): BundleInfo[] {
    // This would typically be populated by webpack-bundle-analyzer
    // For now, return estimated bundle sizes
    return [
      {
        name: 'main',
        size: 250000, // 250KB
        chunks: ['main']
      },
      {
        name: 'vendor',
        size: 180000, // 180KB
        chunks: ['vendor']
      },
      {
        name: 'components',
        size: 95000, // 95KB
        chunks: ['components']
      }
    ];
  }
  static getOptimizationSuggestions(): string[] {
    const bundles = this.getBundleInfo();
    const totalSize = bundles.reduce((sum, bundle) => sum + bundle.size, 0);
    const suggestions: string[] = [];
    if (totalSize > 500000) { // > 500KB
      suggestions.push('💡 Bundle size is large. Consider code splitting.');
    }
    if (bundles.some(b => b.size > 200000)) {
      suggestions.push('💡 Some bundles are large. Use dynamic imports.');
    }
    suggestions.push('💡 Enable gzip compression on the server.');
    suggestions.push('💡 Use CDN for static assets.');
    suggestions.push('💡 Implement tree shaking to remove unused code.');
    return suggestions;
  }
}
// =============================================================================
// PERFORMANCE MONITORING HOOK
// =============================================================================
export const usePerformanceMonitoring = () => {
  const [metrics, setMetrics] = React.useState<Partial<PerformanceMetrics>>({});
  const [isVisible, setIsVisible] = React.useState(false);
  React.useEffect(() => {
    const monitor = PerformanceMonitor.getInstance();
    // Update metrics periodically
    const interval = setInterval(() => {
      setMetrics(monitor.getMetrics());
    }, 1000);
    // Show performance monitor in development
    if (process.env.NODE_ENV === 'development') {
      setTimeout(() => setIsVisible(true), 2000);
    }
    return () => {
      clearInterval(interval);
    };
  }, []);
  const toggleVisibility = React.useCallback(() => {
    setIsVisible(prev => !prev);
  }, []);
  return {
    metrics,
    isVisible,
    toggleVisibility,
    report: PerformanceMonitor.getInstance().generateReport(),
  };
};
// =============================================================================
// INITIALIZATION
// =============================================================================
export const initializePerformanceOptimizations = () => {
  // Preload critical resources
  ResourceOptimizer.preloadCriticalResources();
  // Optimize images after page load
  window.addEventListener('load', () => {
    ResourceOptimizer.optimizeImages();
    ResourceOptimizer.createServiceWorker();
  });
  // Log performance metrics after page load
  window.addEventListener('load', () => {
    setTimeout(() => {
      const monitor = PerformanceMonitor.getInstance();
      console.log(monitor.generateReport());
    }, 3000);
  });
  // Initialize performance monitoring
  const monitor = PerformanceMonitor.getInstance();
  return monitor;
};
// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================
export const measureRenderTime = <T>(
  componentName: string,
  renderFn: () => T
): T => {
  const startTime = performance.now();
  const result = renderFn();
  const endTime = performance.now();
  const renderTime = endTime - startTime;
  if (renderTime > 16) { // > 60fps threshold
    console.warn(`⚠️ ${componentName} render took ${renderTime.toFixed(2)}ms`);
  }
  return result;
};
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): T => {
  let timeout: NodeJS.Timeout;
  return ((...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  }) as T;
};
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): T => {
  let inThrottle: boolean;
  return ((...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  }) as T;
};
export default PerformanceMonitor;