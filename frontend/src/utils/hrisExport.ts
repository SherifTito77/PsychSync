// frontend/src/utils/hrisExport.ts - Export Functionality for HRIS Analytics

import { Employee, HRISStatistics, HRISExportData } from '@/types/hris';

/**
 * Export HRIS data to CSV format
 */
export const exportToCSV = (employees: Employee[], filename: string = 'hris-analytics-export'): void => {
  if (employees.length === 0) {
    alert('No data to export');
    return;
  }

  // Define CSV headers
  const headers = [
    'Employee ID',
    'Name',
    'Email',
    'Position',
    'Department',
    'Location',
    'Status',
    'Hire Date',
    'Assessments Completed',
    'Last Assessment Date',
    'MBTI Type',
    'Emotional Intelligence',
    'Leadership Potential',
    'Team Fit Score',
    'Openness',
    'Conscientiousness',
    'Extraversion',
    'Agreeableness',
    'Neuroticism',
    'Communication Style',
    'Work Style',
    'Strengths',
    'Development Areas'
  ];

  // Convert employee data to CSV rows
  const rows = employees.map(emp => {
    const assessment = emp.assessment_data;
    return [
      emp.id,
      emp.name,
      emp.email || '',
      emp.position,
      emp.department,
      emp.location,
      emp.status,
      emp.hire_date || '',
      assessment?.assessments_completed || 0,
      assessment?.last_assessment_date || '',
      assessment?.mbti_type || '',
      assessment?.emotional_intelligence || '',
      assessment?.leadership_potential || '',
      assessment?.team_fit_score || '',
      assessment?.big_five_scores?.openness || '',
      assessment?.big_five_scores?.conscientiousness || '',
      assessment?.big_five_scores?.extraversion || '',
      assessment?.big_five_scores?.agreeableness || '',
      assessment?.big_five_scores?.neuroticism || '',
      assessment?.personality_profile?.communication_style || '',
      assessment?.personality_profile?.work_style || '',
      assessment?.strengths?.join('; ') || '',
      assessment?.development_areas?.join('; ') || ''
    ].map(field => `"${String(field).replace(/"/g, '""')}"`).join(',');
  });

  // Combine headers and rows
  const csvContent = [headers.join(','), ...rows].join('\n');

  // Create download link
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}.csv`);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Export HRIS statistics summary
 */
export const exportStatisticsSummary = (
  stats: HRISStatistics,
  filename: string = 'hris-statistics-summary'
): void => {
  const summaryData = [
    ['HRIS Analytics Summary', ''],
    ['Generated', new Date().toLocaleString()],
    [''],
    ['Overall Statistics', ''],
    ['Total Employees', stats.totalEmployees],
    ['Total Departments', stats.totalDepartments],
    ['Total Positions', stats.totalPositions],
    ['Total Locations', stats.totalLocations],
    ['Active Rate', `${stats.activePercentage.toFixed(1)}%`],
    ['Assessment Completion Rate', `${stats.assessmentCompletionRate?.toFixed(1) || 0}%`],
    ['Average Leadership Potential', `${stats.avgLeadershipPotential?.toFixed(1) || 0}/100`],
    [''],
    ['Department Breakdown', ''],
    ...stats.departmentCounts.map(dept => [dept.name, `${dept.count} (${dept.percentage.toFixed(1)}%)`]),
    [''],
    ['Position Breakdown', ''],
    ...Object.entries(stats.positionCounts).map(([pos, count]) => [pos, String(count)]),
    [''],
    ['Location Breakdown', ''],
    ...Object.entries(stats.locationCounts).map(([loc, count]) => [loc, String(count)])
  ];

  const csvContent = summaryData.map(row => row.map(field => `"${String(field)}"`).join(',')).join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}.csv`);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Print the current view
 */
export const printView = (): void => {
  // Store original title
  const originalTitle = document.title;

  // Set print-specific title
  document.title = 'HRIS Analytics Dashboard';

  // Add print-specific styles
  const style = document.createElement('style');
  style.textContent = `
    @media print {
      body * {
        visibility: hidden;
      }
      .printable-area, .printable-area * {
        visibility: visible;
      }
      .printable-area {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
      }
      @page {
        size: landscape;
        margin: 1cm;
      }
      .no-print {
        display: none !important;
      }
    }
  `;
  document.head.appendChild(style);

  // Trigger print dialog
  window.print();

  // Cleanup
  setTimeout(() => {
    document.head.removeChild(style);
    document.title = originalTitle;
  }, 100);
};

/**
 * Export to JSON (for developers/API integration)
 */
