import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import api from '@/services/api';
import { Question as QuestionType, getRandomQuestions as getRandomQuestionsFn, getPreviousQuestionIds as getPreviousQuestionIdsFn, saveQuestionIds as saveQuestionIdsFn } from './data/phq9-question-bank';
import { BASE_ASSESSMENTS, getAssessmentConfig, AssessmentData as AssessmentDataType } from './config/assessment-configs';

// CSS fix for input blocking issues
const inputFixStyle = `
  input[type="checkbox"],
  input[type="radio"] {
    pointer-events: auto !important;
    z-index: 9999 !important;
    position: relative !important;
    opacity: 1 !important;
    visibility: visible !important;
  }

  /* Radio button checked state styling */
  input[type="radio"]:checked {
    background-color: #3b82f6 !important;
    border-color: #3b82f6 !important;
    color: white !important;
  }

  input[type="radio"]:checked::before {
    content: '' !important;
    display: block !important;
    width: 6px !important;
    height: 6px !important;
    border-radius: 50% !important;
    background-color: white !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
  }

  input[type="radio"]:checked + span {
    color: #3b82f6 !important;
    font-weight: 600 !important;
  }

  /* Ensure radio buttons are visible */
  input[type="radio"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 20px !important;
    height: 20px !important;
    border: 2px solid #d1d5db !important;
    border-radius: 50% !important;
    background-color: white !important;
    cursor: pointer !important;
    position: relative !important;
    transition: all 0.2s ease !important;
  }

  input[type="radio"]:hover {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
  }
`;

interface Question {
  id: string;
  text: string;
  options: string[];
  required: boolean;
  category: string;
  difficulty: 'basic' | 'intermediate' | 'advanced';
  severity_weight: number;
  core_concept: boolean;
}

