/**
 * Report List Card Component
 *
 * Displays a single report in a card format with actions
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Download, Eye } from 'lucide-react';
import { Report } from '../types';
import { getStatusColor, getFormatIcon } from '../utils/displayHelpers.tsx';

interface ReportListCardProps {
  report: Report;
  onDownload: (reportId: string) => void;
  onView?: (reportId: string) => void;
}

export const ReportListCard: React.FC<ReportListCardProps> = ({ report, onDownload, onView }) => {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-semibold">{report.title}</h3>
              <Badge className={getStatusColor(report.status)}>{report.status}</Badge>
              <div className="flex items-center space-x-1">
                {getFormatIcon(report.file_format)}
                <span className="text-sm text-gray-500">{report.file_format.toUpperCase()}</span>
              </div>
            </div>
            <p className="text-gray-600 mb-3">{report.description}</p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Created: {new Date(report.created_at).toLocaleDateString()}</span>
              <span>Downloads: {report.download_count}</span>
              {report.record_count && <span>Records: {report.record_count}</span>}
              {report.file_size && <span>Size: {(report.file_size / 1024).toFixed(1)} KB</span>}
            </div>
          </div>
          <div className="flex space-x-2">
            {report.status === 'completed' && (
              <Button variant="outline" size="sm" onClick={() => onDownload(report.id)}>
                <Download className="h-4 w-4" />
              </Button>
            )}
            {onView && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onView(report.id)}
              >
                <Eye className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
