/**
 * List Rendering Solutions Guide
 * Comprehensive solutions for common responsive list rendering problems
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

export interface ListSolutionPattern {
  id: string;
  name: string;
  description: string;
  useCase: string;
  implementation: React.ReactNode;
  cssCode: string;
  benefits: string[];
  considerations: string[];
}

export interface ResponsiveListComponentProps {
  items: any[];
  variant?: 'basic' | 'card' | 'navigation' | 'complex';
  density?: 'compact' | 'comfortable' | 'spacious';
  interactive?: boolean;
  onSelect?: (item: any) => void;
  renderItem?: (item: any, index: number) => React.ReactNode;
}

/**
 * Comprehensive solution patterns for responsive list rendering
 */
export class ListRenderingSolutions {
  /**
   * Get all solution patterns
   */
  static getAllSolutions(): ListSolutionPattern[] {
    return [
      this.getBasicResponsiveListSolution(),
      this.getCardBasedListSolution(),
      this.getNavigationListSolution(),
      this.getComplexListSolution(),
      this.getVirtualizedListSolution(),
      this.getProgressiveListSolution()
    ];
  }

  /**
   * Basic responsive list solution
   */
  static getBasicResponsiveListSolution(): ListSolutionPattern {
    return {
      id: 'basic-responsive-list',
      name: 'Basic Responsive List',
      description: 'Foundation for responsive lists with proper text handling and spacing',
      useCase: 'Simple lists with text content that need to work across all viewports',
      implementation: (
        <ResponsiveListComponent
          items={['Item 1', 'Item 2', 'Item 3']}
          variant="basic"
          density="comfortable"
        />
      ),
      cssCode: `
.responsive-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.responsive-list-item {
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  line-height: 1.5;
  word-wrap: break-word;
  overflow-wrap: break-word;
  min-height: 44px; /* Touch target size */
  display: flex;
  align-items: center;
}

/* Mobile */
@media (max-width: 767px) {
  .responsive-list-item {
    padding: 12px 16px;
    font-size: 16px; /* Prevent zoom on iOS */
  }
}

/* Tablet */
@media (min-width: 768px) and (max-width: 1023px) {
  .responsive-list-item {
    padding: 14px 20px;
    font-size: 16px;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .responsive-list-item {
    padding: 16px 24px;
    font-size: 16px;
  }
}

/* Text overflow handling */
.responsive-list-item--truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.responsive-list-item--wrap {
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
}
      `,
      benefits: [
        'Consistent spacing across viewports',
        'Proper touch target sizes',
        'Text wrapping for long content',
        'Accessibility compliant',
        'Minimal CSS requirements'
      ],
      considerations: [
        'May need custom styling for complex content',
        'Consider nested lists for hierarchical data'
      ]
    };
  }

  /**
   * Card-based list solution for complex content
   */
  static getCardBasedListSolution(): ListSolutionPattern {
    return {
      id: 'card-based-list',
      name: 'Card-Based List',
      description: 'Rich list items with cards, avatars, and actions',
      useCase: 'Complex list items with multiple content types (avatar, title, description, actions)',
      implementation: (
        <ResponsiveListComponent
          items={[
            { title: 'Card Item 1', description: 'Description', avatar: 'A1' },
            { title: 'Card Item 2', description: 'Another description', avatar: 'A2' }
          ]}
          variant="card"
          density="comfortable"
        />
      ),
      cssCode: `
.card-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-list-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-height: 44px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card-list-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-list-avatar {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #007aff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  flex-shrink: 0;
}

.card-list-content {
  flex: 1;
  min-width: 0; /* Important for text truncation */
}

.card-list-title {
  font-weight: 600;
  margin: 0 0 4px 0;
  font-size: 16px;
  line-height: 1.4;
}

.card-list-description {
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  margin: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.card-list-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.card-list-action {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  border: none;
  background: #f8f9fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.card-list-action:hover {
  background: #e9ecef;
}

/* Mobile adjustments */
@media (max-width: 767px) {
  .card-list-item {
    padding: 12px;
    gap: 12px;
  }

  .card-list-avatar {
    width: 40px;
    height: 40px;
  }

  .card-list-actions {
    flex-direction: column;
    gap: 4px;
  }

  .card-list-action {
    width: 36px;
    height: 36px;
  }
}
      `,
      benefits: [
        'Rich content support',
        'Visual hierarchy',
        'Touch-friendly actions',
        'Responsive layout',
        'Good for complex data'
      ],
      considerations: [
        'Higher DOM complexity',
        'May need loading states',
        'Consider performance for very large lists'
      ]
    };
  }

