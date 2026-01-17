/**
 * Phase 1: Basic Responsive List Implementation
 * Start small with immediate impact and measurable improvements
 */

import React, { useState } from 'react';

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

  const handleClick = (item: string, index: number) => {
    if (interactive && onSelect) {
      setSelectedIndex(index);
      onSelect(item);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, item: string, index: number) => {
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
  };

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
            onClick={() => handleClick(item, index)}
            onKeyDown={(e) => handleKeyDown(e, item, index)}
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

      <style jsx>{`
        .basic-responsive-list {
          width: 100%;
          max-width: 600px;
          margin: 0 auto;
        }

        .list-title {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: #1a202c;
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
          border-bottom: 1px solid #e2e8f0;
          min-height: 44px; /* Touch target requirement */
          line-height: 1.5;
          word-wrap: break-word;
          overflow-wrap: break-word;
          color: #2d3748;
          transition: background-color 0.2s ease;
        }

        .list-item:last-child {
          border-bottom: none;
        }

        .list-item.interactive {
          cursor: pointer;
        }

        .list-item.interactive:hover {
          background-color: #f7fafc;
        }

        .list-item.interactive:focus {
          outline: 2px solid #3182ce;
          outline-offset: -2px;
          background-color: #ebf8ff;
        }

        .list-item.selected {
          background-color: #ebf8ff;
          border-left: 3px solid #3182ce;
        }

        .item-content {
          flex: 1;
          min-width: 0; /* Important for text truncation */
        }

        .item-indicator {
          margin-left: 12px;
          font-size: 1rem;
          color: #3182ce;
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
            color: #f7fafc;
          }

          .responsive-list {
            background: #2d3748;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
          }

          .list-item {
            color: #e2e8f0;
            border-bottom-color: #4a5568;
          }

          .list-item.interactive:hover {
            background-color: #4a5568;
          }

          .list-item.selected {
            background-color: #2c5282;
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
      <p style={{ marginBottom: '2rem', color: '#718096' }}>
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