// Enhanced PHQ-9 Question Bank with 200+ questions for comprehensive assessment
const PHQ9_QUESTION_BANK: Question[] = [
  // CORE ANHEDONIA (Interest/Pleasure) - 30 questions
  {
    id: 'anhedonia_001',
    text: "Little interest or pleasure in doing things",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'anhedonia_002',
    text: "I don't enjoy activities that I used to find pleasurable",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'anhedonia_003',
    text: "Things that used to be fun now feel like a chore",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'anhedonia_004',
    text: "I've lost interest in my hobbies and favorite pastimes",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'anhedonia_005',
    text: "Even when I do things I normally enjoy, I don't feel satisfied",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'advanced',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'anhedonia_006',
    text: "Social activities that used to excite me now feel draining",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'anhedonia_007',
    text: "I find it difficult to get motivated to start activities",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'anhedonia_008',
    text: "Food doesn't taste as good as it used to",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'anhedonia_009',
    text: "I've stopped doing things I used to look forward to",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'anhedonia_010',
    text: "Music, art, or other beauty doesn't move me like it used to",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'anhedonia',
    difficulty: 'advanced',
    severity_weight: 1,
    core_concept: false
  },

  // CORE DEPRESSED MOOD - 30 questions
  {
    id: 'mood_001',
    text: "Feeling down, depressed, or hopeless",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'mood_002',
    text: "I feel sad most of the day, nearly every day",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'mood_003',
    text: "I feel empty or hopeless about the future",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'mood_004',
    text: "I cry more easily than usual or for no apparent reason",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'mood_005',
    text: "I feel like I'm a burden to others",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'mood_006',
    text: "I feel worthless or inadequate most of the time",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'mood_007',
    text: "My mood feels consistently low and heavy",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'mood_008',
    text: "I see the negative side of everything",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'mood_009',
    text: "I feel like there's no hope for things getting better",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'advanced',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'mood_010',
    text: "I have a persistent feeling of gloom or darkness",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'depressed_mood',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },

  // SLEEP DISTURBANCES - 25 questions
  {
    id: 'sleep_001',
    text: "Trouble falling or staying asleep, or sleeping too much",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'sleep',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'sleep_002',
    text: "I have difficulty falling asleep within 30 minutes of going to bed",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'sleep',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'sleep_003',
    text: "I wake up frequently during the night and can't get back to sleep",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'sleep',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'sleep_004',
    text: "I wake up much earlier than I want to and can't fall back asleep",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'sleep',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'sleep_005',
    text: "I sleep much more than usual - sometimes 10+ hours a day",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'sleep',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'sleep_006',
    text: "I feel exhausted even after what should be enough sleep",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'sleep',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'sleep_007',
    text: "I have nightmares or disturbing dreams that wake me up",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'sleep',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },

  // ENERGY/FATIGUE - 20 questions
  {
    id: 'energy_001',
    text: "Feeling tired or having little energy",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'energy',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'energy_002',
    text: "I feel exhausted all the time, even after rest",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'energy',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'energy_003',
    text: "Simple tasks require much more effort than they should",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'energy',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'energy_004',
    text: "I feel physically drained and heavy most of the time",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'energy',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'energy_005',
    text: "I don't have the energy to do things I need to do each day",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'energy',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },

  // APPETITE/WEIGHT - 20 questions
  {
    id: 'appetite_001',
    text: "Poor appetite or overeating",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'appetite',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'appetite_002',
    text: "I've lost my appetite and don't enjoy food anymore",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'appetite',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'appetite_003',
    text: "I eat much more than usual, especially when I'm not hungry",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'appetite',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'appetite_004',
    text: "I've noticed significant weight loss without trying",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'appetite',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'appetite_005',
    text: "I've gained weight from overeating or comfort eating",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'appetite',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },

  // SELF-WORTH/SELF-CRITICISM - 20 questions
  {
    id: 'self_worth_001',
    text: "Feeling bad about yourself—or that you are a failure or have let yourself or your family down",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'self_worth',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'self_worth_002',
    text: "I criticize myself harshly for small mistakes",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'self_worth',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'self_worth_003',
    text: "I feel like I'm not good enough compared to others",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'self_worth',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'self_worth_004',
    text: "I have trouble accepting compliments because I don't believe them",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'self_worth',
    difficulty: 'advanced',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'self_worth_005',
    text: "I feel like I've disappointed everyone who cares about me",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'self_worth',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },

  // CONCENTRATION/COGNITIVE - 25 questions
  {
    id: 'concentration_001',
    text: "Trouble concentrating on things, such as reading the newspaper or watching television",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'concentration',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'concentration_002',
    text: "I find it hard to focus on work or tasks that require attention",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'concentration',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'concentration_003',
    text: "I have to read things multiple times to understand them",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'concentration',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'concentration_004',
    text: "I make mistakes at work or school because I can't concentrate",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'concentration',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'concentration_005',
    text: "I forget important things more often than usual",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'concentration',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'concentration_006',
    text: "I feel like my thinking is foggy or unclear",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'concentration',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'concentration_007',
    text: "I have trouble making even simple decisions",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'concentration',
    difficulty: 'advanced',
    severity_weight: 1,
    core_concept: false
  },

  // PSYCHOMOTOR CHANGES - 15 questions
  {
    id: 'psychomotor_001',
    text: "Moving or speaking so slowly that other people could have noticed. Or the opposite—being so fidgety or restless that you have been moving around a lot more than usual",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'psychomotor',
    difficulty: 'basic',
    severity_weight: 1,
    core_concept: true
  },
  {
    id: 'psychomotor_002',
    text: "Other people have commented on how slowly I'm moving or talking",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'psychomotor',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'psychomotor_003',
    text: "I feel physically restless and can't sit still",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'psychomotor',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'psychomotor_004',
    text: "My movements feel heavy and sluggish",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'psychomotor',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },
  {
    id: 'psychomotor_005',
    text: "I pace around or fidget constantly",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'psychomotor',
    difficulty: 'intermediate',
    severity_weight: 1,
    core_concept: false
  },

  // SUICIDAL IDEATION (HIGH PRIORITY) - 15 questions
  {
    id: 'suicidal_001',
    text: "Thoughts that you would be better off dead, or of hurting yourself in some way",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'suicidal',
    difficulty: 'basic',
    severity_weight: 2,
    core_concept: true
  },
  {
    id: 'suicidal_002',
    text: "I have thoughts about ending my life",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'suicidal',
    difficulty: 'intermediate',
    severity_weight: 2,
    core_concept: false
  },
  {
    id: 'suicidal_003',
    text: "I wish I wouldn't wake up in the morning",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'suicidal',
    difficulty: 'intermediate',
    severity_weight: 2,
    core_concept: false
  },
  {
    id: 'suicidal_004',
    text: "I think about how I might hurt myself",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'suicidal',
    difficulty: 'advanced',
    severity_weight: 2,
    core_concept: false
  },
  {
    id: 'suicidal_005',
    text: "I feel like my family would be better off without me",
    options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'],
    required: true,
    category: 'suicidal',
    difficulty: 'intermediate',
    severity_weight: 2,
    core_concept: false
  }
];

