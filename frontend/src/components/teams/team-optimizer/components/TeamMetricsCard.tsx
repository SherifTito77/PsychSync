/**
 * Team Metrics Card Component
 *
 * Displays team composition metrics and statistics
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { TeamMember } from '../types';
import { calculateTeamStats } from '../utils/teamMetrics';

interface TeamMetricsCardProps {
  team: TeamMember[];
}

export const TeamMetricsCard: React.FC<TeamMetricsCardProps> = ({ team }) => {
  const stats = calculateTeamStats(team);

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="text-center p-3 bg-blue-50 rounded-lg">
        <div className="text-2xl font-bold text-blue-600">{team.length}</div>
        <p className="text-sm text-blue-700">Team Size</p>
      </div>
      <div className="text-center p-3 bg-green-50 rounded-lg">
        <div className="text-2xl font-bold text-green-600">
          {stats.averagePerformance.toFixed(1)}%
        </div>
        <p className="text-sm text-green-700">Avg Performance</p>
      </div>
      <div className="text-center p-3 bg-purple-50 rounded-lg">
        <div className="text-2xl font-bold text-purple-600">
          {stats.averageSkills.toFixed(1)}
        </div>
        <p className="text-sm text-purple-700">Avg Skills</p>
      </div>
      <div className="text-center p-3 bg-orange-50 rounded-lg">
        <div className="text-2xl font-bold text-orange-600">
          {stats.averageExperience.toFixed(1)}
        </div>
        <p className="text-sm text-orange-700">Avg Experience</p>
      </div>
    </div>
  );
};
