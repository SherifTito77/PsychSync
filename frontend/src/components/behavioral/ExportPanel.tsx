/**
 * Export & Sharing Panel Component
 * Provides export options and sharing capabilities
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Download,
  Share2,
  FileText,
  Mail,
  Link,
  Calendar,
  Clock,
  CheckCircle,
  Copy
} from 'lucide-react';

interface ExportOption {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  format: string;
}

interface ExportPanelProps {
  onExport: (format: string, options: any) => Promise<void>;
  onShare: (method: string, options: any) => Promise<void>;
  isExporting?: boolean;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({
  onExport,
  onShare,
  isExporting = false
}) => {
  const [selectedSections, setSelectedSections] = useState<string[]>([
    'overview',
    'patterns',
    'mental-health',
    'wellness',
    'insights'
  ]);

  const [shareLink, setShareLink] = useState<string>('');
  const [linkCopied, setLinkCopied] = useState(false);
  const [emailSchedule, setEmailSchedule] = useState<string>('');

  const exportOptions: ExportOption[] = [
    {
      id: 'pdf-summary',
      label: 'PDF Summary Report',
      description: 'Executive summary with key metrics and recommendations',
      icon: <FileText className="h-5 w-5" />,
      format: 'pdf'
    },
    {
      id: 'pdf-detailed',
      label: 'Detailed PDF Report',
      description: 'Complete analytics with all charts and data',
      icon: <FileText className="h-5 w-5" />,
      format: 'pdf-detailed'
    },
    {
      id: 'csv-data',
      label: 'CSV Data Export',
      description: 'Raw data for further analysis',
      icon: <Download className="h-5 w-5" />,
      format: 'csv'
    },
    {
      id: 'png-dashboard',
      label: 'Dashboard Snapshot',
      description: 'High-resolution image of current dashboard',
      icon: <Download className="h-5 w-5" />,
      format: 'png'
    }
  ];

  const sections = [
    { id: 'overview', label: 'Overview & Risk Assessment' },
    { id: 'patterns', label: 'Behavioral Patterns' },
    { id: 'mental-health', label: 'Mental Health Insights' },
    { id: 'wellness', label: 'Wellness Metrics' },
    { id: 'insights', label: 'AI-Generated Insights' },
    { id: 'recommendations', label: 'Recommendations' }
  ];

  const handleExport = async (format: string) => {
    await onExport(format, {
      sections: selectedSections,
      includeCharts: true,
      timestamp: new Date().toISOString()
    });
  };

  const generateShareLink = async () => {
    const link = await onShare('link', {
      expiresIn: '7d',
      allowDownload: false
    });
    setShareLink(link);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareLink);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  const scheduleEmailReport = async () => {
    await onShare('email', {
      schedule: emailSchedule,
      sections: selectedSections
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Share2 className="h-5 w-5 text-blue-600" />
          Export & Share
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Export Options */}
        <div>
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Reports
          </h4>
          <div className="space-y-3">
            <div className="text-sm text-gray-600 mb-2">Select sections to include:</div>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {sections.map(section => (
                <label
                  key={section.id}
                  className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={selectedSections.includes(section.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedSections([...selectedSections, section.id]);
                      } else {
                        setSelectedSections(selectedSections.filter(s => s !== section.id));
                      }
                    }}
                    className="rounded"
                  />
                  <span className="text-sm">{section.label}</span>
                </label>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {exportOptions.map(option => (
                <button
                  key={option.id}
                  onClick={() => handleExport(option.format)}
                  disabled={isExporting || selectedSections.length === 0}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="flex items-start gap-3">
                    <div className="text-blue-600">{option.icon}</div>
                    <div className="flex-1">
                      <div className="font-semibold text-sm">{option.label}</div>
                      <div className="text-xs text-gray-500 mt-1">{option.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Sharing Options */}
        <div className="border-t pt-6">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Share2 className="h-4 w-4" />
            Sharing Options
          </h4>
          <div className="space-y-4">
            {/* Generate Shareable Link */}
            <div className="p-4 border rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Link className="h-4 w-4 text-gray-600" />
                  <span className="text-sm font-medium">Shareable Link</span>
                </div>
                <Badge variant="outline">Expires in 7 days</Badge>
              </div>
              {!shareLink ? (
                <Button
                  onClick={generateShareLink}
                  variant="outline"
                  className="w-full"
                >
                  Generate Share Link
                </Button>
              ) : (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={shareLink}
                    readOnly
                    className="flex-1 px-3 py-2 border rounded text-sm bg-gray-50"
                  />
                  <Button
                    onClick={copyToClipboard}
                    variant="outline"
                    size="sm"
                  >
                    {linkCopied ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-2" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>

            {/* Email Schedule */}
            <div className="p-4 border rounded-lg space-y-3">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-medium">Email Reports</span>
              </div>
              <select
                value={emailSchedule}
                onChange={(e) => setEmailSchedule(e.target.value)}
                className="w-full px-3 py-2 border rounded text-sm"
              >
                <option value="">Select frequency...</option>
                <option value="daily">Daily Summary</option>
                <option value="weekly">Weekly Report</option>
                <option value="biweekly">Bi-Weekly Digest</option>
                <option value="monthly">Monthly Review</option>
              </select>
              <Button
                onClick={scheduleEmailReport}
                disabled={!emailSchedule}
                variant="outline"
                className="w-full"
                size="sm"
              >
                Schedule Email Reports
              </Button>
            </div>
          </div>
        </div>

        {/* Info Box */}
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start gap-2 text-sm text-blue-700">
            <Clock className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <p>
              <strong>Note:</strong> Exported reports include data as of {new Date().toLocaleDateString()}.
              Large reports may take a few moments to generate.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
