import React from 'react';
import DashboardLayout from '../components/layout/DashboardLayout';
const Settings: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Settings</h1>
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Account Settings</h2>
            <p className="text-gray-600">Account settings functionality coming soon...</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Notification Preferences</h2>
            <p className="text-gray-600">Notification settings coming soon...</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Privacy & Security</h2>
            <p className="text-gray-600">Privacy settings coming soon...</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};
export default Settings;