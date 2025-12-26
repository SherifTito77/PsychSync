/**
 * Phase 1: Simple Responsive List Implementation
 * Start small with immediate impact and measurable improvements
 */

import React, { useState } from 'react';
import './SimpleResponsiveList.css';

interface SimpleResponsiveListProps {
  items: string[];
  title?: string;
  onSelect?: (item: string) => void;
  interactive?: boolean;
}

export const SimpleResponsiveList: React.FC<SimpleResponsiveListProps> = ({
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
    <div className="simple-responsive-list">
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
    </div>
  );
};

// Usage example component
export const SimpleListExample: React.FC = () => {
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
    alert(`Selected: ${member}`);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>PsychSync Team Directory</h1>
      <p style={{ marginBottom: '2rem', color: '#718096' }}>
        Click any team member to view their profile. This list is fully responsive
        and accessible across all devices.
      </p>

      <SimpleResponsiveList
        items={teamMembers}
        title="Team Members"
        interactive
        onSelect={handleMemberSelect}
      />
    </div>
  );
};

export default SimpleResponsiveList;