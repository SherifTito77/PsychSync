import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getMonitoringStats, MonitoringStats } from '@/services/emailMonitoringService';
import { emailExportService, ExportOptions } from '@/services/emailExportService';

const EmailDataExport: React.FC = () => {
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'json' | 'pdf'>('csv');
  const [exportSuccess, setExportSuccess] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const result = await getMonitoringStats();
      if (result.success && result.data) {
        setStats(result.data);
      }
      setLoading(false);
    };

    fetchData();
  }, []);

  const handleExport = async () => {
    if (!stats) return;

    setExporting(true);
    setExportSuccess(false);

    try {
      await emailExportService.exportData({
        format: selectedFormat,
        includeCharts: true
      });

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      alert(`Export failed: ${error}`);
    } finally {
      setExporting(false);
    }
  };

  const getFormatDescription = (format: 'csv' | 'json' | 'pdf'): string => {
    switch (format) {
      case 'csv':
        return 'Spreadsheet-compatible format for data analysis';
      case 'json':
        return 'Machine-readable format with full metadata';
      case 'pdf':
        return 'Professional report with insights and recommendations';
      default:
        return '';
    }
  };

  const getFormatIcon = (format: 'csv' | 'json' | 'pdf'): string => {
    switch (format) {
      case 'csv':
        return '📊';
      case 'json':
        return '📋';
      case 'pdf':
        return '📄';
      default:
        return '💾';
    }
  };

  if (loading || !stats) {
    return <div className="p-6">Loading export options...</div>;
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">💾 Export Email Analytics</h2>
        <p className="text-gray-600">Download your email monitoring data in various formats</p>
      </div>

      {/* Export Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {(['csv', 'json', 'pdf'] as const).map((format) => (
          <Card
            key={format}
            className={`cursor-pointer transition-all ${
              selectedFormat === format
                ? 'ring-2 ring-blue-500 bg-blue-50'
                : 'hover:shadow-md'
            }`}
            onClick={() => setSelectedFormat(format)}
          >
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-4xl mb-2">{getFormatIcon(format)}</div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  {format.toUpperCase()}
                </h3>
                <p className="text-sm text-gray-500">
                  {getFormatDescription(format)}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Data Preview */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>📋 Export Preview ({selectedFormat.toUpperCase()})</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
            {emailExportService.getExportPreview(stats, selectedFormat)}
          </pre>
        </CardContent>
      </Card>

      {/* Export Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>📦 What's Included</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Statistics</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Total email count</li>
                <li>• Hourly/daily/weekly metrics</li>
                <li>• Daily averages</li>
                <li>• Growth trends</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Analysis</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Category breakdown</li>
                <li>• Behavioral insights</li>
                <li>• Alert history</li>
                <li>• Recommendations</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Export Button */}
      <div className="flex justify-center">
        <Button
          size="lg"
          onClick={handleExport}
          disabled={exporting}
          className="min-w-64"
        >
          {exporting ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12c0-4.411-3.589-8-8-8v4c2.205 0 4 1.795 4 4v4a5 5 0 005.291 4.921z"></path>
              </svg>
              Exporting...
            </span>
          ) : exportSuccess ? (
            <span className="flex items-center">
              ✅ Export Complete!
            </span>
          ) : (
            <span className="flex items-center">
              {getFormatIcon(selectedFormat)}
              Export as {selectedFormat.toUpperCase()}
            </span>
          )}
        </Button>
      </div>

      {/* Additional Options */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>⚙️ Export Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">Include Charts</h4>
                <p className="text-sm text-gray-500">
                  Embed visualizations in the export (when supported)
                </p>
              </div>
              <input
                type="checkbox"
                defaultChecked={true}
                className="w-5 h-5 text-blue-600 rounded"
                disabled
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">Date Range</h4>
                <p className="text-sm text-gray-500">
                  Last 7 days of data (fixed for now)
                </p>
              </div>
              <span className="text-sm text-gray-500">Last 7 days</span>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-gray-900">File Size</h4>
                <p className="text-sm text-gray-500">
                  Estimated export file size
                </p>
              </div>
              <span className="text-sm text-gray-500">
                {selectedFormat === 'pdf' ? '~50 KB' : selectedFormat === 'json' ? '~15 KB' : '~5 KB'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tips */}
      <Card className="mt-6 bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h3 className="font-medium text-blue-900 mb-2">💡 Export Tips</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• <strong>CSV:</strong> Best for importing into Excel, Google Sheets, or data analysis tools</li>
            <li>• <strong>JSON:</strong> Ideal for developers, API integrations, or custom processing</li>
            <li>• <strong>PDF:</strong> Perfect for sharing reports, presentations, or archiving</li>
            <li>• All formats include behavioral insights and recommendations</li>
          </ul>
        </CardContent>
      </Card>

      {/* Schedule Export (Future Feature) */}
      <Card className="mt-6 opacity-60">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>📅 Scheduled Exports</span>
            <span className="text-sm bg-gray-200 px-2 py-1 rounded">Coming Soon</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">
            Schedule automatic weekly or monthly exports to your email. Stay tuned for this feature!
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default EmailDataExport;
