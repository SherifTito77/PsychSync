/**
 * Wellbeing Assessment Questions
 *
 * 54 comprehensive wellbeing questions across 7 categories.
 */

import { WellbeingQuestion } from '../types';

export const WELLBEING_QUESTIONS: WellbeingQuestion[] = [
  // Physical Wellbeing (10 questions)
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

  // Mental/Emotional Wellbeing (10 questions)
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

  // Social Wellbeing (8 questions)
  { id: 'wb_21', category: 'Social', text: 'How satisfied are you with your social connections?', options: ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied'] },
  { id: 'wb_22', category: 'Social', text: 'How often do you feel lonely?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_23', category: 'Social', text: 'Do you have people you can rely on for support?', options: ['Definitely Yes', 'Mostly Yes', 'Somewhat', 'No'] },
  { id: 'wb_24', category: 'Social', text: 'How would you rate your communication skills?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_25', category: 'Social', text: 'How comfortable are you in social situations?', options: ['Very Comfortable', 'Comfortable', 'Somewhat Comfortable', 'Uncomfortable'] },
  { id: 'wb_26', category: 'Social', text: 'How often do you engage in meaningful conversations?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_27', category: 'Social', text: 'How would you rate your ability to set healthy boundaries?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_28', category: 'Social', text: 'How connected do you feel to your community?', options: ['Very Connected', 'Connected', 'Somewhat Connected', 'Not Connected'] },

  // Work/Life Balance (8 questions)
  { id: 'wb_29', category: 'Work', text: 'How would you rate your work-life balance?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_30', category: 'Work', text: 'How often does work interfere with personal life?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_31', category: 'Work', text: 'Do you feel energized or drained after work?', options: ['Energized', 'Mostly Energized', 'Neutral', 'Drained'] },
  { id: 'wb_32', category: 'Work', text: 'How satisfied are you with your current work/role?', options: ['Very Satisfied', 'Satisfied', 'Neutral', 'Dissatisfied'] },
  { id: 'wb_33', category: 'Work', text: 'How often do you bring work stress home?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_34', category: 'Work', text: 'How would you rate your ability to disconnect from work?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_35', category: 'Work', text: 'How often do you have time for hobbies outside work?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_36', category: 'Work', text: 'How would you rate your workplace relationships?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },

  // Meaning & Purpose (6 questions)
  { id: 'wb_37', category: 'Purpose', text: 'Do you feel your life has meaning and purpose?', options: ['Strongly Agree', 'Agree', 'Neutral', 'Disagree'] },
  { id: 'wb_38', category: 'Purpose', text: 'How often do you engage in activities you find meaningful?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_39', category: 'Purpose', text: 'How would you rate your sense of direction in life?', options: ['Very Clear', 'Clear', 'Somewhat Clear', 'Unclear'] },
  { id: 'wb_40', category: 'Purpose', text: 'Do you feel your values align with your actions?', options: ['Always', 'Usually', 'Sometimes', 'Rarely'] },
  { id: 'wb_41', category: 'Purpose', text: 'How often do you work toward personal goals?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_42', category: 'Purpose', text: 'How would you rate your personal growth and development?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },

  // Financial Wellbeing (6 questions)
  { id: 'wb_43', category: 'Financial', text: 'How often do you worry about finances?', options: ['Never', 'Rarely', 'Sometimes', 'Often'] },
  { id: 'wb_44', category: 'Financial', text: 'How would you rate your financial security?', options: ['Very Secure', 'Secure', 'Somewhat Secure', 'Insecure'] },
  { id: 'wb_45', category: 'Financial', text: 'How often do you save or invest for the future?', options: ['Monthly', 'Often', 'Sometimes', 'Rarely'] },
  { id: 'wb_46', category: 'Financial', text: 'How would you rate your ability to manage expenses?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_47', category: 'Financial', text: 'How comfortable are you with your current financial situation?', options: ['Very Comfortable', 'Comfortable', 'Somewhat Comfortable', 'Uncomfortable'] },
  { id: 'wb_48', category: 'Financial', text: 'Do you have an emergency fund or savings?', options: ['Yes, 6+ months', 'Yes, 3-6 months', 'Yes, less than 3 months', 'No'] },

  // Self-Care & Coping (6 questions)
  { id: 'wb_49', category: 'SelfCare', text: 'How often do you make time for self-care?', options: ['Daily', 'Several times a week', 'Once a week', 'Rarely'] },
  { id: 'wb_50', category: 'SelfCare', text: 'Do you practice relaxation techniques (meditation, mindfulness, etc.)?', options: ['Daily', 'Several times a week', 'Occasionally', 'Never'] },
  { id: 'wb_51', category: 'SelfCare', text: 'How would you rate your work-life boundaries?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_52', category: 'SelfCare', text: 'How often do you take breaks when needed?', options: ['Always', 'Usually', 'Sometimes', 'Rarely'] },
  { id: 'wb_53', category: 'SelfCare', text: 'How would you rate your stress management techniques?', options: ['Excellent', 'Good', 'Fair', 'Poor'] },
  { id: 'wb_54', category: 'SelfCare', text: 'How often do you engage in hobbies or activities you enjoy?', options: ['Daily', 'Often', 'Sometimes', 'Rarely'] },
];

// Group questions by category
export const QUESTIONS_BY_CATEGORY = WELLBEING_QUESTIONS.reduce((acc, question) => {
  if (!acc[question.category]) {
    acc[question.category] = [];
  }
  acc[question.category].push(question);
  return acc;
}, {} as Record<string, WellbeingQuestion[]>);

export const CATEGORIES = Object.keys(QUESTIONS_BY_CATEGORY);
export const QUESTIONS_PER_GROUP = 3; // Show 3 questions at a time
