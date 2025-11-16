// frontend/src/components/teams/AddMemberModal.tsx
import React, { useState, useEffect } from 'react';
import { teamService } from '../../services/teamService';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';
interface AddMemberModalProps {
  teamId: number;
  onClose: () => void;
  onSuccess: () => void;
}
interface User {
  id: number;
  email: string;
  full_name: string;
}
const AddMemberModal: React.FC<AddMemberModalProps> = ({
  teamId,
  onClose,
  onSuccess,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [role, setRole] = useState<'member' | 'admin' | 'owner'>('member');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    loadUsers();
  }, []);
  const loadUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const response = await api.get<User[]>('/admin/users');
      setUsers(response.data);
    } catch (error: any) {
      setError('Failed to load users');
    } finally {
      setIsLoadingUsers(false);
    }
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!selectedUserId) {
      setError('Please select a user');
      return;
    }
    setIsLoading(true);
    try {
      await teamService.addMember(teamId, {
        user_id: selectedUserId,
        role: role,
      });
      onSuccess();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to add member');
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="fixed z-10 inset-0 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <div className="mt-3 text-center sm:mt-0 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Add Team Member
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Add a new member to your team.
              </p>
              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
                {isLoadingUsers ? (
                  <div className="flex justify-center py-4">
                    <LoadingSpinner size="medium" />
                  </div>
                ) : (
                  <>
                    <div>
                      <label
                        htmlFor="user"
                        className="block text-sm font-medium text-gray-700"
                      >
                        User *
                      </label>
                      <select
                        id="user"
                        required
                        value={selectedUserId || ''}
                        onChange={(e) =>
                          setSelectedUserId(
                            e.target.value ? parseInt(e.target.value) : null
                          )
                        }
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      >
                        <option value="">Select a user...</option>
                        {users.map((user) => (
                          <option key={user.id} value={user.id}>
                            {user.full_name} ({user.email})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label
                        htmlFor="role"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Role *
                      </label>
                      <select
                        id="role"
                        required
                        value={role}
                        onChange={(e) =>
                          setRole(e.target.value as 'member' | 'admin' | 'owner')
                        }
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      >
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                        <option value="owner">Owner</option>
                      </select>
                      <p className="mt-1 text-xs text-gray-500">
                        Members can view, Admins can manage, Owners have full control
                      </p>
                    </div>
                  </>
                )}
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    disabled={isLoading || isLoadingUsers}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <LoadingSpinner size="small" className="mr-2" />
                        Adding...
                      </>
                    ) : (
                      'Add Member'
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={onClose}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default AddMemberModal;
