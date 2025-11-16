// frontend/src/components/assessments/QuestionRenderer.tsx
import React from 'react';
import { Question } from '../../services/assessmentService';
interface QuestionRendererProps {
  question: Question;
  questionNumber: string;
  value: any;
  onChange: (value: any) => void;
}
const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  question,
  questionNumber,
  value,
  onChange,
}) => {
  const renderQuestionInput = () => {
    switch (question.question_type) {
      case 'multiple_choice':
        return renderMultipleChoice();
      case 'rating_scale':
        return renderRatingScale();
      case 'text':
        return renderTextInput();
      case 'yes_no':
        return renderYesNo();
      case 'likert':
        return renderLikert();
      default:
        return <p className="text-sm text-gray-500">Unsupported question type</p>;
    }
  };
  const renderMultipleChoice = () => {
    const options = question.config?.options || [];
    return (
      <div className="space-y-2">
        {options.map((option: string, index: number) => (
          <label
            key={index}
            className="flex items-center p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
          >
            <input
              type="radio"
              name={`question-${question.id}`}
              value={option}
              checked={value === option}
              onChange={(e) => onChange(e.target.value)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
            />
            <span className="ml-3 text-sm text-gray-900">{option}</span>
          </label>
        ))}
      </div>
    );
  };
  const renderRatingScale = () => {
    const min = question.config?.min || 1;
    const max = question.config?.max || 5;
    const labels = question.config?.labels || {};
    const options = [];
    for (let i = min; i <= max; i++) {
      options.push(i);
    }
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          {options.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onChange(option)}
              className={`flex-1 mx-1 py-3 px-4 border-2 rounded-md text-center transition-colors ${
                value === option
                  ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="text-lg font-semibold">{option}</div>
              {labels[option] && (
                <div className="text-xs text-gray-500 mt-1">{labels[option]}</div>
              )}
            </button>
          ))}
        </div>
      </div>
    );
  };
  const renderTextInput = () => {
    return (
      <textarea
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        placeholder="Type your answer here..."
      />
    );
  };
  const renderYesNo = () => {
    return (
      <div className="flex space-x-4">
        <button
          type="button"
          onClick={() => onChange(true)}
          className={`flex-1 py-3 px-6 border-2 rounded-md text-center transition-colors ${
            value === true
              ? 'border-green-600 bg-green-50 text-green-700'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <span className="text-lg font-semibold">Yes</span>
        </button>
        <button
          type="button"
          onClick={() => onChange(false)}
          className={`flex-1 py-3 px-6 border-2 rounded-md text-center transition-colors ${
            value === false
              ? 'border-red-600 bg-red-50 text-red-700'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <span className="text-lg font-semibold">No</span>
        </button>
      </div>
    );
  };
  const renderLikert = () => {
    const labels = question.config?.labels || [
      'Strongly Disagree',
      'Disagree',
      'Neutral',
      'Agree',
      'Strongly Agree',
    ];
    return (
      <div className="space-y-2">
        {labels.map((label: string, index: number) => (
          <label
            key={index}
            className="flex items-center p-3 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
          >
            <input
              type="radio"
              name={`question-${question.id}`}
              value={index + 1}
              checked={value === index + 1}
              onChange={(e) => onChange(parseInt(e.target.value))}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
            />
            <span className="ml-3 text-sm text-gray-900">{label}</span>
          </label>
        ))}
      </div>
    );
  };
  return (
    <div className="border-b border-gray-200 pb-8 last:border-b-0">
      <div className="mb-4">
        <h3 className="text-base font-medium text-gray-900">
          {questionNumber}. {question.question_text}
          {question.is_required && <span className="text-red-500 ml-1">*</span>}
        </h3>
        {question.help_text && (
          <p className="mt-1 text-sm text-gray-500">{question.help_text}</p>
        )}
      </div>
      {renderQuestionInput()}
    </div>
  );
};
export default QuestionRenderer;
