// frontend/src/pages/Profile.tsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
const Profile: React.FC = () => {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await api.put('/users/me', {
        full_name: formData.full_name,
      });
      setMessage({ type: 'success', text: 'Profile updated successfully' });
      setIsEditing(false);
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to update profile' 
      });
    }
  };
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    try {
      await api.post('/users/me/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      setMessage({ type: 'success', text: 'Password changed successfully' });
      setIsChangingPassword(false);
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Failed to change password' 
      });
    }
  };
  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="bg-white shadow rounded-lg">
        {/* Header */}
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your account information and preferences
          </p>
        </div>
        {/* Message Display */}
        {message && (
          <div className={`mx-4 mt-4 p-4 rounded-md ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
          </div>
        )}
        {/* Profile Information */}
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h2>
          {!isEditing ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Full Name</label>
                <p className="mt-1 text-sm text-gray-900">{user?.full_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Account Created</label>
                <p className="mt-1 text-sm text-gray-900">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
              <button
                onClick={() => setIsEditing(true)}
                className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                Edit Profile
              </button>
            </div>
          ) : (
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                  Full Name
                </label>
                <input
                  type="text"
                  id="full_name"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email (cannot be changed)
                </label>
                <input
                  type="email"
                  id="email"
                  value={formData.email}
                  disabled
                  className="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 shadow-sm"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false);
                    setFormData({ full_name: user?.full_name || '', email: user?.email || '' });
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
        {/* Password Section */}
        <div className="px-4 py-5 sm:p-6 border-t border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Change Password</h2>
          {!isChangingPassword ? (
            <button
              onClick={() => setIsChangingPassword(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Change Password
            </button>
          ) : (
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label htmlFor="current_password" className="block text-sm font-medium text-gray-700">
                  Current Password
                </label>
                <input
                  type="password"
                  id="current_password"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">
                  New Password
                </label>
                <input
                  type="password"
                  id="new_password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  Must be at least 8 characters with uppercase, lowercase, and numbers
                </p>
              </div>
              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  id="confirm_password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div className="flex space-x-3">
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  Update Password
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsChangingPassword(false);
                    setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
        {/* Danger Zone */}
        <div className="px-4 py-5 sm:p-6 border-t border-gray-200 bg-red-50">
          <h2 className="text-lg font-medium text-red-900 mb-4">Danger Zone</h2>
          <p className="text-sm text-red-700 mb-4">
            Once you logout, you'll need to sign in again to access your account.
          </p>
          <button
            onClick={logout}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};
export default Profile;