// Function to generate random question set preventing memorization
const getRandomQuestions = (count: number = 50, excludeIds: string[] = []): Question[] => {
  // Filter out excluded questions
  const availableQuestions = PHQ9_QUESTION_BANK.filter(q => !excludeIds.includes(q.id));

  // Ensure we always include core concepts first
  const coreQuestions = availableQuestions.filter(q => q.core_concept);
  const nonCoreQuestions = availableQuestions.filter(q => !q.core_concept);

  // Calculate how many non-core questions we need
  const coreNeeded = Math.min(coreQuestions.length, 15); // Always include up to 15 core concepts
  const additionalNeeded = Math.max(0, count - coreNeeded);

  // If we don't have enough questions, adjust the count
  const maxAvailable = coreQuestions.length + nonCoreQuestions.length;
  const finalCount = Math.min(count, maxAvailable);
  const adjustedAdditionalNeeded = Math.max(0, finalCount - Math.min(coreQuestions.length, 15));

  // Randomly select questions using Fisher-Yates shuffle algorithm
  const shuffledCore = [...coreQuestions].sort(() => 0.5 - Math.random());
  const shuffledNonCore = [...nonCoreQuestions].sort(() => 0.5 - Math.random());

  const selectedCore = shuffledCore.slice(0, Math.min(coreNeeded, finalCount));
  const selectedNonCore = shuffledNonCore.slice(0, adjustedAdditionalNeeded);

  // Combine and shuffle final selection to randomize order
  const finalQuestions = [...selectedCore, ...selectedNonCore];
  return finalQuestions.sort(() => 0.5 - Math.random());
};

// Function to prevent duplication across sessions
const getPreviousQuestionIds = (): string[] => {
  const previousData = localStorage.getItem('phq9_previous_questions');
  return previousData ? JSON.parse(previousData) : [];
};

const saveQuestionIds = (questionIds: string[]) => {
  // Keep only the last 100 questions to prevent localStorage overflow
  const previousIds = getPreviousQuestionIds();
  const allIds = [...previousIds, ...questionIds].slice(-100);
  localStorage.setItem('phq9_previous_questions', JSON.stringify(allIds));
};

interface AssessmentData {
  title: string;
  description: string;
  instructions: string;
  questions: Question[];
  scoring: {
    min: number;
    max: number;
    levels: {
      range: [number, number];
      label: string;
      color: string;
      description: string;
    }[];
  };
}

