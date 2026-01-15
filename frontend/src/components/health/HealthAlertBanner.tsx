/**
 * Health Alert Banner Component
 *
 * Displays automated health intervention alerts with different severity levels.
 * Supports dismissal, acknowledgement, and quick actions.
 *
 * Features:
 * - Animated alert banner
 * - Severity-based styling (critical, high, medium, low)
 * - Action buttons for quick responses
 * - Dismissible alerts
 * - Resource links
 */

import React, { useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  X,
  AlertTriangle,
  Activity,
  Phone,
  Clock,
  CheckCircle,
  ExternalLink,
  ChevronRight,
} from 'lucide-react';
import type { Intervention } from '@/types/healthMonitoring';

interface HealthAlertBannerProps {
  intervention: Intervention;
  onDismiss?: () => void;
  onAcknowledge?: () => void;
}

export const HealthAlertBanner: React.FC<HealthAlertBannerProps> = ({
  intervention,
  onDismiss,
  onAcknowledge,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getUrgencyStyles = (urgency: string) => {
    switch (urgency) {
      case 'critical':
        return {
          container: 'border-red-500 bg-red-50 dark:bg-red-950',
          icon: 'text-red-600',
          title: 'text-red-900 dark:text-red-100',
          description: 'text-red-800 dark:text-red-200',
        };
      case 'high':
        return {
          container: 'border-orange-500 bg-orange-50 dark:bg-orange-950',
          icon: 'text-orange-600',
          title: 'text-orange-900 dark:text-orange-100',
          description: 'text-orange-800 dark:text-orange-200',
        };
      case 'medium':
        return {
          container: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950',
          icon: 'text-yellow-600',
          title: 'text-yellow-900 dark:text-yellow-100',
          description: 'text-yellow-800 dark:text-yellow-200',
        };
      default:
        return {
          container: 'border-blue-500 bg-blue-50 dark:bg-blue-950',
          icon: 'text-blue-600',
          title: 'text-blue-900 dark:text-blue-100',
          description: 'text-blue-800 dark:text-blue-200',
        };
    }
  };

  const getUrgencyIcon = (urgency: string) => {
    switch (urgency) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4" />;
      case 'high':
        return <Activity className="h-4 w-4" />;
      case 'medium':
        return <Clock className="h-4 w-4" />;
      default:
        return <CheckCircle className="h-4 w-4" />;
    }
  };

  const styles = getUrgencyStyles(intervention.urgency);

  return (
    <Alert className={`${styles.container} relative transition-all duration-300`}>
      {/* Close Button */}
      {onDismiss && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-2 top-2 h-6 w-6 p-0 opacity-50 hover:opacity-100"
          onClick={onDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      )}

      {/* Alert Content */}
      <div className="flex items-start gap-3 pr-8">
        <div className={`${styles.icon} mt-0.5 flex-shrink-0`}>
          {getUrgencyIcon(intervention.urgency)}
        </div>

        <div className="flex-1 space-y-2">
          {/* Title and Badge */}
          <div className="flex items-center gap-2 flex-wrap">
            <AlertTitle className={styles.title}>
              {intervention.title}
            </AlertTitle>
            <Badge
              variant="outline"
              className={`${styles.icon} border-current`}
            >
              {intervention.urgency.toUpperCase()}
            </Badge>
            {intervention.intervention_type && (
              <Badge variant="secondary" className="text-xs">
                {intervention.intervention_type.replace(/_/g, ' ')}
              </Badge>
            )}
          </div>

          {/* Message */}
          <AlertDescription className={styles.description}>
            {intervention.message}
          </AlertDescription>

          {/* Actions Required */}
          {intervention.actions_required.length > 0 && (
            <div className="space-y-1">
              <Button
                variant="link"
                className="h-auto p-0 text-sm underline"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? 'Hide' : 'Show'} actions required
                <ChevronRight className={`ml-1 h-3 w-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </Button>

              {isExpanded && (
                <ol className="list-decimal list-inside space-y-1 text-sm ml-2">
                  {intervention.actions_required.map((action, i) => (
                    <li key={i} className={styles.description}>{action}</li>
                  ))}
                </ol>
              )}
            </div>
          )}

          {/* Resources */}
          {intervention.resources.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {intervention.resources.map((resource, i) => (
                <Button
                  key={i}
                  variant="outline"
                  size="sm"
                  asChild
                  className={`text-xs ${resource.type === 'crisis' ? 'border-red-500 text-red-700 hover:bg-red-100' : ''}`}
                >
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1"
                  >
                    {resource.type === 'crisis' && <Phone className="h-3 w-3" />}
                    {resource.title}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </Button>
              ))}
            </div>
          )}

          {/* Follow-up Info */}
          {intervention.follow_up_required && (
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Follow-up in {intervention.follow_up_days} day(s)
            </div>
          )}

          {/* Acknowledge Button */}
          {onAcknowledge && (
            <div className="pt-2">
              <Button
                size="sm"
                variant="outline"
                onClick={onAcknowledge}
                className="text-xs"
              >
                <CheckCircle className="mr-1 h-3 w-3" />
                Acknowledge & Dismiss
              </Button>
            </div>
          )}
        </div>
      </div>
    </Alert>
  );
};

/**
 * Health Alert Container
 *
 * Displays multiple health alerts in a stackable format
 */
interface HealthAlertContainerProps {
  interventions: Intervention[];
  onDismiss?: (interventionId: string) => void;
  onAcknowledge?: (interventionId: string) => void;
}

export const HealthAlertContainer: React.FC<HealthAlertContainerProps> = ({
  interventions,
  onDismiss,
  onAcknowledge,
}) => {
  if (interventions.length === 0) {
    return null;
  }

  // Sort by urgency
  const urgencyOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  const sortedInterventions = [...interventions].sort(
    (a, b) => urgencyOrder[a.urgency] - urgencyOrder[b.urgency]
  );

  return (
    <div className="space-y-3">
      {sortedInterventions.map((intervention) => (
        <HealthAlertBanner
          key={intervention.intervention_id}
          intervention={intervention}
          onDismiss={
            onDismiss
              ? () => onDismiss(intervention.intervention_id)
              : undefined
          }
          onAcknowledge={
            onAcknowledge
              ? () => onAcknowledge(intervention.intervention_id)
              : undefined
          }
        />
      ))}
    </div>
  );
};

export default HealthAlertBanner;
