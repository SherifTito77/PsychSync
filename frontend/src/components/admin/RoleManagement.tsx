// src/components/admin/RoleManagement.tsx - Admin panel for managing user roles
import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useRoleNavigation } from '../../hooks/useRoleNavigation';
import api from '../../services/api';
import Icon from '../common/Icon';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'user' | 'employee' | 'hr' | 'manager' | 'admin' | 'super_admin';
  department?: string;
  is_active: boolean;
  created_at: string;
}

interface UpdateRoleData {
  user_id: string;
  role: string;
}

const RoleManagement: React.FC = () => {
  const { user: currentUser } = useAuth();
  const { isAdmin } = useRoleNavigation();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  // Check if current user can manage roles
  const canManageRoles = isAdmin || isSuperAdmin;

  useEffect(() => {
    if (!canManageRoles) return;

    fetchUsers();
  }, [canManageRoles]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/users'); // Assuming this endpoint exists
      setUsers(response.data as User[]);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    // Prevent users from changing their own role
    if (userId === currentUser?.id) {
      alert('You cannot change your own role');
      return;
    }

    // Prevent non-super-admins from promoting to super_admin
    if (newRole === 'super_admin' && !isSuperAdmin) {
      alert('Only Super Admins can assign Super Admin role');
      return;
    }

    try {
      setUpdatingUserId(userId);
      await api.patch(`/api/v1/users/${userId}/role`, { role: newRole });

      // Update local state
      setUsers(users.map(u =>
        u.id === userId
          ? {
              ...u,
              role: newRole as any,
              is_hr: ['hr', 'admin', 'super_admin', 'manager'].includes(newRole)
            }
          : u
      ));
    } catch (error) {
      console.error('Failed to update role:', error);
      alert('Failed to update user role');
    } finally {
      setUpdatingUserId(null);
    }
  };

  // Filter users
  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      const matchesSearch =
        user.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesRole = roleFilter === 'all' || user.role === roleFilter;

      return matchesSearch && matchesRole;
    });
  }, [users, searchQuery, roleFilter]);

  const roleCounts = useMemo(() => {
    return users.reduce((acc, user) => {
      acc[user.role] = (acc[user.role] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [users]);

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'admin':
        return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'hr':
      case 'manager':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'employee':
      case 'user':
      default:
        return 'bg-blue-100 text-blue-700 border-blue-200';
    }
  };

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'Super Admin';
      case 'admin':
        return 'Administrator';
      case 'hr':
        return 'HR Manager';
      case 'manager':
        return 'Manager';
      case 'employee':
        return 'Employee';
      case 'user':
        return 'User';
      default:
        return role;
    }
  };

  if (!canManageRoles) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <Icon size="lg" className="mb-4">🔒</Icon>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h2>
        <p className="text-gray-600">You don't have permission to manage user roles.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Role Management</h1>
            <p className="text-sm text-gray-600 mt-1">
              Manage user roles and permissions
            </p>
          </div>
          <button
            onClick={fetchUsers}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {Object.entries({
            super_admin: 'Super Admin',
            admin: 'Admin',
            hr: 'HR',
            manager: 'Manager',
            employee: 'Employee',
            user: 'User'
          }).map(([key, label]) => (
            <div key={key} className="bg-gray-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-gray-900">
                {roleCounts[key] || 0}
              </div>
              <div className="text-xs text-gray-600 mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search users by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Role Filter */}
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Roles</option>
            <option value="super_admin">Super Admin</option>
            <option value="admin">Admin</option>
            <option value="hr">HR Manager</option>
            <option value="manager">Manager</option>
            <option value="employee">Employee</option>
            <option value="user">User</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p className="mt-2 text-gray-600">Loading users...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Department
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Change Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                          <span className="text-sm font-medium text-indigo-600">
                            {user.full_name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.full_name}
                            {user.id === currentUser?.id && (
                              <span className="ml-2 text-xs text-gray-500">(You)</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {user.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {user.department || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${getRoleBadgeColor(user.role)}`}>
                        {getRoleDisplayName(user.role)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        disabled={updatingUserId === user.id || user.id === currentUser?.id}
                        className={`text-sm border rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                          updatingUserId === user.id
                            ? 'opacity-50 cursor-not-allowed'
                            : 'bg-white'
                        }`}
                      >
                        <option value="employee">Employee</option>
                        <option value="hr">HR Manager</option>
                        <option value="manager">Manager</option>
                        {(isSuperAdmin || user.role === 'super_admin') && (
                          <option value="admin">Administrator</option>
                        )}
                        {isSuperAdmin && (
                          <option value="super_admin">Super Admin</option>
                        )}
                      </select>
                      {updatingUserId === user.id && (
                        <span className="ml-2 text-xs text-indigo-600">Updating...</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        user.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredUsers.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                <Icon size="md" className="mb-2">🔍</Icon>
                <p>No users found matching your criteria</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">Role Permissions Guide</h3>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• <strong>Super Admin:</strong> Full system access, can assign any role</li>
          <li>• <strong>Admin:</strong> All features except super admin actions</li>
          <li>• <strong>HR Manager:</strong> Employee features + HR analytics, risk detection</li>
          <li>• <strong>Manager:</strong> Employee features + team management</li>
          <li>• <strong>Employee:</strong> Basic features, clinical tools</li>
        </ul>
      </div>
    </div>
  );
};

export default RoleManagement;
