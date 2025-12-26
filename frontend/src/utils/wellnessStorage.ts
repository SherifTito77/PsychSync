/**
 * LocalStorage utilities for Wellbeing Assessment persistence
 */

export interface StoredAssessmentResult {
  id: string;
  date: string;
  overallPercentage: number;
  categoryScores: Record<string, { score: number; max: number; percentage: number }>;
  responses: Record<string, string>;
}

export interface WellbeingGoals {
  category: string;
  currentScore: number;
  targetScore: number;
  targetDate: string;
  achieved: boolean;
}

export interface ActionItemProgress {
  category: string;
  actionIndex: number;
  completed: boolean;
  completedDate?: string;
}

export interface WellnessStreak {
  lastAssessmentDate: string;
  currentStreak: number;
  longestStreak: number;
  totalAssessments: number;
}

const STORAGE_KEYS = {
  ASSESSMENT_HISTORY: 'wellbeing_assessment_history',
  GOALS: 'wellbeing_goals',
  ACTION_PROGRESS: 'wellbeing_action_progress',
  STREAK: 'wellbeing_streak',
  THEME: 'wellbeing_theme'
};

/**
 * Save assessment result to history
 */
export function saveAssessmentResult(result: StoredAssessmentResult): void {
  const history = getAssessmentHistory();
  history.unshift(result); // Add to beginning

  // Keep only last 30 assessments
  const trimmed = history.slice(0, 30);

  localStorage.setItem(STORAGE_KEYS.ASSESSMENT_HISTORY, JSON.stringify(trimmed));

  // Update streak
  updateStreak();
}

/**
 * Get all assessment history
 */
export function getAssessmentHistory(): StoredAssessmentResult[] {
  const stored = localStorage.getItem(STORAGE_KEYS.ASSESSMENT_HISTORY);
  return stored ? JSON.parse(stored) : [];
}

/**
 * Get previous assessment result (if exists)
 */
export function getPreviousAssessment(): StoredAssessmentResult | null {
  const history = getAssessmentHistory();
  return history.length > 1 ? history[1] : null;
}

/**
 * Save goals
 */
export function saveGoals(goals: WellbeingGoals[]): void {
  localStorage.setItem(STORAGE_KEYS.GOALS, JSON.stringify(goals));
}

/**
 * Get goals
 */
export function getGoals(): WellbeingGoals[] {
  const stored = localStorage.getItem(STORAGE_KEYS.GOALS);
  return stored ? JSON.parse(stored) : [];
}

/**
 * Update action item progress
 */
export function updateActionProgress(category: string, actionIndex: number, completed: boolean): void {
  const progress = getActionProgress();
  const key = `${category}-${actionIndex}`;

  if (completed) {
    progress[key] = {
      category,
      actionIndex,
      completed: true,
      completedDate: new Date().toISOString()
    };
  } else {
    delete progress[key];
  }

  localStorage.setItem(STORAGE_KEYS.ACTION_PROGRESS, JSON.stringify(progress));
}

/**
 * Get all action progress
 */
export function getActionProgress(): Record<string, ActionItemProgress> {
  const stored = localStorage.getItem(STORAGE_KEYS.ACTION_PROGRESS);
  return stored ? JSON.parse(stored) : {};
}

/**
 * Get completed actions for a category
 */
export function getCompletedActions(category: string): number[] {
  const progress = getActionProgress();
  return Object.values(progress)
    .filter(p => p.category === category && p.completed)
    .map(p => p.actionIndex);
}

/**
 * Update streak information
 */
export function updateStreak(): void {
  const streak = getStreak();
  const today = new Date().toISOString().split('T')[0];
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

  if (streak.lastAssessmentDate === today) {
    // Already assessed today, don't update
    return;
  }

  if (streak.lastAssessmentDate === yesterday || streak.lastAssessmentDate === today) {
    streak.currentStreak += 1;
  } else {
    streak.currentStreak = 1;
  }

  streak.lastAssessmentDate = today;
  streak.totalAssessments += 1;
  streak.longestStreak = Math.max(streak.longestStreak, streak.currentStreak);

  localStorage.setItem(STORAGE_KEYS.STREAK, JSON.stringify(streak));
}

/**
 * Get streak information
 */
export function getStreak(): WellnessStreak {
  const stored = localStorage.getItem(STORAGE_KEYS.STREAK);
  if (stored) {
    return JSON.parse(stored);
  }

  return {
    lastAssessmentDate: '',
    currentStreak: 0,
    longestStreak: 0,
    totalAssessments: 0
  };
}

/**
 * Get theme preference
 */
export function getTheme(): 'light' | 'dark' {
  const stored = localStorage.getItem(STORAGE_KEYS.THEME);
  return (stored === 'dark' || stored === 'light') ? stored : 'light';
}

/**
 * Save theme preference
 */
export function setTheme(theme: 'light' | 'dark'): void {
  localStorage.setItem(STORAGE_KEYS.THEME, theme);
}

/**
 * Clear all wellbeing data
 */
export function clearAllWellbeingData(): void {
  Object.values(STORAGE_KEYS).forEach(key => {
    localStorage.removeItem(key);
  });
}
