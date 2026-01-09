/**
 * Analytics Overview Component
 *
 * Displays high-level analytics metrics cards
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Clock, Calendar, Settings } from 'lucide-react';
import { ReportAnalytics, ReportSchedule } from '../types';

interface AnalyticsOverviewProps {
  analytics: ReportAnalytics;
  schedules: ReportSchedule[];
}

export const AnalyticsOverview: React.FC<AnalyticsOverviewProps> = ({ analytics, schedules }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
          <FileText className="h-4 w-4 text-blue-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{analytics.generation_stats.total_reports}</div>
          <p className="text-xs text-gray-500">
            {analytics.generation_stats.success_rate.toFixed(1)}% success rate
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Generation Time</CardTitle>
          <Clock className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {analytics.performance.avg_generation_time_seconds.toFixed(1)}s
          </div>
          <p className="text-xs text-gray-500">Per report</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Schedules</CardTitle>
          <Calendar className="h-4 w-4 text-purple-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{schedules.filter((s) => s.is_active).length}</div>
          <p className="text-xs text-gray-500">Automated reports</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Available Templates</CardTitle>
          <Settings className="h-4 w-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{analytics.popular_templates.length}</div>
          <p className="text-xs text-gray-500">Report templates</p>
        </CardContent>
      </Card>
    </div>
  );
};
