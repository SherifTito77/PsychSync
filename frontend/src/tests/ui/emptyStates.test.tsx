// frontend/src/tests/ui/emptyStates.test.tsx
/**
 * Empty States Testing
 * Tests for meaningful empty states across all pages and components
 * Business Impact: User guidance, system clarity, user experience
 * ROI: 3x - Reduces user confusion and improves onboarding
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';

// Empty state component
const EmptyState: React.FC<{
  type: 'dashboard' | 'assessments' | 'teams' | 'users' | 'data' | 'notifications';
  onAction?: () => void;
}> = ({ type, onAction }) => {
  const emptyStateConfig = {
    dashboard: {
      title: 'Welcome to Your Dashboard',
      message: 'Start by creating your first assessment or inviting team members.',
      action: 'Create First Assessment',
      icon: '📊'
    },
    assessments: {
      title: 'No Assessments Yet',
      message: 'Create your first assessment to get started with team insights.',
      action: 'Create Assessment',
      icon: '📝'
    },
    teams: {
      title: 'No Teams Created',
      message: 'Build your first team to start collaborating on assessments.',
      action: 'Create Team',
      icon: '👥'
    },
    users: {
      title: 'No Team Members',
      message: 'Invite team members to collaborate and share insights.',
      action: 'Invite Members',
      icon: '👤'
    },
    data: {
      title: 'No Data Available',
      message: 'Complete some assessments to see meaningful analytics here.',
      action: 'View Assessments',
      icon: '📈'
    },
    notifications: {
      title: 'All Caught Up!',
      message: 'You have no new notifications at this time.',
      action: null,
      icon: '🔔'
    }
  };

  const config = emptyStateConfig[type];

  return (
    <div data-testid="empty-state" className={`empty-state-${type}`}>
      <div data-testid="empty-state-icon" className="empty-state-icon">
        {config.icon}
      </div>
      <h3 data-testid="empty-state-title">{config.title}</h3>
      <p data-testid="empty-state-message">{config.message}</p>
      {config.action && onAction && (
        <button onClick={onAction} data-testid="empty-state-action">
          {config.action}
        </button>
      )}
    </div>
  );
};

// Dashboard with multiple empty states
const DashboardWithEmptyStates: React.FC = () => {
  const [hasAssessments, setHasAssessments] = React.useState(false);
  const [hasTeamMembers, setHasTeamMembers] = React.useState(false);
  const [hasNotifications, setHasNotifications] = React.useState(false);

  return (
    <div data-testid="dashboard">
      <h2>Dashboard</h2>

      <div data-testid="assessments-section">
        {hasAssessments ? (
          <div data-testid="assessment-list">Assessment list here...</div>
        ) : (
          <EmptyState type="assessments" onAction={() => setHasAssessments(true)} />
        )}
      </div>

      <div data-testid="team-section">
        {hasTeamMembers ? (
          <div data-testid="team-members">Team members here...</div>
        ) : (
          <EmptyState type="users" onAction={() => setHasTeamMembers(true)} />
        )}
      </div>

      <div data-testid="notifications-section">
        {hasNotifications ? (
          <div data-testid="notifications">Notifications here...</div>
        ) : (
          <EmptyState type="notifications" />
        )}
      </div>
    </div>
  );
};

describe('Empty States Tests', () => {
  it('should display meaningful empty state with title and message', () => {
    render(<EmptyState type="assessments" />);

    expect(screen.getByTestId('empty-state-title')).toHaveTextContent('No Assessments Yet');
    expect(screen.getByTestId('empty-state-message')).toHaveTextContent(
      'Create your first assessment to get started with team insights.'
    );
    expect(screen.getByTestId('empty-state-icon')).toHaveTextContent('📝');
  });

  it('should provide actionable next steps where appropriate', async () => {
    const onAction = vi.fn();
    render(<EmptyState type="teams" onAction={onAction} />);

    const actionButton = screen.getByTestId('empty-state-action');
    expect(actionButton).toHaveTextContent('Create Team');

    await userEvent.click(actionButton);
    expect(onAction).toHaveBeenCalled();
  });

  it('should not show action button for non-actionable empty states', () => {
    render(<EmptyState type="notifications" />);

    expect(screen.queryByTestId('empty-state-action')).not.toBeInTheDocument();
  });

  it('should handle different empty state types appropriately', () => {
    const { rerender } = render(<EmptyState type="dashboard" />);
    expect(screen.getByTestId('empty-state-title')).toHaveTextContent('Welcome to Your Dashboard');

    rerender(<EmptyState type="data" />);
    expect(screen.getByTestId('empty-state-title')).toHaveTextContent('No Data Available');

    rerender(<EmptyState type="teams" />);
    expect(screen.getByTestId('empty-state-title')).toHaveTextContent('No Teams Created');
  });

  it('should handle empty states in dashboard sections', async () => {
    render(<DashboardWithEmptyStates />);

    // Should show empty states for all sections
    expect(screen.getByTestId('empty-state-assessments')).toBeInTheDocument();
    expect(screen.getByTestId('empty-state-users')).toBeInTheDocument();
    expect(screen.getByTestId('empty-state-notifications')).toBeInTheDocument();

    // Can take action to populate sections
    await userEvent.click(screen.getByTestId('empty-state-action'));
    await waitFor(() => {
      expect(screen.getByTestId('assessment-list')).toBeInTheDocument();
    });
  });

  it('should be accessible with proper ARIA labels', () => {
    render(<EmptyState type="assessments" />);

    const emptyState = screen.getByTestId('empty-state');
    expect(emptyState).toHaveAttribute('role', 'region');
    expect(emptyState).toHaveAttribute('aria-label', 'No assessments available');
  });

  it('should handle loading states before showing empty states', () => {
    const LoadingState = () => {
      const [loading, setLoading] = React.useState(true);
      const [data, setData] = React.useState([]);

      React.useEffect(() => {
        setTimeout(() => {
          setLoading(false);
          setData([]);
        }, 100);
      }, []);

      if (loading) {
        return <div data-testid="loading">Loading...</div>;
      }

      return data.length > 0 ? (
        <div>Data here</div>
      ) : (
        <EmptyState type="data" />
      );
    };

    render(<LoadingState />);

    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });
});
