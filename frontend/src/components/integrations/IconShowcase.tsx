/**
 * Icon Showcase Component
 *
 * Visual reference for all available icons in the Corporate Integrations system
 */

import React, { useState } from 'react';
import {
  getDataSourceIcon,
  getCategoryIcon,
  getSeverityIcon,
  getStatusIcon,
  getCategoryColor,
  getSeverityColor,
  getStatusColor,
  EmailIcon,
  SlackIcon,
  CalendarIcon,
  JiraIcon,
  WearableIcon,
  SyncIcon,
  SettingsIcon,
  CheckCircleIcon,
  AlertCircleIcon,
} from './IntegrationIcons';

interface IconData {
  name: string;
  category: string;
  Icon: React.FC<{ className?: string }>;
  color: string;
}

const ICON_SHOWCASE_DATA: IconData[] = [
  // Data Source Icons
  { name: 'Email', category: 'Communication', Icon: EmailIcon, color: 'text-blue-600' },
  { name: 'Slack', category: 'Communication', Icon: SlackIcon, color: 'text-purple-600' },
  { name: 'Calendar', category: 'Productivity', Icon: CalendarIcon, color: 'text-green-600' },
  { name: 'Jira', category: 'Productivity', Icon: JiraIcon, color: 'text-blue-500' },
  { name: 'Wearable', category: 'Other', Icon: WearableIcon, color: 'text-pink-600' },

  // Action Icons
  { name: 'Sync', category: 'Actions', Icon: SyncIcon, color: 'text-gray-700' },
  { name: 'Settings', category: 'Actions', Icon: SettingsIcon, color: 'text-gray-700' },
  { name: 'Success', category: 'Status', Icon: CheckCircleIcon, color: 'text-green-500' },
  { name: 'Alert', category: 'Status', Icon: AlertCircleIcon, color: 'text-yellow-500' },
];

