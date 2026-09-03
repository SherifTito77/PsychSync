/**
 * Phase 1: Basic Responsive List Implementation
 * Start small with immediate impact and measurable improvements
 */

import React, { useState, useCallback, useMemo } from 'react';

interface BasicResponsiveListProps {
  items: string[];
  title?: string;
  onSelect?: (item: string) => void;
  interactive?: boolean;
}

export const BasicResponsiveList: React.FC<BasicResponsiveListProps> = ({
  items,
  title,
  onSelect,
  interactive = false
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);

  const handleClick = useCallback((item: string, index: number) => {
    if (interactive && onSelect) {
      setSelectedIndex(index);
      onSelect(item);
    }
  }, [interactive, onSelect]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent, item: string, index: number) => {
    if (!interactive || !onSelect) return;

    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        handleClick(item, index);
        break;
      case 'ArrowDown':
        e.preventDefault();
        const nextIndex = Math.min(index + 1, items.length - 1);
        setSelectedIndex(nextIndex);
        break;
      case 'ArrowUp':
        e.preventDefault();
        const prevIndex = Math.max(index - 1, 0);
        setSelectedIndex(prevIndex);
        break;
    }
  }, [interactive, onSelect, handleClick, items.length]);

  // Memoize the click handlers for each item to prevent re-renders
  const itemHandlers = useMemo(() => {
    return items.map((item, index) => ({
      onClick: () => handleClick(item, index),
      onKeyDown: (e: React.KeyboardEvent) => handleKeyDown(e, item, index)
    }));
  }, [items, handleClick, handleKeyDown]);

  return (
    <div className="basic-responsive-list">
      {title && <h2 className="list-title">{title}</h2>}

      <ul
        className="responsive-list"
        role={interactive ? 'listbox' : 'list'}
        aria-label={title}
      >
        {items.map((item, index) => (
          <li
            key={index}
            className={`list-item ${interactive ? 'interactive' : ''} ${
              selectedIndex === index ? 'selected' : ''
            }`}
            onClick={itemHandlers[index].onClick}
            onKeyDown={itemHandlers[index].onKeyDown}
            role={interactive ? 'option' : 'listitem'}
            aria-selected={interactive && selectedIndex === index}
            tabIndex={interactive && selectedIndex === index ? 0 : -1}
          >
            <span className="item-content">{item}</span>
            {interactive && (
              <span className="item-indicator" aria-hidden="true">
                {selectedIndex === index ? '✓' : '→'}
              </span>
            )}
          </li>
        ))}
      </ul>

      <style>{`
        .basic-responsive-list {
          width: 100%;
          max-width: 600px;
          margin: 0 auto;
        }

        .list-title {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: var(--color-gray-900);
        }

        .responsive-list {
          list-style: none;
          padding: 0;
          margin: 0;
          background: white;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .list-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px; /* Mobile first */
          border-bottom: 1px solid var(--color-gray-200);
          min-height: 44px; /* Touch target requirement */
          line-height: 1.5;
          word-wrap: break-word;
          overflow-wrap: break-word;
          color: var(--color-gray-800);
          transition: background-color 0.2s ease;
        }

        .list-item:last-child {
          border-bottom: none;
        }

        .list-item.interactive {
          cursor: pointer;
        }

        .list-item.interactive:hover {
          background-color: var(--color-gray-50);
        }

        .list-item.interactive:focus {
          outline: 2px solid var(--color-primary-600);
          outline-offset: -2px;
          background-color: var(--color-blue-50);
        }

        .list-item.selected {
          background-color: var(--color-blue-50);
          border-left: 3px solid var(--color-primary-600);
        }

        .item-content {
          flex: 1;
          min-width: 0; /* Important for text truncation */
        }

        .item-indicator {
          margin-left: 12px;
          font-size: 1rem;
          color: var(--color-primary-600);
          font-weight: 600;
        }

        /* Responsive scaling */
        @media (min-width: 768px) {
          .list-item {
            padding: 14px 20px;
            font-size: 1rem;
          }
        }

        @media (min-width: 1024px) {
          .list-item {
            padding: 16px 24px;
          }

          .list-item.interactive:hover {
            transform: translateX(2px);
          }
        }

        /* Accessibility */
        @media (prefers-reduced-motion: reduce) {
          .list-item {
            transition: none;
          }
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
          .list-title {
            color: var(--color-gray-50);
          }

          .responsive-list {
            background: var(--color-gray-800);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
          }

          .list-item {
            color: var(--color-gray-200);
            border-bottom-color: var(--color-gray-600);
          }

          .list-item.interactive:hover {
            background-color: var(--color-gray-600);
          }

          .list-item.selected {
            background-color: var(--color-primary-800);
          }
        }
      `}</style>
    </div>
  );
};

// Usage example component
export const BasicListExample: React.FC = () => {
  const teamMembers = [
    'Sarah Chen - Frontend Developer',
    'Mike Johnson - Backend Engineer',
    'Emily Davis - UX Designer',
    'Alex Kim - Product Manager',
    'Lisa Wang - DevOps Engineer',
    'James Taylor - QA Engineer'
  ];

  const handleMemberSelect = (member: string) => {
    console.log('Selected team member:', member);
    // In a real app, this would navigate to member details
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>PsychSync Team Directory</h1>
      <p style={{ marginBottom: '2rem', color: 'var(--color-gray-600)' }}>
        Click any team member to view their profile. This list is fully responsive
        and accessible across all devices.
      </p>

      <BasicResponsiveList
        items={teamMembers}
        title="Team Members"
        interactive
        onSelect={handleMemberSelect}
      />
    </div>
  );
};

export default BasicResponsiveList;
