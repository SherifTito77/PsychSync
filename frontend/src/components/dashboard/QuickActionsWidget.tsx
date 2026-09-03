// frontend/src/components/dashboard/QuickActionsWidget.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../common/Icon';

export interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: string;
  route?: string;
  onClick?: () => void;
  category: 'team' | 'assessment' | 'analytics' | 'integration' | 'settings';
  keyboardShortcut?: string;
  featured?: boolean;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'create-team',
    title: 'Create New Team',
    description: 'Build a new team for optimization',
    icon: '👥',
    route: '/teams',
    category: 'team',
    featured: true,
  },
  {
    id: 'run-assessment',
    title: 'Run Assessment',
    description: 'Start a new personality assessment',
    icon: '📊',
    route: '/assessments',
    category: 'assessment',
    featured: true,
  },
  {
    id: 'optimize-teams',
    title: 'Optimize Teams',
    description: 'AI-powered team composition analysis',
    icon: '⚡',
    route: '/team-optimizer',
    category: 'analytics',
    featured: true,
  },
  {
    id: 'view-analytics',
    title: 'View Analytics',
    description: 'Detailed performance insights',
    icon: '📈',
    route: '/analytics',
    category: 'analytics',
  },
  {
    id: 'hris-connector',
    title: 'HRIS Integration',
    description: 'Connect your HR data source',
    icon: '🏢',
    route: '/hris-connector',
    category: 'integration',
  },
  {
    id: 'team-composition',
    title: 'Team Composition',
    description: 'Analyze team dynamics',
    icon: '🎯',
    route: '/teams',
    category: 'team',
  },
  {
    id: 'clinical-dashboard',
    title: 'Clinical Dashboard',
    description: 'Mental health overview',
    icon: '🧠',
    route: '/clinical',
    category: 'analytics',
  },
  {
    id: 'settings',
    title: 'Settings',
    description: 'Manage your preferences',
    icon: '⚙️',
    route: '/settings',
    category: 'settings',
  },
];

const CATEGORY_COLORS = {
  team: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    hover: 'hover:border-blue-300',
    text: 'text-blue-600',
  },
  assessment: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    hover: 'hover:border-green-300',
    text: 'text-green-600',
  },
  analytics: {
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    hover: 'hover:border-purple-300',
    text: 'text-purple-600',
  },
  integration: {
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    hover: 'hover:border-indigo-300',
    text: 'text-indigo-600',
  },
  settings: {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    hover: 'hover:border-gray-300',
    text: 'text-gray-600',
  },
};

interface QuickActionItemProps {
  action: QuickAction;
}

const QuickActionItem: React.FC<QuickActionItemProps> = ({ action }) => {
  const navigate = useNavigate();
  const colors = CATEGORY_COLORS[action.category];

  const handleClick = () => {
    if (action.onClick) {
      action.onClick();
    } else if (action.route) {
      navigate(action.route);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`
        relative p-4 rounded-lg border-2 text-left
        transition-all duration-200
        ${colors.bg} ${colors.border} ${colors.hover}
        hover:shadow-md
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
        mobile-touch-target
        ${action.featured ? 'ring-2 ring-indigo-200' : ''}
      `}
      aria-label={`Quick action: ${action.title}`}
    >
      {action.featured && (
        <div className="absolute -top-2 -right-2 bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-0.5 rounded-full">
          Featured
        </div>
      )}

      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${colors.bg} flex-shrink-0`}>
          <Icon size="sm" className={colors.text}>{action.icon}</Icon>
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-sm sm:text-base truncate">
            {action.title}
          </h3>
          <p className="text-xs sm:text-sm text-gray-600 mt-1 line-clamp-2">
            {action.description}
          </p>

          {action.keyboardShortcut && (
            <div className="mt-2 flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 text-xs font-mono bg-white border border-gray-300 rounded text-gray-600">
                {action.keyboardShortcut}
              </kbd>
            </div>
          )}
        </div>
      </div>
    </button>
  );
};

interface QuickActionsWidgetProps {
  maxVisible?: number;
}

const QuickActionsWidget: React.FC<QuickActionsWidgetProps> = ({
  maxVisible = 6,
}) => {
  const [filter, setFilter] = useState<string>('all');

  const categories = [
    { value: 'all', label: 'All Actions', icon: '📋' },
    { value: 'team', label: 'Teams', icon: '👥' },
    { value: 'assessment', label: 'Assessments', icon: '📊' },
    { value: 'analytics', label: 'Analytics', icon: '📈' },
    { value: 'integration', label: 'Integrations', icon: '🔗' },
    { value: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  const filteredActions =
    filter === 'all'
      ? QUICK_ACTIONS
      : QUICK_ACTIONS.filter((action) => action.category === filter);

  const displayedActions = filteredActions.slice(0, maxVisible);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mobile-card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mobile-text-responsive">
          Quick Actions
        </h2>
        <div className="text-xs text-gray-500">
          Press <kbd className="px-1 py-0.5 bg-gray-100 border rounded">⌘K</kbd> for search
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-4 overflow-x-auto pb-2">
        {categories.map((category) => (
          <button
            key={category.value}
            onClick={() => setFilter(category.value)}
            className={`
              px-3 py-1.5 rounded-lg text-sm font-medium
              flex items-center gap-1.5 whitespace-nowrap
              transition-all duration-200
              ${
                filter === category.value
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
              focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
              mobile-touch-target-mini
            `}
            aria-label={`Filter by ${category.label}`}
            aria-pressed={filter === category.value}
          >
            <span>{category.icon}</span>
            <span className="hidden sm:inline">{category.label}</span>
          </button>
        ))}
      </div>

      {/* Actions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
        {displayedActions.map((action) => (
          <QuickActionItem key={action.id} action={action} />
        ))}
      </div>

      {/* Show More Indicator */}
      {filteredActions.length > maxVisible && (
        <div className="mt-4 text-center">
          <button
            onClick={() => setFilter('all')}
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            View all {filteredActions.length} actions →
          </button>
        </div>
      )}
    </div>
  );
};

export default QuickActionsWidget;
export { QUICK_ACTIONS };
