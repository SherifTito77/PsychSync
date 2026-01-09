/**
 * Wellbeing Question Card Component
 *
 * Displays a single wellbeing question with response options.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { WellbeingQuestion } from '../types';

interface QuestionCardProps {
  question: WellbeingQuestion;
  selectedAnswer: string | undefined;
  onResponseChange: (answer: string) => void;
  questionNumber: number;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  selectedAnswer,
  onResponseChange,
  questionNumber,
}) => {
  return (
    <Card className="w-full max-w-3xl mx-auto mb-6">
      <CardHeader>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">Question {questionNumber}</span>
          <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
            {question.category}
          </span>
        </div>
        <CardTitle className="text-xl">{question.text}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {question.options.map((option) => (
            <label
              key={option}
              className={`
                flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all
                ${
                  selectedAnswer === option
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <input
                type="radio"
                name={question.id}
                value={option}
                checked={selectedAnswer === option}
                onChange={(e) => onResponseChange(e.target.value)}
                className="mr-3"
              />
              <span className="flex-1">{option}</span>
            </label>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
