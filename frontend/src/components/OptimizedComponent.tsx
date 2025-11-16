// frontend/src/components/OptimizedComponent.tsx
/**
 * Optimized React component wrapper with performance enhancements
 */
import React, { memo, useMemo, useCallback, ReactNode, ComponentType } from 'react';
import { usePerformanceMonitor } from '@/hooks/usePerformanceOptimizations';
// Performance-optimized wrapper for React components
export function withPerformanceMonitoring<P extends object>(
  WrappedComponent: ComponentType<P>,
  componentName: string
): ComponentType<P> {
  const MonitoredComponent = memo((props: P) => {
    usePerformanceMonitor(componentName);
    return <WrappedComponent {...props} />;
  });
  MonitoredComponent.displayName = `withPerformanceMonitoring(${componentName})`;
  return MonitoredComponent;
}
// Virtual list component for large datasets
interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => ReactNode;
  overscan?: number;
  className?: string;
}
export const VirtualList = memo(<T,>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  className = '',
}: VirtualListProps<T>) => {
  const [scrollTop, setScrollTop] = React.useState(0);
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
  return (
    <div
      className={`virtual-list ${className}`}
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: visibleRange.startIndex * itemHeight,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, index) => (
            <div
              key={visibleRange.startIndex + index}
              style={{ height: itemHeight }}
              className="virtual-list-item"
            >
              {renderItem(item, visibleRange.startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});
VirtualList.displayName = 'VirtualList';
// Lazy loading component wrapper
interface LazyComponentProps {
  fallback?: ReactNode;
  children: ReactNode;
  rootMargin?: string;
  threshold?: number;
}
export const LazyComponent = memo(({
  fallback = null,
  children,
  rootMargin = '50px',
  threshold = 0.1,
}: LazyComponentProps) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin, threshold }
    );
    observer.observe(container);
    return () => observer.disconnect();
  }, [rootMargin, threshold]);
  return (
    <div ref={containerRef}>
      {isVisible ? children : fallback}
    </div>
  );
});
LazyComponent.displayName = 'LazyComponent';
// Optimized image component with lazy loading and error handling
interface OptimizedImageProps {
  src: string;
  alt: string;
  placeholder?: string;
  className?: string;
  width?: number | string;
  height?: number | string;
  onLoad?: () => void;
  onError?: () => void;
}
export const OptimizedImage = memo(({
  src,
  alt,
  placeholder,
  className = '',
  width,
  height,
  onLoad,
  onError,
}: OptimizedImageProps) => {
  const [imageSrc, setImageSrc] = React.useState(placeholder || '');
  const [isLoaded, setIsLoaded] = React.useState(false);
  const [hasError, setHasError] = React.useState(false);
  const imgRef = React.useRef<HTMLImageElement>(null);
  React.useEffect(() => {
    const img = imgRef.current;
    if (!img) return;
    img.onload = () => {
      setImageSrc(src);
      setIsLoaded(true);
      setHasError(false);
      onLoad?.();
    };
    img.onerror = () => {
      setHasError(true);
      setIsLoaded(false);
      onError?.();
    };
    // Start loading
    img.src = src;
    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src, onLoad, onError]);
  return (
    <div className={`optimized-image ${className} ${isLoaded ? 'loaded' : 'loading'} ${hasError ? 'error' : ''}`}>
      <img
        ref={imgRef}
        src={imageSrc}
        alt={alt}
        style={{ width, height }}
        loading="lazy"
      />
      {!isLoaded && !hasError && placeholder && (
        <div className="image-placeholder" style={{ width, height }} />
      )}
      {hasError && (
        <div className="image-error" style={{ width, height }}>
          Failed to load image
        </div>
      )}
    </div>
  );
});
OptimizedImage.displayName = 'OptimizedImage';
// Performance monitor component for development
interface PerformanceMonitorProps {
  componentName: string;
  children: ReactNode;
}
export const PerformanceMonitor = memo(({
  componentName,
  children,
}: PerformanceMonitorProps) => {
  const metrics = usePerformanceMonitor(componentName);
  if (process.env.NODE_ENV !== 'development') {
    return <>{children}</>;
  }
  return (
    <>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'fixed',
            bottom: 10,
            right: 10,
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '8px',
            borderRadius: '4px',
            fontSize: '12px',
            zIndex: 9999,
          }}
        >
          <div>{componentName}</div>
          <div>Renders: {metrics.renderCount}</div>
          <div>Avg: {metrics.averageRenderTime.toFixed(2)}ms</div>
          <div>Last: {metrics.lastRenderTime.toFixed(2)}ms</div>
        </div>
      )}
    </>
  );
});
PerformanceMonitor.displayName = 'PerformanceMonitor';
// Optimized form input with debounced changes
interface OptimizedInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  onChange: (value: string) => void;
  debounceMs?: number;
}
export const OptimizedInput = memo(({
  onChange,
  debounceMs = 300,
  ...props
}: OptimizedInputProps) => {
  const [value, setValue] = React.useState(props.value || '');
  const debouncedOnChange = React.useMemo(
    () => lodash.debounce((newValue: string) => onChange(newValue), debounceMs),
    [onChange, debounceMs]
  );
  React.useEffect(() => {
    setValue(props.value || '');
  }, [props.value]);
  const handleChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setValue(newValue);
    debouncedOnChange(newValue);
  }, [debouncedOnChange]);
  // Cleanup debounce on unmount
  React.useEffect(() => {
    return () => {
      debouncedOnChange.cancel();
    };
  }, [debouncedOnChange]);
  return <input {...props} value={value} onChange={handleChange} />;
});
OptimizedInput.displayName = 'OptimizedInput';
// Code splitting utility
export const createLazyComponent = <T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  fallback: ReactNode = null,
  componentName?: string
) => {
  const LazyComponent = React.lazy(importFunc);
  const WrappedComponent = memo((props: React.ComponentProps<T>) => (
    <React.Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </React.Suspense>
  ));
  if (componentName) {
    WrappedComponent.displayName = componentName;
  }
  return WrappedComponent;
};