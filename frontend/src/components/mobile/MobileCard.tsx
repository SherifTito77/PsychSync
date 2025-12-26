// frontend/src/components/mobile/MobileCard.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronRightIcon,
  HeartIcon,
  ShareIcon,
  EllipsisVerticalIcon,
  TrashIcon,
  ArchiveBoxIcon
} from '@heroicons/react/24/outline';

interface MobileCardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  imageUrl?: string;
  badge?: string;
  badgeColor?: string;
  actions?: React.ReactNode;
  onPress?: () => void;
  onLongPress?: () => void;
  swipeActions?: {
    left?: {
      label: string;
      icon: React.ElementType;
      color: string;
      action: () => void;
    };
    right?: {
      label: string;
      icon: React.ElementType;
      color: string;
      action: () => void;
    };
  };
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const MobileCard: React.FC<MobileCardProps> = ({
  children,
  title,
  subtitle,
  imageUrl,
  badge,
  badgeColor = 'blue',
  actions,
  onPress,
  onLongPress,
  swipeActions,
  dismissible = false,
  onDismiss,
  className = '',
  style = {}
}) => {
  const [isSwiped, setIsSwiped] = useState(false);
  const [startX, setStartX] = useState(0);
  const [currentX, setCurrentX] = useState(0);
  const [isPressed, setIsPressed] = useState(false);

  const handleTouchStart = (e: React.TouchEvent) => {
    setStartX(e.touches[0].clientX);
    setCurrentX(e.touches[0].clientX);
    setIsPressed(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!startX) return;

    const touchX = e.touches[0].clientX;
    const deltaX = touchX - startX;
    setCurrentX(deltaX);

    // Only allow swipe if we have swipe actions
    if (swipeActions && (swipeActions.left || swipeActions.right)) {
      // Limit swipe distance
      if (Math.abs(deltaX) > 150) {
        setIsSwiped(true);
      }
    }
  };

  const handleTouchEnd = () => {
    if (isSwiped && swipeActions) {
      // Trigger action based on swipe direction
      if (currentX > 100 && swipeActions.right) {
        swipeActions.right.action();
      } else if (currentX < -100 && swipeActions.left) {
        swipeActions.left.action();
      }
    }

    // Reset state
    setIsSwiped(false);
    setCurrentX(0);
    setStartX(0);
    setIsPressed(false);
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onLongPress) {
      onLongPress();
    }
  };

  const handlePress = () => {
    if (onPress) {
      onPress();
    }
  };

  // Long press detection
  React.useEffect(() => {
    let pressTimer: NodeJS.Timeout;

    const handlePressStart = () => {
      pressTimer = setTimeout(() => {
        if (onLongPress) {
          onLongPress();
        }
      }, 500);
    };

    const handlePressEnd = () => {
      if (pressTimer) {
        clearTimeout(pressTimer);
      }
    };

    if (isPressed) {
      handlePressStart();
    }

    return () => {
      handlePressEnd();
    };
  }, [isPressed, onLongPress]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`
          mobile-swipe-card
          mobile-card
          relative overflow-hidden
          ${isPressed ? 'shadow-lg' : 'shadow-sm'}
          ${className}
        `}
        style={{
          transform: `translateX(${isSwiped ? (currentX > 0 ? 60 : -60) : 0}px)`,
          transition: 'transform 0.3s ease, box-shadow 0.2s ease',
          ...style
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onContextMenu={handleContextMenu}
        onClick={handlePress}
      >
        {/* Left swipe action */}
        {swipeActions?.left && (
          <div className="mobile-swipe-actions" style={{ backgroundColor: swipeActions.left.color }}>
            <swipeActions.left.icon className="w-5 h-5" />
            <span className="ml-2 text-sm font-medium">{swipeActions.left.label}</span>
          </div>
        )}

        {/* Right swipe action */}
        {swipeActions?.right && (
          <div className="mobile-swipe-actions" style={{ backgroundColor: swipeActions.right.color }}>
            <span className="mr-2 text-sm font-medium">{swipeActions.right.label}</span>
            <swipeActions.right.icon className="w-5 h-5" />
          </div>
        )}

        {/* Dismissible overlay */}
        {dismissible && (
          <button
            onClick={() => onDismiss?.()}
            className="absolute top-2 right-2 p-1 rounded-full bg-red-500 text-white opacity-0 hover:opacity-100 transition-opacity z-10"
            aria-label="Dismiss"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        )}

        {/* Badge */}
        {badge && (
          <div className="absolute top-2 right-2 mobile-badge bg-blue-500 text-white">
            {badge}
          </div>
        )}

        {/* Card content */}
        <div className="p-4">
          {/* Image */}
          {imageUrl && (
            <div className="mb-3">
              <img
                src={imageUrl}
                alt={title || 'Card image'}
                className="w-full h-32 object-cover rounded-lg"
              />
            </div>
          )}

          {/* Header */}
          {(title || subtitle) && (
            <div className="mb-3">
              {title && (
                <h3 className="mobile-h3 text-gray-900 truncate">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="mobile-caption text-gray-500 truncate">
                  {subtitle}
                </p>
              )}
            </div>
          )}

          {/* Children content */}
          <div className="mb-3">
            {children}
          </div>

          {/* Actions */}
          {actions && (
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <div className="flex space-x-2">
                {actions}
              </div>
              <ChevronRightIcon className="w-4 h-4 text-gray-400" />
            </div>
          )}
        </div>

        {/* Ripple effect */}
        {isPressed && (
          <div className="absolute inset-0 bg-blue-500 opacity-10 pointer-events-none" />
        )}
      </motion.div>
    </AnimatePresence>
  );
};

