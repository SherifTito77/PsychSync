/**
 * Simple Responsive List Component
 *
 * A mobile-first, accessible list component with keyboard navigation.
 * Migrated to use CSS modules with Tailwind utilities.
 */

import React, { useState } from 'react';
import styles from './SimpleResponsiveList.module.css';

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
    <div className={styles.container}>
      {title && <h2 className={styles.title}>{title}</h2>}

      <ul
        className={styles.list}
        role={interactive ? 'listbox' : 'list'}
        aria-label={title}
      >
        {items.map((item, index) => (
          <li
            key={index}
            className={[
              styles.item,
              interactive ? styles.itemInteractive : '',
              selectedIndex === index ? styles.itemSelected : ''
            ].join(' ')}
            onClick={() => handleClick(item, index)}
            onKeyDown={(e) => handleKeyDown(e, item, index)}
            role={interactive ? 'option' : 'listitem'}
            aria-selected={interactive && selectedIndex === index}
            tabIndex={interactive && selectedIndex === index ? 0 : -1}
          >
            <span className={styles.itemContent}>{item}</span>
            {interactive && (
              <span className={styles.itemIndicator} aria-hidden="true">
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