// frontend/src/components/teams/CreateTeamModal.tsx
import React, { useState, useEffect } from 'react';
import { teamService } from '../../services/teamService';
import LoadingSpinner from '../common/LoadingSpinner';
import { useAnalytics } from '../../services/analytics/tracker';
interface CreateTeamModalProps {
  onClose: () => void;
  onSuccess: () => void;
}
const CreateTeamModal: React.FC<CreateTeamModalProps> = ({ onClose, onSuccess }) => {
  const { track, trackFunnel } = useAnalytics();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Track modal open
  useEffect(() => {
    track('user_modal_opened', {
      modal_id: 'create_team',
      page: 'teams'
    });
  }, [track]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.name.length < 3) {
      setError('Team name must be at least 3 characters');
      return;
    }

    setIsLoading(true);

    // Track team creation funnel start
    trackFunnel('team_creation', 'started', {
      has_description: !!formData.description,
      name_length: formData.name.length
    });

    try {
      const team = await teamService.createTeam({
        name: formData.name,
        description: formData.description || undefined,
      });

      // Track successful team creation
      trackFunnel('team_creation', 'completed', {
        team_id: team.id,
        team_name: team.name,
        has_description: !!formData.description
      });

      onSuccess();
    } catch (error: any) {
      // Track team creation failure
      track('system_error_occurred', {
        error_type: 'team_creation_failed',
        error_message: error.response?.data?.detail || 'Failed to create team',
        funnel_step: 'team_creation'
      });

      setError(error.response?.data?.detail || 'Failed to create team');
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="fixed z-10 inset-0 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>
        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <div className="mt-3 text-center sm:mt-0 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Create New Team
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Create a new team to collaborate with your colleagues.
              </p>
              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
                <div>
                  <label
                    htmlFor="name"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Team Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    required
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., Clinical Psychology Team"
                  />
                </div>
                <div>
                  <label
                    htmlFor="description"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Description
                  </label>
                  <textarea
                    id="description"
                    rows={3}
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Brief description of the team's purpose..."
                  />
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <LoadingSpinner size="small" className="mr-2" />
                        Creating...
                      </>
                    ) : (
                      'Create Team'
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      track('user_modal_closed', {
                        modal_id: 'create_team',
                        page: 'teams',
                        had_input: !!formData.name
                      });
                      onClose();
                    }}
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
export default CreateTeamModal;
