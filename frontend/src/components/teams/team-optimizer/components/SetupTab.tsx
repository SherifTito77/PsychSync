/**
 * Setup Tab Component
 *
 * Configuration interface for team requirements and member selection
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Progress from '@/components/ui/progress';
import { Brain, RefreshCw, Upload, Download, Users, Search, Settings } from 'lucide-react';
import { TeamRequirement, TeamMember } from '../types';
import { MemberList } from './MemberList';
import { TeamMetricsCard } from './TeamMetricsCard';

interface SetupTabProps {
  requirements: TeamRequirement;
  setRequirements: (req: TeamRequirement) => void;
  currentTeam: TeamMember[];
  availableCandidates: TeamMember[];
  selectedMembers: string[];
  isOptimizing: boolean;
  onToggleMember: (id: string) => void;
  onOptimize: () => void;
}

export const SetupTab: React.FC<SetupTabProps> = ({
  requirements,
  setRequirements,
  currentTeam,
  availableCandidates,
  selectedMembers,
  isOptimizing,
  onToggleMember,
  onOptimize,
}) => {
  return (
    <div className="space-y-6">
      {/* Requirements Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Team Requirements
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-4">Basic Requirements</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Team Size</label>
                  <input
                    type="number"
                    value={requirements.teamSize}
                    onChange={(e) =>
                      setRequirements({
                        ...requirements,
                        teamSize: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                    min="1"
                    max="20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Project Type</label>
                  <select
                    value={requirements.projectType}
                    onChange={(e) =>
                      setRequirements({
                        ...requirements,
                        projectType: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="Digital Transformation">Digital Transformation</option>
                    <option value="Product Development">Product Development</option>
                    <option value="Process Improvement">Process Improvement</option>
                    <option value="Research & Development">Research & Development</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Deadline</label>
                  <input
                    type="date"
                    value={requirements.deadline}
                    onChange={(e) =>
                      setRequirements({
                        ...requirements,
                        deadline: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Budget ($)</label>
                  <input
                    type="number"
                    value={requirements.budget}
                    onChange={(e) =>
                      setRequirements({
                        ...requirements,
                        budget: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                    min="0"
                    step="10000"
                  />
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Optimization Objectives</h3>
              <div className="space-y-2">
                {['Performance', 'Collaboration', 'Innovation', 'Leadership', 'Stability', 'Diversity'].map(
                  (objective) => (
                    <label key={objective} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={requirements.objectives.includes(objective)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setRequirements({
                              ...requirements,
                              objectives: [...requirements.objectives, objective],
                            });
                          } else {
                            setRequirements({
                              ...requirements,
                              objectives: requirements.objectives.filter((o) => o !== objective),
                            });
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm">{objective}</span>
                    </label>
                  )
                )}
              </div>
            </div>
          </div>

          <div className="mt-6">
            <div className="flex justify-end gap-4">
              <Button variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Import Requirements
              </Button>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Configuration
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Team Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Current Team Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3">Team Members</h4>
              <MemberList members={currentTeam} title="" />
            </div>
            <div>
              <h4 className="font-semibold mb-3">Current State Metrics</h4>
              <TeamMetricsCard team={currentTeam} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Candidates */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Available Candidates
          </CardTitle>
        </CardHeader>
        <CardContent>
          <MemberList
            members={availableCandidates}
            title=""
            description={`${availableCandidates.length} candidates available for team composition`}
            onMemberClick={onToggleMember}
            selectedMembers={selectedMembers}
            showSelection
          />
        </CardContent>
      </Card>

      {/* Optimization Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Optimization Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Selected: {selectedMembers.length} / {requirements.teamSize} members
            </div>
            <Button
              onClick={onOptimize}
              disabled={isOptimizing || selectedMembers.length !== requirements.teamSize}
              className="flex items-center gap-2"
            >
              <Brain className="h-4 w-4" />
              {isOptimizing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>Optimize Team Composition</>
              )}
            </Button>
          </div>

          {isOptimizing && (
            <div className="mt-4">
              <Progress value={50} className="mb-2" />
              <p className="text-sm text-gray-600 text-center">
                Analyzing team dynamics and compatibility...
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
