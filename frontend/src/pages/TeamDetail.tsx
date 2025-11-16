// frontend/src/pages/TeamDetail.tsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { teamService, TeamWithMembers, TeamMember } from '../services/teamService';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import AddMemberModal from '../components/teams/AddMemberModal';
import EditTeamModal from '../components/teams/EditTeamModal';
const TeamDetail: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [team, setTeam] = useState<TeamWithMembers | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddMember, setShowAddMember] = useState(false);
  const [showEditTeam, setShowEditTeam] = useState(false);
  const [error, setError] = useState('');
  const currentMember = team?.members.find((m) => String(m.user_id) === String(user?.id));
  const isAdminOrOwner = currentMember?.role === 'admin' || currentMember?.role === 'owner';
  const isOwner = currentMember?.role === 'owner';
  useEffect(() => {
    loadTeam();
  }, [teamId]);
  const loadTeam = async () => {
    if (!teamId) return;
    setIsLoading(true);
    setError('');
    try {
      const data = await teamService.getTeam(parseInt(teamId));
      setTeam(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load team');
    } finally {
      setIsLoading(false);
    }
  };
  const handleDeleteTeam = async () => {
    if (!teamId || !team) return;
    if (!confirm(`Are you sure you want to delete "${team.name}"? This action cannot be undone.`)) {
      return;
    }
    try {
      await teamService.deleteTeam(parseInt(teamId));
      navigate('/teams');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete team');
    }
  };
  const handleRemoveMember = async (memberId: number, memberName: string) => {
    if (!teamId) return;
    if (!confirm(`Are you sure you want to remove ${memberName} from the team?`)) {
      return;
    }
    try {
      await teamService.removeMember(parseInt(teamId), memberId);
      loadTeam();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to remove member');
    }
  };
  const handleLeaveTeam = async () => {
    if (!teamId || !team) return;
    if (!confirm(`Are you sure you want to leave "${team.name}"?`)) {
      return;
    }
    try {
      await teamService.leaveTeam(parseInt(teamId));
      navigate('/teams');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to leave team');
    }
  };
  const handleUpdateRole = async (userId: number, newRole: string) => {
    if (!teamId) return;
    try {
      await teamService.updateMemberRole(parseInt(teamId), userId, { role: newRole as any });
      loadTeam();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update role');
    }
  };
  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-100 text-purple-800';
      case 'admin':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }
  if (error || !team) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-800">{error || 'Team not found'}</p>
        <Link to="/teams" className="mt-2 text-sm text-red-600 hover:text-red-500">
          ← Back to teams
        </Link>
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <Link
            to="/teams"
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center mb-2"
          >
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to teams
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-gray-900">{team.name}</h1>
            {!team.is_active && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                Inactive
              </span>
            )}
          </div>
          {team.description && (
            <p className="mt-2 text-sm text-gray-500">{team.description}</p>
          )}
        </div>
        {/* Actions */}
        <div className="flex space-x-2">
          {isAdminOrOwner && (
            <>
              <button
                onClick={() => setShowEditTeam(true)}
                className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Edit Team
              </button>
              <button
                onClick={() => setShowAddMember(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700"
              >
                Add Member
              </button>
            </>
          )}
          {isOwner && (
            <button
              onClick={handleDeleteTeam}
              className="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700"
            >
              Delete Team
            </button>
          )}
          {!isOwner && (
            <button
              onClick={handleLeaveTeam}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Leave Team
            </button>
          )}
        </div>
      </div>
      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Members
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {team.member_count}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Created
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {new Date(team.created_at).toLocaleDateString()}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Your Role
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 capitalize">
                    {currentMember?.role}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Members List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Team Members
          </h3>
        </div>
        <ul className="divide-y divide-gray-200">
          {team.members.map((member) => (
            <li key={member.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-indigo-600 font-medium text-sm">
                        {member.user.full_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">
                      {member.user.full_name}
                      {String(member.user_id) === String(user?.id) && (
                        <span className="ml-2 text-gray-500">(You)</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">{member.user.email}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  {isAdminOrOwner && String(member.user_id) !== String(user?.id) ? (
                    <select
                      value={member.role}
                      onChange={(e) => handleUpdateRole(member.user_id, e.target.value)}
                      disabled={member.role === 'owner' && !isOwner}
                      className="text-sm border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
                    >
                      <option value="member">Member</option>
                      <option value="admin">Admin</option>
                      {isOwner && <option value="owner">Owner</option>}
                    </select>
                  ) : (
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(
                        member.role
                      )}`}
                    >
                      {member.role}
                    </span>
                  )}
                  {isAdminOrOwner &&
                    String(member.user_id) !== String(user?.id) &&
                    (member.role !== 'owner' || isOwner) && (
                      <button
                        onClick={() =>
                          handleRemoveMember(member.user_id, member.user.full_name)
                        }
                        className="text-red-600 hover:text-red-900 text-sm font-medium"
                      >
                        Remove
                      </button>
                    )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
      {/* Modals */}
      {showAddMember && teamId && (
        <AddMemberModal
          teamId={parseInt(teamId)}
          onClose={() => setShowAddMember(false)}
          onSuccess={loadTeam}
        />
      )}
      {showEditTeam && teamId && (
        <EditTeamModal
          team={team}
          onClose={() => setShowEditTeam(false)}
          onSuccess={loadTeam}
        />
      )}
    </div>
  );
};
export default TeamDetail;
