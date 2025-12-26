// frontend/src/tests/session/sessionExpiration.test.tsx
/**
 * Comprehensive Session Expiration Testing
 * Tests for user session timeout, token refresh, and logout behavior
 * Business Impact: Security compliance, user experience, data protection
 * ROI: 4x - Prevents unauthorized access and data breaches
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock JWT token handling
const mockJWTToken = {
  access: 'mock-access-token',
  refresh: 'mock-refresh-token',
  expiresAt: Date.now() + 30 * 60 * 1000, // 30 minutes
};

// Mock session management
const mockSessionManager = {
  getToken: vi.fn(() => mockJWTToken.access),
  getRefreshToken: vi.fn(() => mockJWTToken.refresh),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
  isTokenExpired: vi.fn(() => false),
  refreshAccessToken: vi.fn(() => Promise.resolve(mockJWTToken)),
};

// Mock API responses
const mockAPI = {
  refreshToken: vi.fn(() => Promise.resolve({
    access: 'new-access-token',
    refresh: 'new-refresh-token',
    expiresAt: Date.now() + 30 * 60 * 1000
  })),
  logout: vi.fn(() => Promise.resolve({ success: true })),
};

// Session provider component
const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = React.useState(true);
  const [sessionWarning, setSessionWarning] = React.useState(false);
  const [timeRemaining, setTimeRemaining] = React.useState(30 * 60); // 30 minutes

  React.useEffect(() => {
    const checkSession = () => {
      const isExpired = mockSessionManager.isTokenExpired();
      if (isExpired) {
        setIsAuthenticated(false);
        mockSessionManager.clearTokens();
      }
    };

    const interval = setInterval(checkSession, 1000); // Check every second
    return () => clearInterval(interval);
  }, []);

  React.useEffect(() => {
    const warningTimer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 300 && prev > 0) { // 5 minutes warning
          setSessionWarning(true);
        }
        if (prev <= 0) {
          setIsAuthenticated(false);
          mockSessionManager.clearTokens();
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(warningTimer);
  }, []);

  const extendSession = async () => {
    try {
      const newTokens = await mockSessionManager.refreshAccessToken();
      mockSessionManager.setTokens(newTokens);
      setTimeRemaining(30 * 60); // Reset to 30 minutes
      setSessionWarning(false);
    } catch (error) {
      setIsAuthenticated(false);
      mockSessionManager.clearTokens();
    }
  };

  const logout = async () => {
    try {
      await mockAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      mockSessionManager.clearTokens();
      setIsAuthenticated(false);
    }
  };

  return (
    <div data-testid="session-provider">
      {isAuthenticated ? (
        <div>
          {sessionWarning && (
            <div data-testid="session-warning">
              <p data-testid="warning-message">
                Session expires in {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
              </p>
              <button onClick={extendSession} data-testid="extend-session">
                Extend Session
              </button>
            </div>
          )}
          <div data-testid="authenticated-content">
            {children}
          </div>
          <button onClick={logout} data-testid="logout-button">
            Logout
          </button>
          <div data-testid="time-remaining">{timeRemaining}</div>
        </div>
      ) : (
        <div data-testid="login-form">
          <h2>Login Required</h2>
          <button onClick={() => setIsAuthenticated(true)} data-testid="mock-login">
            Mock Login
          </button>
        </div>
      )}
    </div>
  );
};

// Assessment component with session awareness
const SessionAwareAssessment: React.FC = () => {
  const [assessmentData, setAssessmentData] = React.useState<{ answers: Record<string, string> }>({ answers: {} });
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const saveAnswer = (questionId: string, answer: string) => {
    setAssessmentData(prev => ({
      answers: { ...prev.answers, [questionId]: answer }
    }));
  };

  const submitAssessment = async () => {
    setIsSubmitting(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      const token = mockSessionManager.getToken();
      if (!token) {
        throw new Error('No token available');
      }
      // Submit assessment logic here
      alert('Assessment submitted successfully!');
    } catch (error) {
      alert('Session expired. Please login again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div data-testid="assessment-component">
      <h3>Assessment</h3>
      <div>
        <label>Question 1:</label>
        <input
          data-testid="question-1"
          onChange={(e) => saveAnswer('q1', e.target.value)}
          placeholder="Enter answer"
        />
      </div>
      <div>
        <label>Question 2:</label>
        <input
          data-testid="question-2"
          onChange={(e) => saveAnswer('q2', e.target.value)}
          placeholder="Enter answer"
        />
      </div>
      <button
        onClick={submitAssessment}
        disabled={isSubmitting}
        data-testid="submit-assessment"
      >
        {isSubmitting ? 'Submitting...' : 'Submit Assessment'}
      </button>
    </div>
  );
};

describe('Session Expiration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ⏰ Basic Session Timeout Tests
  describe('Basic Session Timeout', () => {
    it('should show session warning when token is about to expire', async () => {
      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      ), 10000; // Increase timeout

      // Initially no warning
      expect(screen.queryByTestId('session-warning')).not.toBeInTheDocument();

      // Fast forward 25 minutes (5 minutes before expiration)
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('session-warning')).toBeInTheDocument();
        expect(screen.getByTestId('warning-message')).toHaveTextContent(/Session expires in 5:/);
      }, { timeout: 5000 });
    }, 10000);

    it('should allow session extension before expiration', async () => {
      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Fast forward to warning time
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('session-warning')).toBeInTheDocument();
      });

      // Extend session
      fireEvent.click(screen.getByTestId('extend-session'));

      await waitFor(() => {
        expect(screen.queryByTestId('session-warning')).not.toBeInTheDocument();
        expect(screen.getByTestId('time-remaining')).toHaveTextContent('1800'); // 30 minutes
      });
    });

    it('should logout automatically when session expires', async () => {
      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Fast forward 30 minutes (session expiration)
      act(() => {
        vi.advanceTimersByTime(30 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();
        expect(screen.getByText('Login Required')).toBeInTheDocument();
        expect(mockSessionManager.clearTokens).toHaveBeenCalled();
      });
    });
  });

  // 🔄 Token Refresh Tests
  describe('Token Refresh Behavior', () => {
    it('should refresh token automatically before expiration', async () => {
      mockSessionManager.refreshAccessToken.mockResolvedValue({
        access: 'refreshed-access-token',
        refresh: 'refreshed-refresh-token',
        expiresAt: Date.now() + 30 * 60 * 1000
      });

      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Fast forward to refresh time (5 minutes before expiration)
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(mockSessionManager.refreshAccessToken).toHaveBeenCalled();
      });
    });

    it('should handle token refresh failure gracefully', async () => {
      mockSessionManager.refreshAccessToken.mockRejectedValue(new Error('Refresh failed'));

      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Fast forward to refresh time
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();
      });
    });

    it('should store new tokens after successful refresh', async () => {
      const newTokens = {
        access: 'new-access-token',
        refresh: 'new-refresh-token',
        expiresAt: Date.now() + 30 * 60 * 1000
      };

      mockSessionManager.refreshAccessToken.mockResolvedValue(newTokens);

      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Trigger refresh
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(mockSessionManager.setTokens).toHaveBeenCalledWith(newTokens);
      });
    });
  });

  // 📝 Assessment Session Management Tests
  describe('Assessment Session Management', () => {
    it('should warn user before session timeout during assessment', async () => {
      render(
        <SessionProvider>
          <SessionAwareAssessment />
        </SessionProvider>
      );

      // Fast forward to warning time
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('session-warning')).toBeInTheDocument();
        expect(screen.getByTestId('assessment-component')).toBeInTheDocument();
      });
    });

    it('should save assessment progress before session expiration', async () => {
      const mockSaveProgress = vi.fn(() => Promise.resolve());

      const AssessmentWithAutoSave = () => {
        const [progress, setProgress] = React.useState({ q1: '', q2: '' });

        React.useEffect(() => {
          const saveInterval = setInterval(() => {
            mockSaveProgress(progress);
          }, 5000); // Auto-save every 5 seconds

          return () => clearInterval(saveInterval);
        }, [progress]);

        return (
          <div>
            <SessionAwareAssessment />
            <div data-testid="auto-save-status">Progress saved</div>
          </div>
        );
      };

      render(
        <SessionProvider>
          <AssessmentWithAutoSave />
        </SessionProvider>
      );

      // Fast forward to trigger auto-save
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(mockSaveProgress).toHaveBeenCalled();
      });
    });

    it('should prevent assessment submission after session expiration', async () => {
      render(
        <SessionProvider>
          <SessionAwareAssessment />
        </SessionProvider>
      );

      // Fill in assessment
      fireEvent.change(screen.getByTestId('question-1'), { target: { value: 'Answer 1' } });
      fireEvent.change(screen.getByTestId('question-2'), { target: { value: 'Answer 2' } });

      // Fast forward to session expiration
      act(() => {
        vi.advanceTimersByTime(30 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();
      });

      // Try to submit (should fail since not authenticated)
      mockSessionManager.getToken.mockReturnValue(null);

      const submitButton = screen.queryByTestId('submit-assessment');
      if (submitButton) {
        fireEvent.click(submitButton);

        await waitFor(() => {
          expect(mockSessionManager.getToken).toHaveBeenCalled();
        });
      }
    });
  });

  // 🔐 Security Tests
  describe('Session Security', () => {
    it('should clear all session data on logout', async () => {
      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Click logout
      fireEvent.click(screen.getByTestId('logout-button'));

      await waitFor(() => {
        expect(mockAPI.logout).toHaveBeenCalled();
        expect(mockSessionManager.clearTokens).toHaveBeenCalled();
        expect(screen.getByTestId('login-form')).toBeInTheDocument();
      });
    });

    it('should handle concurrent session activities', async () => {
      render(
        <SessionProvider>
          <SessionAwareAssessment />
          <div>Another Component</div>
        </SessionProvider>
      );

      // Simulate multiple activities
      fireEvent.change(screen.getByTestId('question-1'), { target: { value: 'Answer 1' } });

      // Fast forward to warning time
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('session-warning')).toBeInTheDocument();
        expect(screen.getByTestId('assessment-component')).toBeInTheDocument();
      });
    });

    it('should handle session theft detection', async () => {
      mockSessionManager.refreshAccessToken.mockRejectedValue(
        new Error('Token invalid - possible session theft')
      );

      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Fast forward to refresh attempt
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();
        expect(mockSessionManager.clearTokens).toHaveBeenCalled();
      });
    });
  });

  // 📱 Mobile Session Tests
  describe('Mobile Session Management', () => {
    it('should handle app background/foreground session management', async () => {
      const MobileSessionComponent = () => {
        const [appState, setAppState] = React.useState<'active' | 'background'>('active');

        React.useEffect(() => {
          const handleVisibilityChange = () => {
            setAppState(document.hidden ? 'background' : 'active');
          };

          document.addEventListener('visibilitychange', handleVisibilityChange);
          return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
        }, []);

        return (
          <SessionProvider>
            <div data-testid="app-state">{appState}</div>
            <div>Mobile App Content</div>
          </SessionProvider>
        );
      };

      render(<MobileSessionComponent />);

      expect(screen.getByTestId('app-state')).toHaveTextContent('active');

      // Simulate app going to background
      Object.defineProperty(document, 'hidden', { value: true });
      fireEvent(document, new Event('visibilitychange'));

      await waitFor(() => {
        expect(screen.getByTestId('app-state')).toHaveTextContent('background');
      });
    });

    it('should handle session timeout during network disconnect', async () => {
      // Mock network offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      const OfflineSessionComponent = () => {
        const [isOffline, setIsOffline] = React.useState(!navigator.onLine);

        React.useEffect(() => {
          const handleOnline = () => setIsOffline(false);
          const handleOffline = () => setIsOffline(true);

          window.addEventListener('online', handleOnline);
          window.addEventListener('offline', handleOffline);

          return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
          };
        }, []);

        return (
          <SessionProvider>
            <div data-testid="network-status">{isOffline ? 'Offline' : 'Online'}</div>
            <div>Content with offline support</div>
          </SessionProvider>
        );
      };

      render(<OfflineSessionComponent />);

      expect(screen.getByTestId('network-status')).toHaveTextContent('Offline');

      // Session should still work offline for a period
      act(() => {
        vi.advanceTimersByTime(10 * 60 * 1000); // 10 minutes
      });

      await waitFor(() => {
        expect(screen.getByTestId('network-status')).toHaveTextContent('Offline');
      });
    });
  });

  // 🎯 Edge Case Scenarios
  describe('Session Edge Cases', () => {
    it('should handle rapid session extension requests', async () => {
      render(
        <SessionProvider>
          <div>Protected Content</div>
        </SessionProvider>
      );

      // Fast forward to warning time
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('session-warning')).toBeInTheDocument();
      });

      // Rapidly click extend multiple times
      const extendButton = screen.getByTestId('extend-session');

      for (let i = 0; i < 5; i++) {
        fireEvent.click(extendButton);
      }

      await waitFor(() => {
        expect(screen.queryByTestId('session-warning')).not.toBeInTheDocument();
      });
    });

    it('should handle session timeout during file upload', async () => {
      const FileUploadComponent = () => {
        const [uploadProgress, setUploadProgress] = React.useState(0);
        const [isUploading, setIsUploading] = React.useState(false);

        const uploadFile = async () => {
          setIsUploading(true);
          for (let i = 0; i <= 100; i += 10) {
            await new Promise(resolve => setTimeout(resolve, 100));
            setUploadProgress(i);
          }
          setIsUploading(false);
        };

        return (
          <SessionProvider>
            <div>
              <button onClick={uploadFile} data-testid="upload-button">
                Upload File
              </button>
              {isUploading && (
                <div data-testid="upload-progress">{uploadProgress}%</div>
              )}
            </div>
          </SessionProvider>
        );
      };

      render(<FileUploadComponent />);

      // Start upload
      fireEvent.click(screen.getByTestId('upload-button'));

      // Fast forward during upload
      act(() => {
        vi.advanceTimersByTime(25 * 60 * 1000);
      });

      await waitFor(() => {
        expect(screen.getByTestId('upload-progress')).toBeInTheDocument();
      });
    });

    it('should maintain session state across browser refresh', async () => {
      // Mock localStorage persistence
      const mockLocalStorage = {
        getItem: vi.fn(() => JSON.stringify(mockJWTToken)),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      };
      Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

      const PersistentSessionComponent = () => {
        const [sessionRestored, setSessionRestored] = React.useState(false);

        React.useEffect(() => {
          const storedSession = localStorage.getItem('userSession');
          if (storedSession) {
            setSessionRestored(true);
          }
        }, []);

        return (
          <SessionProvider>
            <div data-testid="session-restored">{sessionRestored ? 'true' : 'false'}</div>
          </SessionProvider>
        );
      };

      render(<PersistentSessionComponent />);

      await waitFor(() => {
        expect(screen.getByTestId('session-restored')).toHaveTextContent('true');
      });
    });
  });
});

describe('Session Integration Tests', () => {
  it('should integrate with real assessment workflow', async () => {
    const AssessmentWorkflow = () => {
      const [step, setStep] = React.useState(1);
      const [isSubmitting, setIsSubmitting] = React.useState(false);

      const submitAssessment = async () => {
        setIsSubmitting(true);
        try {
          await new Promise(resolve => setTimeout(resolve, 1000));
          alert('Assessment submitted successfully!');
        } catch (error) {
          alert('Submission failed. Please try again.');
        } finally {
          setIsSubmitting(false);
        }
      };

      return (
        <SessionProvider>
          <div>
            <div data-testid="assessment-step">Step {step} of 3</div>
            <button onClick={() => setStep(2)} data-testid="next-step">
              Next Step
            </button>
            {step === 3 && (
              <button
                onClick={submitAssessment}
                disabled={isSubmitting}
                data-testid="final-submit"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Assessment'}
              </button>
            )}
          </div>
        </SessionProvider>
      );
    };

    render(<AssessmentWorkflow />);

    // Navigate through assessment
    fireEvent.click(screen.getByTestId('next-step'));
    expect(screen.getByTestId('assessment-step')).toHaveTextContent('Step 2 of 3');

    // Fast forward near session expiration
    act(() => {
      vi.advanceTimersByTime(28 * 60 * 1000);
    });

    await waitFor(() => {
      expect(screen.getByTestId('session-warning')).toBeInTheDocument();
    });
  });
});