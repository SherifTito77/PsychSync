/**
 * Phase 3: Virtualized List for Large Datasets
 * High-performance scrolling for 1000+ items
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';

interface VirtualizedListProps {
  items: any[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: any, index: number) => React.ReactNode;
  onItemClick?: (item: any, index: number) => void;
  className?: string;
}

export const VirtualizedList: React.FC<VirtualizedListProps> = ({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  onItemClick,
  className = ''
}) => {
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

  // Handle scroll
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  // Handle item click
  const handleItemClick = (item: any, index: number) => {
    if (onItemClick) {
      onItemClick(item, visibleRange.startIndex + index);
    }
  };

  return (
    <div
      ref={containerRef}
      className={`virtualized-list ${className}`}
      style={{
        height: containerHeight,
        overflowY: 'auto',
        position: 'relative'
      }}
      onScroll={handleScroll}
    >
      {/* Spacer to maintain scroll height */}
      <div
        style={{
          height: items.length * itemHeight,
          position: 'relative'
        }}
      >
        {/* Visible items */}
        {visibleItems.map((item, index) => (
          <div
            key={visibleRange.startIndex + index}
            className="virtualized-item"
            style={{
              position: 'absolute',
              top: (visibleRange.startIndex + index) * itemHeight,
              left: 0,
              right: 0,
              height: itemHeight
            }}
            onClick={() => handleItemClick(item, index)}
          >
            {renderItem(item, visibleRange.startIndex + index)}
          </div>
        ))}
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

  // Render individual user item
  const renderUserItem = (user: User, index: number) => (
    <div className="user-item">
      <div className="user-avatar">{user.avatar}</div>
      <div className="user-info">
        <div className="user-name">{user.name}</div>
        <div className="user-email">{user.email}</div>
        <div className="user-role">{user.role}</div>
      </div>
      <div className="user-actions">
        <button
          className="action-btn"
          onClick={(e) => {
            e.stopPropagation();
            console.log('View user:', user);
          }}
        >
          View
        </button>
        <button
          className="action-btn"
          onClick={(e) => {
            e.stopPropagation();
            console.log('Edit user:', user);
          }}
        >
          Edit
        </button>
      </div>
    </div>
  );

  const handleUserSelect = (user: User, index: number) => {
    setSelectedUser(user);
    console.log(`Selected user at index ${index}:`, user);
  };

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
            fontSize: '16px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            marginBottom: '10px'
          }}
        />

        {selectedUser && (
          <div style={{
            padding: '10px',
            backgroundColor: '#e3f2fd',
            borderRadius: '4px',
            fontSize: '14px'
          }}>
            Selected: <strong>{selectedUser.name}</strong> ({selectedUser.email})
          </div>
        )}
      </div>

      {/* Virtualized list */}
      <div style={{ flex: 1, border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden' }}>
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
        backgroundColor: '#f5f5f5',
        borderRadius: '4px',
        fontSize: '12px',
        color: '#666'
      }}>
        Total Users: {users.length} |
        Filtered: {filteredUsers.length} |
        Rendering: Only visible items (performance optimized)
      </div>

      <style jsx>{`
        .user-item {
          display: flex;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid #eee;
          background: white;
          cursor: pointer;
          transition: background-color 0.2s ease;
          height: 80px;
          box-sizing: border-box;
        }

        .user-item:hover {
          background-color: #f8f9fa;
        }

        .user-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: #007aff;
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
          color: #333;
          margin-bottom: 2px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .user-email {
          color: #666;
          font-size: 14px;
          margin-bottom: 2px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .user-role {
          color: #007aff;
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
          border: 1px solid #ddd;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .action-btn:hover {
          background-color: #f0f0f0;
          border-color: #007aff;
          color: #007aff;
        }

        .virtualized-list {
          /* Custom scrollbar for better UX */
          scrollbar-width: thin;
          scrollbar-color: #ccc #f5f5f5;
        }

        .virtualized-list::-webkit-scrollbar {
          width: 8px;
        }

        .virtualized-list::-webkit-scrollbar-track {
          background: #f5f5f5;
        }

        .virtualized-list::-webkit-scrollbar-thumb {
          background: #ccc;
          border-radius: 4px;
        }

        .virtualized-list::-webkit-scrollbar-thumb:hover {
          background: #999;
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