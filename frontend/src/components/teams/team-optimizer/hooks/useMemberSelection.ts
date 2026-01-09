/**
 * Member Selection Hook
 *
 * Manages selection state for team members and candidates
 */

import { useState } from 'react';

export const useMemberSelection = () => {
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);

  const toggleMemberSelection = (memberId: string) => {
    setSelectedMembers(prev =>
      prev.includes(memberId)
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    );
  };

  const isMemberSelected = (memberId: string): boolean => {
    return selectedMembers.includes(memberId);
  };

  const clearSelection = () => {
    setSelectedMembers([]);
  };

  return {
    selectedMembers,
    toggleMemberSelection,
    isMemberSelected,
    clearSelection,
    setSelectedMembers,
  };
};
