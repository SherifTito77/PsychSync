/**
 * Template Card Component
 *
 * Displays a single report template with usage stats
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Edit } from 'lucide-react';
import { ReportTemplate } from '../types';

interface TemplateCardProps {
  template: ReportTemplate;
  onUse?: (templateId: string) => void;
  onEdit?: (templateId: string) => void;
}

export const TemplateCard: React.FC<TemplateCardProps> = ({ template, onUse, onEdit }) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg">{template.name}</CardTitle>
          <div className="flex space-x-2">
            {template.is_public && <Badge variant="secondary">Public</Badge>}
            <Badge variant="outline">{template.report_type}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-gray-600 mb-4">{template.description}</p>
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Used {template.usage_count} times</span>
          <span>{new Date(template.created_at).toLocaleDateString()}</span>
        </div>
        <div className="mt-4 flex space-x-2">
          {onUse && (
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onUse(template.id)}
            >
              Use Template
            </Button>
          )}
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(template.id)}
            >
              <Edit className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
