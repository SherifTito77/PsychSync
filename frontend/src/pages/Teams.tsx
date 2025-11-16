// frontend/src/pages/Teams.tsx
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { teamService, Team } from '../services/teamService';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import CreateTeamModal from '../components/teams/CreateTeamModal';
import { useTeam } from '../contexts/TeamContext';
import Button from '../components/common/Button';
const Teams: React.FC = () => {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMyTeams, setShowMyTeams] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    loadTeams();
  }, [showMyTeams]);
  const loadTeams = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await teamService.getTeams(showMyTeams);
      setTeams(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load teams');
    } finally {
      setIsLoading(false);
    }
  };
  const handleTeamCreated = () => {
    setShowCreateModal(false);
    loadTeams();
  };
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Teams</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your teams and collaborate with colleagues
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Create Team
        </button>
      </div>
      {/* Filter Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setShowMyTeams(true)}
            className={`${
              showMyTeams
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            My Teams
          </button>
          <button
            onClick={() => setShowMyTeams(false)}
            className={`${
              !showMyTeams
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            All Teams
          </button>
        </nav>
      </div>
      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}
      {/* Teams Grid */}
      {teams.length === 0 ? (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No teams</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new team.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <svg
                className="-ml-1 mr-2 h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Create Team
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {teams.map((team) => (
            <Link
              key={team.id}
              to={`/teams/${team.id}`}
              className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {team.name}
                  </h3>
                  {!team.is_active && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Inactive
                    </span>
                  )}
                </div>
                {team.description && (
                  <p className="mt-2 text-sm text-gray-500 line-clamp-2">
                    {team.description}
                  </p>
                )}
                <div className="mt-4 flex items-center text-sm text-gray-500">
                  <svg
                    className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400"
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
                  Created {new Date(team.created_at).toLocaleDateString()}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
      {/* Create Team Modal */}
      {showCreateModal && (
        <CreateTeamModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleTeamCreated}
        />
      )}
    </div>
  );
};
export default Teams;
// const Teams: React.FC = () => {
//   const { teams, loading, fetchTeams } = useTeam();
//   useEffect(() => {
//     fetchTeams();
//   }, []);
//   if (loading) {
//     return (
//       <div className="flex items-center justify-center p-8">
//         <LoadingSpinner size="large" />
//       </div>
//     );
//   }
//   return (
//     <div className="space-y-6">
//       <div className="flex justify-between items-center">
//         <h1 className="text-3xl font-bold text-gray-900">Team Management</h1>
//         <Button>Create New Team</Button>
//       </div>
//       <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
//         {teams.map((team) => (
//           <div
//             key={team.id}
//             className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
//           >
//             <div className="flex items-center justify-between mb-4">
//               <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
//               <span
//                 className={`px-2 py-1 text-xs font-medium rounded-full ${
//                   team.status === 'active'
//                     ? 'bg-green-100 text-green-800'
//                     : 'bg-gray-100 text-gray-800'
//                 }`}
//               >
//                 {team.status}
//               </span>
//             </div>
//             <p className="text-gray-600 mb-4">{team.description}</p>
//             <div className="flex space-x-2">
//               <Button size="small" variant="secondary">
//                 View Details
//               </Button>
//               <Button size="small">
//                 Optimize
//               </Button>
//             </div>
//           </div>
//         ))}
//       </div>
//       {teams.length === 0 && (
//         <div className="text-center py-12">
//           <div className="text-4xl mb-4">👥</div>
//           <h3 className="text-lg font-medium text-gray-900 mb-2">No teams yet</h3>
//           <p className="text-gray-500 mb-6">
//             Create your first team to start analyzing team dynamics.
//           </p>
//           <Button>Create Your First Team</Button>
//         </div>
//       )}
//     </div>
//   );
// };
// export default Teams;
// import React from "react";
// const Teams: React.FC = () => {
//   return <h1>Teams Page</h1>;
// };
// export default Teams;
