/**
 * Resources Grid Component
 *
 * Displays helpful resources (hotlines, websites, support groups).
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Resource } from '../types';

interface ResourcesGridProps {
  resources: Resource[];
}

export const ResourcesGrid: React.FC<ResourcesGridProps> = ({ resources }) => {
  if (resources.length === 0) return null;

  const handleCall = (phone: string) => {
    window.open(`tel:${phone.replace(/[^\d]/g, '')}`);
  };

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle>Helpful Resources</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {resources.map((resource, index) => (
            <div key={index} className="border rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-2">{resource.title}</h3>
              <p className="text-sm text-gray-600 mb-3">{resource.description}</p>
              <div className="flex space-x-2">
                {resource.phone && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCall(resource.phone!)}
                  >
                    Call
                  </Button>
                )}
                {resource.link && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(resource.link, '_blank')}
                  >
                    Learn More
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