// Specialized card variants
export const AssessmentCard: React.FC<{
  assessment: {
    id: string;
    title: string;
    description: string;
    category: string;
    status: string;
    created_at: string;
    response_count: number;
  };
  onPress?: () => void;
}> = ({ assessment, onPress }) => {
  const statusColors = {
    draft: 'gray',
    published: 'green',
    archived: 'orange'
  };

  return (
    <MobileCard
      title={assessment.title}
      subtitle={`${assessment.category} • ${assessment.response_count} responses`}
      badge={assessment.status}
      badgeColor={statusColors[assessment.status as keyof typeof statusColors] || 'gray'}
      onPress={onPress}
      swipeActions={{
        right: {
          label: 'View',
          icon: ChevronRightIcon,
          color: '#3b82f6',
          action: onPress || (() => {})
        }
      }}
    >
      <p className="mobile-body text-gray-600 line-clamp-2">
        {assessment.description}
      </p>
      <div className="mt-2 flex items-center text-sm text-gray-500">
        <span>Created {new Date(assessment.created_at).toLocaleDateString()}</span>
      </div>
    </MobileCard>
  );
};

export const TeamCard: React.FC<{
  team: {
    id: string;
    name: string;
    description: string;
    member_count: number;
    role: string;
    created_at: string;
  };
  onPress?: () => void;
}> = ({ team, onPress }) => {
  return (
    <MobileCard
      title={team.name}
      subtitle={`${team.member_count} members • ${team.role}`}
      onPress={onPress}
      swipeActions={{
        right: {
          label: 'View',
          icon: ChevronRightIcon,
          color: '#10b981',
          action: onPress || (() => {})
        }
      }}
    >
      <p className="mobile-body text-gray-600 line-clamp-2">
        {team.description}
      </p>
      <div className="mt-2 flex items-center text-sm text-gray-500">
        <span>Created {new Date(team.created_at).toLocaleDateString()}</span>
      </div>
    </MobileCard>
  );
};

export const NotificationCard: React.FC<{
  notification: {
    id: string;
    title: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
  };
  onDismiss?: () => void;
}> = ({ notification, onDismiss }) => {
  const typeColors = {
    info: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444'
  };

  return (
    <MobileCard
      title={notification.title}
      dismissible
      onDismiss={onDismiss}
      swipeActions={{
        left: {
          label: 'Dismiss',
          icon: ArchiveBoxIcon,
          color: '#6b7280',
          action: onDismiss || (() => {})
        }
      }}
    >
      <div className="flex items-start space-x-3">
        <div
          className="w-2 h-2 rounded-full mt-2 flex-shrink-0"
          style={{ backgroundColor: typeColors[notification.type] }}
        />
        <div className="flex-1">
          <p className="mobile-body text-gray-700">
            {notification.message}
          </p>
          <p className="mobile-caption text-gray-500 mt-1">
            {new Date().toLocaleTimeString()}
          </p>
        </div>
      </div>
    </MobileCard>
  );
};

export const SwipeableListItem: React.FC<{
  item: {
    id: string;
    title: string;
    subtitle?: string;
    icon?: React.ElementType;
  };
  onPress?: () => void;
  onArchive?: () => void;
  onDelete?: () => void;
}> = ({ item, onPress, onArchive, onDelete }) => {
  const Icon = item.icon;

  return (
    <MobileCard
      swipeActions={{
        left: {
          label: 'Archive',
          icon: ArchiveBoxIcon,
          color: '#3b82f6',
          action: onArchive || (() => {})
        },
        right: {
          label: 'Delete',
          icon: TrashIcon,
          color: '#ef4444',
          action: onDelete || (() => {})
        }
      }}
      onPress={onPress}
    >
      <div className="flex items-center space-x-3">
        {Icon && <Icon className="w-5 h-5 text-gray-400" />}
        <div className="flex-1">
          <h4 className="mobile-body font-medium text-gray-900">
            {item.title}
          </h4>
          {item.subtitle && (
            <p className="mobile-caption text-gray-500">
              {item.subtitle}
            </p>
          )}
        </div>
      </div>
    </MobileCard>
  );
};

export default MobileCard;