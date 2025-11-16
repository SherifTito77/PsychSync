// frontend/src/components/assessments/EditAssessmentModal.tsx
import React, { useState, useEffect } from 'react';
import {
  assessmentService,
  AssessmentWithSections,
} from '../../services/assessmentService';
import { teamService, Team } from '../../services/teamService';
import LoadingSpinner from '../common/LoadingSpinner';
interface EditAssessmentModalProps {
  assessment: AssessmentWithSections;
  onClose: () => void;
  onSuccess: () => void;
}
const EditAssessmentModal: React.FC<EditAssessmentModalProps> = ({
  assessment,
  onClose,
  onSuccess,
}) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [formData, setFormData] = useState({
    title: assessment.title,
    description: assessment.description || '',
    category: assessment.category,
    instructions: assessment.instructions || '',
    estimated_duration: assessment.estimated_duration?.toString() || '',
    is_public: assessment.is_public,
    allow_anonymous: assessment.allow_anonymous,
    randomize_questions: assessment.randomize_questions,
    show_progress: assessment.show_progress,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    loadTeams();
  }, []);
  const loadTeams = async () => {
    try {
      const data = await teamService.getTeams(true);
      setTeams(data);
    } catch (error) {
      console.error('Failed to load teams');
    }
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (formData.title.length < 3) {
      setError('Title must be at least 3 characters');
      return;
    }
    setIsLoading(true);
    try {
      await assessmentService.updateAssessment(assessment.id, {
        title: formData.title,
        description: formData.description || undefined,
        category: formData.category,
        instructions: formData.instructions || undefined,
        estimated_duration: formData.estimated_duration
          ? parseInt(formData.estimated_duration)
          : undefined,
        is_public: formData.is_public,
        allow_anonymous: formData.allow_anonymous,
        randomize_questions: formData.randomize_questions,
        show_progress: formData.show_progress,
      });
      onSuccess();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to update assessment');
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
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6">
          <div>
            <div className="mt-3 text-center sm:mt-0 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Edit Assessment
              </h3>
              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label
                      htmlFor="title"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Title *
                    </label>
                    <input
                      type="text"
                      id="title"
                      required
                      value={formData.title}
                      onChange={(e) =>
                        setFormData({ ...formData, title: e.target.value })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="category"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Category *
                    </label>
                    <select
                      id="category"
                      required
                      value={formData.category}
                      onChange={(e) =>
                        setFormData({ ...formData, category: e.target.value })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    >
                      <option value="personality">Personality</option>
                      <option value="cognitive">Cognitive</option>
                      <option value="clinical">Clinical</option>
                      <option value="behavioral">Behavioral</option>
                      <option value="developmental">Developmental</option>
                      <option value="neuropsychological">Neuropsychological</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label
                      htmlFor="estimated_duration"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Estimated Duration (minutes)
                    </label>
                    <input
                      type="number"
                      id="estimated_duration"
                      value={formData.estimated_duration}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          estimated_duration: e.target.value,
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div className="md:col-span-2">
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
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label
                      htmlFor="instructions"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Instructions
                    </label>
                    <textarea
                      id="instructions"
                      rows={3}
                      value={formData.instructions}
                      onChange={(e) =>
                        setFormData({ ...formData, instructions: e.target.value })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <div className="flex items-center">
                      <input
                        id="is_public"
                        type="checkbox"
                        checked={formData.is_public}
                        onChange={(e) =>
                          setFormData({ ...formData, is_public: e.target.checked })
                        }
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="is_public"
                        className="ml-2 block text-sm text-gray-900"
                      >
                        Public assessment
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        id="allow_anonymous"
                        type="checkbox"
                        checked={formData.allow_anonymous}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            allow_anonymous: e.target.checked,
                          })
                        }
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="allow_anonymous"
                        className="ml-2 block text-sm text-gray-900"
                      >
                        Allow anonymous responses
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        id="randomize_questions"
                        type="checkbox"
                        checked={formData.randomize_questions}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            randomize_questions: e.target.checked,
                          })
                        }
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="randomize_questions"
                        className="ml-2 block text-sm text-gray-900"
                      >
                        Randomize question order
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        id="show_progress"
                        type="checkbox"
                        checked={formData.show_progress}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            show_progress: e.target.checked,
                          })
                        }
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="show_progress"
                        className="ml-2 block text-sm text-gray-900"
                      >
                        Show progress indicator
                      </label>
                    </div>
                  </div>
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
                        Saving...
                      </>
                    ) : (
                      'Save Changes'
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
export default EditAssessmentModal;
