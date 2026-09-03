import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Flame, Shield } from 'lucide-react';

interface Hotspot {
  type: string;
  severity: number;
  description: string;
  priority: string;
}

interface HotspotListProps {
  hotspots: Hotspot[];
}

export const HotspotList: React.FC<HotspotListProps> = ({ hotspots }) => {
  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityColor = (severity: number) => {
    if (severity >= 0.7) return 'text-red-600 bg-red-50';
    if (severity >= 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getHotspotIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'toxicity': return <Flame className="h-5 w-5 text-red-600" />;
      case 'behavioral': return <Shield className="h-5 w-5 text-yellow-600" />;
      default: return <AlertTriangle className="h-5 w-5 text-orange-600" />;
    }
  };

  if (hotspots.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Shield className="h-16 w-16 mx-auto mb-4 text-green-400" />
        <p className="text-lg font-medium text-green-600">No Hotspots Detected</p>
        <p className="text-sm">All systems operating within healthy parameters</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {hotspots.map((hotspot, index) => (
        <Card
          key={index}
          className={`border-l-4 transition-all hover:shadow-lg ${
            hotspot.priority === 'high'
              ? 'border-l-red-500 bg-red-50/30'
              : hotspot.priority === 'medium'
              ? 'border-l-yellow-500 bg-yellow-50/30'
              : 'border-l-green-500 bg-green-50/30'
          }`}
        >
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4 flex-1">
                <div className={`p-3 rounded-full ${getSeverityColor(hotspot.severity)}`}>
                  {getHotspotIcon(hotspot.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="font-semibold text-lg capitalize">{hotspot.type.replace(/_/g, ' ')}</h3>
                    <Badge className={getPriorityColor(hotspot.priority)}>
                      {hotspot.priority.toUpperCase()}
                    </Badge>
                    <Badge variant="outline">
                      {(hotspot.severity * 100).toFixed(0)}% severity
                    </Badge>
                  </div>
                  <p className="text-gray-700 mb-3">{hotspot.description}</p>

                  {/* Severity Bar */}
                  <div className="flex items-center space-x-3">
                    <span className="text-xs text-gray-500">Severity:</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-xs">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          hotspot.severity >= 0.7 ? 'bg-red-600' :
                          hotspot.severity >= 0.4 ? 'bg-yellow-600' :
                          'bg-green-600'
                        }`}
                        style={{ width: `${hotspot.severity * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-medium">{(hotspot.severity * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              {/* Priority Icon */}
              <div className="ml-4">
                {hotspot.priority === 'high' && (
                  <div className="animate-pulse">
                    <AlertTriangle className="h-8 w-8 text-red-600" />
                  </div>
                )}
                {hotspot.priority === 'medium' && (
                  <Shield className="h-8 w-8 text-yellow-600" />
                )}
                {hotspot.priority === 'low' && (
                  <Shield className="h-8 w-8 text-green-600" />
                )}
              </div>
            </div>

            {/* Recommended Actions */}
            {hotspot.priority === 'high' && (
              <div className="mt-4 pt-4 border-t border-red-200">
                <p className="text-sm font-medium text-red-800 mb-2">⚠️ Recommended Actions:</p>
                <ul className="text-sm text-red-700 space-y-1">
                  <li>• Review with HR within 24-48 hours</li>
                  <li>• Conduct private check-ins with affected team members</li>
                  <li>• Document all observations and interventions</li>
                </ul>
              </div>
            )}

            {hotspot.priority === 'medium' && (
              <div className="mt-4 pt-4 border-t border-yellow-200">
                <p className="text-sm font-medium text-yellow-800 mb-2">⚡ Recommended Actions:</p>
                <ul className="text-sm text-yellow-700 space-y-1">
                  <li>• Monitor closely over the next week</li>
                  <li>• Consider preventive coaching</li>
                  <li>• Schedule follow-up assessment</li>
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
