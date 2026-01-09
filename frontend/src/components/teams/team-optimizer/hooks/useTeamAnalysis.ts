/**
 * Team Analysis Hook
 *
 * Manages team data and performs analysis calculations
 */

import { useState, useEffect } from 'react';
import { TeamMember } from '../types';
import { MOCK_TEAM_MEMBERS, MOCK_CANDIDATES } from '../constants/mockData';

export const useTeamAnalysis = () => {
  const [currentTeam, setCurrentTeam] = useState<TeamMember[]>([]);
  const [availableCandidates, setAvailableCandidates] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize with mock data
    // In production, this would fetch from API
    setCurrentTeam(MOCK_TEAM_MEMBERS);
    setAvailableCandidates(MOCK_CANDIDATES);
    setLoading(false);
  }, []);

  return {
    currentTeam,
    availableCandidates,
    loading,
    setCurrentTeam,
    setAvailableCandidates,
  };
};