  /**
   * Navigation list solution
   */
  static getNavigationListSolution(): ListSolutionPattern {
    return {
      id: 'navigation-list',
      name: 'Navigation List',
      description: 'Optimized for navigation menus and lists with interactive elements',
      useCase: 'Navigation menus, settings lists, and any list where items are primary interactive elements',
      implementation: (
        <ResponsiveListComponent
          items={['Home', 'Profile', 'Settings', 'Help', 'Logout']}
          variant="navigation"
          density="compact"
          interactive
        />
      ),
      cssCode: `
.navigation-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.navigation-list-item {
  display: block;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  text-align: left;
  font-size: 16px;
  line-height: 1.5;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f0f0f0;
  min-height: 44px;
  text-decoration: none;
  color: inherit;
  position: relative;
}

.navigation-list-item:hover {
  background-color: #f8f9fa;
}

.navigation-list-item:focus {
  outline: 2px solid #007aff;
  outline-offset: -2px;
}

.navigation-list-item:active {
  background-color: #e9ecef;
}

/* Icons and badges */
.navigation-list-item::before {
  content: attr(data-icon);
  margin-right: 12px;
  width: 20px;
  text-align: center;
  display: inline-block;
}

.navigation-list-item::after {
  content: attr(data-badge);
  position: absolute;
  right: 16px;
  background: #dc3545;
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 12px;
  font-weight: bold;
}

/* Mobile enhancements */
@media (max-width: 767px) {
  .navigation-list-item {
    padding: 16px;
    font-size: 17px; /* Larger touch target */
  }

  .navigation-list-item:focus {
    outline: none;
    background-color: #f0f8ff;
  }
}

/* Accessibility improvements */
@media (prefers-reduced-motion: reduce) {
  .navigation-list-item {
    transition: none;
  }
}

@media (prefers-color-scheme: dark) {
  .navigation-list-item {
    color: #fff;
    border-bottom-color: #333;
  }

  .navigation-list-item:hover {
    background-color: #2d3748;
  }
}
      `,
      benefits: [
        'Excellent keyboard navigation',
        'Touch-friendly design',
        'Accessibility compliant',
        'Dark mode support',
        'Icon and badge support'
      ],
      considerations: [
        'Requires proper ARIA labeling',
        'Test with screen readers',
        'Consider skip links for long lists'
      ]
    };
  }

  /**
   * Complex list solution with mixed content
   */
  static getComplexListSolution(): ListSolutionPattern {
    return {
      id: 'complex-list',
      name: 'Complex Mixed Content List',
      description: 'Handles lists with mixed content types, nested structures, and complex interactions',
      useCase: 'Dashboard items, activity feeds, and lists with heterogeneous content',
      implementation: (
        <ResponsiveListComponent
          items={[
            {
              type: 'header',
              title: 'Recent Activity'
            },
            {
              type: 'item',
              title: 'Task Completed',
              description: 'User finished important task',
              timestamp: '2 hours ago',
              actions: ['view', 'edit']
            }
          ]}
          variant="complex"
          density="comfortable"
        />
      ),
      cssCode: `
.complex-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.complex-list-section {
  margin-bottom: 24px;
}

.complex-list-header {
  padding: 12px 16px;
  font-weight: 600;
  color: #333;
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  position: sticky;
  top: 0;
  z-index: 10;
}

.complex-list-item {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: start;
  min-height: 60px;
}

.complex-list-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  flex-shrink: 0;
}

.complex-list-content {
  min-width: 0;
}

.complex-list-title {
  font-weight: 600;
  margin: 0 0 4px 0;
  font-size: 16px;
  line-height: 1.4;
  word-wrap: break-word;
}

.complex-list-description {
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  margin: 0 0 8px 0;
  word-wrap: break-word;
}

.complex-list-metadata {
  font-size: 12px;
  color: #999;
}

.complex-list-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.complex-list-action {
  padding: 6px 12px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background: white;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.complex-list-action:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

/* Mobile responsive adjustments */
@media (max-width: 767px) {
  .complex-list-item {
    grid-template-columns: auto 1fr;
    gap: 12px;
    padding: 12px;
  }

  .complex-list-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
    margin-top: 8px;
  }

  .complex-list-action {
    padding: 8px 16px;
    font-size: 16px; /* Prevent zoom */
  }
}

/* Tablet adjustments */
@media (min-width: 768px) and (max-width: 1023px) {
  .complex-list-item {
    padding: 14px;
    gap: 14px;
  }
}
      `,
      benefits: [
        'Handles mixed content types',
        'Sectioned organization',
        'Rich metadata support',
        'Responsive grid layout',
        'Sticky headers for navigation'
      ],
      considerations: [
        'Higher complexity',
        'May need loading states',
        'Consider virtualization for large datasets'
      ]
    };
  }

