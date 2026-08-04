import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { emailAlertService, AlertRule } from '@/services/emailAlertService';

interface AlertConfigurationProps {
  onClose?: () => void;
}

const AlertConfiguration: React.FC<AlertConfigurationProps> = ({ onClose }) => {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load current rules
    setRules(emailAlertService.getRules());
  }, []);

  const handleToggleRule = (ruleId: string) => {
    setRules((prev) =>
      prev.map((rule) =>
        rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
      )
    );
  };

  const handleThresholdChange = (ruleId: string, newThreshold: number) => {
    setRules((prev) =>
      prev.map((rule) =>
        rule.id === ruleId ? { ...rule, threshold: newThreshold } : rule
      )
    );
  };

  const handleSave = () => {
    // Save all rules
    rules.forEach((rule) => {
      emailAlertService.updateRule(rule.id, {
        enabled: rule.enabled,
        threshold: rule.threshold,
      });
    });

    setSaved(true);
    setTimeout(() => setSaved(false), 2000);

    // Save to localStorage for persistence
    localStorage.setItem('alertRules', JSON.stringify(rules));
  };

  const handleReset = () => {
    // Reset to defaults
    const defaultRules: AlertRule[] = [
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

    setRules(defaultRules);
    localStorage.removeItem('alertRules');
  };

  const getRuleDescription = (rule: AlertRule): string => {
    switch (rule.condition) {
      case 'emails_last_hour':
        return `Alert when emails received in one hour exceeds ${rule.threshold}`;
      case 'security_emails':
        return `Alert when security-related emails exceed ${rule.threshold}`;
      case 'new_senders':
        return `Alert when unique senders exceed ${rule.threshold}`;
      case 'financial_emails':
        return `Alert when financial emails exceed ${rule.threshold}`;
      default:
        return `Custom threshold: ${rule.threshold}`;
    }
  };

  const getRuleIcon = (rule: AlertRule): string => {
    switch (rule.condition) {
      case 'emails_last_hour':
        return '📧';
      case 'security_emails':
        return '🔒';
      case 'new_senders':
        return '👥';
      case 'financial_emails':
        return '💰';
      default:
        return '⚙️';
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">⚙️ Alert Configuration</h2>
          <p className="text-gray-600">Customize when and how you receive email alerts</p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      {/* Quick Tips */}
      <Card className="mb-6 bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h3 className="font-medium text-blue-900 mb-2">💡 Quick Tips</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Set thresholds based on your typical email volume</li>
            <li>• Lower thresholds = more frequent alerts</li>
            <li>• Disable rules you don't need to reduce noise</li>
            <li>• Changes are saved to your browser's local storage</li>
          </ul>
        </CardContent>
      </Card>

      {/* Alert Rules */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Alert Rules</h3>

        {rules.map((rule) => (
          <Card key={rule.id} className={rule.enabled ? '' : 'opacity-60'}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-2xl">{getRuleIcon(rule)}</span>
                    <h4 className="text-lg font-medium text-gray-900">{rule.name}</h4>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          rule.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {rule.enabled ? 'ENABLED' : 'DISABLED'}
                      </span>
                      {rule.lastTriggered && (
                        <span className="text-xs text-gray-500">
                          Last: {new Date(rule.lastTriggered).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">{getRuleDescription(rule)}</p>

                  {/* Threshold Slider */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-700">Threshold: {rule.threshold}</span>
                      <span className="text-gray-500">Max: 100</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="100"
                      value={rule.threshold}
                      onChange={(e) => handleThresholdChange(rule.id, parseInt(e.target.value))}
                      disabled={!rule.enabled}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                    <div className="flex justify-between text-xs text-gray-400">
                      <span>1</span>
                      <span>25</span>
                      <span>50</span>
                      <span>75</span>
                      <span>100</span>
                    </div>
                  </div>
                </div>

                {/* Toggle Switch */}
                <div className="ml-6">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={rule.enabled}
                      onChange={() => handleToggleRule(rule.id)}
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex justify-between">
        <Button variant="outline" onClick={handleReset}>
          🔄 Reset to Defaults
        </Button>
        <div className="flex space-x-3">
          {saved && (
            <span className="text-green-600 flex items-center">
              ✅ Saved successfully!
            </span>
          )}
          <Button onClick={handleSave}>💾 Save Changes</Button>
        </div>
      </div>

      {/* Additional Settings */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>🔔 Notification Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">Browser Notifications</h4>
                <p className="text-sm text-gray-500">
                  Receive alerts even when browser is minimized
                </p>
              </div>
              <Button
                variant="outline"
                onClick={async () => {
                  const granted = await emailAlertService.requestNotificationPermission();
                  alert(granted ? '✅ Notifications enabled!' : '❌ Notifications blocked');
                }}
              >
                Enable Notifications
              </Button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">Test Alerts</h4>
                <p className="text-sm text-gray-500">
                  Send a test notification to verify setup
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  emailAlertService.showNotification(
                    '🧪 Test Alert',
                    'This is a test notification from Email Monitor',
                    'info'
                  );
                }}
              >
                Send Test Alert
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AlertConfiguration;
