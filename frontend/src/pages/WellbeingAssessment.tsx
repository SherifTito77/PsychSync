import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProgressChart } from '@/components/charts/ProgressChart';
import { useTheme } from '@/contexts/ThemeContext';
import {
  saveAssessmentResult,
  getAssessmentHistory,
  getPreviousAssessment,
  saveGoals,
  getGoals,
  updateActionProgress,
  getActionProgress,
  getCompletedActions,
  getStreak,
  clearAllWellbeingData,
  type StoredAssessmentResult,
  type WellbeingGoals,
  type WellnessStreak
} from '@/utils/wellnessStorage';
import { exportToPDF, exportToJSON } from '@/utils/exportUtils';

// Comprehensive Wellbeing Assessment Questions
const WELLBEING_QUESTIONS = [
  // Physical Wellbeing
  { id: 'wb_1', category: 'Physical', text: 'How would you rate your overall physical health?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_2', category: 'Physical', text: 'How often do you engage in physical exercise (30+ minutes)?', options: ['Daily', 'Several times a week', 'Once a week', 'Rarely/Never'] },
  { id: 'wb_3', category: 'Physical', text: 'How would you rate your sleep quality?', options: ['Very Good', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_4', category: 'Physical', text: 'How often do you feel rested after sleep?', options: ['Always', 'Usually', 'Sometimes', 'Rarely'] },
  { id: 'wb_5', category: 'Physical', text: 'How would you rate your energy levels throughout the day?', options: ['High Energy', 'Moderately High', 'Moderate', 'Low Energy'] },
  { id: 'wb_6', category: 'Physical', text: 'How would you rate your nutrition and eating habits?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_7', category: 'Physical', text: 'How often do you experience physical pain or discomfort?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_8', category: 'Physical', text: 'How consistent is your exercise routine?', options: ['Very Consistent', 'Mostly Consistent', 'Somewhat Consistent', 'Not Consistent'] },
  { id: 'wb_9', category: 'Physical', text: 'How many hours of sleep do you typically get per night?', options: ['8+ hours', '7-8 hours', '5-6 hours', 'Less than 5 hours'] },
  { id: 'wb_10', category: 'Physical', text: 'How often do you stay hydrated throughout the day?', options: ['Always', 'Usually', 'Sometimes', 'Rarely'] },

  // Mental/Emotional Wellbeing
  { id: 'wb_11', category: 'Emotional', text: 'How often do you feel positive and optimistic?', options: ['Always', 'Usually', 'Sometimes', 'Rarely'] },
  { id: 'wb_12', category: 'Emotional', text: 'How well are you able to cope with daily stressors?', options: ['Very Well', 'Well', 'Moderately', 'Poorly'] },
  { id: 'wb_13', category: 'Emotional', text: 'How often do you feel overwhelmed?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_14', category: 'Emotional', text: 'Do you feel you have someone to talk to when stressed?', options: ['Always', 'Usually', 'Sometimes', 'Never'] },
  { id: 'wb_15', category: 'Emotional', text: 'How would you rate your emotional stability?', options: ['Very Stable', 'Stable', 'Somewhat Stable', 'Unstable'] },
  { id: 'wb_16', category: 'Emotional', text: 'How often do you experience anxiety or excessive worry?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_17', category: 'Emotional', text: 'How would you rate your ability to bounce back from setbacks?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_18', category: 'Emotional', text: 'How often do you practice mindfulness or meditation?', options: ['Daily', 'Several times a week', 'Occasionally', 'Never'] },
  { id: 'wb_19', category: 'Emotional', text: 'How would you rate your self-esteem and self-worth?', options: ['Very High', 'High', 'Moderate', 'Low'] },
  { id: 'wb_20', category: 'Emotional', text: 'How often do you experience joy or happiness?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },

  // Social Wellbeing
  { id: 'wb_21', category: 'Social', text: 'How satisfied are you with your social connections?', options: ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied'] },
  { id: 'wb_22', category: 'Social', text: 'How often do you feel lonely?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_23', category: 'Social', text: 'Do you have people you can rely on for support?', options: ['Definitely Yes', 'Mostly Yes', 'Somewhat', 'No'] },
  { id: 'wb_24', category: 'Social', text: 'How would you rate your communication skills?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_25', category: 'Social', text: 'How comfortable are you in social situations?', options: ['Very Comfortable', 'Comfortable', 'Somewhat Comfortable', 'Uncomfortable'] },
  { id: 'wb_26', category: 'Social', text: 'How often do you engage in meaningful conversations?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_27', category: 'Social', text: 'How would you rate your ability to set healthy boundaries?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_28', category: 'Social', text: 'How connected do you feel to your community?', options: ['Very Connected', 'Connected', 'Somewhat Connected', 'Not Connected'] },

  // Work/Life Balance
  { id: 'wb_29', category: 'Work', text: 'How would you rate your work-life balance?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_30', category: 'Work', text: 'How often does work interfere with personal life?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_31', category: 'Work', text: 'Do you feel energized or drained after work?', options: ['Energized', 'Mostly Energized', 'Neutral', 'Drained'] },
  { id: 'wb_32', category: 'Work', text: 'How satisfied are you with your current work/role?', options: ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied'] },
  { id: 'wb_33', category: 'Work', text: 'How often do you bring work stress home?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_34', category: 'Work', text: 'How would you rate your ability to disconnect from work?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_35', category: 'Work', text: 'How often do you have time for hobbies outside work?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_36', category: 'Work', text: 'How would you rate your workplace relationships?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },

  // Meaning & Purpose
  { id: 'wb_37', category: 'Purpose', text: 'Do you feel your life has meaning and purpose?', options: ['Strongly Agree', 'Agree', 'Neutral', 'Disagree'] },
  { id: 'wb_38', category: 'Purpose', text: 'How often do you engage in activities you find meaningful?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_39', category: 'Purpose', text: 'How would you rate your sense of direction in life?', options: ['Very Clear', 'Clear', 'Somewhat Clear', 'Unclear'] },
  { id: 'wb_40', category: 'Purpose', text: 'Do you feel your values align with your actions?', options: ['Always', 'Usually', 'Sometimes', 'Rarely'] },
  { id: 'wb_41', category: 'Purpose', text: 'How often do you work toward personal goals?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_42', category: 'Purpose', text: 'How would you rate your personal growth and development?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },

  // Financial Wellbeing
  { id: 'wb_43', category: 'Financial', text: 'How often do you worry about finances?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_44', category: 'Financial', text: 'How would you rate your financial security?', options: ['Very Secure', 'Secure', 'Somewhat Secure', 'Insecure'] },
  { id: 'wb_45', category: 'Financial', text: 'How often do you save or invest for the future?', options: ['Monthly', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_46', category: 'Financial', text: 'How would you rate your ability to manage expenses?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_47', category: 'Financial', text: 'How comfortable are you with your current financial situation?', options: ['Very Comfortable', 'Comfortable', 'Somewhat Comfortable', 'Uncomfortable'] },
  { id: 'wb_48', category: 'Financial', text: 'Do you have an emergency fund or savings?', options: ['Yes, 6+ months', 'Yes, 3-6 months', 'Yes, less than 3 months', 'No'] },

  // Self-Care & Coping
  { id: 'wb_49', category: 'SelfCare', text: 'How often do you make time for self-care?', options: ['Daily', 'Several times a week', 'Once a week', 'Rarely'] },
  { id: 'wb_50', category: 'SelfCare', text: 'Do you practice relaxation techniques (meditation, mindfulness, etc.)?', options: ['Daily', 'Several times a week', 'Occasionally', 'Never'] },
  { id: 'wb_51', category: 'SelfCare', text: 'How would you rate your work-life boundaries?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_52', category: 'SelfCare', text: 'How often do you take breaks when needed?', options: ['Always', 'Usually', 'Sometimes', 'Rarely'] },
  { id: 'wb_53', category: 'SelfCare', text: 'How would you rate your stress management techniques?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_54', category: 'SelfCare', text: 'How often do you engage in hobbies or activities you enjoy?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
];

// Group questions by category
const QUESTIONS_BY_CATEGORY = WELLBEING_QUESTIONS.reduce((acc, question) => {
  if (!acc[question.category]) {
    acc[question.category] = [];
  }
  acc[question.category].push(question);
  return acc;
}, {} as Record<string, typeof WELLBEING_QUESTIONS>);

const CATEGORIES = Object.keys(QUESTIONS_BY_CATEGORY);
const QUESTIONS_PER_GROUP = 3; // Show 3 questions at a time

const WellbeingAssessment: React.FC = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [currentCategoryIndex, setCurrentCategoryIndex] = useState(0);
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [showResults, setShowResults] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  // New state for enhanced features
  const [scoreFilter, setScoreFilter] = useState<'all' | 'low' | 'medium' | 'high'>('all');
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [selectedGoalCategory, setSelectedGoalCategory] = useState<string | null>(null);
  const [assessmentHistory, setAssessmentHistory] = useState<StoredAssessmentResult[]>([]);
  const [previousResult, setPreviousResult] = useState<StoredAssessmentResult | null>(null);
  const [streak, setStreak] = useState<WellnessStreak>(getStreak());
  const [goals, setGoals] = useState<WellbeingGoals[]>(getGoals());
  const [actionProgress, setActionProgress] = useState<Record<string, boolean>>({});
  const [showConfetti, setShowConfetti] = useState(false);

  // Load data on mount
  useEffect(() => {
    setAssessmentHistory(getAssessmentHistory());
    setPreviousResult(getPreviousAssessment());
    setStreak(getStreak());

    // Load action progress
    const progress = getActionProgress();
    const progressMap: Record<string, boolean> = {};
    Object.values(progress).forEach(p => {
      progressMap[`${p.category}-${p.actionIndex}`] = p.completed;
    });
    setActionProgress(progressMap);
  }, []);

  // Save result when assessment is completed
  useEffect(() => {
    if (showResults) {
      const { categoryScores, overallPercentage } = calculateScores();
      const result = {
        id: `${Date.now()}`,
        date: new Date().toISOString(),
        overallPercentage,
        categoryScores,
        responses
      };

      saveAssessmentResult(result);
      setAssessmentHistory(getAssessmentHistory());
      setPreviousResult(getPreviousAssessment());
      setStreak(getStreak());
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 3000);
    }
  }, [showResults]);

  const currentCategory = CATEGORIES[currentCategoryIndex];
  const categoryQuestions = QUESTIONS_BY_CATEGORY[currentCategory] || [];

  // Calculate total groups across all categories
  const getTotalGroups = () => {
    return CATEGORIES.reduce((total, cat) => {
      const questionCount = QUESTIONS_BY_CATEGORY[cat].length;
      return total + Math.ceil(questionCount / QUESTIONS_PER_GROUP);
    }, 0);
  };

  // Get current group of questions
  const getCurrentQuestionGroup = () => {
    const startIndex = currentGroupIndex * QUESTIONS_PER_GROUP;
    return categoryQuestions.slice(startIndex, startIndex + QUESTIONS_PER_GROUP);
  };

  // Calculate overall progress
  const getProgress = () => {
    let completedGroups = 0;
    for (let i = 0; i < currentCategoryIndex; i++) {
      completedGroups += Math.ceil(QUESTIONS_BY_CATEGORY[CATEGORIES[i]].length / QUESTIONS_PER_GROUP);
    }
    completedGroups += currentGroupIndex;
    return ((completedGroups + 1) / getTotalGroups()) * 100;
  };

  const handleResponse = (questionId: string, option: string) => {
    setResponses(prev => ({ ...prev, [questionId]: option }));
  };

  const isCurrentGroupComplete = () => {
    const currentQuestions = getCurrentQuestionGroup();
    return currentQuestions.every(q => responses[q.id]);
  };

  const handleNext = () => {
    const totalGroupsInCategory = Math.ceil(categoryQuestions.length / QUESTIONS_PER_GROUP);

    if (currentGroupIndex < totalGroupsInCategory - 1) {
      // More groups in current category
      setCurrentGroupIndex(prev => prev + 1);
    } else if (currentCategoryIndex < CATEGORIES.length - 1) {
      // Move to next category
      setCurrentCategoryIndex(prev => prev + 1);
      setCurrentGroupIndex(0);
    } else {
      // Assessment complete
      setShowResults(true);
    }
  };

  const handleBack = () => {
    if (currentGroupIndex > 0) {
      setCurrentGroupIndex(prev => prev - 1);
    } else if (currentCategoryIndex > 0) {
      const prevCategory = CATEGORIES[currentCategoryIndex - 1];
      const prevCategoryGroups = Math.ceil(QUESTIONS_BY_CATEGORY[prevCategory].length / QUESTIONS_PER_GROUP);
      setCurrentCategoryIndex(prev => prev - 1);
      setCurrentGroupIndex(prevCategoryGroups - 1);
    } else {
      navigate('/');
    }
  };

  const calculateScores = () => {
    const optionScores: Record<string, number> = {
      // Score 4 - Best responses
      'Excellent': 4, 'Very Good': 4, 'Always': 4, 'Very Satisfied': 4, 'Definitely Yes': 4,
      'Very Well': 4, 'Strongly Agree': 4, 'Energized': 4, 'Very Secure': 4, 'Daily': 4,
      'Very Stable': 4, 'High Energy': 4, 'Very High': 4, 'Very Comfortable': 4,
      'Very Connected': 4, 'Very Clear': 4, '8+ hours': 4, 'Yes, 6+ months': 4, 'Monthly': 4,

      // Score 3 - Good responses
      'Good': 3, 'Usually': 3, 'Satisfied': 3, 'Mostly Yes': 3, 'Well': 3,
      'Agree': 3, 'Mostly Energized': 3, 'Secure': 3, 'Several times a week': 3,
      'Stable': 3, 'Moderately High': 3, 'Comfortable': 3, 'Connected': 3,
      'Clear': 3, '7-8 hours': 3, 'Yes, 3-6 months': 3, 'Mostly Consistent': 3,
      'Often': 3, 'High': 3,

      // Score 2 - Moderate responses
      'Fair': 2, 'Sometimes': 2, 'Neutral': 2, 'Somewhat': 2, 'Moderately': 2,
      'Somewhat Stable': 2, 'Moderate': 2, 'Somewhat Comfortable': 2, 'Somewhat Connected': 2,
      'Somewhat Clear': 2, '5-6 hours': 2, 'Yes, less than 3 months': 2, 'Somewhat Consistent': 2,
      'Somewhat Secure': 2, 'Occasionally': 2, 'Once a week': 2,

      // Score 1 - Poor responses
      'Rarely': 1, 'Poor': 1, 'Dissatisfied': 1, 'No': 1, 'Poorly': 1,
      'Disagree': 1, 'Drained': 1, 'Insecure': 1, 'Unstable': 1, 'Low Energy': 1,
      'Uncomfortable': 1, 'Not Connected': 1, 'Unclear': 1, 'Less than 5 hours': 1,
      'Low': 1, 'Not Consistent': 1,

      // Score 0 - Worst responses (for reverse-scored items)
      'Never': 0, 'Rarely/Never': 0,
      // Note: 'Never' can be 0 or 4 depending on context. For positive behaviors (exercise) it's 0, for negative experiences (pain) it's 4

      // Special handling for 'Never' - it needs context-based scoring
      // We'll handle this in the logic below
    };

    // Helper function to get score with context awareness
    const getScoreForOption = (questionId: string, option: string): number => {
      // For questions where "Never" is a POSITIVE response (pain, worry, loneliness, etc.)
      const positiveNeverQuestions = [
        'wb_7', 'wb_13', 'wb_16', 'wb_22', 'wb_30', 'wb_33', 'wb_43'  // Pain, overwhelmed, anxiety, lonely, work interference, etc.
      ];

      // For questions where "Never" is a NEGATIVE response (exercise, mindfulness, self-care, etc.)
      const negativeNeverQuestions = [
        'wb_2', 'wb_18', 'wb_26', 'wb_35', 'wb_38', 'wb_41', 'wb_49', 'wb_50', 'wb_54'  // Exercise, mindfulness, meaningful activities, etc.
      ];

      if (option === 'Never') {
        if (positiveNeverQuestions.includes(questionId)) {
          return 4; // Never experiencing pain/worry is GOOD
        } else if (negativeNeverQuestions.includes(questionId)) {
          return 0; // Never exercising/practicing self-care is POOR
        }
        return 0; // Default
      }

      if (option === 'Often') {
        // For negative items (worry, pain, loneliness), "Often" is bad
        if (positiveNeverQuestions.includes(questionId)) {
          return 1; // Often experiencing negative things is POOR
        }
        // For positive items (meaningful conversations, hobbies), "Often" is good
        return 3;
      }

      return optionScores[option] ?? 2; // Default to middle score if unknown
    };

    const categories = ['Physical', 'Emotional', 'Social', 'Work', 'Purpose', 'Financial', 'SelfCare'];
    const categoryScores: Record<string, { score: number; max: number; percentage: number; questions: Array<{question: typeof WELLBEING_QUESTIONS[0]; userAnswer: string; score: number}> }> = {};

    categories.forEach(category => {
      const categoryQuestions = WELLBEING_QUESTIONS.filter(q => q.category === category);
      let totalScore = 0;
      let maxScore = 0;
      const questionDetails: Array<{question: typeof WELLBEING_QUESTIONS[0]; userAnswer: string; score: number}> = [];

      categoryQuestions.forEach(q => {
        const response = responses[q.id];
        if (response) {
          const score = getScoreForOption(q.id, response);
          totalScore += score;
          maxScore += 4;
          questionDetails.push({
            question: q,
            userAnswer: response,
            score
          });
        }
      });

      categoryScores[category] = {
        score: totalScore,
        max: maxScore,
        percentage: maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0,
        questions: questionDetails
      };
    });

    // Calculate overall score
    const totalScore = Object.values(categoryScores).reduce((sum, cat) => sum + cat.score, 0);
    const maxScore = Object.values(categoryScores).reduce((sum, cat) => sum + cat.max, 0);
    const overallPercentage = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;

    return { categoryScores, overallPercentage, totalScore, maxScore };
  };

  // Get detailed category insights
  const getCategoryInsights = (category: string, scores: any) => {
    const sortedQuestions = [...scores.questions].sort((a, b) => b.score - a.score);
    const bestQuestions = sortedQuestions.slice(0, 2);
    const worstQuestions = sortedQuestions.slice(-2).reverse();

    return {
      best: bestQuestions.map(q => ({
        text: q.question.text,
        answer: q.userAnswer,
        score: q.score
      })),
      worst: worstQuestions.map(q => ({
        text: q.question.text,
        answer: q.userAnswer,
        score: q.score
      }))
    };
  };

  // Generate personalized action plan based on weakest areas
  const getPersonalizedActionPlan = (categoryScores: any) => {
    const sortedCategories = Object.entries(categoryScores)
      .sort(([, a]: any, [, b]: any) => a.percentage - b.percentage)
      .slice(0, 3); // Top 3 areas to improve

    const actionPlans: Record<string, {priority: string; actions: string[]}> = {
      Physical: {
        priority: 'HIGH',
        actions: [
          'Schedule 30 minutes of moderate exercise 3-4x per week',
          'Establish a consistent sleep schedule (same bedtime/wake time)',
          'Stay hydrated - aim for 8 glasses of water daily',
          'Add one more serving of vegetables to your meals'
        ]
      },
      Emotional: {
        priority: 'HIGH',
        actions: [
          'Practice 5 minutes of daily mindfulness or meditation',
          'Journal your thoughts and feelings for 10 minutes daily',
          'Reach out to a friend or family member when feeling stressed',
          'Identify and challenge negative thought patterns'
        ]
      },
      Social: {
        priority: 'MEDIUM',
        actions: [
          'Schedule regular catch-ups with friends or family',
          'Join a club, group, or class based on your interests',
          'Practice active listening in conversations',
          'Set healthy boundaries in relationships'
        ]
      },
      Work: {
        priority: 'HIGH',
        actions: [
          'Create clear boundaries between work and personal time',
          'Take regular breaks during the workday',
          'Practice the "2-minute rule" for tasks',
          'Review and adjust your workload with your manager'
        ]
      },
      Purpose: {
        priority: 'MEDIUM',
        actions: [
          'Identify your core values and align activities with them',
          'Set 3 specific personal goals for the next month',
          'Engage in activities that bring you joy and meaning',
          'Volunteer or help others to find purpose'
        ]
      },
      Financial: {
        priority: 'MEDIUM',
        actions: [
          'Create or review your monthly budget',
          'Set up automatic savings (even $50/month helps)',
          'Build an emergency fund (start with $500)',
          'Review and reduce recurring expenses'
        ]
      },
      SelfCare: {
        priority: 'HIGH',
        actions: [
          'Schedule self-care time like you would any appointment',
          'Learn and practice stress management techniques',
          'Say "no" to commitments that drain you',
          'Engage in hobbies purely for enjoyment'
        ]
      }
    };

    return sortedCategories.map(([category, scores]: [string, any]) => ({
      category,
      percentage: scores.percentage,
      ...actionPlans[category]
    }));
  };

  // Identify strengths and growth areas
  const getStrengthsAndGrowthAreas = (categoryScores: any) => {
    const sorted = Object.entries(categoryScores)
      .sort(([, a]: any, [, b]: any) => b.percentage - a.percentage);

    const strengths = sorted.slice(0, 2).filter(([, cat]: any) => cat.percentage >= 60);
    const growthAreas = sorted.slice(-3).reverse().filter(([, cat]: any) => cat.percentage < 75);

    return { strengths, growthAreas };
  };

  // Priority scoring based on impact and ease
  const getPriorityRanking = (categoryScores: any) => {
    const categoryPriority: Record<string, {impact: number; ease: number; score: number}> = {
      Physical: { impact: 5, ease: 3, score: 0 },
      Emotional: { impact: 5, ease: 4, score: 0 },
      Social: { impact: 3, ease: 4, score: 0 },
      Work: { impact: 4, ease: 3, score: 0 },
      Purpose: { impact: 4, ease: 2, score: 0 },
      Financial: { impact: 3, ease: 3, score: 0 },
      SelfCare: { impact: 5, ease: 4, score: 0 }
    };

    Object.entries(categoryScores).forEach(([category, scores]: [string, any]) => {
      const priority = categoryPriority[category];
      if (priority) {
        // Lower percentage = higher urgency (inverse scoring)
        const urgency = (100 - scores.percentage) / 100;
        priority.score = Math.round((priority.impact + priority.ease) * (1 + urgency) * 10) / 10;
      }
    });

    return Object.entries(categoryPriority)
      .sort(([, a]: any, [, b]: any) => b.score - a.score)
      .slice(0, 4)
      .map(([category, data]) => ({
        category,
        ...data,
        currentScore: (categoryScores as any)[category].percentage
      }));
  };

  const getOverallLevel = (percentage: number) => {
    if (percentage >= 75) return {
      label: 'Excellent Wellbeing',
      color: 'green',
      description: 'You demonstrate strong wellbeing across multiple areas of life.',
      recommendations: [
        'Maintain your healthy habits and routines',
        'Consider sharing your strategies with others who might benefit',
        'Continue prioritizing self-care and work-life balance'
      ]
    };
    if (percentage >= 50) return {
      label: 'Good Wellbeing',
      color: 'blue',
      description: 'You have solid wellbeing foundations with room for growth in some areas.',
      recommendations: [
        'Focus on improving your lowest-scoring wellbeing areas',
        'Set specific, achievable goals for enhancement',
        'Consider trying new stress management techniques'
      ]
    };
    if (percentage >= 25) return {
      label: 'Moderate Wellbeing',
      color: 'yellow',
      description: 'Some areas of your life need attention and care.',
      recommendations: [
        'Prioritize self-care and stress reduction',
        'Seek support from friends, family, or professionals',
        'Start with small, manageable changes in daily routines'
      ]
    };
    return {
      label: 'Needs Attention',
      color: 'red',
      description: 'Your wellbeing would benefit from focused attention and support.',
      recommendations: [
        'Consider speaking with a mental health professional',
        'Reach out to your support network',
        'Focus on basic self-care: sleep, nutrition, and physical activity',
        'Contact crisis resources if feeling overwhelmed'
      ]
    };
  };

  // === NEW ENHANCED HANDLERS ===

  // Handler for action item checkbox toggles
  const handleActionToggle = (category: string, actionIndex: number) => {
    const key = `${category}-${actionIndex}`;
    const newState = { ...actionProgress };
    newState[key] = !newState[key];
    setActionProgress(newState);

    // Persist to localStorage
    updateActionProgress(category, actionIndex, newState[key]);
  };

  // Handler for opening goal modal
  const handleOpenGoalModal = (category: string, currentScore: number) => {
    setSelectedGoalCategory({ category, currentScore });
    setShowGoalModal(true);
  };

  // Handler for setting a goal
  const handleSetGoal = (goal: Omit<WellbeingGoals, 'achieved'>) => {
    const existingGoals = getGoals();
    const updatedGoals = existingGoals.filter(g => g.category !== goal.category);
    updatedGoals.push({ ...goal, achieved: false });
    saveGoals(updatedGoals);
    setGoals(updatedGoals);
    setShowGoalModal(false);
    setSelectedGoalCategory(null);
  };

  // Handler for score filter changes
  const handleScoreFilterChange = (filter: 'all' | 'low' | 'medium' | 'high') => {
    setScoreFilter(filter);
  };

  // Handler for expanding/collapsing all categories
  const handleExpandCollapseAll = (expand: boolean) => {
    if (expand) {
      setExpandedCategory('all');
    } else {
      setExpandedCategory(null);
    }
  };

  // Handler for PDF export
  const handleExportPDF = () => {
    exportToPDF('wellbeing-results', `wellbeing-results-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  // Handler for JSON export
  const handleExportJSON = () => {
    const { categoryScores, overallPercentage, totalScore, maxScore } = calculateScores();
    const exportData = {
      date: new Date().toISOString(),
      overallPercentage,
      totalScore,
      maxScore,
      categoryScores,
      responses: responses,
      assessmentHistory: assessmentHistory.slice(0, 5)
    };
    exportToJSON(exportData, `wellbeing-results-${new Date().toISOString().split('T')[0]}.json`);
  };

  // Handler for retaking assessment
  const handleRetake = () => {
    setResponses({});
    setCurrentCategoryIndex(0);
    setCurrentGroupIndex(0);
    setShowResults(false);
    setExpandedCategory(null);
    setScoreFilter('all');
    setPreviousResult(calculateScores());
  };

  // Handler for clearing all data
  const handleClearAllData = () => {
    if (confirm('Are you sure you want to delete all your wellbeing assessment history? This cannot be undone.')) {
      clearAllWellbeingData();
      setAssessmentHistory([]);
      setPreviousResult(null);
      setStreak({ lastAssessmentDate: '', currentStreak: 0, longestStreak: 0, totalAssessments: 0 });
      setGoals([]);
      setActionProgress({});
    }
  };

  // Save assessment result to history when completed
  useEffect(() => {
    if (showResults) {
      const { categoryScores, overallPercentage, totalScore, maxScore } = calculateScores();

      // Only save if we haven't saved this one yet
      const lastResult = assessmentHistory[0];
      const now = new Date().toISOString();

      if (!lastResult || new Date(lastResult.date).toISOString() !== now) {
        const result: StoredAssessmentResult = {
          id: `assessment-${Date.now()}`,
          date: new Date().toISOString(),
          overallPercentage,
          categoryScores: Object.entries(categoryScores).map(([cat, data]: [string, any]) => ({
            category: cat,
            score: data.score,
            max: data.max,
            percentage: data.percentage
          })),
          responses: { ...responses }
        };

        saveAssessmentResult(result);
        setAssessmentHistory(prev => [result, ...prev]);

        // Trigger confetti for good scores
        if (overallPercentage >= 70) {
          setShowConfetti(true);
          setTimeout(() => setShowConfetti(false), 5000);
        }
      }
    }
  }, [showResults]);

  if (showResults) {
    const { categoryScores, overallPercentage, totalScore, maxScore } = calculateScores();
    const overallLevel = getOverallLevel(overallPercentage);
    const { strengths, growthAreas } = getStrengthsAndGrowthAreas(categoryScores);
    const actionPlan = getPersonalizedActionPlan(categoryScores);
    const priorityRanking = getPriorityRanking(categoryScores);

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100 p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          {/* Overall Score with Enhanced Header */}
          <div className="mb-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-3xl">Wellbeing Assessment Results</CardTitle>
                    <p className="text-gray-600 mt-2">Comprehensive analysis across 7 key life areas with actionable insights</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {/* Streak Counter */}
                    <div className="text-center px-4 py-2 bg-purple-100 rounded-lg">
                      <div className="text-2xl font-bold text-purple-700">🔥 {streak.currentStreak}</div>
                      <div className="text-xs text-purple-600">Day Streak</div>
                    </div>
                    {/* Dark Mode Toggle */}
                    <Button
                      onClick={toggleTheme}
                      variant="outline"
                      className="p-2"
                      title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
                    >
                      {theme === 'light' ? '🌙' : '☀️'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-6">
                  <div className={`inline-block px-8 py-4 rounded-full text-white text-3xl font-bold mb-4 ${
                    overallLevel.color === 'green' ? 'bg-green-600' :
                    overallLevel.color === 'blue' ? 'bg-blue-600' :
                    overallLevel.color === 'yellow' ? 'bg-yellow-600' : 'bg-red-600'
                  }`}>
                    {overallPercentage}% Wellbeing Score
                  </div>
                  <p className={`text-2xl font-bold mt-4 ${
                    overallLevel.color === 'green' ? 'text-green-700' :
                    overallLevel.color === 'blue' ? 'text-blue-700' :
                    overallLevel.color === 'yellow' ? 'text-yellow-700' : 'text-red-700'
                  }`}>
                    {overallLevel.label}
                  </p>
                  <p className="text-gray-600 mt-2">{overallLevel.description}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Confetti Celebration Effect */}
          {showConfetti && (
            <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
              <div className="text-6xl animate-bounce">🎉</div>
            </div>
          )}

          {/* Progress Timeline Chart */}
          {assessmentHistory.length >= 2 && (
            <div className="mb-6">
              <ProgressChart data={assessmentHistory.map(h => ({
                date: h.date,
                overall: h.overallPercentage,
                physical: h.categoryScores['Physical']?.percentage || 0,
                emotional: h.categoryScores['Emotional']?.percentage || 0,
                social: h.categoryScores['Social']?.percentage || 0,
                work: h.categoryScores['Work']?.percentage || 0,
                purpose: h.categoryScores['Purpose']?.percentage || 0,
                financial: h.categoryScores['Financial']?.percentage || 0,
                selfCare: h.categoryScores['SelfCare']?.percentage || 0
              }))} />
            </div>
          )}

          {/* Previous vs Current Comparison */}
          {previousResult && (
            <div className="mb-6">
              <Card className="bg-blue-50 border-blue-200">
                <CardHeader>
                  <CardTitle className="text-xl text-blue-800">📊 Comparison with Previous Assessment</CardTitle>
                  <p className="text-sm text-blue-700">
                    Last taken: {new Date(previousResult.date).toLocaleDateString()}
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(categoryScores).map(([category, scores]: [string, any]) => {
                      const prevScore = previousResult.categoryScores[category]?.percentage || 0;
                      const change = scores.percentage - prevScore;
                      const isImprovement = change > 0;
                      return (
                        <div key={category} className="bg-white rounded-lg p-4 border border-blue-200">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-semibold">{category}</span>
                            <span className={`text-sm font-bold ${
                              isImprovement ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {change > 0 ? '+' : ''}{change}%
                            </span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Before: {prevScore}%</span>
                            <span className="text-gray-800 font-medium">Now: {scores.percentage}%</span>
                          </div>
                          {isImprovement && (
                            <div className="mt-2 text-xs text-green-600">📈 Improving!</div>
                          )}
                          {change < 0 && (
                            <div className="mt-2 text-xs text-orange-600">📉 Needs attention</div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-4 text-center">
                    <div className="inline-block px-4 py-2 bg-white rounded-lg border border-blue-300">
                      <span className="text-sm text-gray-600">Overall Change: </span>
                      <span className={`font-bold text-lg ${
                        (overallPercentage - (previousResult.overallPercentage || 0)) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {overallPercentage - (previousResult.overallPercentage || 0) > 0 ? '+' : ''}{overallPercentage - (previousResult.overallPercentage || 0)}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Filter & Export Controls */}
          <div className="mb-6">
            <Card>
              <CardContent className="pt-6">
                <div className="flex flex-wrap gap-4 items-center justify-between">
                  <div className="flex flex-wrap gap-3 items-center">
                    <span className="text-sm font-medium text-gray-700">Filter by Score:</span>
                    <div className="flex gap-2">
                      {(['all', 'low', 'medium', 'high'] as const).map(filter => (
                        <Button
                          key={filter}
                          onClick={() => handleScoreFilterChange(filter)}
                          variant={scoreFilter === filter ? 'default' : 'outline'}
                          size="sm"
                          className={
                            scoreFilter === filter
                              ? 'bg-purple-600 text-white'
                              : 'bg-white text-gray-700 hover:bg-purple-50'
                          }
                        >
                          {filter === 'all' ? 'All' : filter === 'low' ? 'Low (<50%)' : filter === 'medium' ? 'Medium (50-75%)' : 'High (>75%)'}
                        </Button>
                      ))}
                    </div>
                    <div className="border-l border-gray-300 h-6 mx-2" />
                    <Button
                      onClick={() => handleExpandCollapseAll(expandedCategory === null)}
                      variant="outline"
                      size="sm"
                    >
                      {expandedCategory === null ? '📂 Expand All' : '📁 Collapse All'}
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleExportPDF} variant="outline" size="sm">
                      📄 PDF
                    </Button>
                    <Button onClick={handleExportJSON} variant="outline" size="sm">
                      💾 JSON
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Priority Ranking - NEW */}
          <div className="mb-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">🎯 Your Priority Focus Areas</CardTitle>
                <p className="text-sm text-gray-600">Ranked by impact on your overall wellbeing and ease of improvement</p>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {priorityRanking.map((item, index) => (
                    <div key={item.category} className="relative">
                      <div className="bg-gradient-to-br from-purple-100 to-blue-100 rounded-lg p-4 border-2 border-purple-300">
                        <div className="absolute -top-2 -left-2 w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                          {index + 1}
                        </div>
                        <h4 className="font-bold text-lg mt-2">{item.category}</h4>
                        <p className="text-sm text-gray-600">Current: {item.currentScore}%</p>
                        <div className="mt-2 flex justify-between text-xs">
                          <span>Impact: {'⭐'.repeat(Math.round(item.impact / 1.5))}</span>
                          <span>Ease: {'🔧'.repeat(Math.round(item.ease / 1.5))}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Strengths & Growth Areas - NEW */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Strengths */}
            <Card className="bg-green-50 border-green-200">
              <CardHeader>
                <CardTitle className="text-xl text-green-800">💪 Your Strengths</CardTitle>
                <p className="text-sm text-green-700">Areas where you're doing well</p>
              </CardHeader>
              <CardContent>
                {strengths.length > 0 ? (
                  <div className="space-y-3">
                    {strengths.map(([category, cat]: [string, any]) => (
                      <div key={category} className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-semibold text-green-800">{category}</span>
                          <span className="text-sm font-bold text-green-600">{cat.percentage}%</span>
                        </div>
                        <div className="w-full bg-green-100 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full" style={{ width: `${cat.percentage}%` }} />
                        </div>
                        <p className="text-xs text-gray-600 mt-2">Keep up the great work in this area!</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">Complete the assessment to discover your strengths.</p>
                )}
              </CardContent>
            </Card>

            {/* Growth Areas */}
            <Card className="bg-orange-50 border-orange-200">
              <CardHeader>
                <CardTitle className="text-xl text-orange-800">🌱 Growth Opportunities</CardTitle>
                <p className="text-sm text-orange-700">Areas with room for improvement</p>
              </CardHeader>
              <CardContent>
                {growthAreas.length > 0 ? (
                  <div className="space-y-3">
                    {growthAreas.map(([category, cat]: [string, any]) => (
                      <div key={category} className="bg-white rounded-lg p-3 border border-orange-200">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-semibold text-orange-800">{category}</span>
                          <span className="text-sm font-bold text-orange-600">{cat.percentage}%</span>
                        </div>
                        <div className="w-full bg-orange-100 rounded-full h-2">
                          <div className="bg-orange-500 h-2 rounded-full" style={{ width: `${cat.percentage}%` }} />
                        </div>
                        <p className="text-xs text-gray-600 mt-2">Small improvements here can make a big difference!</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600">Complete the assessment to identify growth areas.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Personalized Action Plan - NEW */}
          <div className="mb-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">📋 Your Personalized Action Plan</CardTitle>
                <p className="text-sm text-gray-600">Specific steps based on your weakest wellbeing areas</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {actionPlan.map((plan) => (
                    <div key={plan.category} className="border rounded-lg overflow-hidden">
                      <div className={`p-4 ${
                        plan.priority === 'HIGH' ? 'bg-red-50' : 'bg-yellow-50'
                      }`}>
                        <div className="flex justify-between items-center">
                          <h4 className="font-bold text-lg">{plan.category} Wellbeing</h4>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">{plan.percentage}%</span>
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                              plan.priority === 'HIGH' ? 'bg-red-600 text-white' : 'bg-yellow-600 text-white'
                            }`}>
                              {plan.priority} PRIORITY
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="p-4 bg-white">
                        <h5 className="font-semibold mb-2 text-gray-700">Action Steps:</h5>
                        <ul className="space-y-2">
                          {plan.actions.map((action, idx) => {
                            const isChecked = actionProgress[`${plan.category}-${idx}`] || false;
                            return (
                              <li key={idx} className="flex items-start">
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  onChange={() => handleActionToggle(plan.category, idx)}
                                  className="mt-1 mr-3 h-4 w-4 text-purple-600 rounded"
                                  id={`${plan.category}-action-${idx}`}
                                />
                                <label
                                  htmlFor={`${plan.category}-action-${idx}`}
                                  className={`text-sm cursor-pointer ${isChecked ? 'line-through text-gray-400' : 'text-gray-700'}`}
                                >
                                  {action}
                                </label>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Category Breakdown - NEW with Filter */}
          <div className="mb-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">📊 Detailed Category Breakdown</CardTitle>
                <p className="text-sm text-gray-600">Click on a category to see your highest and lowest scoring questions</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(categoryScores)
                    .filter(([, scores]: [string, any]) => {
                      if (scoreFilter === 'all') return true;
                      if (scoreFilter === 'low') return scores.percentage < 50;
                      if (scoreFilter === 'medium') return scores.percentage >= 50 && scores.percentage < 75;
                      if (scoreFilter === 'high') return scores.percentage >= 75;
                      return true;
                    })
                    .map(([category, scores]: [string, any]) => {
                      const insights = getCategoryInsights(category, scores);
                      const isExpanded = expandedCategory === category || expandedCategory === 'all';
                      const currentGoal = goals.find(g => g.category === category);
                      return (
                        <div key={category} className="border rounded-lg overflow-hidden">
                          <div
                            onClick={() => setExpandedCategory(isExpanded ? null : category)}
                            onKeyPress={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                setExpandedCategory(isExpanded ? null : category);
                              }
                            }}
                            role="button"
                            tabIndex={0}
                            className="w-full p-4 bg-gray-50 hover:bg-gray-100 transition-colors flex justify-between items-center cursor-pointer"
                          >
                            <div className="flex-1">
                              <div className="flex justify-between items-center">
                                <div>
                                  <span className="font-semibold">{category}</span>
                                  {currentGoal && (
                                    <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                                      🎯 Goal: {currentGoal.targetScore}%
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className="text-sm font-bold">{scores.percentage}%</span>
                                  <Button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleOpenGoalModal(category, scores.percentage);
                                    }}
                                    variant="ghost"
                                    size="sm"
                                    className="text-xs"
                                    title="Set goal"
                                  >
                                    🎯 Set Goal
                                  </Button>
                                </div>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                                <div
                                  className={`h-2 rounded-full ${
                                    scores.percentage >= 75 ? 'bg-green-500' :
                                    scores.percentage >= 50 ? 'bg-blue-500' :
                                    scores.percentage >= 25 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${scores.percentage}%` }}
                                />
                              </div>
                            </div>
                            <span className="ml-4 text-gray-500">
                              {isExpanded ? '▼' : '▶'}
                            </span>
                          </div>

                          {isExpanded && (
                            <div className="p-4 bg-white border-t">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Best performing */}
                                <div className="bg-green-50 rounded-lg p-3">
                                  <h5 className="font-semibold text-green-800 mb-2">✅ Strongest Areas</h5>
                                  {insights.best.map((item: any, idx: number) => (
                                    <div key={idx} className="mb-2 pb-2 border-b border-green-200 last:border-0">
                                      <p className="text-sm text-gray-700">{item.text}</p>
                                      <div className="flex justify-between items-center mt-1">
                                        <span className="text-xs text-gray-500">Your answer: {item.answer}</span>
                                        <span className="text-xs font-bold text-green-600">{item.score}/4</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>

                                {/* Areas to improve */}
                                <div className="bg-orange-50 rounded-lg p-3">
                                  <h5 className="font-semibold text-orange-800 mb-2">📈 Areas to Improve</h5>
                                  {insights.worst.map((item: any, idx: number) => (
                                    <div key={idx} className="mb-2 pb-2 border-b border-orange-200 last:border-0">
                                      <p className="text-sm text-gray-700">{item.text}</p>
                                      <div className="flex justify-between items-center mt-1">
                                        <span className="text-xs text-gray-500">Your answer: {item.answer}</span>
                                        <span className="text-xs font-bold text-orange-600">{item.score}/4</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>
                {Object.entries(categoryScores).filter(([, scores]: [string, any]) => {
                  if (scoreFilter === 'all') return false;
                  if (scoreFilter === 'low') return scores.percentage < 50;
                  if (scoreFilter === 'medium') return scores.percentage >= 50 && scores.percentage < 75;
                  if (scoreFilter === 'high') return scores.percentage >= 75;
                  return false;
                }).length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No categories match the selected filter. Try a different filter.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Question Response Summary - NEW */}
          <div className="mb-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">📝 Your Complete Response Summary</CardTitle>
                <p className="text-sm text-gray-600">Review all your answers and see how they contributed to your scores</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {Object.entries(categoryScores).map(([category, scores]: [string, any]) => (
                    <div key={category} className="border-b pb-4 last:border-0">
                      <h4 className="font-bold text-lg mb-3 text-purple-800">{category} Wellbeing</h4>
                      <div className="space-y-2">
                        {scores.questions.map((q: any, idx: number) => (
                          <div key={idx} className="flex justify-between items-start text-sm p-2 rounded hover:bg-gray-50">
                            <p className="flex-1 text-gray-700">{q.question.text}</p>
                            <div className="flex items-center gap-2 ml-4">
                              <span className="font-medium text-gray-800">{q.userAnswer}</span>
                              <span className={`px-2 py-1 rounded text-xs font-bold ${
                                q.score >= 3 ? 'bg-green-100 text-green-800' :
                                q.score === 2 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {q.score}/4
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Overall Recommendations */}
          <div className="mb-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">💡 General Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {overallLevel.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-indigo-600 mr-3 mt-1">✓</span>
                      <span className="text-gray-700">{rec}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Important Note */}
            <div className="mb-6">
              <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  <strong>Important:</strong> This assessment is for informational purposes only.
                  If you're struggling, please consider speaking with a mental health professional.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={handleRetake}
                variant="outline"
                className="flex-1"
              >
                🔄 Retake Assessment
              </Button>
              <Button
                onClick={() => navigate('/clinical-assessments')}
                className="flex-1"
              >
                📋 More Assessments
              </Button>
              <Button
                onClick={() => navigate('/')}
                variant="ghost"
                className="flex-1"
              >
                🏠 Back to Home
              </Button>
            </div>
          </div>

          {/* Goal Setting Modal */}
          {showGoalModal && selectedGoalCategory && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg max-w-md w-full p-6">
                <h3 className="text-xl font-bold mb-4">🎯 Set Your {selectedGoalCategory.category} Goal</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Current score: <strong>{selectedGoalCategory.currentScore}%</strong>
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Score (%)
                    </label>
                    <input
                      type="number"
                      min={selectedGoalCategory.currentScore + 1}
                      max="100"
                      defaultValue={Math.min(selectedGoalCategory.currentScore + 10, 100)}
                      id="goal-target-score"
                      className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Date
                    </label>
                    <input
                      type="date"
                      id="goal-target-date"
                      min={new Date().toISOString().split('T')[0]}
                      defaultValue={new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button
                    onClick={() => {
                      const targetScore = parseInt((document.getElementById('goal-target-score') as HTMLInputElement)?.value || '80');
                      const targetDate = (document.getElementById('goal-target-date') as HTMLInputElement)?.value || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
                      handleSetGoal({
                        category: selectedGoalCategory.category,
                        currentScore: selectedGoalCategory.currentScore,
                        targetScore,
                        targetDate
                      });
                    }}
                    className="flex-1"
                  >
                    Save Goal
                  </Button>
                  <Button
                    onClick={() => {
                      setShowGoalModal(false);
                      setSelectedGoalCategory(null);
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  const progress = getProgress();
  const currentQuestions = getCurrentQuestionGroup();
  const totalGroupsInCategory = Math.ceil(categoryQuestions.length / QUESTIONS_PER_GROUP);
  const isLastGroup = currentCategoryIndex === CATEGORIES.length - 1 && currentGroupIndex === totalGroupsInCategory - 1;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Button onClick={handleBack} variant="ghost">
            ← Back
          </Button>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{currentCategory} Wellbeing ({currentGroupIndex + 1}/{totalGroupsInCategory})</span>
            <span>Category {currentCategoryIndex + 1} of {CATEGORIES.length}</span>
            <span>{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-purple-600 h-2 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Questions Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl">{currentCategory} Wellbeing Assessment</CardTitle>
              <span className="text-sm bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
                {currentQuestions.length} Questions
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {currentQuestions.map((question, qIndex) => (
                <div key={question.id} className="border-b border-gray-200 pb-6 last:border-0">
                  <p className="text-lg font-medium text-gray-900 mb-4">
                    {qIndex + 1}. {question.text}
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {question.options.map((option) => {
                      const isSelected = responses[question.id] === option;
                      return (
                        <button
                          key={option}
                          onClick={() => handleResponse(question.id, option)}
                          className={`text-left p-3 border-2 rounded-lg transition-all ${
                            isSelected
                              ? 'bg-purple-100 border-purple-500 font-medium'
                              : 'border-gray-300 hover:bg-purple-50 hover:border-purple-400'
                          }`}
                        >
                          <span className="flex items-center">
                            <span className={`w-5 h-5 rounded-full border-2 mr-3 flex items-center justify-center ${
                              isSelected ? 'border-purple-500 bg-purple-500' : 'border-gray-400'
                            }`}>
                              {isSelected && <span className="w-2 h-2 rounded-full bg-white" />}
                            </span>
                            {option}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* Navigation Buttons */}
            <div className="mt-8 flex justify-between">
              <Button
                onClick={handleBack}
                variant="outline"
                className="px-6"
              >
                ← Previous
              </Button>
              <Button
                onClick={handleNext}
                disabled={!isCurrentGroupComplete()}
                className="px-6"
              >
                {isLastGroup ? 'View Results' : 'Next →'}
              </Button>
            </div>

            {!isCurrentGroupComplete() && (
              <p className="text-sm text-orange-600 mt-3 text-center">
                Please answer all questions before continuing
              </p>
            )}
          </CardContent>
        </Card>

        {/* Info Tip */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>💡 Tip:</strong> Answer honestly for the most accurate results.
            Your responses are confidential and help provide personalized recommendations.
          </p>
        </div>
      </div>
    </div>
  );
};

export default WellbeingAssessment;
