/**
 * Schedule Card Component
 *
 * Displays a single report schedule with execution stats
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Edit, Play } from 'lucide-react';
import { ReportSchedule } from '../types';
import { getDeliveryIcon } from '../utils/displayHelpers.tsx';

interface ScheduleCardProps {
  schedule: ReportSchedule;
  onEdit?: (scheduleId: string) => void;
  onRun?: (scheduleId: string) => void;
}

export const ScheduleCard: React.FC<ScheduleCardProps> = ({ schedule, onEdit, onRun }) => {
  const successRate =
    schedule.success_count + schedule.failure_count > 0
      ? (schedule.success_count / (schedule.success_count + schedule.failure_count)) * 100
      : 0;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-semibold">{schedule.name}</h3>
              <Badge variant={schedule.is_active ? 'default' : 'secondary'}>
                {schedule.is_active ? 'Active' : 'Inactive'}
              </Badge>
              <Badge variant="outline">{schedule.frequency}</Badge>
            </div>
            <p className="text-gray-600 mb-3">{schedule.description}</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
              <div className="flex items-center space-x-2">
                {getDeliveryIcon(schedule.delivery_method)}
                <span>{schedule.delivery_method}</span>
              </div>
              <div>
                <span className="font-medium">Success Rate:</span> {successRate.toFixed(1)}%
              </div>
              {schedule.next_run && (
                <div>
                  <span className="font-medium">Next Run:</span>{' '}
                  {new Date(schedule.next_run).toLocaleDateString()}
                </div>
              )}
              {schedule.last_run && (
                <div>
                  <span className="font-medium">Last Run:</span>{' '}
                  {new Date(schedule.last_run).toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
          <div className="flex space-x-2">
            {onEdit && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(schedule.id)}
              >
                <Edit className="h-4 w-4" />
              </Button>
            )}
            {onRun && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRun(schedule.id)}
              >
                <Play className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
