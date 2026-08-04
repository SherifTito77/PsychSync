/**
 * Automated Tests for Memory-Safe Event Listener Hooks
 * Vitest version
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useEventListener, useWindowResize, useKeyDown } from '../useCleanupEventListener';

describe('useEventListener', () => {
  let mockElement: any;

  beforeEach(() => {
    mockElement = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should add event listener on mount', () => {
    const handler = vi.fn();

    renderHook(() =>
      useEventListener('click', handler, mockElement)
    );

    expect(mockElement.addEventListener).toHaveBeenCalledWith(
      'click',
      expect.any(Function),
      undefined
    );
  });

  it('should remove event listener on unmount', () => {
    const handler = vi.fn();

    const { unmount } = renderHook(() =>
      useEventListener('click', handler, mockElement)
    );

    expect(mockElement.removeEventListener).not.toHaveBeenCalled();

    unmount();

    expect(mockElement.removeEventListener).toHaveBeenCalledWith(
      'click',
      expect.any(Function),
      undefined
    );
  });

  it('should pass options to addEventListener', () => {
    const handler = vi.fn();
    const options = { capture: true, passive: true };

    renderHook(() =>
      useEventListener('click', handler, mockElement, options)
    );

    expect(mockElement.addEventListener).toHaveBeenCalledWith(
      'click',
      expect.any(Function),
      options
    );
  });

  it('should pass options to removeEventListener', () => {
    const handler = vi.fn();
    const options = { capture: true };

    const { unmount } = renderHook(() =>
      useEventListener('click', handler, mockElement, options)
    );

    unmount();

    expect(mockElement.removeEventListener).toHaveBeenCalledWith(
      'click',
      expect.any(Function),
      options
    );
  });

  it('should update handler without adding multiple listeners', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();

    const { rerender } = renderHook(
      ({ hndlr, opts }) => useEventListener('click', hndlr, mockElement, opts),
      {
        initialProps: { hndlr: handler1, opts: undefined }
      }
    );

    expect(mockElement.addEventListener).toHaveBeenCalledTimes(1);

    rerender({ hndlr: handler2, opts: undefined });

    // Should add again with new handler
    expect(mockElement.addEventListener).toHaveBeenCalledTimes(2);

    // Should remove old listener
    expect(mockElement.removeEventListener).toHaveBeenCalledTimes(1);
  });

  it('should call handler when event is triggered', () => {
    const handler = vi.fn();
    let storedHandler: any;

    mockElement.addEventListener.mockImplementation((event, hndlr) => {
      storedHandler = hndlr;
    });

    renderHook(() => useEventListener('click', handler, mockElement));

    // Simulate event
    const mockEvent = new Event('click');
    storedHandler(mockEvent);

    expect(handler).toHaveBeenCalledWith(mockEvent);
  });
});

describe('useWindowResize', () => {
  it('should add window resize listener on mount', () => {
    const addSpy = vi.spyOn(window, 'addEventListener');
    const handler = vi.fn();

    renderHook(() => useWindowResize(handler));

    expect(addSpy).toHaveBeenCalledWith('resize', expect.any(Function));

    addSpy.mockRestore();
  });

  it('should remove window resize listener on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const handler = vi.fn();

    const { unmount } = renderHook(() => useWindowResize(handler));

    unmount();

    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function));

    removeSpy.mockRestore();
  });

  it('should call handler when window is resized', () => {
    const handler = vi.fn();
    let storedHandler: any;

    vi.spyOn(window, 'addEventListener').mockImplementation((event, hndlr) => {
      if (event === 'resize') storedHandler = hndlr;
    });

    renderHook(() => useWindowResize(handler));

    // Simulate resize event
    const mockEvent = new Event('resize');
    window.dispatchEvent(mockEvent);

    expect(handler).toHaveBeenCalled();
  });
});

describe('useKeyDown', () => {
  it('should add keydown listener for specific key', () => {
    const addSpy = vi.spyOn(window, 'addEventListener');
    const handler = vi.fn();

    renderHook(() => useKeyDown('Escape', handler));

    expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function));

    addSpy.mockRestore();
  });

  it('should only call handler when specific key is pressed', () => {
    const handler = vi.fn();
    let storedHandler: any;

    vi.spyOn(window, 'addEventListener').mockImplementation((event, hndlr) => {
      storedHandler = hndlr;
    });

    renderHook(() => useKeyDown('Escape', handler));

    // Press different key
    const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    storedHandler(escapeEvent);

    expect(handler).toHaveBeenCalledTimes(1);
    handler.mockClear();

    // Press Enter instead
    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' });
    storedHandler(enterEvent);

    expect(handler).not.toHaveBeenCalled();
  });

  it('should pass the keyboard event to handler', () => {
    const handler = vi.fn();
    let storedHandler: any;

    vi.spyOn(window, 'addEventListener').mockImplementation((event, hndlr) => {
      storedHandler = hndlr;
    });

    renderHook(() => useKeyDown('Escape', handler));

    const mockEvent = new KeyboardEvent('keydown', {
      key: 'Escape',
      code: 'Escape',
      keyCode: 27,
    });

    storedHandler(mockEvent);

    expect(handler).toHaveBeenCalledWith(mockEvent);
  });
});

describe('Memory Leak Prevention - Event Listeners', () => {
  it('should not leak event listeners', () => {
    const mockWindow = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };

    const handler = vi.fn();

    const { unmount: unmount1 } = renderHook(() =>
      useEventListener('click', handler, mockWindow)
    );

    const { unmount: unmount2 } = renderHook(() =>
      useEventListener('resize', handler, mockWindow)
    );

    expect(mockWindow.removeEventListener).not.toHaveBeenCalled();

    unmount1();

    expect(mockWindow.removeEventListener).toHaveBeenCalledTimes(1);

    unmount2();

    expect(mockWindow.removeEventListener).toHaveBeenCalledTimes(2);
  });

  it('should cleanup when rapidly remounting', () => {
    const addSpy = vi.spyOn(window, 'addEventListener');
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const handler = vi.fn();

    // Mount and unmount multiple times
    for (let i = 0; i < 10; i++) {
      const { unmount } = renderHook(() =>
        useWindowResize(handler)
      );
      unmount();
    }

    // Should balance add and remove calls
    expect(addSpy).toHaveBeenCalledTimes(10);
    expect(removeSpy).toHaveBeenCalledTimes(10);

    addSpy.mockRestore();
    removeSpy.mockRestore();
  });

  it('should update listener without accumulating', () => {
    const mockElement = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };

    const handler1 = vi.fn();
    const handler2 = vi.fn();

    const { rerender } = renderHook(
      (hndlr) => useEventListener('click', hndlr, mockElement),
      { initialProps: handler1 }
    );

    expect(mockElement.addEventListener).toHaveBeenCalledTimes(1);

    // Update handler multiple times
    rerender(handler2);
    rerender(handler1);
    rerender(handler2);

    // Should have added listeners for each update
    // But also removed old ones
    expect(mockElement.addEventListener).toHaveBeenCalledTimes(4);
    expect(mockElement.removeEventListener).toHaveBeenCalledTimes(3);
  });
});