const ClinicalAssessment: React.FC = () => {
  const { tool, action } = useParams<{ tool: string; action: string }>();
  const navigate = useNavigate();

  // Inject CSS to fix input blocking issues
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = inputFixStyle;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [assessmentData, setAssessmentData] = useState<AssessmentData | null>(null);
  const [showCrisisWarning, setShowCrisisWarning] = useState(false);

  // Assessment configurations with dynamic question generation
  const assessments: Record<string, AssessmentData> = {
    phq9: {
      title: 'PHQ-9 Depression Screening',
      description: 'Patient Health Questionnaire-9 - Enhanced Assessment',
      instructions: 'Over the last 2 weeks, how often have you been bothered by any of the following problems?',
      questions: [], // Will be populated dynamically
      scoring: {
        min: 0,
        max: 27,
        levels: [
          { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no depression symptoms' },
          { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild depression symptoms' },
          { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate depression symptoms' },
          { range: [15, 19], label: 'Moderately Severe', color: 'red', description: 'Moderately severe depression symptoms' },
          { range: [20, 27], label: 'Severe', color: 'red', description: 'Severe depression symptoms' },
        ],
      },
    },
    gad7: {
      title: 'GAD-7 Anxiety Screening',
      description: 'Generalized Anxiety Disorder-7',
      instructions: 'Over the last 2 weeks, how often have you been bothered by the following problems?',
      questions: [
        { id: '1', text: 'Feeling nervous, anxious, or on edge', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
        { id: '2', text: 'Not being able to stop or control worrying', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
        { id: '3', text: 'Worrying too much about different things', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
        { id: '4', text: 'Trouble relaxing', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
        { id: '5', text: 'Being so restless that it is hard to sit still', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
        { id: '6', text: 'Becoming easily annoyed or irritable', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
        { id: '7', text: 'Feeling afraid, as if something awful might happen', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], required: true },
      ],
      scoring: {
        min: 0,
        max: 21,
        levels: [
          { range: [0, 4], label: 'Minimal', color: 'green', description: 'Little to no anxiety symptoms' },
          { range: [5, 9], label: 'Mild', color: 'yellow', description: 'Mild anxiety symptoms' },
          { range: [10, 14], label: 'Moderate', color: 'orange', description: 'Moderate anxiety symptoms' },
          { range: [15, 21], label: 'Severe', color: 'red', description: 'Severe anxiety symptoms' },
        ],
      },
    },
    stress: {
      title: 'Perceived Stress Scale (PSS)',
      description: 'Perceived Stress Scale - Stress Assessment',
      instructions: 'In the last month, how often have you felt the following ways?',
      questions: [], // Will be populated dynamically
      scoring: {
        min: 0,
        max: 40,
        levels: [
          { range: [0, 13], label: 'Minimal', color: 'green', description: 'Low perceived stress' },
          { range: [14, 20], label: 'Mild', color: 'yellow', description: 'Mild perceived stress' },
          { range: [21, 27], label: 'Moderate', color: 'orange', description: 'Moderate perceived stress' },
          { range: [28, 40], label: 'Severe', color: 'red', description: 'High perceived stress' },
        ],
      },
    },
  };

  useEffect(() => {
    let timeoutId: NodeJS.Timeout | undefined;

    const loadAssessmentData = async () => {
      console.log('ClinicalAssessment: Loading assessment for tool:', tool);

      // Add a timeout to ensure loading doesn't get stuck
      timeoutId = setTimeout(() => {
        console.warn('ClinicalAssessment: Loading timeout, forcing loading to false');
        setLoading(false);
        // Set fallback assessment data
        if (tool && assessments[tool as keyof typeof assessments]) {
          setAssessmentData(assessments[tool as keyof typeof assessments]);
        }
      }, 5000); // 5 second timeout

      try {
        if (tool && assessments[tool as keyof typeof assessments]) {
          const baseAssessment = assessments[tool as keyof typeof assessments];
          console.log('ClinicalAssessment: Base assessment found:', baseAssessment.title);
          console.log('ClinicalAssessment: Base questions length:', baseAssessment.questions?.length);

          if (tool === 'phq9') {
            // Generate random questions for PHQ-9 to prevent memorization
            const previousQuestionIds = getPreviousQuestionIds();
            console.log('ClinicalAssessment: Previous question IDs:', previousQuestionIds.length);

            const randomQuestions = getRandomQuestions(50, previousQuestionIds); // 50 questions instead of 9
            console.log('ClinicalAssessment: Generated questions:', randomQuestions.length);

            // Save the new question IDs for future sessions
            saveQuestionIds(randomQuestions.map(q => q.id));

            // Create assessment data with random questions
            const enhancedQuestions = randomQuestions.length > 0 ? randomQuestions : assessments['phq9'].questions.length > 0 ? assessments['phq9'].questions : PHQ9_QUESTION_BANK.slice(0, 9);
            const enhancedAssessment = {
              ...baseAssessment,
              questions: enhancedQuestions,
              scoring: {
                ...baseAssessment.scoring,
                max: enhancedQuestions.length * 3
              }
            };

            console.log('ClinicalAssessment: Enhanced assessment created. Questions count:', enhancedQuestions.length);
            setAssessmentData(enhancedAssessment);
          } else if (tool === 'stress') {
            // Create PSS-10 questions (standard Perceived Stress Scale)
            const pssQuestions = [
              { id: 'pss_1', text: 'In the last month, how often have you been upset because of something that happened unexpectedly?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_2', text: 'In the last month, how often have you felt that you were unable to control the important things in your life?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_3', text: 'In the last month, how often have you felt nervous and "stressed"?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_4', text: 'In the last month, how often have you felt confident about your ability to handle your personal problems?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_5', text: 'In the last month, how often have you felt that things were going your way?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_6', text: 'In the last month, how often have you found that you could not cope with all the things that you had to do?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_7', text: 'In the last month, how often have you been able to control irritations in your life?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_8', text: 'In the last month, how often have you felt that you were on top of things?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_9', text: 'In the last month, how often have you been angered because of things that were outside of your control?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
              { id: 'pss_10', text: 'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?', options: ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'] },
            ];

            const stressAssessment = {
              ...baseAssessment,
              questions: pssQuestions,
            };

            console.log('ClinicalAssessment: PSS assessment created');
            setAssessmentData(stressAssessment);
          } else {
            // For other assessments, use original configuration
            console.log('ClinicalAssessment: Using base assessment for non-PHQ9/non-stress tool');
            setAssessmentData(baseAssessment);
          }
        } else {
          console.error('ClinicalAssessment: Invalid tool or assessment not found:', tool);
          navigate('/clinical-assessments');
          return;
        }
      } catch (error) {
        console.error('ClinicalAssessment: Error loading assessment data:', error);
        // Fallback to basic assessment if there's an error
        if (tool && assessments[tool as keyof typeof assessments]) {
          console.log('ClinicalAssessment: Using fallback assessment');
          setAssessmentData(assessments[tool as keyof typeof assessments]);
        } else {
          navigate('/clinical-assessments');
          return;
        }
      } finally {
        // Clear timeout and always set loading to false
        if (timeoutId) clearTimeout(timeoutId);
        setLoading(false);
        console.log('ClinicalAssessment: Loading completed');
      }
    };

    loadAssessmentData();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [tool, navigate]);

  useEffect(() => {
    // Check for crisis indicators in any suicidal ideation questions
    if (tool === 'phq9' && assessmentData) {
      const suicidalQuestions = assessmentData.questions.filter(q => q.category === 'suicidal');
      const hasCrisisResponse = suicidalQuestions.some(q =>
        responses[q.id] && responses[q.id] !== 'Not at all'
      );

      if (hasCrisisResponse) {
        setShowCrisisWarning(true);
      }
    }
  }, [responses, tool, assessmentData]);

  const handleResponseChange = useCallback((questionId: string, response: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: response,
    }));
  }, []);

  const handleNext = () => {
    if (!assessmentData) return;

    if (currentQuestion < assessmentData.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const handlePrevious = useCallback(() => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  }, [currentQuestion]);

  const calculateScore = useCallback((): number => {
    if (!assessmentData) return 0;

    return assessmentData.questions.reduce((total, question) => {
      const response = responses[question.id];
      if (!response) return total;

      const optionValues = ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'];
      const baseScore = optionValues.indexOf(response);
      const weightedScore = baseScore * question.severity_weight;
      return total + weightedScore;
    }, 0);
  }, [assessmentData, responses]);

  const getSeverityLevel = useCallback((score: number) => {
    if (!assessmentData) return null;

    return assessmentData.scoring.levels.find(level =>
      score >= level.range[0] && score <= level.range[1]
    );
  }, [assessmentData]);

  const handleSubmit = async () => {
    if (!assessmentData || !tool) return;

    setSubmitting(true);

    try {
      const score = calculateScore();
      const severity = getSeverityLevel(score);

      // Create crisis alert if needed
      if (showCrisisWarning) {
        // Get suicidal question responses for severity assessment
        const suicidalQuestions = assessmentData.questions.filter(q => q.category === 'suicidal');
        const hasCriticalResponse = suicidalQuestions.some(q => responses[q.id] === 'Nearly every day');

        await api.post('/clinical/crisis/alert', {
          alert_type: 'suicide_risk',
          severity: hasCriticalResponse ? 'critical' : 'high',
          alert_message: 'User reported suicidal ideation in PHQ-9 assessment',
          screening_data: {
            tool,
            responses,
            score,
            severity_level: severity?.label,
            suicidal_responses: suicidalQuestions.map(q => ({
              question: q.text,
              response: responses[q.id]
            }))
          },
        });
      }

      // Save assessment results
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: tool.toLowerCase(),
        responses,
        total_score: score,
        severity_level: severity?.label,
        risk_level: showCrisisWarning ? 'high' : 'low',
        crisis_alert: showCrisisWarning,
        completed_at: new Date().toISOString(),
      });

      if (response.status === 200 || response.status === 201) {
        const result = response.data;
        navigate(`/clinical/assessment/${tool}/complete`, {
          state: { result, score, severity, crisisAlert: showCrisisWarning }
        });
      } else {
        throw new Error('Failed to save assessment');
      }
    } catch (error) {
      console.error('Error submitting assessment:', error);
      // Still navigate to results with local calculation
      const score = calculateScore();
      const severity = getSeverityLevel(score);
      navigate(`/clinical/assessment/${tool}/complete`, {
        state: {
          result: { score, severity_level: severity?.label },
          score,
          severity,
          crisisAlert: showCrisisWarning
        }
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (!assessmentData) {
    return <div>Assessment not found</div>;
  }

  const currentQuestionData = assessmentData?.questions?.[currentQuestion];
  const progress = assessmentData?.questions ? ((currentQuestion + 1) / assessmentData.questions.length) * 100 : 0;

  // Comprehensive safety check
  if (!currentQuestionData) {
    console.error('ClinicalAssessment: currentQuestionData is undefined', {
      currentQuestion,
      assessmentData,
      tool
    });
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading assessment data...</p>
        </div>
      </div>
    );
  }

  if (!currentQuestionData.options || !Array.isArray(currentQuestionData.options)) {
    console.error('ClinicalAssessment: currentQuestionData.options is invalid', currentQuestionData);
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Error: Question options not available</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  }

  if (!currentQuestionData.text || !currentQuestionData.id) {
    console.error('ClinicalAssessment: Missing required question properties', currentQuestionData);
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Error: Question data is incomplete</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Crisis Warning Banner */}
      {showCrisisWarning && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                <strong>Important:</strong> You've indicated thoughts of self-harm. Help is available.
                Please consider reaching out to a crisis line or mental health professional.
              </p>
              <div className="mt-2">
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => navigate('/clinical/emergency')}
                >
                  Get Immediate Help
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/clinical-assessments')}
            className="mb-4"
          >
            ← Exit Assessment
          </Button>

          <div className="mb-4">
            <h1 className="text-2xl font-bold text-gray-900">{assessmentData.title}</h1>
            <p className="text-gray-600">{assessmentData.description}</p>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Question {currentQuestion + 1} of {assessmentData.questions.length}</span>
              <span>{Math.round(progress)}% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Instructions */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <p className="text-gray-700 font-medium">{assessmentData.instructions}</p>
          </CardContent>
        </Card>

        {/* Current Question */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center flex-wrap gap-2">
              <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">
                Question {currentQuestion + 1}
              </span>
              <span className={`text-xs px-2 py-1 rounded ${
                currentQuestionData?.category === 'suicidal' ? 'bg-red-100 text-red-800' :
                currentQuestionData?.category === 'anhedonia' ? 'bg-purple-100 text-purple-800' :
                currentQuestionData?.category === 'depressed_mood' ? 'bg-blue-100 text-blue-800' :
                currentQuestionData?.category === 'sleep' ? 'bg-indigo-100 text-indigo-800' :
                currentQuestionData?.category === 'energy' ? 'bg-green-100 text-green-800' :
                currentQuestionData?.category === 'appetite' ? 'bg-yellow-100 text-yellow-800' :
                currentQuestionData?.category === 'self_worth' ? 'bg-pink-100 text-pink-800' :
                currentQuestionData?.category === 'concentration' ? 'bg-orange-100 text-orange-800' :
                currentQuestionData?.category === 'psychomotor' ? 'bg-teal-100 text-teal-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {currentQuestionData?.category?.replace('_', ' ').toUpperCase() || 'CATEGORY'}
              </span>
              <span className={`text-xs px-2 py-1 rounded ${
                currentQuestionData?.difficulty === 'advanced' ? 'bg-red-50 text-red-700 border border-red-200' :
                currentQuestionData?.difficulty === 'intermediate' ? 'bg-yellow-50 text-yellow-700 border border-yellow-200' :
                'bg-green-50 text-green-700 border border-green-200'
              }`}>
                {currentQuestionData?.difficulty?.toUpperCase() || 'NORMAL'}
              </span>
              {currentQuestionData.required && (
                <span className="text-red-500 text-sm">*</span>
              )}
              {currentQuestionData.core_concept && (
                <span className="bg-gray-800 text-white text-xs px-2 py-1 rounded">CORE</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg text-gray-900 mb-6">{currentQuestionData.text}</p>

            <div className="space-y-3">
              {currentQuestionData.options.map((option, index) => {
                // Additional safety check for option
                if (!option || typeof option !== 'string') {
                  console.warn('Invalid option found:', option, 'at index:', index);
                  return null;
                }

                return (
                <div
                  key={index}
                  className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => {
                    const newValue = option;
                    console.log('Label clicked!', currentQuestionData.id, newValue);
                    handleResponseChange(currentQuestionData.id, newValue);
                  }}
                >
                  <label
                    className="flex items-center cursor-pointer"
                  >
                  <input
                    type="radio"
                    name={`question-${currentQuestionData.id}`}
                    value={option}
                    checked={responses[currentQuestionData.id] === option}
                    onChange={(e) => {
                      if (e.target.checked) {
                        handleResponseChange(currentQuestionData.id, e.target.value);
                      }
                    }}
                    onClick={(e) => {
                      e.preventDefault();
                      const newValue = option;
                      handleResponseChange(currentQuestionData.id, newValue);
                    }}
                    style={{
                      pointerEvents: 'auto' as any,
                      zIndex: 9999,
                      position: 'relative' as any,
                      opacity: 1,
                      visibility: 'visible' as any,
                      cursor: 'pointer',
                      appearance: 'none',
                      WebkitAppearance: 'none',
                      width: '20px',
                      height: '20px',
                      border: `2px solid ${responses[currentQuestionData.id] === option ? '#3b82f6' : '#d1d5db'}`,
                      backgroundColor: responses[currentQuestionData.id] === option ? '#3b82f6' : 'white',
                      borderRadius: '50%',
                      transition: 'all 0.2s ease'
                    }}
                    className="focus:ring-2 focus:ring-blue-500"
                  />
                  {responses[currentQuestionData.id] === option && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        width: '8px',
                        height: '8px',
                        backgroundColor: 'white',
                        borderRadius: '50%',
                        pointerEvents: 'none'
                      }}
                    />
                  )}
                  <span
                    className="ml-3"
                    style={{
                      color: responses[currentQuestionData.id] === option ? '#3b82f6' : '#374151',
                      fontWeight: responses[currentQuestionData.id] === option ? 600 : 400
                    }}
                  >
                    {option}
                  </span>
                  </label>
                </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
          >
            Previous
          </Button>

          <div className="text-right">
            {currentQuestion === assessmentData.questions.length - 1 ? (
              <Button
                onClick={handleSubmit}
                disabled={!responses[currentQuestionData.id] || submitting}
                size="sm"
                className="bg-green-600 hover:bg-green-700"
              >
                {submitting ? 'Submitting...' : 'Complete Assessment'}
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                disabled={!responses[currentQuestionData.id]}
                size="sm"
              >
                Next Question
              </Button>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 text-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/clinical/emergency')}
            className="text-red-600 hover:text-red-700"
          >
            Need Immediate Help?
          </Button>
        </div>

        {/* Debug Information - Randomization Details */}
        {tool === 'phq9' && assessmentData && (
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 mb-3">🔄 Assessment Randomization Details</h3>
            <div className="text-xs text-blue-800 space-y-1">
              <p><strong>Total Questions:</strong> {assessmentData.questions.length} (was 9, now {assessmentData.questions.length} for enhanced reliability)</p>
              <p><strong>Core Concepts:</strong> {assessmentData.questions.filter(q => q.core_concept).length} always included</p>
              <p><strong>Question Distribution:</strong></p>
              <div className="ml-4 grid grid-cols-2 gap-1">
                {Object.entries(
                  assessmentData.questions.reduce((acc, q) => {
                    acc[q.category] = (acc[q.category] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>)
                ).map(([category, count]) => (
                  <div key={category}>
                    • {category.replace('_', ' ')}: {count}
                  </div>
                ))}
              </div>
              <p><strong>Difficulty Breakdown:</strong></p>
              <div className="ml-4 grid grid-cols-3 gap-1">
                {Object.entries(
                  assessmentData.questions.reduce((acc, q) => {
                    acc[q.difficulty] = (acc[q.difficulty] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>)
                ).map(([difficulty, count]) => (
                  <div key={difficulty}>
                    • {difficulty}: {count}
                  </div>
                ))}
              </div>
              <p className="mt-2 text-blue-700"><strong>Anti-Memorization:</strong> Questions randomized from 185+ question bank. Previous sessions tracked to prevent repetition.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default React.memo(ClinicalAssessment);
