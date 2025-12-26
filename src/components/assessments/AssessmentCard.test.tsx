import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AssessmentCard } from '@/components/assessments/AssessmentCard';

describe('AssessmentCard Component', () => {
  const mockAssessment = {
    id: '1',
    title: 'MBTI Assessment',
    description: 'Discover your personality type',
    duration: 15,
    questions: 90
  };

  it('renders assessment information correctly', () => {
    render(<AssessmentCard assessment={mockAssessment} />);

    expect(screen.getByText('MBTI Assessment')).toBeInTheDocument();
    expect(screen.getByText('Discover your personality type')).toBeInTheDocument();
    expect(screen.getByText('15 minutes')).toBeInTheDocument();
    expect(screen.getByText('90 questions')).toBeInTheDocument();
  });

  it('shows start assessment button', () => {
    render(<AssessmentCard assessment={mockAssessment} />);
    expect(screen.getByRole('button', { name: /start assessment/i })).toBeInTheDocument();
  });
});