export const IconShowcase: React.FC = () => {
  const [selectedSize, setSelectedSize] = useState<'small' | 'medium' | 'large'>('medium');

  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-6 h-6',
    large: 'w-8 h-8',
  };

  return (
    <div className="icon-showcase p-6 bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Icon System Showcase</h2>
        <p className="text-gray-600">Visual reference for Corporate Integrations icons</p>
      </div>

      {/* Size Selector */}
      <div className="mb-8 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Icon Size</h3>
        <div className="flex gap-2">
          {(['small', 'medium', 'large'] as const).map((size) => (
            <button
              key={size}
              onClick={() => setSelectedSize(size)}
              className={`px-4 py-2 rounded font-medium capitalize transition-colors ${
                selectedSize === size
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Data Source Icons */}
      <section className="mb-10">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-2xl">📦</span>
          Data Source Icons
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ICON_SHOWCASE_DATA.filter(icon => icon.category !== 'Actions' && icon.category !== 'Status').map((icon) => (
            <div
              key={icon.name}
              className="flex items-center gap-4 p-4 border rounded-lg hover:shadow-md transition-shadow"
            >
              <div className={`p-3 bg-gray-50 rounded-lg ${icon.color}`}>
                <icon.Icon className={sizeClasses[selectedSize]} />
              </div>
              <div>
                <div className="font-semibold text-gray-900">{icon.name}</div>
                <div className="text-sm text-gray-500">{icon.category}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Severity Icons */}
      <section className="mb-10">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-2xl">⚠️</span>
          Severity Icons
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {(['low', 'medium', 'high', 'critical'] as const).map((severity) => {
            const SeverityIcon = getSeverityIcon(severity);
            const color = getSeverityColor(severity);
            return (
              <div
                key={severity}
                className="flex flex-col items-center gap-2 p-4 border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className={`p-3 bg-gray-50 rounded-lg ${color}`}>
                  <SeverityIcon className={sizeClasses[selectedSize]} />
                </div>
                <div className="text-center">
                  <div className="font-semibold text-gray-900 capitalize">{severity}</div>
                  <div className="text-xs text-gray-500">severity</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Status Icons */}
      <section className="mb-10">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-2xl">📊</span>
          Status Icons
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {(['active', 'disabled', 'error', 'syncing'] as const).map((status) => {
            const StatusIcon = getStatusIcon(status);
            const color = getStatusColor(status);
            return (
              <div
                key={status}
                className="flex flex-col items-center gap-2 p-4 border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className={`p-3 bg-gray-50 rounded-lg ${color}`}>
                  <StatusIcon className={sizeClasses[selectedSize]} />
                </div>
                <div className="text-center">
                  <div className="font-semibold text-gray-900 capitalize">{status}</div>
                  <div className="text-xs text-gray-500">status</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Category Icons */}
      <section className="mb-10">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-2xl">📂</span>
          Category Icons
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {(['communication', 'productivity', 'hr', 'other'] as const).map((category) => {
            const CategoryIcon = getCategoryIcon(category);
            const color = getCategoryColor(category);
            return (
              <div
                key={category}
                className="flex flex-col items-center gap-2 p-4 border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className={`p-3 bg-gray-50 rounded-lg ${color}`}>
                  <CategoryIcon className={sizeClasses[selectedSize]} />
                </div>
                <div className="text-center">
                  <div className="font-semibold text-gray-900 capitalize">{category}</div>
                  <div className="text-xs text-gray-500">category</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Usage Examples */}
      <section className="mb-10">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-2xl">💻</span>
          Usage Examples
        </h3>

        {/* Integration Card Example */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Integration Card</h4>
          <div className="p-4 border rounded-lg bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                  <EmailIcon className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Email Metadata</div>
                  <div className="text-sm text-gray-500">Last synced: 2 hours ago</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                <span className="text-sm text-green-600 font-medium">Active</span>
              </div>
            </div>
          </div>
        </div>

        {/* Insight Card Example */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Insight Card</h4>
          <div className="p-4 border rounded-lg bg-orange-50 border-orange-200">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-orange-100 rounded-lg text-orange-600">
                <AlertCircleIcon className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-orange-900">HIGH</span>
                  <span className="text-sm font-medium text-gray-900">Burnout Risk Detected</span>
                </div>
                <div className="text-sm text-gray-700">
                  Meeting load exceeds 80% of workday with limited focus time.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Badge Examples */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Status Badges</h4>
          <div className="flex flex-wrap gap-2">
            {['Active', 'Syncing', 'Error', 'Disabled'].map((status) => {
              const statusKey = status.toLowerCase() as 'active' | 'syncing' | 'error' | 'disabled';
              const StatusIcon = getStatusIcon(statusKey);
              const color = getStatusColor(statusKey);
              return (
                <div
                  key={status}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${color} bg-gray-50 border`}
                >
                  <StatusIcon className="w-3 h-3" />
                  <span>{status}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Color Palette Reference */}
      <section>
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span className="text-2xl">🎨</span>
          Color Palette
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { name: 'Blue', class: 'text-blue-600', hex: '#2563EB' },
            { name: 'Green', class: 'text-green-600', hex: '#16A34A' },
            { name: 'Purple', class: 'text-purple-600', hex: '#9333EA' },
            { name: 'Yellow', class: 'text-yellow-500', hex: '#EAB308' },
            { name: 'Orange', class: 'text-orange-500', hex: '#F97316' },
            { name: 'Red', class: 'text-red-500', hex: '#EF4444' },
            { name: 'Pink', class: 'text-pink-600', hex: '#DB2777' },
            { name: 'Gray', class: 'text-gray-600', hex: '#4B5563' },
          ].map((color) => (
            <div
              key={color.name}
              className="flex items-center gap-3 p-3 border rounded-lg"
            >
              <div
                className="w-10 h-10 rounded-lg shadow-sm"
                style={{ backgroundColor: color.hex }}
              />
              <div>
                <div className="font-semibold text-gray-900">{color.name}</div>
                <div className="text-xs text-gray-500 font-mono">{color.hex}</div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default IconShowcase;
