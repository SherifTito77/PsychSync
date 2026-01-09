/**
 * Team Composition Optimizer - Main Orchestrator
 *
 * Advanced interface for optimizing team composition based on personality traits,
 * skills diversity, and performance predictors. Uses AI-powered recommendations.
 *
 * SPLIT from 1,253 lines → ~200 lines (84% reduction)
 */

import React, { useState, useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Brain, Target } from 'lucide-react';

import { TeamRequirement, TeamCompositionOptimizerProps } from './types';
import { useTeamAnalysis } from './hooks/useTeamAnalysis';
import { useOptimization } from './hooks/useOptimization';
import { useMemberSelection } from './hooks/useMemberSelection';
import {
  preparePersonalityRadarData,
  prepareSkillCoverageData,
  getRecommendedTeam,
} from './utils/teamMetrics';
import { DEFAULT_REQUIREMENTS } from './constants/mockData';

// Components
import { SetupTab } from './components/SetupTab';
import { ResultsTab } from './components/ResultsTab';
import { ComparisonTab } from './components/ComparisonTab';

const TeamCompositionOptimizer: React.FC<TeamCompositionOptimizerProps> = ({
  currentTeamId,
  projectId,
  onOptimizationComplete,
}) => {
  const [selectedTab, setSelectedTab] = useState('setup');
  const [requirements, setRequirements] = useState<TeamRequirement>(DEFAULT_REQUIREMENTS);

  // Custom hooks
  const { currentTeam, availableCandidates } = useTeamAnalysis();
  const { isOptimizing, optimizationResult, handleOptimize } = useOptimization(onOptimizationComplete);
  const { selectedMembers, toggleMemberSelection } = useMemberSelection();

  // Prepare chart data
  const personalityRadarData = useMemo(
    () => preparePersonalityRadarData(currentTeam, requirements, optimizationResult),
    [currentTeam, requirements, optimizationResult]
  );

  const skillCoverageData = useMemo(
    () => prepareSkillCoverageData(requirements, optimizationResult),
    [requirements, optimizationResult]
  );

  const recommendedTeam = useMemo(
    () =>
      optimizationResult
        ? getRecommendedTeam(
            currentTeam,
            availableCandidates,
            optimizationResult.recommendedMembers,
            requirements.teamSize
          )
        : [],
    [optimizationResult, currentTeam, availableCandidates, requirements.teamSize]
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Team Composition Optimizer</h1>
          <p className="text-muted-foreground">
            AI-powered team optimization for maximum performance and collaboration
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Brain className="h-3 w-3" />
            AI-Powered
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Target className="h-3 w-3" />
            {optimizationResult ? 'Optimized' : 'Ready'}
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-4">
          <SetupTab
            requirements={requirements}
            setRequirements={setRequirements}
            currentTeam={currentTeam}
            availableCandidates={availableCandidates}
            selectedMembers={selectedMembers}
            isOptimizing={isOptimizing}
            onToggleMember={toggleMemberSelection}
            onOptimize={handleOptimize}
          />
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          <ResultsTab
            optimizationResult={optimizationResult}
            personalityRadarData={personalityRadarData}
            skillCoverageData={skillCoverageData}
            recommendedTeam={recommendedTeam}
          />
        </TabsContent>

        <TabsContent value="comparison" className="space-y-4">
          <ComparisonTab requirements={requirements} skillCoverageData={skillCoverageData} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TeamCompositionOptimizer;
