// frontend/src/components/assessments/AddQuestionModal.tsx
import React, { useState } from 'react';
import { assessmentService } from '../../services/assessmentService';
import LoadingSpinner from '../common/LoadingSpinner';
interface AddQuestionModalProps {
  assessmentId: number;
  sectionId: number;
  onClose: () => void;
  onSuccess: () => void;
}
const AddQuestionModal: React.FC<AddQuestionModalProps> = ({
  assessmentId,
  sectionId,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    question_type: 'multiple_choice',
    question_text: '',
    help_text: '',
    order: 0,
    is_required: true,
    // Config for different question types
    options: ['', ''], // For multiple choice
    min_value: '1',
    max_value: '5',
    scale_labels: {} as Record<string, string>,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const questionTypes = [
    { value: 'multiple_choice', label: 'Multiple Choice' },
    { value: 'rating_scale', label: 'Rating Scale' },
    { value: 'text', label: 'Text Response' },
    { value: 'yes_no', label: 'Yes/No' },
    { value: 'likert', label: 'Likert Scale' },
  ];
  const handleAddOption = () => {
    setFormData({ ...formData, options: [...formData.options, ''] });
  };
  const handleRemoveOption = (index: number) => {
    const newOptions = formData.options.filter((_, i) => i !== index);
    setFormData({ ...formData, options: newOptions });
  };
  const handleOptionChange = (index: number, value: string) => {
    const newOptions = [...formData.options];
    newOptions[index] = value;
    setFormData({ ...formData, options: newOptions });
  };
  const buildConfig = () => {
    switch (formData.question_type) {
      case 'multiple_choice':
        return {
          options: formData.options.filter((opt) => opt.trim() !== ''),
          allow_multiple: false,
        };
      case 'rating_scale':
        return {
          min: parseInt(formData.min_value),
          max: parseInt(formData.max_value),
          labels: formData.scale_labels,
        };
      case 'likert':
        return {
          scale: 5,
          labels: [
            'Strongly Disagree',
            'Disagree',
            'Neutral',
            'Agree',
            'Strongly Agree',
          ],
        };
      default:
        return undefined;
    }
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (formData.question_text.length < 5) {
      setError('Question must be at least 5 characters');
      return;
    }
    if (
      formData.question_type === 'multiple_choice' &&
      formData.options.filter((opt) => opt.trim() !== '').length < 2
    ) {
      setError('Multiple choice questions need at least 2 options');
      return;
    }
    setIsLoading(true);
    try {
      await assessmentService.addQuestion(assessmentId, sectionId, {
        question_type: formData.question_type,
        question_text: formData.question_text,
        help_text: formData.help_text || undefined,
        order: formData.order,
        is_required: formData.is_required,
        config: buildConfig(),
      });
      onSuccess();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to add question');
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
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full sm:p-6 max-h-[90vh] overflow-y-auto">
          <div>
            <div className="mt-3 text-center sm:mt-0 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Add Question
              </h3>
              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
                <div>
                  <label
                    htmlFor="question_type"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Question Type *
                  </label>
                  <select
                    id="question_type"
                    required
                    value={formData.question_type}
                    onChange={(e) =>
                      setFormData({ ...formData, question_type: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    {questionTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label
                    htmlFor="question_text"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Question Text *
                  </label>
                  <textarea
                    id="question_text"
                    required
                    rows={3}
                    value={formData.question_text}
                    onChange={(e) =>
                      setFormData({ ...formData, question_text: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Enter your question..."
                  />
                </div>
                <div>
                  <label
                    htmlFor="help_text"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Help Text (Optional)
                  </label>
                  <input
                    type="text"
                    id="help_text"
                    value={formData.help_text}
                    onChange={(e) =>
                      setFormData({ ...formData, help_text: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Additional guidance for respondents..."
                  />
                </div>
                {/* Multiple Choice Options */}
                {formData.question_type === 'multiple_choice' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Options *
                    </label>
                    {formData.options.map((option, index) => (
                      <div key={index} className="flex items-center space-x-2 mb-2">
                        <input
                          type="text"
                          value={option}
                          onChange={(e) => handleOptionChange(index, e.target.value)}
                          className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                          placeholder={`Option ${index + 1}`}
                        />
                        {formData.options.length > 2 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveOption(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <svg
                              className="w-5 h-5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={handleAddOption}
                      className="mt-2 text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      + Add Option
                    </button>
                  </div>
                )}
                {/* Rating Scale Config */}
                {formData.question_type === 'rating_scale' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label
                        htmlFor="min_value"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Minimum Value
                      </label>
                      <input
                        type="number"
                        id="min_value"
                        value={formData.min_value}
                        onChange={(e) =>
                          setFormData({ ...formData, min_value: e.target.value })
                        }
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="max_value"
                        className="block text-sm font-medium text-gray-700"
                      >
                        Maximum Value
                      </label>
                      <input
                        type="number"
                        id="max_value"
                        value={formData.max_value}
                        onChange={(e) =>
                          setFormData({ ...formData, max_value: e.target.value })
                        }
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      />
                    </div>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label
                      htmlFor="order"
                      className="block text-sm font-medium text-gray-700"
                    >
                      Order
                    </label>
                    <input
                      type="number"
                      id="order"
                      value={formData.order}
                      onChange={(e) =>
                        setFormData({ ...formData, order: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div className="flex items-center">
                    <input
                      id="is_required"
                      type="checkbox"
                      checked={formData.is_required}
                      onChange={(e) =>
                        setFormData({ ...formData, is_required: e.target.checked })
                      }
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <label
                      htmlFor="is_required"
                      className="ml-2 block text-sm text-gray-900"
                    >
                      Required question
                    </label>
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
                        Adding...
                      </>
                    ) : (
                      'Add Question'
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
export default AddQuestionModal;
