/**
 * Phase 3: Virtualized List for Large Datasets
 * High-performance scrolling for 1000+ items
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { tokens } from '@/utils/designTokens';

interface VirtualizedListProps<T = unknown> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  onItemClick?: (item: T, index: number) => void;
  className?: string;
}

export const VirtualizedList = <T,>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  onItemClick,
  className = ''
}: VirtualizedListProps<T>): React.ReactElement => {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Calculate visible range
  const visibleRange = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / itemHeight) + 1, // Add buffer
      items.length
    );
    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, items.length]);

  // Get visible items
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex);
  }, [items, visibleRange]);

  // Handle scroll - memoized
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  // Handle item click - memoized
  const handleItemClick = useCallback((item: T, index: number) => {
    if (onItemClick) {
      onItemClick(item, visibleRange.startIndex + index);
    }
  }, [onItemClick, visibleRange.startIndex]);

  // Memoize container style
  const containerStyle = useMemo(() => ({
    height: containerHeight,
    overflowY: 'auto' as const,
    position: 'relative' as const
  }), [containerHeight]);

  // Memoize spacer style
  const spacerStyle = useMemo(() => ({
    height: items.length * itemHeight,
    position: 'relative' as const
  }), [items.length, itemHeight]);

  // Memoize item handlers to prevent re-renders
  const itemHandlers = useMemo(() => {
    return visibleItems.map((item, index) => ({
      onClick: () => handleItemClick(item, index)
    }));
  }, [visibleItems, handleItemClick]);

  return (
    <div
      ref={containerRef}
      className={`virtualized-list ${className}`}
      style={containerStyle}
      onScroll={handleScroll}
    >
      {/* Spacer to maintain scroll height */}
      <div style={spacerStyle}>
        {/* Visible items */}
        {visibleItems.map((item, index) => {
          const itemStyle = useMemo(() => ({
            position: 'absolute' as const,
            top: (visibleRange.startIndex + index) * itemHeight,
            left: 0,
            right: 0,
            height: itemHeight
          }), [index, itemHeight, visibleRange.startIndex]);

          return (
            <div
              key={visibleRange.startIndex + index}
              className="virtualized-item"
              style={itemStyle}
              onClick={itemHandlers[index].onClick}
            >
              {renderItem(item, visibleRange.startIndex + index)}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Virtualized user list example
interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  avatar: string;
}

export const VirtualizedUserList: React.FC = () => {
  // Generate large dataset for demonstration
  const [users] = useState<User[]>(() =>
    Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
      email: `user${i + 1}@example.com`,
      role: ['Developer', 'Designer', 'Manager', 'QA Engineer'][i % 4],
      avatar: `${String.fromCharCode(65 + (i % 26))}${i + 1}`
    }))
  );

  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter users based on search
  const filteredUsers = useMemo(() => {
    return users.filter(user =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.role.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [users, searchTerm]);

  // Memoize user action handlers to prevent re-renders
  const handleViewUser = useCallback((e: React.MouseEvent, user: User) => {
    e.stopPropagation();
    console.log('View user:', user);
  }, []);

  const handleEditUser = useCallback((e: React.MouseEvent, user: User) => {
    e.stopPropagation();
    console.log('Edit user:', user);
  }, []);

  // Render individual user item - memoized
  const renderUserItem = useCallback((user: User, index: number) => (
    <div className="user-item">
      <div className="user-avatar">{user.avatar}</div>
      <div className="user-info">
        <div className="user-name">{user.name}</div>
        <div className="user-email">{user.email}</div>
        <div className="user-role">{user.role}</div>
      </div>
      <div className="user-actions">
        <button
          type="button"
          className="action-btn"
          onClick={(e) => handleViewUser(e, user)}
        >
          View
        </button>
        <button
          type="button"
          className="action-btn"
          onClick={(e) => handleEditUser(e, user)}
        >
          Edit
        </button>
      </div>
    </div>
  ), [handleViewUser, handleEditUser]);

  const handleUserSelect = useCallback((user: User, index: number) => {
    setSelectedUser(user);
    console.log(`Selected user at index ${index}:`, user);
  }, []);

  return (
    <div style={{ padding: '20px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1>Virtualized User Directory ({filteredUsers.length.toLocaleString()} users)</h1>
        <p>
          This list uses virtualization to efficiently handle 1000+ users with smooth scrolling.
          Only visible items are rendered to DOM.
        </p>

        {/* Search functionality */}
        <input
          type="text"
          placeholder="Search users..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            width: '100%',
            maxWidth: '400px',
            padding: '12px',
            fontSize: 'var(--font-size-base)',
            border: '1px solid var(--color-gray-300)',
            borderRadius: '4px',
            marginBottom: '10px'
          }}
        />

        {selectedUser && (
          <div style={{
            padding: '10px',
            backgroundColor: 'var(--color-blue-50)',
            borderRadius: '4px',
            fontSize: 'var(--font-size-sm)'
          }}>
            Selected: <strong>{selectedUser.name}</strong> ({selectedUser.email})
          </div>
        )}
      </div>

      {/* Virtualized list */}
      <div style={{ flex: 1, border: '1px solid var(--color-gray-300)', borderRadius: '8px', overflow: 'hidden' }}>
        <VirtualizedList
          items={filteredUsers}
          itemHeight={80} // Height of each user item
          containerHeight={600} // Visible container height
          renderItem={renderUserItem}
          onItemClick={handleUserSelect}
          className="user-directory"
        />
      </div>

      {/* Performance info */}
      <div style={{
        marginTop: '10px',
        padding: '10px',
        backgroundColor: 'var(--color-gray-100)',
        borderRadius: '4px',
        fontSize: 'var(--font-size-xs)',
        color: 'var(--color-gray-600)'
      }}>
        Total Users: {users.length} |
        Filtered: {filteredUsers.length} |
        Rendering: Only visible items (performance optimized)
      </div>

      <style>{`
        .user-item {
          display: flex;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid var(--color-gray-200);
          background: white;
          cursor: pointer;
          transition: background-color 0.2s ease;
          height: 80px;
          box-sizing: border-box;
        }

        .user-item:hover {
          background-color: var(--color-gray-50);
        }

        .user-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: var(--color-primary-600);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          margin-right: 12px;
          flex-shrink: 0;
        }

        .user-info {
          flex: 1;
          min-width: 0;
        }

        .user-name {
          font-weight: 600;
          color: var(--color-gray-900);
          margin-bottom: 2px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .user-email {
          color: var(--color-gray-600);
          font-size: 14px;
          margin-bottom: 2px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .user-role {
          color: var(--color-primary-600);
          font-size: 12px;
          font-weight: 500;
        }

        .user-actions {
          display: flex;
          gap: 8px;
          flex-shrink: 0;
        }

        .action-btn {
          padding: 6px 12px;
          border: 1px solid var(--color-gray-300);
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .action-btn:hover {
          background-color: var(--color-gray-200);
          border-color: var(--color-primary-600);
          color: var(--color-primary-600);
        }

        .virtualized-list {
          /* Custom scrollbar for better UX */
          scrollbar-width: thin;
          scrollbar-color: var(--color-gray-300) var(--color-gray-100);
        }

        .virtualized-list::-webkit-scrollbar {
          width: 8px;
        }

        .virtualized-list::-webkit-scrollbar-track {
          background: var(--color-gray-100);
        }

        .virtualized-list::-webkit-scrollbar-thumb {
          background: var(--color-gray-300);
          border-radius: 4px;
        }

        .virtualized-list::-webkit-scrollbar-thumb:hover {
          background: var(--color-gray-500);
        }

        .virtualized-item {
          /* Performance optimization */
          contain: layout style paint;
        }
      `}</style>
    </div>
  );
};

export default VirtualizedList;
