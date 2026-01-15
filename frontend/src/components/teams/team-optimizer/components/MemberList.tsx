/**
 * Member List Component
 *
 * Displays list of team members with their metrics
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users } from 'lucide-react';
import { TeamMember } from '../types';
import { getScoreColor, calculateTeamStats } from '../utils/teamMetrics';

interface MemberListProps {
  members: TeamMember[];
  title: string;
  description?: string;
  onMemberClick?: (memberId: string) => void;
  selectedMembers?: string[];
  showSelection?: boolean;
}

export const MemberList: React.FC<MemberListProps> = ({
  members,
  title,
  description,
  onMemberClick,
  selectedMembers = [],
  showSelection = false,
}) => {
  const stats = calculateTeamStats(members);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          {title}
        </CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {members.map((member) => (
            <div
              key={member.id}
              className={`flex items-center justify-between p-3 border rounded-lg ${
                onMemberClick ? 'hover:bg-gray-50 cursor-pointer' : ''
              }`}
              onClick={() => onMemberClick?.(member.id)}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                  <Users className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{member.name}</h3>
                    {showSelection && selectedMembers.includes(member.id) && (
                      <Badge variant="default">Selected</Badge>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    {member.role} • {member.department}
                  </div>
                  <div className="flex gap-1 mt-1">
                    {member.skills.slice(0, 2).map((skill) => (
                      <Badge key={skill} variant="secondary" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-sm text-gray-600">Performance</div>
                <div className={`font-bold ${getScoreColor(member.performanceScore)}`}>
                  {(member.performanceScore * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">Collaboration</div>
                <div className={`font-bold ${getScoreColor(member.collaborationScore)}`}>
                  {(member.collaborationScore * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
