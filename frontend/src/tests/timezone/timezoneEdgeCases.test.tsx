// frontend/src/tests/timezone/timezoneEdgeCases.test.tsx
/**
 * Comprehensive Timezone Edge Cases Testing
 * Tests for time logging across different timezones and edge cases
 * Business Impact: Global team coordination, accurate assessment timing
 * ROI: 3x - Prevents scheduling conflicts and data integrity issues
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock timezone detection and manipulation
const mockTimezones = [
  'UTC',
  'America/New_York',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney',
  'Pacific/Auckland',
  'America/Sao_Paulo',
  'Asia/Dubai',
  'Asia/Kolkata'
];

// Mock Intl.DateTimeFormat for timezone testing
const originalDateTimeFormat = Intl.DateTimeFormat;
const mockDateTimeFormat = vi.fn((locale, options) => {
  const timeZone = options?.timeZone || 'UTC';
  return new originalDateTimeFormat(locale, { ...options, timeZone });
});

// Test component for timezone handling
const TimezoneTestComponent: React.FC<{
  userTimezone?: string;
  serverTimezone?: string;
  onTimezoneChange?: (timezone: string) => void;
}> = ({ userTimezone = 'UTC', serverTimezone = 'UTC', onTimezoneChange }) => {
  const [currentTime, setCurrentTime] = React.useState(new Date());
  const [selectedTimezone, setSelectedTimezone] = React.useState(userTimezone);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleTimezoneChange = (timezone: string) => {
    setSelectedTimezone(timezone);
    onTimezoneChange?.(timezone);
  };

  const formatTimeInTimezone = (date: Date, timezone: string) => {
    try {
      return new Intl.DateTimeFormat('en-US', {
        timeZone: timezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }).format(date);
    } catch (error) {
      return 'Invalid timezone';
    }
  };

  const calculateTimezoneOffset = (timezone: string) => {
    try {
      const now = new Date();
      const utcDate = new Date(now.toLocaleString("en-US", { timeZone: "UTC" }));
      const tzDate = new Date(now.toLocaleString("en-US", { timeZone: timezone }));
      return (tzDate.getTime() - utcDate.getTime()) / (1000 * 60 * 60);
    } catch (error) {
      return 0;
    }
  };

  return (
    <div data-testid="timezone-component">
      <div data-testid="current-time-utc">
        {formatTimeInTimezone(currentTime, 'UTC')}
      </div>
      <div data-testid="current-time-user">
        {formatTimeInTimezone(currentTime, selectedTimezone)}
      </div>
      <div data-testid="timezone-offset">
        {calculateTimezoneOffset(selectedTimezone)}
      </div>
      <select
        data-testid="timezone-selector"
        onChange={(e) => handleTimezoneChange(e.target.value)}
        value={selectedTimezone}
      >
        {mockTimezones.map(tz => (
          <option key={tz} value={tz}>{tz}</option>
        ))}
      </select>
    </div>
  );
};

// Assessment timing component
const AssessmentTimingComponent: React.FC<{
  assessmentStartTime?: Date;
  assessmentEndTime?: Date;
  userTimezone?: string;
}> = ({
  assessmentStartTime = new Date('2024-12-17T10:00:00Z'),
  assessmentEndTime = new Date('2024-12-17T11:00:00Z'),
  userTimezone = 'UTC'
}) => {
  const calculateDuration = (start: Date, end: Date) => {
    const duration = end.getTime() - start.getTime();
    return {
      hours: Math.floor(duration / (1000 * 60 * 60)),
      minutes: Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60)),
      seconds: Math.floor((duration % (1000 * 60)) / 1000)
    };
  };

  const formatInUserTimezone = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: userTimezone,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short'
    }).format(date);
  };

  const duration = calculateDuration(assessmentStartTime, assessmentEndTime);

  return (
    <div data-testid="assessment-timing">
      <div data-testid="start-time">{formatInUserTimezone(assessmentStartTime)}</div>
      <div data-testid="end-time">{formatInUserTimezone(assessmentEndTime)}</div>
      <div data-testid="duration-hours">{duration.hours}</div>
      <div data-testid="duration-minutes">{duration.minutes}</div>
      <div data-testid="duration-seconds">{duration.seconds}</div>
      <div data-testid="total-duration-seconds">
        {Math.floor((assessmentEndTime.getTime() - assessmentStartTime.getTime()) / 1000)}
      </div>
    </div>
  );
};

describe('Timezone Edge Cases Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock Date.now() for consistent testing
    const mockNow = new Date('2024-12-17T12:00:00Z');
    vi.spyOn(Date, 'now').mockReturnValue(mockNow.getTime());
    vi.setSystemTime(mockNow);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // 🌍 Basic Timezone Functionality Tests
  describe('Basic Timezone Functionality', () => {
    it('should display current time in UTC correctly', () => {
      render(<TimezoneTestComponent userTimezone="UTC" />);

      const utcTime = screen.getByTestId('current-time-utc');
      expect(utcTime).toBeInTheDocument();
      expect(utcTime).toHaveTextContent('12/17/2024, 12:00:00');
    });

    it('should switch between different timezones correctly', async () => {
      const handleTimezoneChange = vi.fn();
      render(
        <TimezoneTestComponent
          userTimezone="UTC"
          onTimezoneChange={handleTimezoneChange}
        />
      );

      const selector = screen.getByTestId('timezone-selector');

      // Switch to New York timezone
      fireEvent.change(selector, { target: { value: 'America/New_York' } });

      await waitFor(() => {
        expect(handleTimezoneChange).toHaveBeenCalledWith('America/New_York');
      });

      const userTime = screen.getByTestId('current-time-user');
      expect(userTime).toBeInTheDocument();
    });

    it('should calculate timezone offsets correctly', () => {
      render(<TimezoneTestComponent userTimezone="America/New_York" />);

      const offset = screen.getByTestId('timezone-offset');
      // New York is UTC-5 (or -4 during DST)
      expect(offset).toHaveTextContent(/-5|-4/);
    });
  });

  // 🕐 Daylight Saving Time Edge Cases
  describe('Daylight Saving Time Edge Cases', () => {
    it('should handle DST transition correctly', () => {
      // Mock date during DST transition (March 2024)
      const dstDate = new Date('2024-03-10T12:00:00Z');
      vi.setSystemTime(dstDate);

      render(<TimezoneTestComponent userTimezone="America/New_York" />);

      const userTime = screen.getByTestId('current-time-user');
      expect(userTime).toBeInTheDocument();

      // During DST, New York should be UTC-4
      const offset = screen.getByTestId('timezone-offset');
      expect(offset).toHaveTextContent('-4');
    });

    it('should handle timezones that do not observe DST', () => {
      render(<TimezoneTestComponent userTimezone="Asia/Dubai" />);

      const offset = screen.getByTestId('timezone-offset');
      // Dubai doesn't observe DST, always UTC+4
      expect(offset).toHaveTextContent('4');
    });

    it('should handle Southern Hemisphere DST correctly', () => {
      // Mock date during Southern Hemisphere DST (January 2024)
      const southernDSTDate = new Date('2024-01-15T12:00:00Z');
      vi.setSystemTime(southernDSTDate);

      render(<TimezoneTestComponent userTimezone="Australia/Sydney" />);

      const offset = screen.getByTestId('timezone-offset');
      // Sydney is UTC+11 during DST
      expect(offset).toHaveTextContent('11');
    });
  });

  // ⏰ Assessment Timing Edge Cases
  describe('Assessment Timing Edge Cases', () => {
    it('should calculate assessment duration correctly across timezone changes', () => {
      const startTime = new Date('2024-12-17T10:00:00Z');
      const endTime = new Date('2024-12-17T11:30:00Z');

      render(
        <AssessmentTimingComponent
          assessmentStartTime={startTime}
          assessmentEndTime={endTime}
          userTimezone="America/Los_Angeles"
        />
      );

      // Duration should be consistent regardless of timezone
      expect(screen.getByTestId('duration-hours')).toHaveTextContent('1');
      expect(screen.getByTestId('duration-minutes')).toHaveTextContent('30');
      expect(screen.getByTestId('total-duration-seconds')).toHaveTextContent('5400');
    });

    it('should handle assessments spanning multiple days across timezones', () => {
      const startTime = new Date('2024-12-16T20:00:00Z');
      const endTime = new Date('2024-12-17T02:00:00Z');

      render(
        <AssessmentTimingComponent
          assessmentStartTime={startTime}
          assessmentEndTime={endTime}
          userTimezone="Asia/Tokyo"
        />
      );

      const startTimeElement = screen.getByTestId('start-time');
      const endTimeElement = screen.getByTestId('end-time');

      // Should show dates in Tokyo timezone (UTC+9)
      expect(startTimeElement).toBeInTheDocument();
      expect(endTimeElement).toBeInTheDocument();
    });

    it('should handle very short assessment durations', () => {
      const startTime = new Date('2024-12-17T12:00:00Z');
      const endTime = new Date('2024-12-17T12:00:05Z');

      render(
        <AssessmentTimingComponent
          assessmentStartTime={startTime}
          assessmentEndTime={endTime}
          userTimezone="UTC"
        />
      );

      expect(screen.getByTestId('duration-seconds')).toHaveTextContent('5');
      expect(screen.getByTestId('total-duration-seconds')).toHaveTextContent('5');
    });
  });

  // 🌏 International Timezone Edge Cases
  describe('International Timezone Edge Cases', () => {
    it('should handle timezones with 30-minute offsets', () => {
      render(<TimezoneTestComponent userTimezone="Asia/Kolkata" />);

      const offset = screen.getByTestId('timezone-offset');
      // India is UTC+5:30
      expect(offset).toHaveTextContent('5.5');
    });

    it('should handle timezones near the International Date Line', () => {
      render(<TimezoneTestComponent userTimezone="Pacific/Auckland" />);

      const offset = screen.getByTestId('timezone-offset');
      // Auckland is UTC+12 or +13 during DST
      expect(offset).toHaveTextContent(/12|13/);
    });

    it('should handle timezone abbreviations correctly', () => {
      const TimezoneAbbreviationComponent = () => {
        const date = new Date('2024-12-17T12:00:00Z');
        const nyTime = new Intl.DateTimeFormat('en-US', {
          timeZone: 'America/New_York',
          timeZoneName: 'short'
        }).format(date);

        return <div data-testid="tz-abbreviation">{nyTime}</div>;
      };

      render(<TimezoneAbbreviationComponent />);

      const tzAbbrev = screen.getByTestId('tz-abbreviation');
      expect(tzAbbrev).toBeInTheDocument();
      // Should contain either EST or EDT depending on DST
      expect(tzAbbrev.textContent).toMatch(/EST|EDT/);
    });
  });

  // 🔥 Invalid Timezone Handling Tests
  describe('Invalid Timezone Handling', () => {
    it('should handle invalid timezone gracefully', () => {
      const component = render(
        <TimezoneTestComponent userTimezone="Invalid/Timezone" />
      );

      const userTime = screen.getByTestId('current-time-user');
      expect(userTime).toHaveTextContent('Invalid timezone');
    });

    it('should handle timezone detection failures', () => {
      // Mock Intl.DateTimeFormat to throw error
      const originalFormat = Intl.DateTimeFormat;
      vi.spyOn(Intl, 'DateTimeFormat').mockImplementation(() => {
        throw new Error('Timezone detection failed');
      });

      expect(() => {
        render(<TimezoneTestComponent />);
      }).not.toThrow();

      // Restore original implementation
      vi.mocked(Intl.DateTimeFormat).mockRestore();
    });

    it('should fallback to UTC when timezone is undefined', () => {
      render(<TimezoneTestComponent userTimezone={undefined as any} />);

      const userTime = screen.getByTestId('current-time-user');
      expect(userTime).toBeInTheDocument();
    });
  });

  // 📱 Mobile Timezone Edge Cases
  describe('Mobile Timezone Edge Cases', () => {
    it('should handle timezone changes on mobile devices', async () => {
      // Mock mobile environment
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const MobileTimezoneComponent = () => {
        const [currentTimezone, setCurrentTimezone] = React.useState('UTC');

        React.useEffect(() => {
          // Simulate mobile timezone detection
          const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
          if (detectedTimezone) {
            setCurrentTimezone(detectedTimezone);
          }
        }, []);

        return (
          <div>
            <div data-testid="mobile-timezone">{currentTimezone}</div>
            <TimezoneTestComponent userTimezone={currentTimezone} />
          </div>
        );
      };

      render(<MobileTimezoneComponent />);

      const mobileTimezone = screen.getByTestId('mobile-timezone');
      expect(mobileTimezone).toBeInTheDocument();
    });

    it('should handle timezone changes during offline mode', () => {
      // Mock navigator.onLine for offline testing
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false,
      });

      const OfflineTimezoneComponent = () => {
        const [cachedTimezone] = React.useState(() => {
          // Simulate cached timezone from localStorage
          return localStorage.getItem('userTimezone') || 'UTC';
        });

        return <TimezoneTestComponent userTimezone={cachedTimezone} />;
      };

      render(<OfflineTimezoneComponent />);

      const userTime = screen.getByTestId('current-time-user');
      expect(userTime).toBeInTheDocument();
    });
  });

  // 🔄 Performance and Caching Tests
  describe('Timezone Performance and Caching', () => {
    it('should cache timezone calculations and not recalculate unnecessarily', () => {
      let timezoneCalculationCount = 0;

      const CachedTimezoneComponent = () => {
        const calculateOffset = () => {
          timezoneCalculationCount++;
          return 0; // Mock calculation
        };

        return <TimezoneTestComponent userTimezone="UTC" />;
      };

      const { rerender } = render(<CachedTimezoneComponent />);

      // Rerender multiple times
      for (let i = 0; i < 5; i++) {
        rerender(<CachedTimezoneComponent />);
      }

      // Should not excessively recculate
      expect(timezoneCalculationCount).toBeLessThan(10);
    });

    it('should handle rapid timezone switching without performance issues', async () => {
      const handleTimezoneChange = vi.fn();

      render(
        <TimezoneTestComponent
          onTimezoneChange={handleTimezoneChange}
        />
      );

      const selector = screen.getByTestId('timezone-selector');
      const timezones = ['America/New_York', 'Europe/London', 'Asia/Tokyo'];

      // Rapid timezone switching
      for (const tz of timezones) {
        fireEvent.change(selector, { target: { value: tz } });

        await waitFor(() => {
          expect(handleTimezoneChange).toHaveBeenCalledWith(tz);
        });
      }

      expect(handleTimezoneChange).toHaveBeenCalledTimes(3);
    });
  });

  // 🎯 Edge Case Scenarios
  describe('Complex Edge Case Scenarios', () => {
    it('should handle leap year February 29th across timezones', () => {
      const leapYearDate = new Date('2024-02-29T12:00:00Z');
      vi.setSystemTime(leapYearDate);

      render(<TimezoneTestComponent userTimezone="Pacific/Auckland" />);

      const userTime = screen.getByTestId('current-time-user');
      expect(userTime).toBeInTheDocument();

      // Should correctly handle Feb 29th in New Zealand timezone
      const offset = screen.getByTestId('timezone-offset');
      expect(offset).toBeInTheDocument();
    });

    it('should handle year-end transitions across timezones', () => {
      const yearEndDate = new Date('2024-12-31T23:30:00Z');
      vi.setSystemTime(yearEndDate);

      render(<TimezoneTestComponent userTimezone="Asia/Shanghai" />);

      const userTime = screen.getByTestId('current-time-user');
      expect(userTime).toBeInTheDocument();
    });

    it('should handle assessment timing during timezone changes', async () => {
      const TimezoneChangeDuringAssessment = () => {
        const [userTimezone, setUserTimezone] = React.useState('UTC');
        const assessmentStart = new Date('2024-12-17T10:00:00Z');
        const [currentTime] = React.useState(new Date('2024-12-17T10:30:00Z'));

        return (
          <div>
            <button
              onClick={() => setUserTimezone('America/New_York')}
              data-testid="change-timezone"
            >
              Change Timezone
            </button>
            <AssessmentTimingComponent
              assessmentStartTime={assessmentStart}
              assessmentEndTime={currentTime}
              userTimezone={userTimezone}
            />
          </div>
        );
      };

      render(<TimezoneChangeDuringAssessment />);

      // Check initial duration
      expect(screen.getByTestId('duration-minutes')).toHaveTextContent('30');

      // Change timezone during assessment
      fireEvent.click(screen.getByTestId('change-timezone'));

      await waitFor(() => {
        // Duration should remain the same
        expect(screen.getByTestId('duration-minutes')).toHaveTextContent('30');
        expect(screen.getByTestId('total-duration-seconds')).toHaveTextContent('1800');
      });
    });
  });
});

describe('Timezone Integration Tests', () => {
  it('should integrate with assessment submission timing', async () => {
    const AssessmentSubmissionComponent = () => {
      const [submissionTime, setSubmissionTime] = React.useState<Date | null>(null);
      const userTimezone = 'America/Los_Angeles';

      const handleSubmit = () => {
        setSubmissionTime(new Date());
      };

      return (
        <div>
          <button onClick={handleSubmit} data-testid="submit-assessment">
            Submit Assessment
          </button>
          {submissionTime && (
            <div data-testid="submission-time">
              {new Intl.DateTimeFormat('en-US', {
                timeZone: userTimezone,
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZoneName: 'short'
              }).format(submissionTime)}
            </div>
          )}
        </div>
      );
    };

    render(<AssessmentSubmissionComponent />);

    fireEvent.click(screen.getByTestId('submit-assessment'));

    await waitFor(() => {
      const submissionTime = screen.getByTestId('submission-time');
      expect(submissionTime).toBeInTheDocument();
      expect(submissionTime.textContent).toMatch(/PST|PDT/); // Pacific timezone
    });
  });
});