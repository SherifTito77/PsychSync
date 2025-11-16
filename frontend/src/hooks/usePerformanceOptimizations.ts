// frontend/src/hooks/usePerformanceOptimizations.ts
/**
 * Performance optimization hooks for React components
 * Provides memoization, virtualization, and performance monitoring
 */
import { useCallback, useRef, useEffect, useMemo, useState } from 'react';
// =============================================================================
// PERFORMANCE MONITORING
// =============================================================================
interface PerformanceMetrics {
  renderCount: number;
  lastRenderTime: number;
  averageRenderTime: number;
  renderTimes: number[];
}
export const usePerformanceMonitor = (componentName: string) => {
  const renderCountRef = useRef(0);
  const renderTimesRef = useRef<number[]>([]);
  const lastRenderTimeRef = useRef<number>(0);
  useEffect(() => {
    const startTime = performance.now();
    renderCountRef.current += 1;
    // Clean up old render times (keep last 10)
    if (renderTimesRef.current.length > 10) {
      renderTimesRef.current = renderTimesRef.current.slice(-10);
    }
    renderTimesRef.current.push(startTime);
    lastRenderTimeRef.current = startTime;
    // Log performance warnings in development
    if (process.env.NODE_ENV === 'development') {
      const avgRenderTime = renderTimesRef.current.reduce((a, b) => a + b, 0) / renderTimesRef.current.length;
      if (avgRenderTime > 16) { // > 60fps threshold
        console.warn(`⚠️ ${componentName} render performance: ${avgRenderTime.toFixed(2)}ms average`);
      }
    }
  });
  const metrics = useMemo((): PerformanceMetrics => ({
    renderCount: renderCountRef.current,
    lastRenderTime: lastRenderTimeRef.current,
    averageRenderTime: renderTimesRef.current.length > 0
      ? renderTimesRef.current.reduce((a, b) => a + b, 0) / renderTimesRef.current.length
      : 0,
    renderTimes: [...renderTimesRef.current],
  }), []);
  return metrics;
};
// =============================================================================
// DEBOUNCED AND THROTTLED OPERATIONS
// =============================================================================
// Native implementation of debounce
function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  let timeoutId: NodeJS.Timeout;
  return ((...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  }) as T;
}
// Native implementation of throttle
function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  let inThrottle: boolean;
  return ((...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, delay);
    }
  }) as T;
}
export const useDebouncedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T => {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;
  return useMemo(
    () => debounce((...args: Parameters<T>) => callbackRef.current(...args), delay),
    [delay, ...deps]
  ) as T;
};
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  deps: React.DependencyList = []
): T => {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;
  return useMemo(
    () => throttle((...args: Parameters<T>) => callbackRef.current(...args), delay),
    [delay, ...deps]
  ) as T;
};
// =============================================================================
// INFINITE SCROLL AND VIRTUALIZATION HELPERS
// =============================================================================
interface VirtualScrollConfig {
  itemHeight: number;
  containerHeight: number;
  overscan: number;
}
export const useVirtualScroll = <T>(
  items: T[],
  config: VirtualScrollConfig
) => {
  const [scrollTop, setScrollTop] = useState(0);
  const { itemHeight, containerHeight, overscan } = config;
  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1);
  }, [items, visibleRange]);
  const totalHeight = items.length * itemHeight;
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);
  return {
    visibleItems,
    totalHeight,
    startIndex: visibleRange.startIndex,
    endIndex: visibleRange.endIndex,
    handleScroll,
    offsetY: visibleRange.startIndex * itemHeight,
  };
};
export const useInfiniteScroll = (
  hasMore: boolean,
  onLoadMore: () => void,
  threshold: number = 200
) => {
  const [isLoading, setIsLoading] = useState(false);
  const handleScroll = useCallback(
    throttle((e: React.UIEvent<HTMLDivElement>) => {
      const element = e.currentTarget;
      const isNearBottom = element.scrollHeight - element.scrollTop - element.clientHeight <= threshold;
      if (isNearBottom && hasMore && !isLoading) {
        setIsLoading(true);
        onLoadMore();
        // Reset loading state after a reasonable timeout
        setTimeout(() => setIsLoading(false), 1000);
      }
    }, 200),
    [hasMore, isLoading, onLoadMore, threshold]
  );
  return { handleScroll, isLoading };
};
// =============================================================================
// IMAGE AND RESOURCE OPTIMIZATION
// =============================================================================
export const useLazyImage = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setImageSrc(src);
      setIsLoaded(true);
      setError(null);
    };
    img.onerror = () => {
      setError('Failed to load image');
      setIsLoaded(false);
    };
    // Start loading the image
    img.src = src;
    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src, placeholder]);
  return { imageSrc, isLoaded, error };
};
export const usePreloadResources = (resources: string[]) => {
  const [loadedResources, setLoadedResources] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Set<string>>(new Set());
  useEffect(() => {
    resources.forEach(resource => {
      if (loadedResources.has(resource)) return;
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = resource;
      // Determine resource type
      if (resource.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
        link.as = 'image';
      } else if (resource.match(/\.(woff|woff2|ttf|eot)$/i)) {
        link.as = 'font';
        link.crossOrigin = 'anonymous';
      } else if (resource.match(/\.(css)$/i)) {
        link.as = 'style';
      } else if (resource.match(/\.(js)$/i)) {
        link.as = 'script';
      } else {
        link.as = 'fetch';
      }
      link.onload = () => {
        setLoadedResources(prev => new Set([...prev, resource]));
      };
      link.onerror = () => {
        setErrors(prev => new Set([...prev, resource]));
      };
      document.head.appendChild(link);
    });
  }, [resources]);
  return {
    loadedCount: loadedResources.size,
    totalCount: resources.length,
    isFullyLoaded: loadedResources.size === resources.length,
    errors: Array.from(errors),
  };
};
// =============================================================================
// CACHE AND STATE MANAGEMENT OPTIMIZATION
// =============================================================================
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}
class DataCache {
  private cache = new Map<string, CacheEntry<any>>();
  private maxSize: number;
  private defaultTTL: number;
  constructor(maxSize = 100, defaultTTL = 300000) { // 5 minutes default TTL
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
  }
  set<T>(key: string, data: T, ttl = this.defaultTTL): void {
    // Remove oldest entry if cache is full
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    return entry.data;
  }
  clear(): void {
    this.cache.clear();
  }
  size(): number {
    return this.cache.size;
  }
}
export const useDataCache = (maxSize = 100, defaultTTL = 300000) => {
  const cacheRef = useRef(new DataCache(maxSize, defaultTTL));
  return {
    set: useCallback(<T>(key: string, data: T, ttl?: number) => {
      cacheRef.current.set(key, data, ttl);
    }, []),
    get: useCallback(<T>(key: string): T | null => {
      return cacheRef.current.get<T>(key);
    }, []),
    clear: useCallback(() => {
      cacheRef.current.clear();
    }, []),
    size: useCallback(() => {
      return cacheRef.current.size();
    }, []),
  };
};
// =============================================================================
// FORM AND INPUT OPTIMIZATION
// =============================================================================
export const useOptimizedForm = <T extends Record<string, any>>(
  initialValues: T,
  validate?: (values: T) => Partial<Record<keyof T, string>>,
  debounceMs = 300
) => {
  const [values, setValues] = useState<T>(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Debounced validation
  const debouncedValidate = useDebouncedCallback(
    (newValues: T) => {
      if (validate) {
        const validationErrors = validate(newValues);
        setErrors(validationErrors);
      }
    },
    debounceMs,
    [validate]
  );
  const setValue = useCallback((name: keyof T, value: any) => {
    const newValues = { ...values, [name]: value };
    setValues(newValues);
    // Mark field as touched
    setTouched(prev => ({ ...prev, [name]: true }));
    // Trigger debounced validation
    debouncedValidate(newValues);
  }, [values, debouncedValidate]);
  const setValuesBulk = useCallback((newValues: Partial<T>) => {
    const updatedValues = { ...values, ...newValues };
    setValues(updatedValues);
    // Mark all changed fields as touched
    const newTouched = { ...touched };
    Object.keys(newValues).forEach(key => {
      newTouched[key as keyof T] = true;
    });
    setTouched(newTouched);
    // Trigger debounced validation
    debouncedValidate(updatedValues);
  }, [values, touched, debouncedValidate]);
  const hasError = useCallback((name: keyof T) => {
    return touched[name] && !!errors[name];
  }, [touched, errors]);
  const isValid = useMemo(() => {
    return Object.keys(errors).length === 0;
  }, [errors]);
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);
  return {
    values,
    errors,
    touched,
    isSubmitting,
    setIsSubmitting,
    setValue,
    setValuesBulk,
    hasError,
    isValid,
    reset,
  };
};
// =============================================================================
// PERFORMANCE UTILITIES
// =============================================================================
export const useIdleCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList = []
) => {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;
  useEffect(() => {
    const handleIdle = () => {
      callbackRef.current();
    };
    // Request idle callback if available
    if ('requestIdleCallback' in window) {
      const id = (window as any).requestIdleCallback(handleIdle);
      return () => (window as any).cancelIdleCallback(id);
    } else {
      // Fallback to setTimeout
      const id = setTimeout(handleIdle, 1);
      return () => clearTimeout(id);
    }
  }, deps);
};
export const useIntersectionObserver = (
  options: IntersectionObserverInit = {}
) => {
  const [entries, setEntries] = useState<IntersectionObserverEntry[]>([]);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const observe = useCallback((element: Element) => {
    if (observerRef.current) {
      observerRef.current.observe(element);
    }
  }, []);
  const unobserve = useCallback((element: Element) => {
    if (observerRef.current) {
      observerRef.current.unobserve(element);
    }
  }, []);
  useEffect(() => {
    if (typeof IntersectionObserver !== 'undefined') {
      observerRef.current = new IntersectionObserver(setEntries, options);
    }
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [options]);
  return { entries, observe, unobserve };
};