  /**
   * Virtualized list solution for large datasets
   */
  static getVirtualizedListSolution(): ListSolutionPattern {
    return {
      id: 'virtualized-list',
      name: 'Virtualized List',
      description: 'High-performance list that only renders visible items',
      useCase: 'Large datasets (1000+ items) where performance is critical',
      implementation: <VirtualizedListComponent items={Array.from({length: 1000}, (_, i) => ({id: i, name: `Item ${i}`}))} />,
      cssCode: `
.virtualized-list-container {
  height: 400px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 8px;
}

.virtualized-list-spacer {
  position: relative;
}

.virtualized-list-item {
  position: absolute;
  left: 0;
  right: 0;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  min-height: 44px;
  background: white;
  display: flex;
  align-items: center;
}

.virtualized-list-item:hover {
  background: #f8f9fa;
}

/* Loading skeleton */
.virtualized-list-skeleton {
  height: 44px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-bottom: 1px solid #eee;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Performance optimizations */
.virtualized-list-item {
  contain: layout style paint;
  will-change: transform;
}

/* Smooth scrolling */
.virtualized-list-container {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

/* Mobile touch optimizations */
@media (max-width: 767px) {
  .virtualized-list-item {
    padding: 16px;
    min-height: 48px; /* Larger touch targets */
  }
}
      `,
      benefits: [
        'Excellent performance',
        'Handles huge datasets',
        'Low memory usage',
        'Smooth scrolling',
        'Built-in loading states'
      ],
      considerations: [
        'Complex to implement',
        'Fixed item heights work best',
        'Requires careful testing',
        'May need scrollbar styling'
      ]
    };
  }

  /**
   * Progressive loading list solution
   */
  static getProgressiveListSolution(): ListSolutionPattern {
    return {
      id: 'progressive-list',
      name: 'Progressive Loading List',
      description: 'Loads list items progressively as user scrolls',
      useCase: 'Infinite scroll or paginated lists with dynamic content',
      implementation: <ProgressiveListComponent items={[]} />,
      cssCode: `
.progressive-list-container {
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 8px;
}

.progressive-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.progressive-list-item {
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  min-height: 44px;
  opacity: 0;
  animation: fadeIn 0.3s ease forwards;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.progressive-list-item:nth-child(even) {
  background: #f8f9fa;
}

.progressive-list-loading {
  padding: 24px;
  text-align: center;
  color: #666;
  font-style: italic;
}

.progressive-list-error {
  padding: 24px;
  text-align: center;
  color: #dc3545;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  margin: 16px;
}

.progressive-list-trigger {
  padding: 16px;
  text-align: center;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  margin: 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.progressive-list-trigger:hover {
  background: #e9ecef;
}

/* Skeleton loading */
.progressive-list-skeleton {
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  gap: 12px;
  align-items: center;
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

.skeleton-content {
  flex: 1;
}

.skeleton-title {
  height: 16px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
  width: 60%;
}

.skeleton-description {
  height: 12px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 4px;
  width: 40%;
}
      `,
      benefits: [
        'Fast initial load',
        'Good user experience',
        'Memory efficient',
        'Built-in error handling',
        'Loading states'
      ],
      considerations: [
        'Requires backend pagination',
        'Loading state management',
        'Error recovery needed',
        'May need scroll restoration'
      ]
    };
  }
}

/**
 * Responsive List Component - Main implementation
 */
