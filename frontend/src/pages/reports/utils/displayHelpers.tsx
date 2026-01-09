/**
 * Display Helper Utilities
 *
 * Functions for formatting and styling report elements
 */

import React from 'react';
import { FileText, FileSpreadsheet, FileJson, Mail, Webhook, Download } from 'lucide-react';

/**
 * Get CSS classes for status badges
 */
export const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800';
    case 'generating':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'scheduled':
      return 'bg-purple-100 text-purple-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

/**
 * Get icon component for file format
 */
export const getFormatIcon = (format: string): JSX.Element => {
  switch (format.toLowerCase()) {
    case 'pdf':
      return <FileText className="h-4 w-4" />;
    case 'excel':
      return <FileSpreadsheet className="h-4 w-4" />;
    case 'csv':
      return <FileSpreadsheet className="h-4 w-4" />;
    case 'json':
      return <FileJson className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
};

/**
 * Get icon component for delivery method
 */
export const getDeliveryIcon = (method: string): JSX.Element => {
  switch (method.toLowerCase()) {
    case 'email':
      return <Mail className="h-4 w-4" />;
    case 'webhook':
      return <Webhook className="h-4 w-4" />;
    case 'download':
      return <Download className="h-4 w-4" />;
    default:
      return <Download className="h-4 w-4" />;
  }
};
