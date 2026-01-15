/**
 * Wellbeing Category Progress Component
 *
 * Displays progress through the assessment by category.
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface CategoryProgressProps {
  currentCategoryIndex: number;
  currentGroupIndex: number;
  totalCategories: number;
  categoryName: string;
}

export const CategoryProgress: React.FC<CategoryProgressProps> = ({
  currentCategoryIndex,
  currentGroupIndex,
  totalCategories,
  categoryName,
}) => {
  const categoryProgress = ((currentCategoryIndex + 1) / totalCategories) * 100;

  return (
    <Card className="w-full max-w-3xl mx-auto mb-6">
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">
              Category: {categoryName}
            </span>
            <span className="text-sm text-gray-500">
              {currentCategoryIndex + 1} of {totalCategories} categories
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-purple-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${categoryProgress}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 text-center">
            Question group {currentGroupIndex + 1}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
