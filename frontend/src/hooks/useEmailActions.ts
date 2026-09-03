/**
 * Email Actions Hook
 * Custom hook for managing email actions (reply, forward, compose)
 */

import { useState, useCallback } from 'react';

export type EmailActionMode = 'reply' | 'forward' | 'compose';

export interface OriginalEmail {
  from_email: string;
  subject: string;
  body: string;
  message_id?: string;
  date?: string;
  cc?: string[];
}

interface UseEmailActionsReturn {
  isOpen: boolean;
  mode: EmailActionMode;
  originalEmail: OriginalEmail | null;
  openReply: (email: OriginalEmail) => void;
  openForward: (email: OriginalEmail) => void;
  openCompose: () => void;
  close: () => void;
}

export const useEmailActions = (): UseEmailActionsReturn => {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<EmailActionMode>('compose');
  const [originalEmail, setOriginalEmail] = useState<OriginalEmail | null>(null);

  const openReply = useCallback((email: OriginalEmail) => {
    setMode('reply');
    setOriginalEmail(email);
    setIsOpen(true);
  }, []);

  const openForward = useCallback((email: OriginalEmail) => {
    setMode('forward');
    setOriginalEmail(email);
    setIsOpen(true);
  }, []);

  const openCompose = useCallback(() => {
    setMode('compose');
    setOriginalEmail(null);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    // Reset after animation
    setTimeout(() => {
      setMode('compose');
      setOriginalEmail(null);
    }, 300);
  }, []);

  return {
    isOpen,
    mode,
    originalEmail,
    openReply,
    openForward,
    openCompose,
    close,
  };
};
