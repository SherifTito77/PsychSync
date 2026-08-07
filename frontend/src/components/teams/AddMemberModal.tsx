// frontend/src/components/teams/AddMemberModal.tsx
import React, { useState, useEffect } from 'react';
import { teamService } from '../../services/teamService';
import api from '../../services/api';
import LoadingSpinner from '../common/LoadingSpinner';

interface AddMemberModalProps {
  teamId: string;
  onClose: () => void;
  onSuccess: () => void;
}

interface User {
  id: string;
  email: string;
  full_name: string;
}

const AddMemberModal: React.FC<AddMemberModalProps> = ({
  teamId,
  onClose,
  onSuccess,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [role, setRole] = useState<'member' | 'admin' | 'owner'>('member');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [error, setError] = useState('');
  const [isInviteMode, setIsInviteMode] = useState(false);

  // New user fields
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteFullName, setInviteFullName] = useState('');

  useEffect(() => {
    loadAvailableUsers();
  }, [teamId]);

  const loadAvailableUsers = async () => {
    setIsLoadingUsers(true);
    try {
      // Load users from same organization who are not already team members
      const response = await api.get<User[]>(`/teams/${teamId}/available-users`);
      setUsers(response.data);
    } catch (error: any) {
      console.error('Failed to load available users', error);
      setError('Failed to load available users');
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    setIsLoading(true);
    try {
      let userId = selectedUserId;

      if (isInviteMode) {
        // Use the team invite endpoint which creates the user and adds to team
        await api.post(`/teams/${teamId}/invite`, {
          email: inviteEmail,
          full_name: inviteFullName,
          role: role,
        });
        onSuccess();
        return; // Return early since invite endpoint handles everything
      }

      if (!userId) {
        setError('Please select or create a user');
        setIsLoading(false);
        return;
      }

      // 2. Add to team
      await teamService.addMember(teamId, {
        user_id: userId,
        role: role,
      });

      onSuccess();
    } catch (error: any) {
      setError(error.response?.data?.detail || (typeof error.response?.data?.detail === 'object' ? JSON.stringify(error.response?.data?.detail) : 'Failed to process request'));
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

              <div className="mt-4 flex p-1 bg-gray-100 rounded-md">
                <button
                  onClick={() => setIsInviteMode(false)}
                  className={`flex-1 py-2 text-sm font-medium rounded-md ${!isInviteMode ? 'bg-white shadow text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  Existing User
                </button>
                <button
                  onClick={() => setIsInviteMode(true)}
                  className={`flex-1 py-2 text-sm font-medium rounded-md ${isInviteMode ? 'bg-white shadow text-indigo-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  Invite New User
                </button>
              </div>

              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}

                {isInviteMode ? (
                  <>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                        Email Address *
                      </label>
                      <input
                        type="email"
                        id="email"
                        required
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        placeholder="colleague@example.com"
                      />
                    </div>
                    <div>
                      <label htmlFor="fullName" className="block text-sm font-medium text-gray-700">
                        Full Name
                      </label>
                      <input
                        type="text"
                        id="fullName"
                        value={inviteFullName}
                        onChange={(e) => setInviteFullName(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        placeholder="John Doe"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    {isLoadingUsers ? (
                      <div className="flex justify-center py-4">
                        <LoadingSpinner size="medium" />
                      </div>
                    ) : (
                      <div>
                        <label
                          htmlFor="user"
                          className="block text-sm font-medium text-gray-700"
                        >
                          Select User *
                        </label>
                        <select
                          id="user"
                          required={!isInviteMode}
                          value={selectedUserId || ''}
                          onChange={(e) => setSelectedUserId(e.target.value || null)}
                          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        >
                          <option value="">Select a user...</option>
                          {users.map((user) => (
                            <option key={user.id} value={user.id}>
                              {user.full_name || 'No Name'} ({user.email})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </>
                )}

                <div>
                  <label
                    htmlFor="role"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Role in Team *
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
                </div>

                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    disabled={isLoading || (!isInviteMode && isLoadingUsers)}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <LoadingSpinner size="small" className="mr-2" />
                        Processing...
                      </>
                    ) : (
                      isInviteMode ? 'Invite & Add' : 'Add Member'
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
