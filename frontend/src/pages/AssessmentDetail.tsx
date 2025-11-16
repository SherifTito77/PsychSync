// frontend/src/pages/AssessmentDetail.tsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  assessmentService,
  AssessmentWithSections,
} from '../services/assessmentService';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import EditAssessmentModal from '../components/assessments/EditAssessmentModal';
import AddSectionModal from '../components/assessments/AddSectionModal';
import AddQuestionModal from '../components/assessments/AddQuestionModal';
const AssessmentDetail: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assessment, setAssessment] = useState<AssessmentWithSections | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddSection, setShowAddSection] = useState(false);
  const [showAddQuestion, setShowAddQuestion] = useState<number | null>(null);
  const [error, setError] = useState('');
  const isOwner = String(assessment?.created_by_id) === String(user?.id);
  const canEdit = isOwner; // Add team admin check later
  useEffect(() => {
    loadAssessment();
  }, [assessmentId]);
  const loadAssessment = async () => {
    if (!assessmentId) return;
    setIsLoading(true);
    setError('');
    try {
      const data = await assessmentService.getAssessment(parseInt(assessmentId));
      setAssessment(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load assessment');
    } finally {
      setIsLoading(false);
    }
  };
  const handlePublish = async () => {
    if (!assessmentId || !assessment) return;
    if (assessment.sections.length === 0) {
      alert('Please add at least one section with questions before publishing.');
      return;
    }
    const hasQuestions = assessment.sections.some((s) => s.questions.length > 0);
    if (!hasQuestions) {
      alert('Please add at least one question before publishing.');
      return;
    }
    if (!confirm('Are you sure you want to publish this assessment?')) {
      return;
    }
    try {
      await assessmentService.publishAssessment(parseInt(assessmentId));
      loadAssessment();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to publish assessment');
    }
  };
  const handleArchive = async () => {
    if (!assessmentId || !assessment) return;
    if (!confirm('Are you sure you want to archive this assessment?')) {
      return;
    }
    try {
      await assessmentService.archiveAssessment(parseInt(assessmentId));
      loadAssessment();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to archive assessment');
    }
  };
  const handleDuplicate = async () => {
    if (!assessmentId) return;
    try {
      const duplicated = await assessmentService.duplicateAssessment(
        parseInt(assessmentId)
      );
      navigate(`/assessments/${duplicated.id}`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to duplicate assessment');
    }
  };
  const handleDelete = async () => {
    if (!assessmentId || !assessment) return;
    if (
      !confirm(
        `Are you sure you want to delete "${assessment.title}"? This action cannot be undone.`
      )
    ) {
      return;
    }
    try {
      await assessmentService.deleteAssessment(parseInt(assessmentId));
      navigate('/assessments');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete assessment');
    }
  };
  const handleDeleteSection = async (sectionId: number) => {
    if (!assessmentId) return;
    if (!confirm('Are you sure you want to delete this section?')) {
      return;
    }
    try {
      await assessmentService.deleteSection(parseInt(assessmentId), sectionId);
      loadAssessment();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete section');
    }
  };
  const handleDeleteQuestion = async (questionId: number) => {
    if (!assessmentId) return;
    if (!confirm('Are you sure you want to delete this question?')) {
      return;
    }
    try {
      await assessmentService.deleteQuestion(parseInt(assessmentId), questionId);
      loadAssessment();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete question');
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      case 'archived':
        return 'bg-gray-100 text-gray-800';
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
  if (error || !assessment) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-800">{error || 'Assessment not found'}</p>
        <Link to="/assessments" className="mt-2 text-sm text-red-600 hover:text-red-500">
          ← Back to assessments
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
            to="/assessments"
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
            Back to assessments
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-gray-900">{assessment.title}</h1>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                assessment.status
              )}`}
            >
              {assessment.status}
            </span>
          </div>
          {assessment.description && (
            <p className="mt-2 text-sm text-gray-500">{assessment.description}</p>
          )}
        </div>
        {/* Actions */}
        {assessment.status === 'active' && !canEdit && (
          <Link
            to={`/assessments/${assessment.id}/take`}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700"
          >``
            Take Assessment
          </Link>
        )}  
        {canEdit && assessment.status === 'active' && (
          <Link
            to={`/assessments/${assessment.id}/analytics`}
            className="px-4 py-2 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700"
          >
            View Analytics
          </Link>
        )}      
        {canEdit && (
          <div className="flex space-x-2">
            <button
              onClick={() => setShowEditModal(true)}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Edit Details
            </button>
            {assessment.status === 'draft' && (
              <button
                onClick={handlePublish}
                className="px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700"
              >
                Publish
              </button>
            )}
            {assessment.status === 'active' && (
              <button
                onClick={handleArchive}
                className="px-4 py-2 bg-gray-600 text-white rounded-md text-sm font-medium hover:bg-gray-700"
              >
                Archive
              </button>
            )}
            <button
              onClick={handleDuplicate}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700"
            >
              Duplicate
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700"
            >
              Delete
            </button>
          </div>
        )}
      </div>
      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
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
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Sections
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {assessment.sections.length}
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
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Questions
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {assessment.question_count}
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
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Duration
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {assessment.estimated_duration
                      ? `${assessment.estimated_duration} min`
                      : 'N/A'}
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
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Category
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 capitalize">
                    {assessment.category}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Sections and Questions */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Sections & Questions
          </h3>
          {canEdit && assessment.status === 'draft' && (
            <button
              onClick={() => setShowAddSection(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700"
            >
              Add Section
            </button>
          )}
        </div>
        {assessment.sections.length === 0 ? (
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No sections</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by adding a section to your assessment.
            </p>
            {canEdit && assessment.status === 'draft' && (
              <div className="mt-6">
                <button
                  onClick={() => setShowAddSection(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  Add Section
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {assessment.sections.map((section, sectionIndex) => (
              <div key={section.id} className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-medium text-gray-900">
                      {sectionIndex + 1}. {section.title}
                    </h4>
                    {section.description && (
                      <p className="mt-1 text-sm text-gray-500">{section.description}</p>
                    )}
                  </div>
                  {canEdit && assessment.status === 'draft' && (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setShowAddQuestion(section.id)}
                        className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded text-sm hover:bg-indigo-200"
                      >
                        Add Question
                      </button>
                      <button
                        onClick={() => handleDeleteSection(section.id)}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
                      >
                        Delete Section
                      </button>
                    </div>
                  )}
                </div>
                {section.questions.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No questions in this section</p>
                ) : (
                  <div className="space-y-4 ml-4">
                    {section.questions.map((question, questionIndex) => (
                      <div
                        key={question.id}
                        className="border-l-2 border-gray-300 pl-4"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">
                              {sectionIndex + 1}.{questionIndex + 1}.{' '}
                              {question.question_text}
                              {question.is_required && (
                                <span className="text-red-500 ml-1">*</span>
                              )}
                            </p>
                            {question.help_text && (
                              <p className="mt-1 text-xs text-gray-500">
                                {question.help_text}
                              </p>
                            )}
                            <p className="mt-1 text-xs text-gray-400 capitalize">
                              Type: {question.question_type.replace('_', ' ')}
                            </p>
                          </div>
                          {canEdit && assessment.status === 'draft' && (
                            <button
                              onClick={() => handleDeleteQuestion(question.id)}
                              className="ml-4 text-red-600 hover:text-red-800 text-sm"
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      {/* Modals */}
      {showEditModal && (
        <EditAssessmentModal
          assessment={assessment}
          onClose={() => setShowEditModal(false)}
          onSuccess={loadAssessment}
        />
      )}
      {showAddSection && assessmentId && (
        <AddSectionModal
          assessmentId={parseInt(assessmentId)}
          onClose={() => setShowAddSection(false)}
          onSuccess={loadAssessment}
        />
      )}
      {showAddQuestion && assessmentId && (
        <AddQuestionModal
          assessmentId={parseInt(assessmentId)}
          sectionId={showAddQuestion}
          onClose={() => setShowAddQuestion(null)}
          onSuccess={loadAssessment}
        />
      )}
    </div>
  );
};
export default AssessmentDetail;