const ResponsiveListComponent: React.FC<ResponsiveListComponentProps> = ({
  items,
  variant = 'basic',
  density = 'comfortable',
  interactive = false,
  onSelect,
  renderItem
}) => {
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);

  const handleKeyDown = useCallback((e: React.KeyboardEvent, index: number) => {
    if (!interactive) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(prev => Math.min(prev + 1, items.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (items[index]) {
          onSelect?.(items[index]);
        }
        break;
    }
  }, [interactive, items, onSelect]);

  const renderBasicItem = (item: any, index: number) => (
    <li
      key={index}
      className={`responsive-list-item responsive-list-item--wrap ${
        focusedIndex === index ? 'focused' : ''
      }`}
      onClick={() => interactive && onSelect?.(item)}
      onKeyDown={(e) => handleKeyDown(e, index)}
      tabIndex={interactive ? 0 : -1}
      role={interactive ? 'button' : 'listitem'}
      aria-label={typeof item === 'string' ? item : item.title}
    >
      {typeof item === 'string' ? item : renderItem?.(item, index) || item.title}
    </li>
  );

  const renderCardItem = (item: any, index: number) => (
    <li key={index} className="card-list-item">
      <div className="card-list-avatar">{item.avatar || item.title?.[0] || '?'}</div>
      <div className="card-list-content">
        <h4 className="card-list-title">{item.title}</h4>
        {item.description && (
          <p className="card-list-description">{item.description}</p>
        )}
      </div>
      <div className="card-list-actions">
        <button className="card-list-action" aria-label="View item">
          👁️
        </button>
        <button className="card-list-action" aria-label="Edit item">
          ✏️
        </button>
      </div>
    </li>
  );

  const renderNavigationItem = (item: any, index: number) => (
    <li key={index}>
      <button
        className={`navigation-list-item ${focusedIndex === index ? 'focused' : ''}`}
        onClick={() => onSelect?.(item)}
        onKeyDown={(e) => handleKeyDown(e, index)}
        data-icon={item.icon || '📄'}
        data-badge={item.badge}
      >
        {typeof item === 'string' ? item : item.title}
      </button>
    </li>
  );

  const renderComplexItem = (item: any, index: number) => {
    if (item.type === 'header') {
      return (
        <div key={index} className="complex-list-header">
          {item.title}
        </div>
      );
    }

    return (
      <li key={index} className="complex-list-item">
        <div className="complex-list-icon" style={{ backgroundColor: item.color || '#007aff' }}>
          {item.icon || '📋'}
        </div>
        <div className="complex-list-content">
          <h4 className="complex-list-title">{item.title}</h4>
          {item.description && (
            <p className="complex-list-description">{item.description}</p>
          )}
          {item.timestamp && (
            <div className="complex-list-metadata">{item.timestamp}</div>
          )}
        </div>
        {item.actions && (
          <div className="complex-list-actions">
            {item.actions.map((action: string, actionIndex: number) => (
              <button key={actionIndex} className="complex-list-action">
                {action}
              </button>
            ))}
          </div>
        )}
      </li>
    );
  };

  const renderers = {
    basic: renderBasicItem,
    card: renderCardItem,
    navigation: renderNavigationItem,
    complex: renderComplexItem
  };

  const renderList = () => {
    switch (variant) {
      case 'navigation':
        return (
          <nav>
            <ul className="navigation-list" role="menu">
              {items.map((item, index) => renderNavigationItem(item, index))}
            </ul>
          </nav>
        );
      case 'complex':
        return (
          <div className="complex-list">
            {items.map((item, index) => renderComplexItem(item, index))}
          </div>
        );
      case 'card':
        return (
          <ul className="card-list" role="list">
            {items.map((item, index) => renderCardItem(item, index))}
          </ul>
        );
      default:
        return (
          <ul className="responsive-list" role="list">
            {items.map((item, index) => renderBasicItem(item, index))}
          </ul>
        );
    }
  };

  return renderList();
};

/**
 * Virtualized List Component
 */
const VirtualizedListComponent: React.FC<{ items: any[] }> = ({ items }) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(400);
  const itemHeight = 44;
  const containerRef = useRef<HTMLDivElement>(null);

  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight) + 1,
    items.length
  );

  const visibleItems = items.slice(visibleStart, visibleEnd);

  return (
    <div
      ref={containerRef}
      className="virtualized-list-container"
      style={{ height: containerHeight }}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
    >
      <div className="virtualized-list-spacer" style={{ height: items.length * itemHeight }}>
        {visibleItems.map((item, index) => (
          <div
            key={visibleStart + index}
            className="virtualized-list-item"
            style={{ top: (visibleStart + index) * itemHeight }}
          >
            {typeof item === 'object' ? item.name : item}
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Progressive Loading List Component
 */
const ProgressiveListComponent: React.FC<{ items: any[] }> = ({ items }) => {
  const [visibleItems, setVisibleItems] = useState(items.slice(0, 10));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);

  const loadMore = async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const currentLength = visibleItems.length;
      const newItems = items.slice(currentLength, currentLength + 10);

      if (newItems.length === 0) {
        setHasMore(false);
      } else {
        setVisibleItems(prev => [...prev, ...newItems]);
      }
    } catch (err) {
      setError('Failed to load more items');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="progressive-list-container">
      <ul className="progressive-list">
        {visibleItems.map((item, index) => (
          <li key={index} className="progressive-list-item" style={{ animationDelay: `${index * 50}ms` }}>
            {typeof item === 'object' ? item.name : `Item ${index + 1}`}
          </li>
        ))}
      </ul>

      {loading && (
        <div className="progressive-list-loading">
          <div className="progressive-list-skeleton">
            <div className="skeleton-avatar"></div>
            <div className="skeleton-content">
              <div className="skeleton-title"></div>
              <div className="skeleton-description"></div>
            </div>
          </div>
        </div>
      )}

      {error && <div className="progressive-list-error">{error}</div>}

      {hasMore && !loading && (
        <button className="progressive-list-trigger" onClick={loadMore}>
          Load More Items
        </button>
      )}
    </div>
  );
};

export default ResponsiveListComponent;