export const exportToJSON = (data: HRISExportData, filename: string = 'hris-data-export'): void => {
  const jsonContent = JSON.stringify(data, null, 2);

  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}.json`);
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Generate printable HTML report
 */
export const generatePrintableReport = (
  employees: Employee[],
  stats: HRISStatistics,
  title: string = 'HRIS Analytics Report'
): void => {
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups for this feature');
    return;
  }

  const reportDate = new Date().toLocaleDateString();

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${title}</title>
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          padding: 40px;
          line-height: 1.6;
          color: #333;
        }
        h1 {
          color: #6366f1;
          border-bottom: 3px solid #6366f1;
          padding-bottom: 10px;
        }
        h2 {
          color: #4b5563;
          margin-top: 30px;
          border-left: 4px solid #6366f1;
          padding-left: 15px;
        }
        .report-meta {
          color: #6b7280;
          margin-bottom: 30px;
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin: 20px 0;
        }
        .stat-card {
          background: #f9fafb;
          padding: 15px;
          border-radius: 8px;
          border-left: 4px solid #6366f1;
        }
        .stat-card .value {
          font-size: 24px;
          font-weight: bold;
          color: #6366f1;
        }
        .stat-card .label {
          color: #6b7280;
          font-size: 14px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 20px 0;
        }
        th, td {
          border: 1px solid #e5e7eb;
          padding: 12px;
          text-align: left;
        }
        th {
          background: #f9fafb;
          font-weight: 600;
          color: #374151;
        }
        tr:nth-child(even) {
          background: #f9fafb;
        }
        .badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }
        .badge.active {
          background: #d1fae5;
          color: #065f46;
        }
        .assessment-badge {
          background: #dbeafe;
          color: #1e40af;
        }
        @media print {
          body { padding: 20px; }
          .no-print { display: none; }
        }
      </style>
    </head>
    <body>
      <h1>${title}</h1>
      <div class="report-meta">
        <p>Generated: ${reportDate}</p>
        <p>Total Employees: ${stats.totalEmployees}</p>
      </div>

      <h2>Overview Statistics</h2>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="value">${stats.totalEmployees}</div>
          <div class="label">Total Employees</div>
        </div>
        <div class="stat-card">
          <div class="value">${stats.totalDepartments}</div>
          <div class="label">Departments</div>
        </div>
        <div class="stat-card">
          <div class="value">${stats.totalPositions}</div>
          <div class="label">Positions</div>
        </div>
        <div class="stat-card">
          <div class="value">${stats.activePercentage.toFixed(0)}%</div>
          <div class="label">Active Rate</div>
        </div>
        <div class="stat-card">
          <div class="value">${stats.assessmentCompletionRate?.toFixed(0) || 0}%</div>
          <div class="label">Assessment Completion</div>
        </div>
      </div>

      <h2>Employee Directory</h2>
      <table>
        <thead>
          <tr>
            <th>Employee</th>
            <th>Position</th>
            <th>Department</th>
            <th>Location</th>
            <th>Status</th>
            <th>Assessments</th>
            <th>Leadership Potential</th>
          </tr>
        </thead>
        <tbody>
          ${employees.map(emp => `
            <tr>
              <td><strong>${emp.name}</strong><br><small>${emp.email || emp.id}</small></td>
              <td>${emp.position}</td>
              <td>${emp.department}</td>
              <td>${emp.location}</td>
              <td><span class="badge ${emp.status === 'Active' ? 'active' : ''}">${emp.status}</span></td>
              <td><span class="badge assessment-badge">${emp.assessment_data?.assessments_completed || 0}</span></td>
              <td>${emp.assessment_data?.leadership_potential || 'N/A'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      <div class="no-print" style="margin-top: 40px; text-align: center; color: #6b7280;">
        <p>Generated by PsychSync HRIS Analytics</p>
        <button onclick="window.print()" style="padding: 10px 20px; background: #6366f1; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
          Print Report
        </button>
      </div>
    </body>
    </html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();
};

/**
 * Export filtered data
 */
export const exportFilteredData = (
  employees: Employee[],
  filters: {
    department?: string;
    location?: string;
    status?: string;
    hasAssessment?: boolean;
  },
  format: 'csv' | 'json' = 'csv'
): void => {
  let filtered = [...employees];

  if (filters.department) {
    filtered = filtered.filter(emp => emp.department === filters.department);
  }
  if (filters.location) {
    filtered = filtered.filter(emp => emp.location === filters.location);
  }
  if (filters.status) {
    filtered = filtered.filter(emp => emp.status === filters.status);
  }
  if (filters.hasAssessment) {
    filtered = filtered.filter(emp => emp.assessment_data);
  }

  if (format === 'csv') {
    exportToCSV(filtered, `hris-export-${filters.department || 'all'}-${Date.now()}`);
  } else {
    const exportData: HRISExportData = {
      employees: filtered,
      statistics: {
        totalEmployees: filtered.length,
        totalDepartments: [...new Set(filtered.map(e => e.department))].length,
        totalPositions: [...new Set(filtered.map(e => e.position))].length,
        totalLocations: [...new Set(filtered.map(e => e.location))].length,
        activePercentage: (filtered.filter(e => e.status === 'Active').length / filtered.length) * 100,
        departmentCounts: [],
        positionCounts: {},
        locationCounts: {}
      },
      export_date: new Date().toISOString(),
      filters
    };
    exportToJSON(exportData, `hris-export-${filters.department || 'all'}-${Date.now()}`);
  }
};
