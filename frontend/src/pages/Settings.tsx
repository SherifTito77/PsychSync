import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/layout/DashboardLayout';

interface SettingsData {
  profile: {
    name: string;
    email: string;
    company: string;
    title: string;
    bio: string;
    avatar: string;
  };
  preferences: {
    emailNotifications: boolean;
    weeklyReports: boolean;
    teamUpdates: boolean;
    assessmentReminders: boolean;
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
  };
  privacy: {
    profileVisibility: 'public' | 'team' | 'private';
    shareAssessmentResults: boolean;
    dataSharing: boolean;
    twoFactorEnabled: boolean;
  };
  billing: {
    plan: 'free' | 'pro' | 'enterprise';
    billingEmail: string;
    nextBillingDate?: string;
    cancelAtPeriodEnd: boolean;
  };
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SettingsData>({
    profile: {
      name: '',
      email: '',
      company: '',
      title: '',
      bio: '',
      avatar: ''
    },
    preferences: {
      emailNotifications: true,
      weeklyReports: true,
      teamUpdates: true,
      assessmentReminders: true,
      theme: 'light',
      language: 'en',
      timezone: 'UTC'
    },
    privacy: {
      profileVisibility: 'team',
      shareAssessmentResults: true,
      dataSharing: false,
      twoFactorEnabled: false
    },
    billing: {
      plan: 'free',
      billingEmail: '',
      cancelAtPeriodEnd: false
    }
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/settings');
      if (response.ok) {
        const data = await response.json();
        setSettings(prev => ({ ...prev, ...data }));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      showMessage('Failed to load settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      const response = await fetch('/api/v1/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        showMessage('Settings saved successfully', 'success');
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      showMessage('Failed to save settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  const showMessage = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleProfileChange = (field: keyof SettingsData['profile'], value: string) => {
    setSettings(prev => ({
      ...prev,
      profile: { ...prev.profile, [field]: value }
    }));
  };

  const handlePreferenceChange = (field: keyof SettingsData['preferences'], value: any) => {
    setSettings(prev => ({
      ...prev,
      preferences: { ...prev.preferences, [field]: value }
    }));
  };

  const handlePrivacyChange = (field: keyof SettingsData['privacy'], value: any) => {
    setSettings(prev => ({
      ...prev,
      privacy: { ...prev.privacy, [field]: value }
    }));
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        const formData = new FormData();
        formData.append('avatar', file);

        const response = await fetch('/api/v1/settings/avatar', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const data = await response.json();
          handleProfileChange('avatar', data.avatarUrl);
          showMessage('Avatar updated successfully', 'success');
        }
      } catch (error) {
        showMessage('Failed to upload avatar', 'error');
      }
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: '👤' },
    { id: 'preferences', label: 'Preferences', icon: '⚙️' },
    { id: 'privacy', label: 'Privacy & Security', icon: '🔒' },
    { id: 'billing', label: 'Billing', icon: '💳' }
  ];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">Manage your account settings and preferences</p>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Information</h2>

                {/* Avatar */}
                <div className="flex items-center space-x-6">
                  <div className="shrink-0">
                    <img
                      className="h-20 w-20 object-cover rounded-full"
                      src={settings.profile.avatar || `https://ui-avatars.com/api/?name=${settings.profile.name}&background=3B82F6&color=fff`}
                      alt="Profile"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Profile Picture
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>
                </div>

                {/* Profile Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={settings.profile.name}
                      onChange={(e) => handleProfileChange('name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={settings.profile.email}
                      onChange={(e) => handleProfileChange('email', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Company
                    </label>
                    <input
                      type="text"
                      value={settings.profile.company}
                      onChange={(e) => handleProfileChange('company', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Title
                    </label>
                    <input
                      type="text"
                      value={settings.profile.title}
                      onChange={(e) => handleProfileChange('title', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bio
                  </label>
                  <textarea
                    rows={4}
                    value={settings.profile.bio}
                    onChange={(e) => handleProfileChange('bio', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Tell us about yourself..."
                  />
                </div>
              </div>
            )}

            {activeTab === 'preferences' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Preferences</h2>

                {/* Notification Preferences */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Notifications</h3>
                  <div className="space-y-3">
                    {[
                      { key: 'emailNotifications', label: 'Email notifications' },
                      { key: 'weeklyReports', label: 'Weekly team reports' },
                      { key: 'teamUpdates', label: 'Team updates' },
                      { key: 'assessmentReminders', label: 'Assessment reminders' }
                    ].map(({ key, label }) => (
                      <label key={key} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={settings.preferences[key as keyof SettingsData['preferences'] as boolean]}
                          onChange={(e) => handlePreferenceChange(key as keyof SettingsData['preferences'], e.target.checked)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-gray-700">{label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Display Preferences */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Display</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Theme
                      </label>
                      <select
                        value={settings.preferences.theme}
                        onChange={(e) => handlePreferenceChange('theme', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="auto">Auto</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Language
                      </label>
                      <select
                        value={settings.preferences.language}
                        onChange={(e) => handlePreferenceChange('language', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Timezone
                      </label>
                      <select
                        value={settings.preferences.timezone}
                        onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="UTC">UTC</option>
                        <option value="America/New_York">Eastern Time</option>
                        <option value="America/Chicago">Central Time</option>
                        <option value="America/Denver">Mountain Time</option>
                        <option value="America/Los_Angeles">Pacific Time</option>
                        <option value="Europe/London">London</option>
                        <option value="Europe/Paris">Paris</option>
                        <option value="Asia/Tokyo">Tokyo</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'privacy' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Privacy & Security</h2>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Visibility</h3>
                  <div className="space-y-3">
                    {[
                      { value: 'public', label: 'Public - Anyone can view your profile' },
                      { value: 'team', label: 'Team - Only team members can view your profile' },
                      { value: 'private', label: 'Private - Only you can view your profile' }
                    ].map(({ value, label }) => (
                      <label key={value} className="flex items-center">
                        <input
                          type="radio"
                          value={value}
                          checked={settings.privacy.profileVisibility === value}
                          onChange={(e) => handlePrivacyChange('profileVisibility', e.target.value)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                        />
                        <span className="ml-2 text-gray-700">{label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Data Sharing</h3>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={settings.privacy.shareAssessmentResults}
                        onChange={(e) => handlePrivacyChange('shareAssessmentResults', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-gray-700">
                        Share assessment results with team members
                      </span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={settings.privacy.dataSharing}
                        onChange={(e) => handlePrivacyChange('dataSharing', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-gray-700">
                        Allow anonymous data usage for product improvements
                      </span>
                    </label>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Security</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-700">Two-Factor Authentication</p>
                        <p className="text-sm text-gray-500">Add an extra layer of security to your account</p>
                      </div>
                      <button
                        onClick={() => handlePrivacyChange('twoFactorEnabled', !settings.privacy.twoFactorEnabled)}
                        className={`px-4 py-2 rounded-md text-sm font-medium ${
                          settings.privacy.twoFactorEnabled
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {settings.privacy.twoFactorEnabled ? 'Enabled' : 'Enable'}
                      </button>
                    </div>

                    <div className="pt-4 border-t">
                      <button className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
                        Change Password
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'billing' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Billing Information</h2>

                <div className="bg-gray-50 p-6 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Current Plan</h3>
                      <p className="text-sm text-gray-500 capitalize">{settings.billing.plan}</p>
                    </div>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                      Upgrade Plan
                    </button>
                  </div>

                  {settings.billing.plan !== 'free' && (
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Billing Email:</span>
                        <input
                          type="email"
                          value={settings.billing.billingEmail}
                          onChange={(e) => setSettings(prev => ({
                            ...prev,
                            billing: { ...prev.billing, billingEmail: e.target.value }
                          }))}
                          className="px-2 py-1 border border-gray-300 rounded"
                        />
                      </div>
                      {settings.billing.nextBillingDate && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Next Billing Date:</span>
                          <span>{settings.billing.nextBillingDate}</span>
                        </div>
                      )}
                      {settings.billing.cancelAtPeriodEnd && (
                        <div className="text-orange-600">
                          ⚠️ Your subscription will cancel at the end of the billing period
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Payment Methods</h3>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <p className="text-gray-500 mb-2">No payment methods on file</p>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                      Add Payment Method
                    </button>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Billing History</h3>
                  <div className="text-center py-8 text-gray-500">
                    No billing history available
                  </div>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="pt-6 border-t border-gray-200">
              <div className="flex justify-end">
                <button
                  onClick={saveSettings}
                  disabled={saving}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Settings;