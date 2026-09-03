/**
 * Smart Alerts Component
 * Displays proactive alerts, notifications, and achievements
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Calendar,
  X,
  Bell,
  Gift,
  Zap,
  Heart
} from 'lucide-react';

interface Alert {
  id: string;
  type: 'warning' | 'success' | 'info' | 'achievement';
  title: string;
  message: string;
  severity?: 'low' | 'medium' | 'high';
  actionLabel?: string;
  actionLink?: string;
  timestamp: string;
  dismissible?: boolean;
}

interface SmartAlertsProps {
  alerts: Alert[];
  onDismiss?: (alertId: string) => void;
  onAction?: (alertId: string) => void;
}

export const SmartAlerts: React.FC<SmartAlertsProps> = ({ alerts, onDismiss, onAction }) => {
  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'warning': return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      case 'success': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'achievement': return <Gift className="h-5 w-5 text-purple-500" />;
      default: return <Bell className="h-5 w-5 text-blue-500" />;
    }
  };

  const getAlertStyles = (type: Alert['type'], severity?: string) => {
    const baseStyles = "border-l-4";

    switch (type) {
      case 'warning':
        return `${baseStyles} border-orange-500 bg-orange-50`;
      case 'success':
        return `${baseStyles} border-green-500 bg-green-50`;
      case 'achievement':
        return `${baseStyles} border-purple-500 bg-purple-50`;
      default:
        return `${baseStyles} border-blue-500 bg-blue-50`;
    }
  };

  const getSeverityBadge = (severity?: string) => {
    if (!severity) return null;

    const variants = {
      low: { label: 'Low', variant: 'secondary' as const },
      medium: { label: 'Medium', variant: 'outline' as const },
      high: { label: 'High', variant: 'destructive' as const },
    };

    const config = variants[severity as keyof typeof variants] || variants.low;
    return <Badge variant={config.variant} className="ml-2">{config.label}</Badge>;
  };

  // Sort alerts by severity and type
  const sortedAlerts = [...alerts].sort((a, b) => {
    const severityOrder = { high: 0, medium: 1, low: 2, undefined: 3 };
    const typeOrder = { warning: 0, achievement: 1, info: 2, success: 3 };

    if (a.type !== b.type) return typeOrder[a.type as keyof typeof typeOrder] - typeOrder[b.type as keyof typeof typeOrder];
    return severityOrder[a.severity as keyof typeof severityOrder] - severityOrder[b.severity as keyof typeof severityOrder];
  });

  if (sortedAlerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-blue-600" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No new notifications</p>
            <p className="text-sm mt-2">You're all caught up!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-blue-600" />
            Smart Alerts & Notifications
          </div>
          <Badge variant="secondary">{sortedAlerts.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-lg ${getAlertStyles(alert.type, alert.severity)} relative`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <div className="mt-0.5">{getAlertIcon(alert.type)}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-gray-900">{alert.title}</h4>
                      {getSeverityBadge(alert.severity)}
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {alert.timestamp}
                      </span>
                    </div>
                    {alert.actionLabel && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-3"
                        onClick={() => onAction?.(alert.id)}
                      >
                        {alert.actionLabel}
                      </Button>
                    )}
                  </div>
                </div>
                {alert.dismissible && (
                  <button
                    onClick={() => onDismiss?.(alert.id)}
                    className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Achievement Showcase */}
        {sortedAlerts.some(a => a.type === 'achievement') && (
          <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
            <div className="flex items-start gap-3">
              <Gift className="h-6 w-6 text-purple-600" />
              <div className="flex-1">
                <h5 className="font-semibold text-purple-900 mb-2">Recent Achievements</h5>
                <div className="space-y-2">
                  {sortedAlerts
                    .filter(a => a.type === 'achievement')
                    .slice(0, 3)
                    .map(achievement => (
                      <div key={achievement.id} className="flex items-center gap-2 text-sm">
                        <Zap className="h-4 w-4 text-purple-500" />
                        <span className="text-purple-800">{achievement.title}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
