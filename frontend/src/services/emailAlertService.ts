/**
 * Email Alert Service
 * Manages browser notifications for email monitoring alerts
 */

export interface AlertRule {
  id: string;
  name: string;
  enabled: boolean;
  condition: string;
  threshold: number;
  lastTriggered?: string;
}

export interface AlertNotification {
  id: string;
  title: string;
  body: string;
  timestamp: string;
  type: 'info' | 'warning' | 'critical';
  read: boolean;
}

class EmailAlertService {
  private alerts: AlertNotification[] = [];
  private rules: AlertRule[] = [
    {
      id: 'high-email-volume',
      name: 'High Email Volume',
      enabled: true,
      condition: 'emails_last_hour',
      threshold: 50,
    },
    {
      id: 'security-spike',
      name: 'Security Alert Spike',
      enabled: true,
      condition: 'security_emails',
      threshold: 10,
    },
    {
      id: 'unusual-activity',
      name: 'Unusual Activity',
      enabled: true,
      condition: 'new_senders',
      threshold: 20,
    },
    {
      id: 'financial-activity',
      name: 'High Financial Activity',
      enabled: true,
      condition: 'financial_emails',
      threshold: 15,
    },
  ];

  constructor() {
    this.requestNotificationPermission();
  }

  /**
   * Request browser notification permission
   */
  async requestNotificationPermission(): Promise<boolean> {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }

  /**
   * Show browser notification
   */
  showNotification(
    title: string,
    body: string,
    type: 'info' | 'warning' | 'critical' = 'info'
  ): void {
    // Only show if permission granted and page is visible
    if (Notification.permission === 'granted' && document.hidden) {
      const icon = this.getNotificationIcon(type);

      const notification = new Notification(title, {
        body,
        icon,
        badge: icon,
        tag: `email-alert-${Date.now()}`,
        requireInteraction: type === 'critical',
      });

      notification.onclick = () => {
        window.focus();
        notification.close();
      };

      // Auto-close after 5 seconds for non-critical alerts
      if (type !== 'critical') {
        setTimeout(() => notification.close(), 5000);
      }
    }

    // Store in alerts array
    const alert: AlertNotification = {
      id: `alert-${Date.now()}`,
      title,
      body,
      timestamp: new Date().toISOString(),
      type,
      read: false,
    };

    this.alerts.unshift(alert);

    // Keep only last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(0, 100);
    }

    // Trigger custom event for UI updates
    this.dispatchAlertEvent(alert);
  }

  /**
   * Get notification icon based on type
   */
  private getNotificationIcon(type: string): string {
    const icons = {
      info: '📧',
      warning: '⚠️',
      critical: '🚨',
    };
    return icons[type] || icons.info;
  }

  /**
   * Dispatch custom event for alert
   */
  private dispatchAlertEvent(alert: AlertNotification): void {
    const event = new CustomEvent('emailAlert', {
      detail: alert,
    });
    window.dispatchEvent(event);
  }

  /**
   * Check monitoring stats against alert rules
   */
  checkAlerts(stats: any): void {
    this.rules.forEach((rule) => {
      if (!rule.enabled) return;

      let shouldAlert = false;
      let message = '';

      switch (rule.condition) {
        case 'emails_last_hour':
          shouldAlert = stats.emails_last_hour > rule.threshold;
          message = `${stats.emails_last_hour} emails in the last hour (threshold: ${rule.threshold})`;
          break;

        case 'security_emails':
          shouldAlert = stats.categories?.security > rule.threshold;
          message = `${stats.categories?.security || 0} security-related emails detected`;
          break;

        case 'new_senders':
          // This would require additional data
          shouldAlert = false;
          break;

        case 'financial_emails':
          shouldAlert = stats.categories?.financial > rule.threshold;
          message = `${stats.categories?.financial || 0} financial emails detected`;
          break;
      }

      if (shouldAlert) {
        const type = rule.threshold > 40 ? 'critical' : 'warning';
        this.showNotification(
          `🚨 ${rule.name}`,
          message,
          type
        );

        // Update last triggered time
        rule.lastTriggered = new Date().toISOString();
      }
    });
  }

  /**
   * Get all alerts
   */
  getAlerts(): AlertNotification[] {
    return this.alerts;
  }

  /**
   * Get unread alerts
   */
  getUnreadAlerts(): AlertNotification[] {
    return this.alerts.filter((a) => !a.read);
  }

  /**
   * Mark alert as read
   */
  markAsRead(alertId: string): void {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert) {
      alert.read = true;
    }
  }

  /**
   * Mark all alerts as read
   */
  markAllAsRead(): void {
    this.alerts.forEach((a) => (a.read = true));
  }

  /**
   * Clear all alerts
   */
  clearAlerts(): void {
    this.alerts = [];
  }

  /**
   * Get alert rules
   */
  getRules(): AlertRule[] {
    return this.rules;
  }

  /**
   * Update alert rule
   */
  updateRule(ruleId: string, updates: Partial<AlertRule>): void {
    const rule = this.rules.find((r) => r.id === ruleId);
    if (rule) {
      Object.assign(rule, updates);
    }
  }

  /**
   * Get alert count by type
   */
  getAlertCountByType(): Record<string, number> {
    return this.alerts.reduce((acc, alert) => {
      acc[alert.type] = (acc[alert.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }
}

// Export singleton instance
export const emailAlertService = new EmailAlertService();
