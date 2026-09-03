/**
 * Email Analytics Export Service
 * Exports monitoring data to CSV, JSON, and generates PDF reports
 */

import { getMonitoringStats, MonitoringStats } from './emailMonitoringService';

export interface ExportOptions {
  format: 'csv' | 'json' | 'pdf';
  includeCharts?: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
  categories?: string[];
}

class EmailExportService {
  /**
   * Export monitoring data to CSV format
   */
  async exportToCSV(stats: MonitoringStats): Promise<void> {
    const rows = [
      ['Metric', 'Value', 'Percentage', 'Timestamp'],
      ['Total Emails', stats.total_emails.toString(), '100%', stats.last_check],
      ['Emails Last Hour', stats.emails_last_hour.toString(), `${((stats.emails_last_hour / stats.total_emails) * 100).toFixed(2)}%`, stats.last_check],
      ['Emails Last Day', stats.emails_last_day.toString(), `${((stats.emails_last_day / stats.total_emails) * 100).toFixed(2)}%`, stats.last_check],
      ['Emails Last Week', stats.emails_last_week.toString(), `${((stats.emails_last_week / stats.total_emails) * 100).toFixed(2)}%`, stats.last_check],
      [],
      ['Category', 'Count', 'Percentage'],
      ...Object.entries(stats.categories).map(([cat, count]) => [
        cat,
        count.toString(),
        `${((count / stats.emails_last_week) * 100).toFixed(2)}%`
      ]),
      [],
      ['Alerts'],
      ...stats.alerts.map(alert => [alert])
    ];

    // Convert to CSV string
    const csvContent = rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    // Create download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `email_analytics_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Export monitoring data to JSON format
   */
  async exportToJSON(stats: MonitoringStats): Promise<void> {
    const exportData = {
      metadata: {
        exportDate: new Date().toISOString(),
        emailAccount: 'sherif.tito.77@gmail.com',
        exportFormat: 'JSON',
        version: '1.0'
      },
      statistics: {
        totalEmails: stats.total_emails,
        emailsLastHour: stats.emails_last_hour,
        emailsLastDay: stats.emails_last_day,
        emailsLastWeek: stats.emails_last_week,
        dailyAverage: Math.round(stats.emails_last_week / 7)
      },
      categories: stats.categories,
      alerts: stats.alerts,
      behavioralInsights: this.generateInsights(stats),
      recommendations: this.generateRecommendations(stats)
    };

    const jsonContent = JSON.stringify(exportData, null, 2);

    // Create download
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `email_analytics_${new Date().toISOString().split('T')[0]}.json`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Generate a text-based PDF report (simplified)
   * For full PDF generation, you'd use a library like jsPDF
   */
  async exportToPDF(stats: MonitoringStats): Promise<void> {
    // Generate HTML content for the report
    const reportContent = this.generateHTMLReport(stats);

    // Create a new window with the report
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(reportContent);
      printWindow.document.close();

      // Wait for content to load, then print
      printWindow.onload = () => {
        setTimeout(() => {
          printWindow.print();
        }, 250);
      };
    } else {
      alert('Please allow popups to generate PDF report');
    }
  }

  /**
   * Generate HTML report content
   */
  private generateHTMLReport(stats: MonitoringStats): string {
    const insights = this.generateInsights(stats);
    const recommendations = this.generateRecommendations(stats);

    return `
<!DOCTYPE html>
<html>
<head>
  <title>Email Analytics Report</title>
  <style>
    body {
      font-family: 'Arial', sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    h1 {
      color: #1e40af;
      border-bottom: 3px solid #1e40af;
      padding-bottom: 10px;
    }
    h2 {
      color: #4b5563;
      margin-top: 30px;
    }
    .metric {
      background: #f3f4f6;
      padding: 15px;
      margin: 10px 0;
      border-radius: 8px;
      display: flex;
      justify-content: space-between;
    }
    .metric-label {
      font-weight: bold;
    }
    .category {
      margin: 10px 0;
      padding: 10px;
      background: #fafafa;
      border-left: 4px solid #3b82f6;
    }
    .insight {
      background: #dbeafe;
      padding: 15px;
      margin: 10px 0;
      border-radius: 8px;
    }
    .recommendation {
      background: #dcfce7;
      padding: 15px;
      margin: 10px 0;
      border-radius: 8px;
    }
    .alert {
      background: #fee2e2;
      padding: 15px;
      margin: 10px 0;
      border-radius: 8px;
    }
    .footer {
      margin-top: 50px;
      text-align: center;
      color: #6b7280;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <h1>📧 Email Analytics Report</h1>
  <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>

  <h2>📊 Overview</h2>
  <div class="metric">
    <span class="metric-label">Total Emails:</span>
    <span>${stats.total_emails.toLocaleString()}</span>
  </div>
  <div class="metric">
    <span class="metric-label">Last 24 Hours:</span>
    <span>${stats.emails_last_day}</span>
  </div>
  <div class="metric">
    <span class="metric-label">Last 7 Days:</span>
    <span>${stats.emails_last_week}</span>
  </div>
  <div class="metric">
    <span class="metric-label">Daily Average:</span>
    <span>${Math.round(stats.emails_last_week / 7)} emails/day</span>
  </div>

  <h2>📂 Email Categories</h2>
  ${Object.entries(stats.categories).map(([cat, count]) => `
    <div class="category">
      <strong>${cat.charAt(0).toUpperCase() + cat.slice(1)}:</strong> ${count} emails
    </div>
  `).join('')}

  <h2>💡 Insights</h2>
  ${insights.map(insight => `<div class="insight">${insight}</div>`).join('')}

  <h2>✅ Recommendations</h2>
  ${recommendations.map(rec => `<div class="recommendation">${rec}</div>`).join('')}

  ${stats.alerts.length > 0 && stats.alerts[0] !== 'System normal - no alerts' ? `
    <h2>⚠️ Alerts</h2>
    ${stats.alerts.map(alert => `<div class="alert">${alert}</div>`).join('')}
  ` : ''}

  <div class="footer">
    <p>Generated by PsychSync Email Monitor</p>
    <p>Report ID: ${Date.now()}</p>
  </div>
</body>
</html>
    `;
  }

  /**
   * Generate behavioral insights
   */
  private generateInsights(stats: MonitoringStats): string[] {
    const insights = [];
    const total = Object.values(stats.categories).reduce((a, b) => a + b, 0);

    // Security consciousness
    if (stats.categories.security / total > 0.3) {
      insights.push('🔒 High security awareness: You actively monitor account security with frequent login alerts.');
    }

    // Financial activity
    if (stats.categories.financial > 20) {
      insights.push('💰 Active financial management: High volume of banking and transaction emails.');
    }

    // Professional networking
    if (stats.categories.professional > 15) {
      insights.push('💼 Strong professional presence: Active networking and career-related communication.');
    }

    // Social media
    if (stats.categories.social < 10) {
      insights.push('🎯 Focused communication: Limited social media distractions, maintaining productivity.');
    }

    // Email volume
    if (stats.emails_last_day > 100) {
      insights.push('📈 High email volume: Consider filtering or unsubscribing from promotional content.');
    }

    return insights;
  }

  /**
   * Generate actionable recommendations
   */
  private generateRecommendations(stats: MonitoringStats): string[] {
    const recommendations = [];

    // Security recommendations
    if (stats.categories.security > 20) {
      recommendations.push('Consider consolidating security alerts to reduce notification fatigue while maintaining security awareness.');
    }

    // Financial recommendations
    if (stats.categories.financial > 30) {
      recommendations.push('Your financial activity is high. Ensure you\'re using transaction notifications effectively to monitor spending.');
    }

    // Professional recommendations
    if (stats.categories.professional < 5) {
      recommendations.push('Low professional networking activity. Consider engaging more on LinkedIn or industry forums.');
    }

    // Unsubscribe recommendations
    if (stats.categories.promotional > 20) {
      recommendations.push('High volume of promotional emails. Use tools like Unroll.me to batch unsubscribe.');
    }

    // Time management
    if (stats.emails_last_day > 150) {
      recommendations.push('Email volume is very high. Consider implementing email filtering rules and scheduled checking times.');
    }

    return recommendations;
  }

  /**
   * Export data with options
   */
  async exportData(options: ExportOptions): Promise<void> {
    try {
      const result = await getMonitoringStats();
      if (!result.success || !result.data) {
        throw new Error('Failed to fetch monitoring data');
      }

      const stats = result.data;

      switch (options.format) {
        case 'csv':
          await this.exportToCSV(stats);
          break;
        case 'json':
          await this.exportToJSON(stats);
          break;
        case 'pdf':
          await this.exportToPDF(stats);
          break;
        default:
          throw new Error('Unsupported export format');
      }
    } catch (error) {
      console.error('Export failed:', error);
      throw error;
    }
  }

  /**
   * Get export preview
   */
  getExportPreview(stats: MonitoringStats, format: 'csv' | 'json' | 'pdf'): string {
    switch (format) {
      case 'csv':
        return `Total Emails,${stats.total_emails}\nLast Hour,${stats.emails_last_hour}\nLast Day,${stats.emails_last_day}...`;
      case 'json':
        return JSON.stringify({
          totalEmails: stats.total_emails,
          emailsLastHour: stats.emails_last_hour,
          categories: stats.categories
        }, null, 2);
      case 'pdf':
        return `Email Analytics Report\n\nTotal: ${stats.total_emails}\nLast 24h: ${stats.emails_last_day}...`;
      default:
        return '';
    }
  }
}

// Export singleton instance
export const emailExportService = new EmailExportService();
