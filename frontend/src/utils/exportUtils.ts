/**
 * Export utilities for Wellbeing Assessment results
 */

export function exportToPDF(elementId: string, filename: string = 'wellbeing-results.pdf') {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error('Element not found:', elementId);
    return;
  }

  // Create print-friendly window
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('Please allow popups to export results');
    return;
  }

  // Clone the content
  const content = element.innerHTML;

  // Write to print window
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Wellbeing Assessment Results</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          padding: 20px;
          line-height: 1.6;
        }
        .card {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 20px;
          page-break-inside: avoid;
        }
        h1, h2, h3 {
          color: #333;
        }
        .progress-bar {
          width: 100%;
          height: 30px;
          background: #f0f0f0;
          border-radius: 15px;
          overflow: hidden;
          margin: 10px 0;
        }
        .progress-fill {
          height: 100%;
          transition: width 0.3s;
        }
        @media print {
          .no-print {
            display: none;
          }
          .card {
            break-inside: avoid;
          }
        }
      </style>
    </head>
    <body>
      ${content}
      <script>
        window.onload = function() {
          window.print();
          window.onafterprint = function() {
            window.close();
          };
        };
      </script>
    </body>
    </html>
  `);

  printWindow.document.close();
}

export function exportToCSV(data: any[], filename: string = 'wellness-data.csv') {
  if (data.length === 0) return;

  const headers = Object.keys(data[0]);
  const csv = [
    headers.join(','),
    ...data.map(row => headers.map(h => JSON.stringify(row[h])).join(','))
  ].join('\n');

  downloadFile(csv, filename, 'text/csv');
}

export function exportToJSON(data: any, filename: string = 'wellness-data.json') {
  const json = JSON.stringify(data, null, 2);
  downloadFile(json, filename, 'application/json');
}

function downloadFile(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
