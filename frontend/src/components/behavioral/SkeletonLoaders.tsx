/**
 * Skeleton Loading Components
 * Provides loading states for better perceived performance
 */

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

export const QuickStatsSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-8 bg-gray-200 rounded w-3/4" />
              <div className="h-3 bg-gray-200 rounded w-1/3" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export const ComparisonSkeleton: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <div className="animate-pulse h-6 bg-gray-200 rounded w-1/3" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
              <div className="h-6 bg-gray-200 rounded w-full" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export const AlertSkeleton: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <div className="animate-pulse h-6 bg-gray-200 rounded w-1/3" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-start gap-3 p-4 bg-gray-50 rounded">
              <div className="h-5 w-5 bg-gray-200 rounded" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/3" />
                <div className="h-3 bg-gray-200 rounded w-full" />
                <div className="h-3 bg-gray-200 rounded w-2/3" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export const GoalSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {[...Array(4)].map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="animate-pulse space-y-3">
              <div className="h-5 bg-gray-200 rounded w-3/4" />
              <div className="h-3 bg-gray-200 rounded w-full" />
              <div className="h-3 bg-gray-200 rounded w-2/3" />
              <div className="h-2 bg-gray-200 rounded w-full" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export const PatternAnalysisSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {[...Array(2)].map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <div className="animate-pulse h-6 bg-gray-200 rounded w-1/2" />
          </CardHeader>
          <CardContent>
            <div className="animate-pulse space-y-4">
              <div className="h-64 bg-gray-200 rounded" />
              <div className="space-y-2">
                {[...Array(4)].map((_, j) => (
                  <div key={j} className="h-4 bg-gray-200 rounded" />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export const FullPageSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-2" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
      </div>
      <QuickStatsSkeleton />
      <ComparisonSkeleton />
      <PatternAnalysisSkeleton />
    </div>
  );
};
