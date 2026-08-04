/**
 * Automated Tests for Memory-Safe Timer Hooks
 * Vitest version
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useTimeout, useInterval, useConditionalTimeout } from '../useCleanupTimer';

// Mock timers for testing
beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('useTimeout', () => {
  it('should execute callback after specified delay', () => {
    const callback = vi.fn();
    renderHook(() => useTimeout(callback, 1000));

    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1000);

    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should cleanup timeout on unmount', () => {
    const callback = vi.fn();
    const { unmount } = renderHook(() => useTimeout(callback, 1000));

    // Unmount before timeout completes
    unmount();

    vi.advanceTimersByTime(1000);

    // Callback should NOT be called after unmount
    expect(callback).not.toHaveBeenCalled();
  });

  it('should not create timeout when delay is null', () => {
    const callback = vi.fn();
    renderHook(() => useTimeout(callback, null));

    vi.advanceTimersByTime(1000);

    expect(callback).not.toHaveBeenCalled();
  });

  it('should update callback without restarting timer', () => {
    const callback1 = vi.fn();
    const callback2 = vi.fn();

    const { rerender } = renderHook(
      ({ cb, delay }) => useTimeout(cb, delay),
      { initialProps: { cb: callback1, delay: 1000 } }
    );

    // Update callback
    rerender({ cb: callback2, delay: 1000 });

    vi.advanceTimersByTime(1000);

    // Should call latest callback
    expect(callback1).not.toHaveBeenCalled();
    expect(callback2).toHaveBeenCalledTimes(1);
  });

  it('should restart timer when delay changes', () => {
    const callback = vi.fn();

    const { rerender } = renderHook(
      ({ cb, delay }) => useTimeout(cb, delay),
      { initialProps: { cb: callback, delay: 1000 } }
    );

    // Change delay before first timer completes
    rerender({ cb: callback, delay: 500 });

    vi.advanceTimersByTime(500);

    expect(callback).toHaveBeenCalledTimes(1);
  });
});

describe('useInterval', () => {
  it('should execute callback repeatedly at specified interval', () => {
    const callback = vi.fn();
    renderHook(() => useInterval(callback, 1000));

    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalledTimes(2);

    vi.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalledTimes(3);
  });

  it('should cleanup interval on unmount', () => {
    const callback = vi.fn();
    const { unmount } = renderHook(() => useInterval(callback, 1000));

    vi.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalledTimes(1);

    unmount();

    vi.advanceTimersByTime(2000);

    // Callback should not be called after unmount
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should not create interval when delay is null', () => {
    const callback = vi.fn();
    renderHook(() => useInterval(callback, null));

    vi.advanceTimersByTime(5000);

    expect(callback).not.toHaveBeenCalled();
  });

  it('should restart interval when delay changes', () => {
    const callback = vi.fn();

    const { rerender } = renderHook(
      ({ cb, delay }) => useInterval(cb, delay),
      { initialProps: { cb: callback, delay: 1000 } }
    );

    vi.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalledTimes(1);

    // Change interval
    rerender({ cb: callback, delay: 500 });

    vi.advanceTimersByTime(500);
    expect(callback).toHaveBeenCalledTimes(2);

    vi.advanceTimersByTime(500);
    expect(callback).toHaveBeenCalledTimes(3);
  });

  it('should not accumulate multiple intervals', () => {
    const callback = vi.fn();

    const { rerender } = renderHook(
      ({ cb, delay }) => useInterval(cb, delay),
      { initialProps: { cb: callback, delay: 1000 } }
    );

    // Re-render with same delay
    rerender({ cb: callback, delay: 1000 });
    rerender({ cb: callback, delay: 1000 });

    vi.advanceTimersByTime(1000);

    // Should only be called once, not multiple times
    expect(callback).toHaveBeenCalledTimes(1);
  });
});

describe('useConditionalTimeout', () => {
  it('should execute callback when condition is true', () => {
    const callback = vi.fn();
    renderHook(() => useConditionalTimeout(callback, 1000, true));

    vi.advanceTimersByTime(1000);

    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should not execute callback when condition is false', () => {
    const callback = vi.fn();
    renderHook(() => useConditionalTimeout(callback, 1000, false));

    vi.advanceTimersByTime(1000);

    expect(callback).not.toHaveBeenCalled();
  });

  it('should cleanup when condition changes to false', () => {
    const callback = vi.fn();

    const { rerender } = renderHook(
      ({ cb, delay, condition }) => useConditionalTimeout(cb, delay, condition),
      { initialProps: { cb: callback, delay: 1000, condition: true } }
    );

    // Change condition to false before timeout completes
    rerender({ cb: callback, delay: 1000, condition: false });

    vi.advanceTimersByTime(1000);

    expect(callback).not.toHaveBeenCalled();
  });

  it('should cleanup on unmount', () => {
    const callback = vi.fn();
    const { unmount } = renderHook(() =>
      useConditionalTimeout(callback, 1000, true)
    );

    unmount();

    vi.advanceTimersByTime(1000);

    expect(callback).not.toHaveBeenCalled();
  });

  it('should restart timer when condition becomes true again', () => {
    const callback = vi.fn();

    const { rerender } = renderHook(
      ({ cb, delay, condition }) => useConditionalTimeout(cb, delay, condition),
      { initialProps: { cb: callback, delay: 1000, condition: false } }
    );

    vi.advanceTimersByTime(1000);
    expect(callback).not.toHaveBeenCalled();

    // Enable condition
    rerender({ cb: callback, delay: 1000, condition: true });

    vi.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalledTimes(1);
  });
});

describe('Memory Leak Prevention', () => {
  it('useTimeout should not leak timers', () => {
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

    const { unmount: unmount1 } = renderHook(() =>
      useTimeout(() => {}, 1000)
    );
    const { unmount: unmount2 } = renderHook(() =>
      useTimeout(() => {}, 2000)
    );

    expect(clearTimeoutSpy).not.toHaveBeenCalled();

    unmount1();
    expect(clearTimeoutSpy).toHaveBeenCalledTimes(1);

    unmount2();
    expect(clearTimeoutSpy).toHaveBeenCalledTimes(2);

    clearTimeoutSpy.mockRestore();
  });

  it('useInterval should not leak intervals', () => {
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

    const { unmount: unmount1 } = renderHook(() =>
      useInterval(() => {}, 1000)
    );
    const { unmount: unmount2 } = renderHook(() =>
      useInterval(() => {}, 2000)
    );

    expect(clearIntervalSpy).not.toHaveBeenCalled();

    unmount1();
    expect(clearIntervalSpy).toHaveBeenCalledTimes(1);

    unmount2();
    expect(clearIntervalSpy).toHaveBeenCalledTimes(2);

    clearIntervalSpy.mockRestore();
  });

  it('should cleanup multiple timers from same component', () => {
    const callback = vi.fn();

    const { unmount } = renderHook(() => {
      useTimeout(callback, 1000);
      useTimeout(callback, 2000);
      useInterval(callback, 500);
    });

    // Mount 3 timers
    expect(vi.getTimerCount()).toBe(3);

    unmount();

    // All timers should be cleared
    expect(vi.getTimerCount()).toBe(0);
  });
});
