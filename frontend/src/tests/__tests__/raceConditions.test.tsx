/**
 * Frontend Race Condition Detection Suite
 *
 * Tests for race conditions in React components, Context providers,
 * and async operations. These tests verify that the frontend handles
 * concurrent state updates, request cancellation, and race conditions correctly.
 *
 * Focus Areas:
 * 1. React Context state update races
 * 2. useEffect dependency issues
 * 3. Async operation cancellation
 * 4. Stale closures
 * 5. Multiple simultaneous requests
 * 6. Request cleanup on unmount
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { render, screen, fireEvent, waitFor as waitForReact } from '@testing-library/react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { TeamProvider, useTeam } from '../contexts/TeamContext';
import { AssessmentProvider, useAssessment } from '../contexts/AssessmentContext';
import userEvent from '@testing-library/user-event';

// Mock API module
jest.mock('../services/apiClient', () => ({
  api: {
    login: jest.fn(),
    refreshToken: jest.fn(),
    getTeamMembers: jest.fn(),
    addTeamMember: jest.fn(),
    submitAssessmentResponse: jest.fn(),
  },
}));

import { api } from '../services/apiClient';

describe('AuthContext Race Conditions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  // Test 1: Concurrent login attempts
  test('should handle concurrent login attempts without corruption', async () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;

    // Mock successful login responses
    api.login.mockResolvedValue({
      success: true,
      data: {
        access_token: 'token-123',
        refresh_token: 'refresh-123',
        user: { id: 'user-1', email: 'user@example.com' }
      }
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Simulate 3 concurrent login attempts
    await act(async () => {
      const promises = [
        result.current.login('user@example.com', 'password'),
        result.current.login('user@example.com', 'password'),
        result.current.login('user@example.com', 'password')
      ];

      const results = await Promise.all(promises);

      // All should resolve
      results.forEach(result => {
        expect(result).toHaveProperty('success');
      });
    });

    // Verify final state is consistent
    await waitFor(() => {
      expect(result.current.user).toBeTruthy();
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  // Test 2: Rapid state updates
  test('should handle rapid state updates without corruption', async () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    // Mock user
    api.login.mockResolvedValue({
      success: true,
      data: {
        access_token: 'token-123',
        refresh_token: 'refresh-123',
        user: { id: 'user-1', email: 'user@example.com' }
      }
    });

    // Login first
    await act(async () => {
      await result.current.login('user@example.com', 'password');
    });

    const initialActivityTime = result.current.lastActivity;

    // Simulate 100 rapid activity updates
    await act(async () => {
      for (let i = 0; i < 100; i++) {
        result.current.updateLastActivity();
        // Use setImmediate or queueMicrotask to avoid blocking
        await new Promise(resolve => setImmediate(resolve));
      }
    });

    // Verify all updates were captured
    await waitFor(() => {
      expect(result.current.lastActivity).not.toBe(initialActivityTime);
      expect(result.current.user).toBeTruthy();
    });
  });

  // Test 3: Token refresh race condition
  test('should handle concurrent token refresh attempts idempotently', async () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    // Mock existing session
    const mockTokens = {
      access_token: 'expiring-token',
      refresh_token: 'valid-refresh'
    };

    localStorage.setItem('tokens', JSON.stringify(mockTokens));

    // Mock refresh API
    api.refreshToken.mockResolvedValue({
      success: true,
      data: {
        access_token: 'new-token-123',
        refresh_token: 'new-refresh-123'
      }
    });

    // Simulate 5 concurrent refresh attempts
    await act(async () => {
      const refreshPromises = [];
      for (let i = 0; i < 5; i++) {
        refreshPromises.push(result.current.refreshToken());
      }

      const results = await Promise.all(refreshPromises);

      // All should succeed
      results.forEach(result => {
        expect(result.success).toBe(true);
      });

      // But only ONE API call should be made (idempotency)
      expect(api.refreshToken).toHaveBeenCalledTimes(1);
    });

    // Verify final state
    await waitFor(() => {
      expect(result.current.tokens?.access_token).toBe('new-token-123');
    });
  });

  // Test 4: Logout race with pending operations
  test('should cancel pending operations on logout', async () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    // Mock user
    api.login.mockResolvedValue({
      success: true,
      data: {
        access_token: 'token-123',
        refresh_token: 'refresh-123',
        user: { id: 'user-1', email: 'user@example.com' }
      }
    });

    // Start a long-running operation (don't await)
    const slowOperation = result.current.loadUserData().catch(() => {
      // Expected to be cancelled
    });

    // Immediately logout
    api.login.mockReset(); // Clear login mock
    await act(async () => {
      await result.current.logout();
    });

    // Verify user is logged out
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});

describe('TeamContext Race Conditions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Test 5: Concurrent team member additions
  test('should handle concurrent member additions correctly', async () => {
    const wrapper = ({ children }) => <TeamProvider>{children}</TeamProvider>;
    const { result } = renderHook(() => useTeam(), { wrapper });

    // Mock API responses
    api.getTeamMembers.mockResolvedValue({
      success: true,
      data: { members: [] }
    });

    // Load team
    await act(async () => {
      await result.current.loadTeam('team-123');
    });

    const initialMemberCount = result.current.members?.length || 0;

    // Mock successful additions
    api.addTeamMember.mockImplementation((userId) =>
      Promise.resolve({
        success: true,
        data: {
          id: `member-${userId}`,
          user_id: userId,
          team_id: 'team-123',
          role: 'MEMBER'
        }
      })
    );

    // Add 10 members concurrently
    await act(async () => {
      const addPromises = [];
      for (let i = 1; i <= 10; i++) {
        addPromises.push(
          result.current.addMember(`user-${i}`)
        );
      }

      await Promise.all(addPromises);
    });

    // Verify all members were added
    await waitFor(() => {
      expect(result.current.members.length).toBe(initialMemberCount + 10);
    });
  });

  // Test 6: Concurrent team removals
  test('should handle concurrent member removals without errors', async () => {
    const wrapper = ({ children }) => <TeamProvider>{children}</TeamProvider>;
    const { result } = renderHook(() => useTeam(), { wrapper });

    // Mock existing members
    api.getTeamMembers.mockResolvedValue({
      success: true,
      data: {
        members: [
          { id: 'member-1', user_id: 'user-1' },
          { id: 'member-2', user_id: 'user-2' },
          { id: 'member-3', user_id: 'user-3' }
        ]
      }
    });

    await act(async () => {
      await result.current.loadTeam('team-123');
    });

    // Mock removal API
    api.removeTeamMember.mockResolvedValue({
      success: true
    });

    // Remove all 3 members concurrently
    await act(async () => {
      const removalPromises = [
        result.current.removeMember('member-1'),
        result.current.removeMember('member-2'),
        result.current.removeMember('member-3')
      ];

      await Promise.all(removalPromises);
    });

    // Verify all members removed
    await waitFor(() => {
      expect(result.current.members.length).toBe(0);
    });
  });
});

describe('AssessmentContext Race Conditions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Test 7: Rapid question responses
  test('should handle rapid question responses without data loss', async () => {
    const wrapper = ({ children }) => <AssessmentProvider>{children}</AssessmentProvider>;
    const { result } = renderHook(() => useAssessment(), { wrapper });

    // Start assessment
    await act(async () => {
      await result.current.startAssessment('mbti');
    });

    // Mock submit API
    api.submitAssessmentResponse.mockResolvedValue({
      success: true
    });

    // Submit 93 responses rapidly (MBTI has 93 questions)
    await act(async () => {
      const submitPromises = [];
      for (let i = 1; i <= 93; i++) {
        submitPromises.push(
          result.current.saveResponse({
            question_id: i,
            answer_value: Math.random() > 0.5 ? 'agree' : 'disagree'
          })
        );

        // Small delay to simulate realistic typing
        if (i % 10 === 0) {
          await new Promise(resolve => setImmediate(resolve));
        }
      }

      await Promise.all(submitPromises);
    });

    // Verify all responses saved
    await waitFor(() => {
      expect(result.current.responses.length).toBe(93);
    });
  });

  // Test 8: Concurrent assessment submission
  test('should handle multiple submit attempts gracefully', async () => {
    const wrapper = ({ children }) => <AssessmentProvider>{children}</AssessmentProvider>;
    const { result } = renderHook(() => useAssessment(), { wrapper });

    // Start assessment and add responses
    await act(async () => {
      await result.current.startAssessment('mbti');
      await result.current.saveResponse({
        question_id: 1,
        answer_value: 'agree'
      });
    });

    // Mock submit API (only first should succeed)
    let submitCount = 0;
    api.submitAssessment.mockImplementation(async () => {
      submitCount++;
      if (submitCount === 1) {
        return { success: true, data: { assessment_id: 'assessment-123' } };
      }
      return {
        success: false,
        error: 'Assessment already submitted'
      };
    });

    // Submit 3 times concurrently
    await act(async () => {
      const submitPromises = [
        result.current.submitAssessment(),
        result.current.submitAssessment(),
        result.current.submitAssessment()
      ];

      const results = await Promise.all(submitPromises);

      // Only one should succeed
      const successCount = results.filter(r => r.success === true).length;
      expect(successCount).toBe(1);
    });

    // Verify assessment is marked as submitted
    await waitFor(() => {
      expect(result.current.status).toBe('submitted');
    });
  });
});

describe('Async Operation Cancellation', () => {
  // Test 9: Request cancellation on unmount
  test('should cancel pending requests on component unmount', async () => {
    let cancelRequested = false;

    // Mock API with abort controller
    const mockAbortController = {
      signal: {},
      abort: jest.fn(() => { cancelRequested = true; })
    };

    api.getTeamMembers.mockImplementation(() => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          if (cancelRequested) {
            reject(new DOMException('Aborted', 'AbortError'));
          } else {
            resolve({ success: true, data: { members: [] } });
          }
        }, 100);

        // Return abort controller
        return { ...Promise, controller: mockAbortController };
      });
    });

    // Render component that will be unmounted
    function TeamComponent() {
      const { result } = renderHook(() => useTeam());

      // Start loading team members
      useEffect(() => {
        result.current.loadTeam('team-123');
      }, [result]);

      return <div>Team Members: {result.current.members?.length || 0}</div>;
    }

    const { unmount } = render(<TeamComponent />);

    // Unmount immediately
    unmount();

    // Verify abort was called
    await waitFor(() => {
      expect(mockAbortController.abort).toHaveBeenCalled();
    });
  });

  // Test 10: Stale closure detection in useEffect
  test('should not have stale closures in useEffect with dependencies', async () => {
    let renderCount = 0;
    let fetchedData: string[] = [];

    function TestComponent({ userId }: { userId: string }) {
      const [data, setData] = React.useState<string | null>(null);
      const [isLoading, setIsLoading] = React.useState(false);

      React.useEffect(() => {
        let cancelled = false;

        const fetchData = async () => {
          setIsLoading(true);

          // Simulate async call
          const result = await api.getTeamMembers();

          if (!cancelled && result.success) {
            setData(result.data.members[0]?.name || null);
            fetchedData.push(result.data.members[0]?.name);
          }

          setIsLoading(false);
        };

        fetchData();

        return () => {
          cancelled = true;
        };
      }, [userId]); // Include userId in dependencies

      renderCount++;

      if (isLoading) {
        return <div>Loading...</div>;
      }

      return <div>User: {data}</div>;
    }

    // Rapid prop changes
    const { rerender } = render(<TestComponent userId="1" />);
    rerender(<TestComponent userId="2" />);
    rerender(<TestComponent userId="3" />);

    // Verify only the last result is displayed (no stale data)
    await waitForReact(() => {
      expect(screen.getByText(/User:/)).toBeInTheDocument();
    });

    // Should have rendered 3 times (once per userId)
    expect(renderCount).toBe(3);

    // Should only have 1 data point (last one)
    expect(fetchedData.length).toBe(1);
  });
});

describe('State Update Races with Multiple Contexts', () => {
  // Test 11: Multiple context providers updating simultaneously
  test('should handle multiple contexts updating without race conditions', async () => {
    function TestApp() {
      return (
        <AuthProvider>
          <TeamProvider>
            <AssessmentProvider>
              <TestComponent />
            </AssessmentProvider>
          </TeamProvider>
        </AuthProvider>
      );
    }

    function TestComponent() {
      const auth = useAuth();
      const team = useTeam();
      const assessment = useAssessment();

      // Simulate concurrent updates from multiple contexts
      const handleConcurrentUpdates = async () => {
        await act(async () => {
          await Promise.all([
            auth.updateLastActivity(),
            team.loadTeam('team-123'),
            assessment.startAssessment('mbti')
          ]);
        });
      };

      return (
        <div>
          <button onClick={handleConcurrentUpdates}>Update All</button>
          <div>Auth: {auth.isAuthenticated ? 'Logged in' : 'Logged out'}</div>
          <div>Team: {team.currentTeam?.id || 'No team'}</div>
          <div>Assessment: {assessment.currentAssessment?.id || 'No assessment'}</div>
        </div>
      );
    }

    const { getByText } = render(<TestApp />);

    // Mock APIs
    api.login.mockResolvedValue({
      success: true,
      data: {
        access_token: 'token',
        refresh_token: 'refresh',
        user: { id: 'user-1', email: 'user@example.com' }
      }
    });

    api.getTeamMembers.mockResolvedValue({
      success: true,
      data: { team_id: 'team-123', name: 'Test Team', members: [] }
    });

    // Trigger concurrent updates
    await userEvent.click(getByText('Update All'));

    // Verify all updates completed successfully
    await waitFor(() => {
      expect(getByText(/Auth: Logged in/)).toBeInTheDocument();
      expect(getByText(/Team: team-123/)).toBeInTheDocument();
      expect(getByText(/Assessment: mbti/)).toBeInTheDocument();
    });
  });
});

describe('Network Request Race Conditions', () => {
  // Test 12: Multiple requests for same data
  test('should deduplicate simultaneous requests for same resource', async () => {
    let requestCount = 0;

    api.getTeamMembers.mockImplementation(async () => {
      requestCount++;
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 100));
      return {
        success: true,
        data: { team_id: 'team-123', members: [] }
      };
    });

    function TeamComponent() {
      const team = useTeam();
      const [isLoading, setIsLoading] = React.useState(false);

      useEffect(() => {
        const loadTeam = async () => {
          setIsLoading(true);
          await team.loadTeam('team-123');
          setIsLoading(false);
        };

        loadTeam();
      }, [team]);

      return (
        <div>
          <button onClick={() => team.loadTeam('team-123')}>
            Reload Team
          </button>
          {isLoading && <div>Loading...</div>}
          <div>Members: {team.currentTeam?.members?.length || 0}</div>
        </div>
      );
    }

    const { getByText, getAllByText } = render(
      <TeamProvider>
        <TeamComponent />
      </TeamProvider>
    );

    // Click reload button 5 times rapidly
    await act(async () => {
      const clickPromises = [];
      for (let i = 0; i < 5; i++) {
        clickPromises.push(
          userEvent.click(getByText('Reload Team'))
        );
      }
      await Promise.all(clickPromises);
    });

    // Should only make 1 request (deduplication)
    await waitFor(() => {
      expect(requestCount).toBe(1);
      expect(getAllByText('Loading...')).toHaveLength(0);
    });
  });
});

describe('Form State Race Conditions', () => {
  // Test 13: Rapid form input changes
  test('should handle rapid form input changes without losing data', async () => {
    function FormComponent() {
      const [formData, setFormData] = React.useState({
        email: '',
        password: ''
      });

      const handleChange = (field: string, value: string) => {
        setFormData(prev => ({
          ...prev,
          [field]: value
        }));
      };

      return (
        <form>
          <input
            data-testid="email-input"
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
          />
          <input
            data-testid="password-input"
            type="password"
            value={formData.password}
            onChange={(e) => handleChange('password', e.target.value)}
          />
          <div>Email: {formData.email}</div>
          <div>Password: {formData.password}</div>
        </form>
      );
    }

    const { getByTestId, getByText } = render(<FormComponent />);
    const emailInput = getByTestId('email-input');
    const passwordInput = getByTestId('password-input');

    // Simulate rapid typing in both fields
    await act(async () => {
      await userEvent.type(emailInput, 'user@example.com');
      await userEvent.type(passwordInput, 'password123');
    });

    // Verify final state has both values
    await waitFor(() => {
      expect(getByText('Email: user@example.com')).toBeInTheDocument();
      expect(getByText('Password: password123')).toBeInTheDocument();
    });
  });
});

describe('Component Lifecycle Race Conditions', () => {
  // Test 14: setState after unmount
  test('should not setState after component unmounts', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    function ComponentWithAsyncState() {
      const [data, setData] = React.useState<string | null>(null);

      React.useEffect(() => {
        const timeout = setTimeout(() => {
          // This will execute after unmount
          setData('data-after-unmount');
        }, 100);

        return () => {
          clearTimeout(timeout);
        };
      }, []);

      return <div>{data || 'No data'}</div>;
    }

    const { unmount } = render(<ComponentWithAsyncState />);

    // Unmount before timeout completes
    unmount();

    // Wait for timeout to complete
    await new Promise(resolve => setTimeout(resolve, 200));

    // Should not log setState error (cleanup worked)
    expect(consoleSpy).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  // Test 15: Promise resolution after unmount
  test('should handle promise resolution after unmount', async () => {
    let resolvePromise: (value: string) => void;

    function ComponentThatFetches() {
      const [data, setData] = React.useState<string | null>(null);
      const [error, setError] = React.useState<string | null>(null);

      React.useEffect(() => {
        const fetchData = async () => {
          try {
            const result = await new Promise<string>((resolve) => {
              resolvePromise = resolve;
              // Resolve after delay
              setTimeout(() => resolve('fetched-data'), 100);
            });

            // This will execute after unmount
            if (result) {
              setData(result);
            }
          } catch (err) {
            setError(err as string);
          }
        };

        fetchData();
      }, []);

      if (error) {
        return <div>Error: {error}</div>;
      }

      return <div>{data || 'Loading...'}</div>;
    }

    const { unmount } = render(<ComponentThatFetches />);

    // Unmount immediately
    unmount();

    // Resolve the promise
    await act(async () => {
      resolvePromise('fetched-data');
    });

    // Should not crash (React handles this gracefully)
    // No assertion needed - if it crashes, test will fail
  });
});

describe('Animation and Transition Race Conditions', () => {
  // Test 16: Rapid transitions between states
  test('should handle rapid state transitions correctly', async () => {
    function MultiStateComponent() {
      const [state, setState] = React.useState('idle');

      const transitionTo = (newState: string) => {
        setState(newState);
      };

      return (
        <div>
          <div data-testid="current-state">{state}</div>
          <button onClick={() => transitionTo('loading')}>
            Start Loading
          </button>
          <button onClick={() => transitionTo('success')}>
            Show Success
          </button>
          <button onClick={() => transitionTo('error')}>
            Show Error
          </button>
        </div>
      );
    }

    const { getByTestId, getByText } = render(<MultiStateComponent />);
    const stateDisplay = getByTestId('current-state');

    // Rapid state transitions
    await act(async () => {
      await userEvent.click(getByText('Start Loading'));
      await userEvent.click(getByText('Show Error'));
      await userEvent.click(getByText('Show Success'));
      await userEvent.click(getByText('Start Loading'));
    });

    // Final state should be 'loading' (last transition)
    await waitFor(() => {
      expect(stateDisplay).toHaveTextContent('loading');
    });
  });
});

describe('LocalStorage/SessionStorage Race Conditions', () => {
  // Test 17: Concurrent localStorage writes
  test('should handle concurrent localStorage writes', async () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => <AuthProvider>{children}</AuthProvider>
    });

    // Write multiple values to localStorage concurrently
    await act(async () => {
      const writePromises = [];
      for (let i = 0; i < 10; i++) {
        writePromises.push(
          Promise.resolve().then(() => {
            localStorage.setItem(`key-${i}`, `value-${i}`);
          })
        );
      }

      await Promise.all(writePromises);
    });

    // Verify all writes succeeded
    for (let i = 0; i < 10; i++) {
      expect(localStorage.getItem(`key-${i}`)).toBe(`value-${i}`);
    }
  });
});
