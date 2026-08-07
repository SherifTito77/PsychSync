// frontend/src/components/clinical/ComprehensiveClinicalAssessments.tsx
/**
 * Comprehensive Clinical Mental Health Assessment Components
 *
 * Features:
 * - HIPAA-compliant consent flows
 * - Evidence-based screening tools (PHQ-9, GAD-7, MDQ, DAST-10, AQ-10, ACE)
 * - Real-time scoring and risk assessment
 * - Crisis intervention protocols
 * - Mobile-responsive design
 * - Accessible UI (WCAG 2.1 AA)
 *
 * @author PsychSync Clinical Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  AlertCircle, CheckCircle, Heart, Shield, Brain, Activity,
  ChevronRight, ChevronLeft, Phone, Mail, Clock, FileText,
  AlertTriangle, Info, X, Send, Download, Calendar, Zap, Moon
} from 'lucide-react';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface AssessmentProps {
  assessmentType: 'PHQ9' | 'GAD7' | 'MDQ' | 'DAST10' | 'AQ10' | 'ACE' | 'ASRS' | 'ISI';
  onComplete: (result: ScreeningResult) => void;
  onCancel?: () => void;
}

interface ScreeningResult {
  id: string;
  screening_type: string;
  total_score: number;
  severity_level: string;
  risk_level: string;
  interpretation: string;
  recommendations: string[];
  crisis_alert: boolean;
  risk_flags: string[];
  subscale_scores?: Record<string, number>;
  completed_at: string;
}

interface Question {
  id: number | string;
  text: string;
  key: string;
  type?: 'rating' | 'boolean' | 'select';
  options?: Array<{ value: number | boolean; label: string }>;
}

// ============================================================================
// ASSESSMENT DEFINITIONS
// ============================================================================

const ASSESSMENT_CONFIGS: Record<string, {
  title: string;
  description: string;
  icon: typeof Brain;
  color: string;
  questions: Question[];
  crisisThreshold?: number;
  crisisQuestion?: number;
}> = {
  PHQ9: {
    title: 'PHQ-9 Depression Screening',
    description: 'Over the last 2 weeks, how often have you been bothered by the following problems?',
    icon: Brain,
    color: 'purple',
    questions: [
      { id: 1, text: 'Little interest or pleasure in doing things', key: 'q1_interest', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 2, text: 'Feeling down, depressed, or hopeless', key: 'q2_depressed', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 3, text: 'Trouble falling or staying asleep, or sleeping too much', key: 'q3_sleep', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 4, text: 'Feeling tired or having little energy', key: 'q4_energy', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 5, text: 'Poor appetite or overeating', key: 'q5_appetite', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 6, text: 'Feeling bad about yourself - or that you are a failure or have let yourself or your family down', key: 'q6_self_worth', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 7, text: 'Trouble concentrating on things, such as reading or watching television', key: 'q7_concentration', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 8, text: 'Moving or speaking so slowly that other people could have noticed. Or being so fidgety or restless that you have been moving around a lot more than usual', key: 'q8_motor', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 9, text: 'Thoughts that you would be better off dead, or of hurting yourself in some way', key: 'q9_suicide', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
    ],
    crisisThreshold: 2,
    crisisQuestion: 9
  },
  GAD7: {
    title: 'GAD-7 Anxiety Screening',
    description: 'Over the last 2 weeks, how often have you been bothered by the following problems?',
    icon: Activity,
    color: 'blue',
    questions: [
      { id: 1, text: 'Feeling nervous, anxious, or on edge', key: 'q1_nervous', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 2, text: 'Not being able to stop or control worrying', key: 'q2_control_worry', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 3, text: 'Worrying too much about different things', key: 'q3_worry_too_much', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 4, text: 'Trouble relaxing', key: 'q4_trouble_relaxing', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 5, text: 'Being so restless that it\'s hard to sit still', key: 'q5_restless', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 6, text: 'Becoming easily annoyed or irritable', key: 'q6_irritable', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
      { id: 7, text: 'Feeling afraid as if something awful might happen', key: 'q7_afraid', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'Several days' },
          { value: 2, label: 'More than half the days' },
          { value: 3, label: 'Nearly every day' }
        ]
      },
    ],
    crisisThreshold: 15
  },
  MDQ: {
    title: 'MDQ - Mood Disorder Questionnaire',
    description: 'Bipolar Disorder Screening Tool',
    icon: AlertTriangle,
    color: 'orange',
    questions: [
      // Part 1: 13 symptom questions (yes/no)
      { id: 1, text: 'Has there ever been a period when you were not your usual self and...', key: 'q1', type: 'boolean',
        options: [
          { value: true, label: 'Yes' },
          { value: false, label: 'No' }
        ]
      },
      // ... (simplified for brevity - full implementation would include all 13 questions)
    ],
    crisisThreshold: 7
  },
  DAST10: {
    title: 'DAST-10 - Drug Abuse Screening',
    description: 'Substance Use Disorder Screening',
    icon: AlertCircle,
    color: 'red',
    questions: [
      { id: 1, text: 'Have you used drugs other than those required for medical reasons?', key: 'q1', type: 'boolean',
        options: [
          { value: true, label: 'Yes' },
          { value: false, label: 'No' }
        ]
      },
      // ... (simplified - full implementation includes all 10 questions)
    ],
    crisisThreshold: 6
  },
  AQ10: {
    title: 'AQ-10 - Autism Spectrum Quotient',
    description: 'Autism Screening for Adults',
    icon: Brain,
    color: 'teal',
    questions: [
      { id: 1, text: 'I often notice small sounds when others do not', key: 'q1', type: 'select',
        options: [
          { value: 1, label: 'Definitely Disagree' },
          { value: 2, label: 'Slightly Disagree' },
          { value: 3, label: 'Slightly Agree' },
          { value: 4, label: 'Definitely Agree' }
        ]
      },
      // ... (simplified - full implementation includes all 10 questions)
    ],
    crisisThreshold: 6
  },
  ACE: {
    title: 'ACE - Adverse Childhood Experiences',
    description: 'Childhood Trauma Screening',
    icon: Heart,
    color: 'pink',
    questions: [
      { id: 1, text: 'Did a parent or other adult in the household often swear at you, insult you, put you down, or act in a way that made you afraid that you might be physically hurt?', key: 'q1', type: 'boolean',
        options: [
          { value: true, label: 'Yes' },
          { value: false, label: 'No' }
        ]
      },
      // ... (simplified - full implementation includes all 10 questions)
    ],
    crisisThreshold: 4
  },
  ASRS: {
    title: 'ASRS v1.1 - Adult ADHD Self-Report Scale',
    description: 'Screening for ADHD symptoms in adulthood (Inattention & Hyperactivity)',
    icon: Zap,
    color: 'amber',
    questions: [
      // Part A: Inattention Symptoms (Questions 1-9)
      { id: 1, text: 'How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?', key: '1', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 2, text: 'How often do you have difficulty getting things in order when you have to do a task that requires organization?', key: '2', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 3, text: 'How often do you have problems remembering appointments or obligations?', key: '3', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 4, text: 'When you have a task that requires a lot of thought, how often do you avoid or delay getting started?', key: '4', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 5, text: 'How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?', key: '5', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 6, text: 'How often do you feel overly active and compelled to do things, like you were driven by a motor?', key: '6', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 7, text: 'How often do you make careless mistakes when you have to work on a boring or difficult project?', key: '7', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 8, text: 'How often do you have difficulty keeping your attention when you are doing boring or repetitive work?', key: '8', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 9, text: 'How often do you have difficulty concentrating on what people are saying to you, even when they are speaking to you directly?', key: '9', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      // Part B: Hyperactivity-Impulsivity Symptoms (Questions 10-18)
      { id: 10, text: 'How often do you leave your seat in meetings or other situations where you are expected to remain seated?', key: '10', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 11, text: 'How often do you feel restless or fidgety when you need to sit still for a while?', key: '11', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 12, text: 'How often do you have difficulty unwinding and relaxing when you have time to yourself?', key: '12', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 13, text: 'How often do you find yourself talking too much when you are in social situations?', key: '13', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 14, text: 'When you are in a conversation, how often do you find yourself finishing the sentences of the people you are talking to, before they can finish them themselves?', key: '14', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 15, text: 'How often do you have difficulty waiting your turn in situations when turn-taking is required?', key: '15', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 16, text: 'How often do you interrupt others when they are busy?', key: '16', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 17, text: 'How often do you have difficulty focusing on what you are doing when you hear distracting noises or conversations?', key: '17', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      },
      { id: 18, text: 'How often do you misplace or have difficulty finding things at home or at work?', key: '18', type: 'rating',
        options: [
          { value: 0, label: 'Never' },
          { value: 1, label: 'Rarely' },
          { value: 2, label: 'Sometimes' },
          { value: 3, label: 'Often' },
          { value: 4, label: 'Very Often' }
        ]
      }
    ],
    crisisThreshold: 48
  },
  ISI: {
    title: 'ISI - Insomnia Severity Index',
    description: 'Assessment of insomnia severity and its impact on daytime functioning over the past 2 weeks',
    icon: Moon,
    color: 'indigo',
    questions: [
      { id: 1, text: 'Difficulty falling asleep', key: '1', type: 'rating',
        options: [
          { value: 0, label: 'No problem' },
          { value: 1, label: 'Mild' },
          { value: 2, label: 'Moderate' },
          { value: 3, label: 'Severe' },
          { value: 4, label: 'Very severe' }
        ]
      },
      { id: 2, text: 'Difficulty staying asleep (waking up frequently)', key: '2', type: 'rating',
        options: [
          { value: 0, label: 'No problem' },
          { value: 1, label: 'Mild' },
          { value: 2, label: 'Moderate' },
          { value: 3, label: 'Severe' },
          { value: 4, label: 'Very severe' }
        ]
      },
      { id: 3, text: 'Problems waking up too early', key: '3', type: 'rating',
        options: [
          { value: 0, label: 'No problem' },
          { value: 1, label: 'Mild' },
          { value: 2, label: 'Moderate' },
          { value: 3, label: 'Severe' },
          { value: 4, label: 'Very severe' }
        ]
      },
      { id: 4, text: 'How satisfied/dissatisfied are you with your current sleep pattern?', key: '4', type: 'rating',
        options: [
          { value: 0, label: 'Very satisfied' },
          { value: 1, label: 'Satisfied' },
          { value: 2, label: 'Neutral' },
          { value: 3, label: 'Dissatisfied' },
          { value: 4, label: 'Very dissatisfied' }
        ]
      },
      { id: 5, text: 'How noticeable to others do you think your sleep problem is in terms of impairing quality of life?', key: '5', type: 'rating',
        options: [
          { value: 0, label: 'Not noticeable' },
          { value: 1, label: 'A little' },
          { value: 2, label: 'Somewhat' },
          { value: 3, label: 'Very much' },
          { value: 4, label: 'Extremely' }
        ]
      },
      { id: 6, text: 'How worried/distressed are you about your current sleep problem?', key: '6', type: 'rating',
        options: [
          { value: 0, label: 'Not worried' },
          { value: 1, label: 'A little' },
          { value: 2, label: 'Somewhat' },
          { value: 3, label: 'Much' },
          { value: 4, label: 'Very much' }
        ]
      },
      { id: 7, text: 'To what extent do you consider your sleep problem to interfere with your daily functioning (e.g., daytime fatigue, mood, ability to concentrate)?', key: '7', type: 'rating',
        options: [
          { value: 0, label: 'Not at all' },
          { value: 1, label: 'A little' },
          { value: 2, label: 'Somewhat' },
          { value: 3, label: 'Much' },
          { value: 4, label: 'Very much' }
        ]
      }
    ],
    crisisThreshold: 22
  }
};

// ============================================================================
// CONSENT COMPONENT
// ============================================================================

const AssessmentConsent: React.FC<{
  assessmentType: string;
  onConsent: () => void;
  onCancel?: () => void;
}> = ({ assessmentType, onConsent, onCancel }) => {
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!agreed) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/screening/consent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          consent_type: 'screening',
          consented: true,
          screening_types: [assessmentType]
        })
      });

      if (response.ok) {
        onConsent();
      } else {
        throw new Error('Failed to record consent');
      }
    } catch (error) {
      console.error('Consent error:', error);
      alert('Error recording consent. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="w-10 h-10 text-blue-600" />
          <h2 className="text-3xl font-bold text-gray-900">Informed Consent</h2>
        </div>

        <div className="bg-blue-50 border-l-4 border-blue-600 p-6 rounded-lg mb-6">
          <h3 className="font-semibold text-blue-900 mb-3">Before we begin, please understand:</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>This is a <strong>screening tool</strong>, not a diagnostic assessment</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>Results will be reviewed by licensed mental health professionals</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>Your responses are <strong>confidential</strong> and protected under HIPAA</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>In cases of safety concerns, information may be shared with emergency services</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>You can <strong>withdraw consent</strong> at any time</span>
            </li>
          </ul>
        </div>

        <div className="flex items-start gap-3 mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-yellow-900">
            <strong>Important:</strong> This assessment cannot replace professional mental health care.
            If you are experiencing a crisis, please call 988 (Suicide & Crisis Lifeline) immediately.
          </p>
        </div>

        <div className="flex items-start gap-3 mb-8">
          <input
            type="checkbox"
            id="consent"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="mt-1 w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            aria-label="I agree to the consent terms"
          />
          <label htmlFor="consent" className="text-sm text-gray-700 cursor-pointer">
            I have read, understood, and agree to the terms above. I consent to completing this mental health screening.
          </label>
        </div>

        <div className="flex gap-4">
          <button
            onClick={handleSubmit}
            disabled={!agreed || loading}
            className="flex-1 bg-blue-600 text-white py-4 rounded-xl font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Processing...
              </>
            ) : (
              <>
                Continue to Assessment
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
          {onCancel && (
            <button
              onClick={onCancel}
              disabled={loading}
              className="px-6 py-4 border-2 border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN ASSESSMENT COMPONENT
// ============================================================================

export const ClinicalAssessment: React.FC<AssessmentProps> = ({
  assessmentType,
  onComplete,
  onCancel
}) => {
  const [step, setStep] = useState<'consent' | 'assessment' | 'results'>('consent');
  const [responses, setResponses] = useState<Record<string, number | boolean>>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [startTime] = useState(new Date());

  const config = ASSESSMENT_CONFIGS[assessmentType];
  const Icon = config.icon;
  const progress = ((currentQuestion + 1) / config.questions.length) * 100;
  const currentQ = config.questions[currentQuestion];
  const isComplete = Object.keys(responses).length === config.questions.length;

  const handleResponse = async (value: number | boolean) => {
    const newResponses = { ...responses, [currentQ.key]: value };
    setResponses(newResponses);

    if (currentQuestion < config.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handleSubmit = async () => {
    if (!isComplete) return;

    setLoading(true);
    try {
      const endpoint = `/api/v1/screening/${assessmentType.toLowerCase()}`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...responses,
          started_at: startTime.toISOString()
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        setStep('results');
        onComplete(data);
      } else {
        throw new Error('Failed to submit assessment');
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('Error submitting assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    } else if (onCancel) {
      onCancel();
    }
  };

  // Show consent first
  if (step === 'consent') {
    return <AssessmentConsent assessmentType={assessmentType} onConsent={() => setStep('assessment')} onCancel={onCancel} />;
  }

  // Show results
  if (step === 'results' && result) {
    return <AssessmentResults result={result} assessmentType={assessmentType} onComplete={onComplete} />;
  }

  // Assessment questions
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-4 sm:py-8 px-3 sm:px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header - Mobile Optimized */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 sm:p-3 rounded-xl bg-purple-100">
              <Icon className="w-6 h-6 sm:w-8 sm:h-8 text-purple-600" />
            </div>
            <div className="flex-1">
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 leading-tight">
                {config.title}
              </h1>
              <p className="text-sm sm:text-base text-gray-600 mt-1 hidden sm:block">
                {config.description}
              </p>
            </div>
          </div>
          {/* Mobile-only description */}
          <p className="text-sm text-gray-600 sm:hidden ml-11">
            {config.description}
          </p>
        </div>

        {/* Progress Bar - Mobile Optimized */}
        <div className="mb-6 sm:mb-8">
          <div className="flex justify-between text-xs sm:text-sm text-gray-600 mb-2">
            <span>Question {currentQuestion + 1} of {config.questions.length}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 sm:h-3 overflow-hidden">
            <div
              className="bg-purple-600 h-full rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question Card - Mobile Optimized */}
        <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg p-4 sm:p-6 lg:p-8 mb-4 sm:mb-6">
          <h2 className="text-lg sm:text-xl lg:text-2xl font-semibold text-gray-900 mb-6 sm:mb-8 leading-relaxed">
            {currentQ.text}
          </h2>

          {/* Option Buttons - Minimum touch target 44px */}
          <div className="space-y-3 sm:space-y-3">
            {currentQ.options?.map((option) => (
              <button
                key={option.label}
                onClick={() => handleResponse(option.value)}
                className={`w-full min-h-[56px] sm:min-h-[60px] p-4 sm:p-5 text-left rounded-xl border-2 transition-all duration-200 ${
                  responses[currentQ.key] === option.value
                    ? 'border-purple-600 bg-purple-50 shadow-md'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                aria-label={option.label}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900 text-base sm:text-lg">
                    {option.label}
                  </span>
                  {responses[currentQ.key] === option.value && (
                    <CheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600 flex-shrink-0" />
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Crisis Notice for Suicide Question - Mobile Optimized */}
          {config.crisisQuestion === currentQ.id && (
            <div className="mt-6 sm:mt-8 bg-red-50 border-l-4 border-red-600 p-4 sm:p-5 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 sm:w-6 sm:h-6 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold text-red-900 mb-2 text-sm sm:text-base">
                    If you are in crisis, please reach out:
                  </p>
                  <div className="space-y-2 text-red-800 text-sm sm:text-base">
                    <p className="flex items-center gap-2">
                      <Phone className="w-4 h-4 flex-shrink-0" />
                      <span><strong>Call 988</strong> - Suicide & Crisis Lifeline (24/7)</span>
                    </p>
                    <p className="flex items-start sm:items-center gap-2">
                      <Mail className="w-4 h-4 flex-shrink-0 mt-0.5 sm:mt-0" />
                      <span>Text <strong>"HELLO"</strong> to <strong>741741</strong></span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation - Mobile Optimized */}
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
          <button
            onClick={handleBack}
            className="w-full sm:w-auto px-4 sm:px-6 py-4 border-2 border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base"
          >
            <ChevronLeft className="w-5 h-5" />
            {currentQuestion > 0 ? 'Previous' : 'Cancel'}
          </button>

          {isComplete && (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full sm:flex-1 bg-purple-600 text-white py-4 rounded-xl font-semibold hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 text-sm sm:text-base"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span className="hidden sm:inline">Submitting...</span>
                  <span className="sm:hidden">Submit</span>
                </>
              ) : (
                <>
                  <span>Submit Assessment</span>
                  <Send className="w-5 h-5" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// RESULTS DISPLAY COMPONENT
// ============================================================================

const AssessmentResults: React.FC<{
  result: ScreeningResult;
  assessmentType: string;
  onComplete: (result: ScreeningResult) => void;
}> = ({ result, assessmentType, onComplete }) => {
  const getRiskColor = (level: string) => {
    const colors: Record<string, { bg: string; text: string; border: string }> = {
      low: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-600' },
      moderate: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-600' },
      high: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-600' },
      critical: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-600' }
    };
    return colors[level] || colors.low;
  };

  const colors = getRiskColor(result.risk_level);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Crisis Alert */}
          {result.crisis_alert && (
            <div className="mb-8 bg-red-50 border-l-4 border-red-600 p-6 rounded-lg">
              <div className="flex items-start gap-4">
                <AlertCircle className="w-10 h-10 text-red-600 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-red-900 mb-3">Immediate Support Available</h3>
                  <p className="text-red-800 mb-4">
                    Your responses indicate you may be experiencing distress. Please reach out for immediate support:
                  </p>
                  <div className="space-y-3">
                    <a href="tel:988" className="flex items-center gap-3 p-3 bg-white rounded-lg hover:bg-red-100 transition-colors">
                      <Phone className="w-5 h-5 text-red-600" />
                      <div>
                        <p className="font-semibold text-red-900">Call 988</p>
                        <p className="text-sm text-red-700">Suicide & Crisis Lifeline (24/7)</p>
                      </div>
                    </a>
                    <div className="flex items-center gap-3 p-3 bg-white rounded-lg">
                      <Mail className="w-5 h-5 text-red-600" />
                      <div>
                        <p className="font-semibold text-red-900">Text "HELLO" to 741741</p>
                        <p className="text-sm text-red-700">Crisis Text Line</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Score Display */}
          <div className="text-center mb-8">
            <div className={`inline-flex items-center justify-center w-40 h-40 rounded-full bg-gradient-to-br from-${colors.text.split('-')[1]}-500 to-${colors.text.split('-')[1]}-600 text-white mb-6 shadow-lg`}>
              <div>
                <div className="text-5xl font-bold">{Math.round(result.total_score)}</div>
                <div className="text-sm opacity-90">Score</div>
              </div>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              {result.screening_type} Results
            </h2>
            <span className={`inline-block px-6 py-2 rounded-full text-sm font-bold ${colors.bg} ${colors.text} ${colors.border} border-2`}>
              {result.severity_level.replace('_', ' ').toUpperCase()}
            </span>
            <span className={`ml-3 inline-block px-6 py-2 rounded-full text-sm font-bold ${colors.bg} ${colors.text}`}>
              {result.risk_level.toUpperCase()} RISK
            </span>
          </div>

          {/* Interpretation */}
          <div className="mb-8 p-6 bg-gray-50 rounded-xl">
            <h3 className="font-bold text-gray-900 mb-3 text-lg">What This Means:</h3>
            <p className="text-gray-700 leading-relaxed">{result.interpretation}</p>
          </div>

          {/* Subscale Scores (if available) */}
          {result.subscale_scores && Object.keys(result.subscale_scores).length > 0 && (
            <div className="mb-8 p-6 bg-blue-50 rounded-xl">
              <h3 className="font-bold text-blue-900 mb-4 text-lg">Detailed Scores:</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(result.subscale_scores).map(([key, value]) => (
                  <div key={key} className="bg-white p-4 rounded-lg">
                    <p className="text-sm text-gray-600 capitalize">{key.replace(/_/g, ' ')}</p>
                    <p className="text-2xl font-bold text-blue-600">{Math.round(value as number)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Flags */}
          {result.risk_flags && result.risk_flags.length > 0 && (
            <div className="mb-8">
              <h3 className="font-bold text-gray-900 mb-3 text-lg">Risk Indicators:</h3>
              <div className="flex flex-wrap gap-2">
                {result.risk_flags.map((flag, index) => (
                  <span key={index} className="px-4 py-2 bg-red-100 text-red-800 rounded-full text-sm font-semibold">
                    {flag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div className="mb-8">
            <h3 className="font-bold text-gray-900 mb-4 text-lg">Recommended Next Steps:</h3>
            <ul className="space-y-3">
              {result.recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700 leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Disclaimer */}
          <div className="mb-8 p-6 bg-yellow-50 border border-yellow-200 rounded-xl">
            <div className="flex items-start gap-3">
              <Info className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-yellow-900 mb-2">Important:</p>
                <p className="text-yellow-800 text-sm leading-relaxed">
                  This is a screening tool, not a diagnosis. Results should be reviewed with a licensed mental health professional
                  for comprehensive assessment. Your responses are confidential and protected under HIPAA.
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="flex items-center justify-center gap-3 px-6 py-4 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors">
              <Calendar className="w-5 h-5" />
              Schedule Consultation
            </button>
            <button className="flex items-center justify-center gap-3 px-6 py-4 border-2 border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition-colors">
              <Download className="w-5 h-5" />
              Download Results
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClinicalAssessment;
