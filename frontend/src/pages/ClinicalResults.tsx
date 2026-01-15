import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertTitle } from '@/components/ui/alert';

interface AssessmentResult {
  score: number;
  severity_level: string;
  severity?: {
    label: string;
    color: string;
    description: string;
  };
  crisisAlert: boolean;
  recommendations: string[];
  resources: {
    title: string;
    description: string;
    link?: string;
    phone?: string;
  }[];
}

const ClinicalResults: React.FC = () => {
  const { tool } = useParams<{ tool: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [assessmentMetadata, setAssessmentMetadata] = useState<any>(null);

  useEffect(() => {
    // Check for assessment ID in URL hash
    const hash = window.location.hash.substring(1); // Remove #

    // Get results from location state or fetch from API
    if (location.state?.result) {
      setResult({
        ...location.state.result,
        severity: getSeverityInfo(location.state.result.severity_level),
        crisisAlert: location.state.crisisAlert,
        recommendations: getRecommendations(tool!, location.state.result.severity_level),
        resources: getResources(tool!, location.state.result.severity_level, location.state.crisisAlert),
      });

      // Set metadata from location state
      setAssessmentMetadata({
        assessmentId: location.state.assessmentId,
        completedAt: location.state.completedAt,
        notes: location.state.notes,
        responseData: location.state.responseData,
        providerNotified: location.state.providerNotified,
        nextAssessmentDate: location.state.nextAssessmentDate
      });

      setLoading(false);
    } else if (hash) {
      // Fetch specific assessment by ID from hash
      fetchAssessmentById(hash);
    } else {
      // Fetch results from API if not in state
      fetchResults();
    }
  }, [tool, location.state, window.location.hash]);

  const fetchAssessmentById = async (assessmentId: string) => {
    try {
      const response = await fetch(`/api/v1/clinical/screenings/${assessmentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setResult({
          score: data.total_score,
          severity_level: data.severity_level,
          severity: getSeverityInfo(data.severity_level),
          crisisAlert: data.crisis_alert,
          recommendations: getRecommendations(tool!, data.severity_level),
          resources: getResources(tool!, data.severity_level, data.crisis_alert),
        });

        // Set metadata
        setAssessmentMetadata({
          assessmentId: data.id,
          completedAt: data.completed_at,
          notes: data.notes,
          responseData: data.response_data,
          providerNotified: data.provider_notified,
          nextAssessmentDate: data.next_assessment_date
        });
      }
    } catch (error) {
      console.error('Error fetching assessment:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchResults = async () => {
    try {
      const response = await fetch(`/api/v1/clinical/screenings/latest/${tool}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setResult({
          ...data,
          severity: getSeverityInfo(data.severity_level),
          crisisAlert: data.crisis_alert,
          recommendations: getRecommendations(tool!, data.severity_level),
          resources: getResources(tool!, data.severity_level, data.crisis_alert),
        });
      }
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityInfo = (severityLevel: string) => {
    const severityMap: Record<string, { label: string; color: string; description: string }> = {
      'Minimal': { label: 'Minimal Symptoms', color: 'green', description: 'Little to no symptoms detected' },
      'Mild': { label: 'Mild Symptoms', color: 'yellow', description: 'Mild symptoms that may benefit from self-care' },
      'Moderate': { label: 'Moderate Symptoms', color: 'orange', description: 'Moderate symptoms - consider professional support' },
      'Moderately Severe': { label: 'Moderately Severe', color: 'red', description: 'Significant symptoms - professional treatment recommended' },
      'Severe': { label: 'Severe Symptoms', color: 'red', description: 'Severe symptoms - immediate professional help needed' },
    };
    return severityMap[severityLevel] || severityMap['Minimal'];
  };

  const getRecommendations = (toolType: string, severityLevel: string): string[] => {
    // PCL-5 PTSD specific recommendations
    if (toolType === 'pcl5') {
      const pcl5Recommendations = {
        'Minimal': [
          'Your symptoms suggest minimal PTSD symptoms at this time',
          'Continue to monitor your symptoms and stress levels',
          'Practice good self-care: regular sleep, healthy eating, and exercise',
          'Consider building a strong support network of friends and family',
          'Learn about trauma and its effects to better understand your experiences',
        ],
        'Mild': [
          'Your symptoms suggest mild PTSD symptoms that may benefit from attention',
          'Consider scheduling an appointment with a mental health professional specializing in trauma',
          'Practice grounding techniques when feeling overwhelmed (5-4-3-2-1 method, deep breathing)',
          'Maintain a regular routine and sleep schedule to help with stability',
          'Reach out to trusted friends or family members for support',
          'Consider trauma-focused therapy options like EMDR or Cognitive Processing Therapy',
        ],
        'Moderate': [
          'Your symptoms suggest moderate PTSD symptoms that would benefit from professional treatment',
          'Seek evaluation from a mental health professional with trauma expertise as soon as possible',
          'Evidence-based treatments like EMDR, Cognitive Processing Therapy, or Prolonged Exposure are highly effective',
          'Consider both individual therapy and possibly medication evaluation',
          'Build a comprehensive support system including healthcare providers, family, and peer support',
          'Avoid alcohol and drugs as coping mechanisms - they can worsen PTSD symptoms',
        ],
        'Moderately Severe': [
          'Your symptoms suggest moderately severe PTSD requiring immediate professional attention',
          'Contact a trauma-specialist mental health professional this week',
          'Consider both trauma-focused therapy and medication evaluation',
          'Inform family or trusted friends about your symptoms for immediate support',
          'Create a safety plan for difficult moments and crisis situations',
          'This level of symptoms often responds very well to proper treatment',
        ],
        'Severe': [
          'Your symptoms suggest severe PTSD requiring immediate professional intervention',
          'Contact a mental health professional TODAY - severe symptoms are highly treatable with proper care',
          'Call the Veterans Crisis Line (988 then press 1) if you\'re a veteran, or 988 for civilian support',
          'Consider going to an emergency room or crisis center if you feel unsafe',
          'This is not a life sentence - with proper treatment, severe PTSD symptoms can significantly improve',
          'Avoid being alone - reach out to family, friends, or crisis support immediately',
          'Treatment works and recovery is possible - you deserve help and support',
        ],
      };
      return pcl5Recommendations[severityLevel] || pcl5Recommendations['Minimal'];
    }

    // AUDIT specific recommendations
    if (toolType === 'audit') {
      const auditRecommendations = {
        'Minimal': [
          'Your drinking pattern appears to be low risk',
          'Continue to follow healthy drinking guidelines',
          'Monitor your alcohol consumption and stay within recommended limits',
          'Consider alcohol-free days each week',
        ],
        'Mild': [
          'Your drinking pattern suggests some risk that may require attention',
          'Consider reducing your alcohol consumption',
          'Set limits on drinking days and drinks per occasion',
          'Track your drinking patterns for better awareness',
          'Discuss your alcohol use with your healthcare provider',
        ],
        'Moderate': [
          'Your drinking pattern indicates moderate risk requiring attention',
          'Strongly consider reducing or abstaining from alcohol',
          'Seek professional help from a healthcare provider or addiction specialist',
          'Address underlying reasons for alcohol use with counseling',
          'Build a support system for maintaining reduced drinking',
        ],
        'Severe': [
          'Your drinking pattern indicates high risk requiring immediate attention',
          'Seek professional help immediately for alcohol use disorder',
          'Consider medical detoxification if you experience withdrawal symptoms',
          'Comprehensive treatment including counseling, support groups, and possibly medication',
          'This condition is treatable and recovery is possible with proper support',
        ],
      };
      return auditRecommendations[severityLevel] || auditRecommendations['Minimal'];
    }

    // DASS-21 specific recommendations
    if (toolType === 'dass21') {
      const dass21Recommendations = {
        'Minimal': [
          'Your symptoms suggest minimal distress - continue maintaining good mental health habits',
          'Practice regular self-care: exercise, sleep hygiene, and stress management',
          'Stay connected with friends, family, and supportive communities',
          'Monitor your stress levels and take breaks when feeling overwhelmed',
          'Consider mindfulness or meditation practices to build emotional resilience',
        ],
        'Mild': [
          'Your symptoms suggest mild distress that may benefit from attention and self-care strategies',
          'Consider scheduling an appointment with your primary care provider to discuss symptoms',
          'Try evidence-based stress management: deep breathing, progressive muscle relaxation, mindfulness',
          'Maintain regular exercise (30 minutes daily) - it\'s as effective as some medications for mild depression',
          'Challenge negative thoughts by questioning their accuracy and finding balanced perspectives',
          'Ensure adequate sleep (7-9 hours) and establish consistent sleep/wake times',
        ],
        'Moderate': [
          'Your symptoms suggest moderate distress that would benefit from professional intervention',
          'Seek evaluation from a mental health professional for therapy and/or medication assessment',
          'Evidence-based treatments like CBT have 60-70% success rates for moderate depression/anxiety',
          'Consider both therapy and possibly medication - combined treatment often works best',
          'Build a comprehensive support network including healthcare providers, family, and peers',
          'Address lifestyle factors: reduce alcohol, improve nutrition, establish exercise routine',
        ],
        'Moderately Severe': [
          'Your symptoms suggest moderately severe distress requiring prompt professional attention',
          'Contact a mental health professional within the next week for evaluation and treatment planning',
          'Consider both evidence-based therapy (CBT, ACT, DBT) and medication evaluation',
          'Inform trusted family or friends about your symptoms for immediate support',
          'Create a safety plan if you experience thoughts of self-harm',
          'This level of symptoms responds well to proper treatment with significant improvement expected',
        ],
        'Severe': [
          'Your symptoms suggest severe distress requiring immediate professional intervention',
          'Contact a mental health professional or crisis services TODAY - severe symptoms are highly treatable',
          'Call 988 if you have thoughts of harming yourself or feel unsafe',
          'Consider going to an emergency room if you feel unable to keep yourself safe',
          'Severe depression/anxiety are medical emergencies requiring immediate attention',
          'With proper treatment, most people experience dramatic improvement even from severe symptoms',
          'You are not alone - effective help is available and recovery is possible',
        ],
      };
      return dass21Recommendations[severityLevel] || dass21Recommendations['Minimal'];
    }

    // PHQ-9 specific recommendations
    if (toolType === 'phq9') {
      const phq9Recommendations = {
        'Minimal': [
          'Your symptoms suggest minimal depression - maintain good mental health practices',
          'Continue regular exercise (30 minutes daily) - natural mood booster',
          'Maintain social connections and meaningful activities',
          'Practice good sleep hygiene and regular daily routine',
          'Monitor your mood and seek help early if symptoms worsen',
        ],
        'Mild': [
          'Your symptoms suggest mild depression that often responds well to self-help strategies',
          'Consider behavioral activation: schedule pleasant activities even when motivation is low',
          'Exercise regularly - research shows it\'s as effective as some antidepressants for mild depression',
          'Practice sleep hygiene and establish consistent daily routines',
          'Consider talking to your primary care provider about treatment options',
          'Stay socially connected even when you don\'t feel like it',
        ],
        'Moderate': [
          'Your symptoms suggest moderate depression that would benefit from professional treatment',
          'Seek evaluation from a mental health professional for therapy and/or medication',
          'Evidence-based treatments like CBT or interpersonal therapy are highly effective',
          'Consider antidepressant medication - 60-70% of people respond to first attempt',
          'Combine therapy with exercise and lifestyle modifications for best results',
          'Build a support network and consider sharing your feelings with trusted others',
        ],
        'Moderately Severe': [
          'Your symptoms suggest moderately severe depression requiring prompt professional attention',
          'Contact a mental health professional within the next week for comprehensive treatment',
          'Consider both therapy and medication - combined treatment often works best',
          'If you have thoughts of self-harm, call 988 immediately or go to emergency room',
          'Involve trusted family members or friends in your treatment planning',
          'This level of depression responds well to proper treatment with significant improvement expected',
        ],
        'Severe': [
          'Your symptoms indicate severe depression requiring immediate professional intervention',
          'Contact mental health professional or crisis services TODAY - severe depression is highly treatable',
          'Call 988 immediately if you have thoughts of harming yourself or feel unable to keep yourself safe',
          'Consider going to emergency room if you feel unable to care for yourself or have safety concerns',
          'Severe depression is a medical emergency - immediate treatment can provide rapid relief',
          'With proper treatment, most people experience dramatic improvement even from severe symptoms',
          'You are not alone in this - effective help is available and recovery is possible',
        ],
      };
      return phq9Recommendations[severityLevel] || phq9Recommendations['Minimal'];
    }

    // GAD-7 specific recommendations
    if (toolType === 'gad7') {
      const gad7Recommendations = {
        'Minimal': [
          'Your symptoms suggest minimal anxiety - continue maintaining good stress management habits',
          'Practice regular relaxation techniques like deep breathing or progressive muscle relaxation',
          'Maintain regular exercise routine to reduce stress hormones',
          'Limit caffeine and alcohol, which can worsen anxiety symptoms',
          'Stay connected with supportive friends and family members',
        ],
        'Mild': [
          'Your symptoms suggest mild anxiety that often improves with self-help strategies',
          'Practice daily anxiety management techniques (10-15 minutes of breathing or meditation)',
          'Try the 4-7-8 breathing technique: inhale 4, hold 7, exhale 8',
          'Schedule "worry time" - 15 minutes daily to address concerns, then postpone other worries',
          'Consider mindfulness apps or online CBT programs for anxiety management',
          'Ensure adequate sleep as sleep deprivation worsens anxiety',
        ],
        'Moderate': [
          'Your symptoms suggest moderate anxiety that would benefit from professional treatment',
          'Seek evaluation from a mental health professional for anxiety-focused therapy',
          'Cognitive-behavioral therapy is highly effective for anxiety disorders (70-80% success rates)',
          'Consider anxiety medication consultation with your primary care provider or psychiatrist',
          'Practice regular exposure to feared situations to reduce avoidance patterns',
          'Join a support group for anxiety to learn from others with similar experiences',
        ],
        'Severe': [
          'Your symptoms indicate severe anxiety requiring immediate professional attention',
          'Contact a mental health professional this week for comprehensive anxiety treatment',
          'Consider both therapy and medication for rapid symptom relief',
          'If experiencing panic attacks, learn immediate grounding techniques and safety strategies',
          'Avoid isolation - reach out to supportive friends, family, or crisis services',
          'Severe anxiety responds very well to proper treatment with significant improvement expected',
        ],
      };
      return gad7Recommendations[severityLevel] || gad7Recommendations['Minimal'];
    }

    // Stress Scale specific recommendations
    if (toolType === 'stress') {
      const stressRecommendations = {
        'Minimal': [
          'Your stress levels appear manageable - continue maintaining healthy stress management habits',
          'Practice regular relaxation techniques and stress reduction activities',
          'Maintain work-life balance and set healthy boundaries',
          'Continue regular physical activity and adequate sleep',
          'Monitor stress levels and seek help early if they increase',
        ],
        'Mild': [
          'Your stress levels suggest mild stress that could benefit from attention',
          'Implement daily stress management: 10-15 minutes of meditation or deep breathing',
          'Practice time management: prioritize tasks and set realistic boundaries',
          'Ensure adequate sleep and regular exercise to build stress resilience',
          'Consider reducing caffeine and alcohol, which can increase stress hormones',
          'Schedule regular breaks during work or study periods',
        ],
        'Moderate': [
          'Your stress levels indicate moderate stress requiring attention and management',
          'Develop a comprehensive stress management plan with coping strategies',
          'Consider professional help to develop personalized stress reduction techniques',
          'Evaluate workload and commitments - consider what can be delegated or eliminated',
          'Practice assertive communication to set healthy boundaries',
          'Ensure regular self-care activities and maintain social support connections',
        ],
        'Severe': [
          'Your stress levels are high and require immediate attention and intervention',
          'Seek professional help this week to develop comprehensive stress management strategies',
          'Consider reducing workload or taking time off if possible to prevent burnout',
          'Practice immediate stress reduction techniques multiple times daily',
          'Reach out to your support system - don\'t isolate yourself during high stress periods',
          'High stress is a risk factor for serious health conditions - prioritize stress reduction now',
        ],
      };
      return stressRecommendations[severityLevel] || stressRecommendations['Minimal'];
    }

    // Wellbeing Assessment specific recommendations
    if (toolType === 'wellbeing') {
      const wellbeingRecommendations = {
        'Minimal': [
          'Your wellbeing appears strong - continue practices that support your mental health',
          'Maintain regular exercise, adequate sleep, and healthy nutrition',
          'Continue investing in meaningful relationships and activities',
          'Practice regular gratitude and positive reflection',
          'Consider mentoring others in wellbeing practices',
        ],
        'Mild': [
          'Your wellbeing suggests areas for improvement and growth opportunities',
          'Focus on strengthening areas where you scored lower while maintaining strengths',
          'Implement daily wellbeing practices: gratitude, mindfulness, or meaningful activities',
          'Consider setting specific wellbeing goals and tracking your progress',
          'Invest time in relationships and activities that bring you joy and meaning',
          'Ensure basic self-care: exercise, sleep, nutrition, and social connection',
        ],
        'Moderate': [
          'Your wellbeing suggests several areas that could benefit from attention and improvement',
          'Consider professional support to develop a personalized wellbeing enhancement plan',
          'Focus on building mental wellbeing practices: positive emotions, engagement, relationships',
          'Address specific challenges through therapy, coaching, or support groups',
          'Implement lifestyle changes that support mental and physical health',
          'Build resilience through regular practice of coping skills and self-care',
        ],
        'Low': [
          'Your wellbeing suggests significant challenges requiring comprehensive attention',
          'Seek professional help to address underlying mental health concerns',
          'Focus on basic wellbeing foundations: sleep, nutrition, exercise, and social connection',
          'Consider therapy or counseling to develop coping strategies and address specific concerns',
          'Build a support network and don\'t hesitate to reach out for help',
          'Start with small, achievable improvements in daily routines and self-care practices',
        ],
      };
      return wellbeingRecommendations[severityLevel] || wellbeingRecommendations['Low'];
    }

    // DASS-21 and other general mental health recommendations (fallback)
    const baseRecommendations = [
      'Keep track of your symptoms and how they affect your daily life',
      'Consider sharing these results with a healthcare provider',
      'Practice self-care activities like exercise, sleep hygiene, and stress management',
    ];

    const severityRecommendations: Record<string, string[]> = {
      'Minimal': [
        ...baseRecommendations,
        'Continue monitoring your mental health',
        'Maintain healthy lifestyle habits',
      ],
      'Mild': [
        ...baseRecommendations,
        'Consider talking to a friend or family member about how you\'re feeling',
        'Try stress reduction techniques like mindfulness or meditation',
        'Schedule an appointment with your primary care provider',
      ],
      'Moderate': [
        ...baseRecommendations,
        'Schedule an appointment with a mental health professional',
        'Consider therapy or counseling',
        'Reach out to your support system for help',
      ],
      'Moderately Severe': [
        'Seek professional help as soon as possible',
        'Consider both therapy and medication evaluation',
        'Inform your support system about your symptoms',
        'Follow up regularly with healthcare providers',
      ],
      'Severe': [
        'Seek immediate professional help',
        'Contact a mental health crisis line',
        'Consider emergency services if you have thoughts of harming yourself',
        'Do not wait - severe symptoms need immediate attention',
      ],
    };

    return severityRecommendations[severityLevel] || baseRecommendations;
  };

  const getResources = (toolType: string, severityLevel: string, crisisAlert: boolean) => {
    // PCL-5 PTSD specific resources
    if (toolType === 'pcl5') {
      const crisisResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 free and confidential support for people in distress',
          phone: '988',
        },
        {
          title: 'Crisis Text Line',
          description: 'Text HOME to 741741 for crisis counseling',
          phone: 'Text HOME to 741741',
        },
        {
          title: 'Veterans Crisis Line',
          description: 'For veterans and their families',
          phone: '988 then press 1',
        },
        {
          title: 'SAMHSA National Helpline',
          description: '24/7 treatment referral and information service',
          phone: '1-800-662-HELP (4357)',
        },
      ];

      const pcl5GeneralResources = [
        {
          title: 'PTSD Treatment Options',
          description: 'Learn about evidence-based PTSD treatments and find providers',
          link: '/clinical/resources/ptsd-treatment',
        },
        {
          title: 'EMDR International Association',
          description: 'Find EMDR-trained therapists for trauma treatment',
          link: 'https://emdria.org',
        },
        {
          title: 'National Center for PTSD',
          description: 'Information, apps, and resources for PTSD recovery',
          link: 'https://www.ptsd.va.gov',
        },
        {
          title: 'Trauma-Informed Support Groups',
          description: 'Connect with others who understand trauma recovery',
          link: '/clinical/resources/support-groups',
        },
        {
          title: 'Grounding Techniques & Self-Help',
          description: 'Learn coping skills for managing trauma symptoms',
          link: '/clinical/resources/grounding-techniques',
        },
      ];

      const isSevere = severityLevel === 'Severe' || severityLevel === 'Moderately Severe';
      return isSevere ? crisisResources : [...crisisResources, ...pcl5GeneralResources];
    }

    // AUDIT specific resources
    if (toolType === 'audit') {
      const alcoholResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 support and mental health crisis intervention',
          phone: '988',
        },
        {
          title: 'SAMHSA National Helpline',
          description: '24/7 treatment referral for substance use disorders',
          phone: '1-800-662-HELP (4357)',
        },
        {
          title: 'Alcoholics Anonymous',
          description: 'Find local AA meetings and peer support',
          link: 'https://www.aa.org',
        },
        {
          title: 'SMART Recovery',
          description: 'Science-based addiction recovery support groups',
          link: 'https://www.smartrecovery.org',
        },
        {
          title: 'Find Treatment Providers',
          description: 'Locate substance abuse treatment facilities',
          link: 'https://findtreatment.gov',
        },
      ];
      return alcoholResources;
    }

    // DASS-21 specific resources
    if (toolType === 'dass21') {
      const dass21Resources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 free and confidential support for emotional distress',
          phone: '988',
        },
        {
          title: 'Crisis Text Line',
          description: 'Text HOME to 741741 for crisis counseling',
          phone: 'Text HOME to 741741',
        },
        {
          title: 'SAMHSA National Helpline',
          description: '24/7 treatment referral and information service',
          phone: '1-800-662-HELP (4357)',
        },
        {
          title: 'Anxiety & Depression Association of America',
          description: 'Information, resources, and therapist directory',
          link: 'https://adaa.org',
        },
        {
          title: 'National Alliance on Mental Illness (NAMI)',
          description: 'Support groups, education, and advocacy resources',
          link: 'https://www.nami.org',
        },
        {
          title: 'Depression and Bipolar Support Alliance',
          description: 'Peer-led support groups and resources',
          link: 'https://www.dbsalliance.org',
        },
        {
          title: 'Mindfulness & Meditation Apps',
          description: 'Guided exercises for anxiety and stress management',
          link: '/clinical/resources/mindfulness-apps',
        },
        {
          title: 'Cognitive Behavioral Therapy Resources',
          description: 'Learn CBT techniques for managing depression and anxiety',
          link: '/clinical/resources/cbt-techniques',
        },
      ];

      const isSevere = severityLevel === 'Severe' || severityLevel === 'Moderately Severe';
      const severeResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 immediate support for severe emotional distress',
          phone: '988',
        },
        {
          title: 'Emergency Services',
          description: 'Go to nearest emergency room or call 911 if in immediate danger',
          phone: '911',
        },
        {
          title: 'SAMHSA Disaster Distress Helpline',
          description: 'Immediate crisis counseling and support',
          phone: '1-800-985-5990',
        },
      ];

      return isSevere ? severeResources : dass21Resources;
    }

    // PHQ-9 specific resources
    if (toolType === 'phq9') {
      const depressionResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 free and confidential support for depression and crisis',
          phone: '988',
        },
        {
          title: 'Crisis Text Line',
          description: 'Text HOME to 741741 for depression and crisis support',
          phone: 'Text HOME to 741741',
        },
        {
          title: 'National Suicide Prevention Lifeline',
          description: '24/7 support for people in emotional distress',
          phone: '1-800-273-8255',
        },
        {
          title: 'Depression and Bipolar Support Alliance',
          description: 'Peer-led support groups and depression resources',
          link: 'https://www.dbsalliance.org',
        },
        {
          title: 'American Foundation for Suicide Prevention',
          description: 'Depression awareness, education, and prevention resources',
          link: 'https://afsp.org',
        },
        {
          title: 'National Institute of Mental Health',
          description: 'Evidence-based depression information and treatment resources',
          link: 'https://www.nimh.nih.gov/health/topics/depression',
        },
        {
          title: 'Psychology Today Therapy Finder',
          description: 'Directory of mental health professionals specializing in depression',
          link: 'https://www.psychologytoday.com/us/therapists/depression',
        },
        {
          title: 'Depression Treatment Options',
          description: 'Learn about therapy, medication, and lifestyle approaches',
          link: '/clinical/resources/depression-treatment',
        },
      ];

      const severeDepressionResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: 'Immediate 24/7 support for severe depression and suicidal thoughts',
          phone: '988',
        },
        {
          title: 'Emergency Services',
          description: 'Go to nearest emergency room or call 911 if in immediate danger',
          phone: '911',
        },
        {
          title: 'Crisis Text Line',
          description: '24/7 crisis support via text message',
          phone: 'Text HOME to 741741',
        },
        {
          title: 'SAMHSA Helpline',
          description: '24/7 treatment referral and crisis support',
          phone: '1-800-662-HELP (4357)',
        },
      ];

      return score >= 20 ? severeDepressionResources : depressionResources;
    }

    // GAD-7 specific resources
    if (toolType === 'gad7') {
      const anxietyResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 support for anxiety and emotional distress',
          phone: '988',
        },
        {
          title: 'Anxiety & Depression Association of America',
          description: 'Anxiety disorders information, resources, and therapist directory',
          link: 'https://adaa.org',
        },
        {
          title: 'Anxiety Resource Center',
          description: 'Evidence-based information and self-help resources',
          link: 'https://anxiety.org',
        },
        {
          title: 'Mental Health America',
          description: 'Anxiety screening tools and educational resources',
          link: 'https://mhanational.org/conditions/anxiety-disorders',
        },
        {
          title: 'Calm App',
          description: 'Meditation and sleep app for anxiety management',
          link: 'https://www.calm.com',
        },
        {
          title: 'Headspace App',
          description: 'Guided meditation and mindfulness for anxiety',
          link: 'https://www.headspace.com',
        },
        {
          title: 'Anxiety Support Groups',
          description: 'Find local and online anxiety support communities',
          link: '/clinical/resources/anxiety-support-groups',
        },
        {
          title: 'Therapist Directory for Anxiety',
          description: 'Find specialists in anxiety and panic disorders',
          link: '/clinical/resources/anxiety-therapists',
        },
      ];

      const severeAnxietyResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 immediate support for severe anxiety and panic',
          phone: '988',
        },
        {
          title: 'Panic Disorder Information Hotline',
          description: 'Support for panic attacks and severe anxiety',
          phone: '1-800-64-PANIC (72642)',
        },
        {
          title: 'Crisis Text Line',
          description: '24/7 support via text for anxiety crises',
          phone: 'Text HOME to 741741',
        },
        {
          title: 'Emergency Services',
          description: 'For severe panic attacks or inability to function',
          phone: '911',
        },
      ];

      return score >= 15 ? severeAnxietyResources : anxietyResources;
    }

    // Stress Scale specific resources
    if (toolType === 'stress') {
      const stressResources = [
        {
          title: 'American Institute of Stress',
          description: 'Stress management information and resources',
          link: 'https://www.stress.org',
        },
        {
          title: 'Mindfulness-Based Stress Reduction',
          description: 'Learn MBSR techniques for stress management',
          link: '/clinical/resources/mbsr',
        },
        {
          title: 'Stress Management Apps',
          description: 'Top-rated apps for stress reduction and relaxation',
          link: '/clinical/resources/stress-apps',
        },
        {
          title: 'Work-Life Balance Resources',
          description: 'Strategies for managing work-related stress',
          link: '/clinical/resources/work-life-balance',
        },
        {
          title: 'Progressive Muscle Relaxation Guide',
          description: 'Step-by-step guide to stress reduction technique',
          link: '/clinical/resources/progressive-relaxation',
        },
        {
          title: 'Time Management Tools',
          description: 'Apps and techniques for reducing time-related stress',
          link: '/clinical/resources/time-management',
        },
        {
          title: 'Burnout Prevention Resources',
          description: 'Identify and prevent burnout symptoms',
          link: '/clinical/resources/burnout-prevention',
        },
      ];

      return stressResources;
    }

    // Wellbeing Assessment specific resources
    if (toolType === 'wellbeing') {
      const wellbeingResources = [
        {
          title: 'Positive Psychology Resources',
          description: 'Science-based wellbeing enhancement strategies',
          link: '/clinical/resources/positive-psychology',
        },
        {
          title: 'PERMA Wellbeing Model',
          description: 'Learn the five elements of flourishing',
          link: '/clinical/resources/perma-model',
        },
        {
          title: 'Happify App',
          description: 'Science-based activities and games for emotional wellbeing',
          link: 'https://www.happify.com',
        },
        {
          title: 'Gratitude Journal Resources',
          description: 'Guided gratitude practices and journals',
          link: '/clinical/resources/gratitude-practice',
        },
        {
          title: 'Mindfulness Meditation Resources',
          description: 'Guided meditations for mental wellbeing',
          link: '/clinical/resources/mindfulness-meditation',
        },
        {
          title: 'Life Coaching Directory',
          description: 'Find coaches specializing in wellbeing and life satisfaction',
          link: '/clinical/resources/life-coaching',
        },
        {
          title: 'Purpose and Meaning Resources',
          description: 'Exercises to discover life purpose and meaning',
          link: '/clinical/resources/purpose-meaning',
        },
        {
          title: 'Social Connection Building',
          description: 'Strategies for building meaningful relationships',
          link: '/clinical/resources/social-connection',
        },
      ];

      const lowWellbeingResources = [
        {
          title: '988 Suicide & Crisis Lifeline',
          description: '24/7 support for emotional distress and crisis',
          phone: '988',
        },
        {
          title: 'Mental Health America Screening',
          description: 'Free confidential mental health screening tools',
          link: 'https://screening.mhanational.org',
        },
        {
          title: 'National Alliance on Mental Illness',
          description: 'Support, education, and advocacy resources',
          link: 'https://www.nami.org',
        },
        {
          title: 'Therapist Directory',
          description: 'Find mental health professionals for comprehensive support',
          link: '/clinical/resources/find-therapist',
        },
      ];

      return score <= 30 ? lowWellbeingResources : wellbeingResources;
    }

    // General mental health resources for other assessments
    const baseResources = [
      {
        title: '988 Suicide & Crisis Lifeline',
        description: '24/7 free and confidential support',
        phone: '988',
      },
      {
        title: 'Crisis Text Line',
        description: 'Text HOME to 741741 for crisis counseling',
        phone: 'Text HOME to 741741',
      },
    ];

    const additionalResources = [
      {
        title: 'Find a Therapist',
        description: 'Directory of mental health professionals',
        link: '/clinical/providers',
      },
      {
        title: 'Self-Help Resources',
        description: 'Guided exercises and coping strategies',
        link: '/clinical/resources',
      },
    ];

    return crisisAlert ? baseResources : [...baseResources, ...additionalResources];
  };

  const handleSaveResults = async () => {
    setSaving(true);
    try {
      await fetch('/api/v1/clinical/screenings/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          tool,
          result,
        }),
      });
    } catch (error) {
      console.error('Error saving results:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleShareWithProvider = () => {
    navigate('/clinical/referrals/new', { state: { assessmentResult: result } });
  };

  const handleRetakeAssessment = () => {
    navigate(`/clinical/assessment/${tool}/take`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your results...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Results not found</p>
          <Button onClick={() => navigate('/clinical-assessments')}>
            Back to Assessments
          </Button>
        </div>
      </div>
    );
  }

  const { score, severity, crisisAlert, recommendations, resources } = result;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/clinical-assessments')}
            className="mb-4"
          >
            ← Back to Assessments
          </Button>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Assessment Results
          </h1>
          <div className="flex items-center justify-between">
            <p className="text-lg text-gray-600">
              {tool?.toUpperCase()} - Completed on {
                assessmentMetadata?.completedAt
                  ? new Date(assessmentMetadata.completedAt).toLocaleDateString()
                  : new Date().toLocaleDateString()
              }
            </p>
            {assessmentMetadata?.assessmentId && (
              <p className="text-sm text-gray-500">
                ID: {assessmentMetadata.assessmentId}
              </p>
            )}
          </div>
        </div>

        {/* Assessment Metadata Card */}
        {assessmentMetadata && (
          <Card className="mb-8 bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-900">Assessment Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {assessmentMetadata.responseData && (
                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">Completion Information</h4>
                    <div className="space-y-1 text-gray-700">
                      {assessmentMetadata.responseData.duration && (
                        <p>• Time to complete: {assessmentMetadata.responseData.duration}</p>
                      )}
                      {assessmentMetadata.responseData.questions_answered && (
                        <p>• Questions answered: {assessmentMetadata.responseData.questions_answered}</p>
                      )}
                      {assessmentMetadata.responseData.skipped_questions !== undefined && (
                        <p>• Questions skipped: {assessmentMetadata.responseData.skipped_questions}</p>
                      )}
                    </div>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-blue-900 mb-2">Status & Follow-up</h4>
                  <div className="space-y-1 text-gray-700">
                    {assessmentMetadata.providerNotified !== undefined && (
                      <p>• Provider notified: {assessmentMetadata.providerNotified ? 'Yes' : 'No'}</p>
                    )}
                    {assessmentMetadata.nextAssessmentDate && (
                      <p>• Next assessment: {new Date(assessmentMetadata.nextAssessmentDate).toLocaleDateString()}</p>
                    )}
                  </div>
                </div>

                {assessmentMetadata.notes && (
                  <div className="md:col-span-2">
                    <h4 className="font-semibold text-blue-900 mb-2">Notes</h4>
                    <p className="text-gray-700 italic">{assessmentMetadata.notes}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Crisis Alert */}
        {crisisAlert && (
          <Alert variant="destructive" className="mb-8">
            <AlertTitle>Immediate Attention Recommended</AlertTitle>
            <p className="mt-2">
              Your responses indicate that you may benefit from immediate professional support.
              Please reach out to one of the crisis resources below or contact emergency services.
            </p>
            <div className="mt-4">
              <Button
                variant="destructive"
                onClick={() => navigate('/clinical/emergency')}
              >
                Get Immediate Help
              </Button>
            </div>
          </Alert>
        )}

        {/* Score Summary */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Your Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-6xl font-bold text-gray-900 mb-4">{score}</div>
              <div
                className={`inline-block px-4 py-2 rounded-full text-white font-medium mb-4 ${
                  severity?.color === 'green' ? 'bg-green-500' :
                  severity?.color === 'yellow' ? 'bg-yellow-500' :
                  severity?.color === 'orange' ? 'bg-orange-500' :
                  'bg-red-500'
                }`}
              >
                {severity?.label}
              </div>
              <p className="text-gray-600 max-w-2xl mx-auto">
                {severity?.description}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* PCL-5 Specific Information */}
        {tool === 'pcl5' && (
          <Card className="mb-8 bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-900">Understanding Your PCL-5 Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h4 className="font-semibold text-blue-900 mb-2">What Your Score Means:</h4>
                  <p className="text-sm leading-relaxed">
                    The PCL-5 assesses PTSD symptoms across four clusters: Intrusion (re-experiencing),
                    Avoidance, Negative alterations in cognitions and mood, and Alterations in arousal
                    and reactivity. Your score reflects the frequency and severity of these symptoms
                    over the past month.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-blue-900 mb-2">About PTSD Treatment:</h4>
                  <p className="text-sm leading-relaxed">
                    PTSD is highly treatable with evidence-based therapies. The most effective treatments
                    include EMDR (Eye Movement Desensitization and Reprocessing), Cognitive Processing
                    Therapy, Prolonged Exposure Therapy, and trauma-focused CBT. Many people experience
                    significant improvement within 12-16 weeks of proper treatment.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-blue-900 mb-2">Why Treatment is Important:</h4>
                  <p className="text-sm leading-relaxed">
                    Untreated PTSD can affect your relationships, work, physical health, and overall
                    quality of life. Seeking help is a sign of strength, not weakness. Early intervention
                    can prevent symptoms from worsening and help you regain control of your life.
                  </p>
                </div>

                {severity?.label?.includes('Severe') && (
                  <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
                    <h4 className="font-semibold text-red-900 mb-2">For Severe Symptoms:</h4>
                    <p className="text-sm text-red-800 leading-relaxed">
                      Your symptoms indicate a high level of distress that requires immediate professional
                      attention. This level of severity is very treatable, but delaying care can make
                      recovery more difficult. Please contact a mental health professional today -
                      effective treatment can provide rapid relief from severe symptoms.
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-blue-900 mb-2">Immediate Coping Strategies:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Use grounding techniques: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste</li>
                    <li>• Practice deep breathing: Inhale for 4 counts, hold for 4, exhale for 6, repeat</li>
                    <li>• Contact someone you trust - don't isolate yourself</li>
                    <li>• Engage in physical activity to reduce stress hormones</li>
                    <li>• Limit caffeine and alcohol, which can worsen anxiety and sleep problems</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* DASS-21 Specific Information */}
        {tool === 'dass21' && (
          <Card className="mb-8 bg-green-50 border-green-200">
            <CardHeader>
              <CardTitle className="text-green-900">Understanding Your DASS-21 Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h4 className="font-semibold text-green-900 mb-2">What Your Score Means:</h4>
                  <p className="text-sm leading-relaxed">
                    The DASS-21 measures three core emotional states: Depression (sadness, loss of interest),
                    Anxiety (worry, physical tension), and Stress (feeling overwhelmed, inability to cope).
                    Your total score reflects your overall emotional distress level across all three areas.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-green-900 mb-2">About Mental Health Treatment:</h4>
                  <p className="text-sm leading-relaxed">
                    Depression, anxiety, and stress are highly treatable conditions. Evidence-based treatments
                    include Cognitive Behavioral Therapy (CBT), mindfulness-based approaches, medication when
                    appropriate, and lifestyle modifications. Many people experience significant improvement
                    within 8-12 weeks of proper treatment.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-green-900 mb-2">Why Seeking Help Matters:</h4>
                  <p className="text-sm leading-relaxed">
                    Untreated depression and anxiety can affect your physical health, relationships, work
                    performance, and overall quality of life. Early intervention prevents symptoms from
                    worsening and can help you develop healthy coping strategies for long-term wellbeing.
                  </p>
                </div>

                {severity?.label?.includes('Severe') && (
                  <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
                    <h4 className="font-semibold text-red-900 mb-2">For Severe Symptoms:</h4>
                    <p className="text-sm text-red-800 leading-relaxed">
                      Your symptoms indicate significant emotional distress requiring immediate professional attention.
                      Severe depression or anxiety can impact your ability to function and may carry safety risks.
                      Please contact a mental health professional today - effective treatment can provide
                      rapid relief and prevent further deterioration.
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-green-900 mb-2">Immediate Coping Strategies:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Practice progressive muscle relaxation to reduce physical tension</li>
                    <li>• Use mindfulness techniques: Focus on present moment without judgment</li>
                    <li>• Challenge negative thoughts by questioning their accuracy</li>
                    <li>• Maintain regular exercise - even 10 minutes can boost mood</li>
                    <li>• Establish a consistent sleep routine and limit screen time before bed</li>
                    <li>• Break large tasks into smaller, manageable steps</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-green-900 mb-2">Lifestyle Adjustments:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Limit alcohol and caffeine, which can worsen anxiety and sleep problems</li>
                    <li>• Eat regular meals with protein, vegetables, and whole grains</li>
                    <li>• Connect with supportive friends or family members regularly</li>
                    <li>• Spend time in nature or sunlight for mood regulation</li>
                    <li>• Practice gratitude by noting 3 positive things each day</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* AUDIT Specific Information */}
        {tool === 'audit' && (
          <Card className="mb-8 bg-purple-50 border-purple-200">
            <CardHeader>
              <CardTitle className="text-purple-900">Understanding Your AUDIT Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h4 className="font-semibold text-purple-900 mb-2">What Your Score Means:</h4>
                  <p className="text-sm leading-relaxed">
                    The AUDIT (Alcohol Use Disorders Identification Test) assesses your alcohol consumption patterns,
                    drinking behaviors, and alcohol-related problems. Your score indicates your risk level for
                    alcohol use disorder and helps identify patterns that may be harmful to your health and wellbeing.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-purple-900 mb-2">About Alcohol Use Disorder Treatment:</h4>
                  <p className="text-sm leading-relaxed">
                    Alcohol use disorder is a treatable medical condition, not a moral failing. Effective treatments
                    include cognitive-behavioral therapy, motivational enhancement therapy, medication-assisted treatment,
                    12-step programs like AA, and holistic approaches. Recovery is possible with proper support and treatment.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-purple-900 mb-2">Why Addressing Alcohol Use Matters:</h4>
                  <p className="text-sm leading-relaxed">
                    Excessive alcohol use can damage your liver, heart, and brain, worsen mental health conditions,
                    strain relationships, and impact work performance. Early intervention prevents health complications
                    and helps you regain control over your life and health.
                  </p>
                </div>

                {severity?.label?.includes('High Risk') && (
                  <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
                    <h4 className="font-semibold text-red-900 mb-2">For High Risk Drinking Patterns:</h4>
                    <p className="text-sm text-red-800 leading-relaxed">
                      Your score indicates high-risk drinking patterns requiring immediate professional attention.
                      High-risk drinking can lead to serious health problems, dependence, and safety risks.
                      Please seek help from a healthcare provider or addiction specialist today - treatment works
                      and you don't have to face this alone.
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-purple-900 mb-2">Strategies for Reducing Alcohol Use:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Set clear limits: Decide in advance how much you'll drink</li>
                    <li>• Alternate alcoholic drinks with water or non-alcoholic beverages</li>
                    <li>• Avoid drinking on an empty stomach - eat before and during drinking</li>
                    <li>• Keep a drinking diary to track consumption patterns and triggers</li>
                    <li>• Find alternative stress-reduction activities (exercise, hobbies, meditation)</li>
                    <li>• Remove alcohol from your home to reduce temptation</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-purple-900 mb-2">Health Benefits of Reducing Alcohol:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Improved sleep quality and energy levels</li>
                    <li>• Better mood regulation and reduced anxiety</li>
                    <li>• Weight management and improved physical fitness</li>
                    <li>• Enhanced cognitive function and memory</li>
                    <li>• Better relationships and work performance</li>
                    <li>• Reduced risk of liver disease, heart problems, and certain cancers</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-purple-900 mb-2">Signs You May Need Professional Help:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Drinking more than intended or unable to cut down</li>
                    <li>• Spending significant time obtaining, using, or recovering from alcohol</li>
                    <li>• Continuing to drink despite relationship, work, or health problems</li>
                    <li>• Experiencing withdrawal symptoms when not drinking</li>
                    <li>• Needing more alcohol to achieve the same effect (tolerance)</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* PHQ-9 Specific Information */}
        {tool === 'phq9' && (
          <Card className="mb-8 bg-indigo-50 border-indigo-200">
            <CardHeader>
              <CardTitle className="text-indigo-900">Understanding Your PHQ-9 Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h4 className="font-semibold text-indigo-900 mb-2">What Your Score Means:</h4>
                  <p className="text-sm leading-relaxed">
                    The PHQ-9 (Patient Health Questionnaire-9) assesses depression symptoms based on DSM-5 criteria.
                    It evaluates how often you've been bothered by problems like low mood, loss of interest, sleep issues,
                    energy changes, appetite changes, self-worth, concentration, and thoughts of self-harm over the past two weeks.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-indigo-900 mb-2">About Depression Treatment:</h4>
                  <p className="text-sm leading-relaxed">
                    Depression is a highly treatable medical condition affecting brain chemistry and function.
                    Evidence-based treatments include antidepressant medications, cognitive-behavioral therapy (CBT),
                    interpersonal therapy, exercise, and lifestyle modifications. With proper treatment, 80-90% of people
                    experience significant improvement.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-indigo-900 mb-2">Why Treating Depression Matters:</h4>
                  <p className="text-sm leading-relaxed">
                    Untreated depression can affect physical health, relationships, work performance, and overall quality of life.
                    It increases risk for other medical conditions and can lead to serious complications. Early treatment
                    prevents worsening symptoms and helps restore your ability to enjoy life and function effectively.
                  </p>
                </div>

                {(score >= 20 || severity?.label?.includes('Severe')) && (
                  <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
                    <h4 className="font-semibold text-red-900 mb-2">For Severe Depression Symptoms:</h4>
                    <p className="text-sm text-red-800 leading-relaxed">
                      Your score indicates severe depression requiring immediate professional attention. Severe depression
                      can impair daily functioning and carries significant health risks, including suicide risk.
                      Please contact a mental health professional or crisis services immediately. Effective treatment
                      can provide rapid relief and prevent serious complications.
                    </p>
                    <div className="mt-3 p-3 bg-yellow-50 rounded border border-yellow-200">
                      <p className="text-sm text-yellow-800 font-medium">
                        <strong>Suicide Risk:</strong> If you have thoughts of self-harm, call 988 immediately.
                        Your life is valuable, and help is available 24/7.
                      </p>
                    </div>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-indigo-900 mb-2">Immediate Coping Strategies:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Behavioral activation: Schedule pleasant activities even when you don't feel like it</li>
                    <li>• Physical activity: Even 15 minutes of walking can improve mood within hours</li>
                    <li>• Social connection: Contact friends or family, even briefly</li>
                    <li>• Sleep hygiene: Consistent sleep schedule, limit screen time before bed</li>
                    <li>• Nutrition: Regular meals with protein, fruits, and vegetables</li>
                    <li>• Sunlight exposure: 15 minutes daily can help regulate mood</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-indigo-900 mb-2">Treatment Success Indicators:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Antidepressants typically show improvement in 4-6 weeks</li>
                    <li>• CBT can be as effective as medication for mild-moderate depression</li>
                    <li>• Combined treatment (medication + therapy) often works best</li>
                    <li>• Exercise provides similar benefits to some medications for mild depression</li>
                    <li>• 60-70% of people respond to first treatment attempt</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-indigo-900 mb-2">Support Someone with Depression:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Listen without judgment - avoid "just cheer up" comments</li>
                    <li>• Offer specific help: "Can I drive you to your appointment?"</li>
                    <li>• Encourage treatment while respecting their autonomy</li>
                    <li>• Take threats of self-harm seriously - seek immediate help</li>
                    <li>• Be patient - recovery takes time and has ups and downs</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* GAD-7 Specific Information */}
        {tool === 'gad7' && (
          <Card className="mb-8 bg-teal-50 border-teal-200">
            <CardHeader>
              <CardTitle className="text-teal-900">Understanding Your GAD-7 Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h4 className="font-semibold text-teal-900 mb-2">What Your Score Means:</h4>
                  <p className="text-sm leading-relaxed">
                    The GAD-7 (Generalized Anxiety Disorder-7) assesses anxiety symptoms over the past two weeks.
                    It evaluates how often you've been bothered by nervousness, inability to stop worrying,
                    excessive worry, trouble relaxing, restlessness, irritability, and physical anxiety symptoms.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-teal-900 mb-2">About Anxiety Treatment:</h4>
                  <p className="text-sm leading-relaxed">
                    Anxiety disorders are highly treatable conditions affecting the brain's fear and worry circuits.
                    Evidence-based treatments include cognitive-behavioral therapy (CBT), acceptance and commitment therapy (ACT),
                    medications (SSRIs, SNRIs), mindfulness-based stress reduction, and relaxation techniques.
                    70-80% of people with anxiety disorders experience significant improvement with proper treatment.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-teal-900 mb-2">Why Treating Anxiety Matters:</h4>
                  <p className="text-sm leading-relaxed">
                    Untreated anxiety can lead to chronic stress, physical health problems, social isolation,
                    work impairment, and increased risk for depression. Anxiety disorders often worsen over time
                    without intervention, but early treatment can prevent chronic suffering and disability.
                  </p>
                </div>

                {score >= 15 && (
                  <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
                    <h4 className="font-semibold text-red-900 mb-2">For Severe Anxiety Symptoms:</h4>
                    <p className="text-sm text-red-800 leading-relaxed">
                      Your score indicates severe anxiety requiring immediate professional attention. Severe anxiety
                      can significantly impair daily functioning and may lead to panic attacks or depression.
                      Please contact a mental health professional this week. Effective treatments can provide
                      rapid relief and prevent chronic anxiety patterns.
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-teal-900 mb-2">Immediate Anxiety Management Techniques:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• 4-7-8 breathing: Inhale 4, hold 7, exhale 8 - activates parasympathetic nervous system</li>
                    <li>• Progressive muscle relaxation: Tense and release muscle groups systematically</li>
                    <li>• Grounding: 5-4-3-2-1 technique using all five senses</li>
                    <li>• "Worry time": Schedule 15 minutes daily to worry, postpone other worries</li>
                    <li>• Physical exercise: Reduces anxiety hormones and improves mood</li>
                    <li>• Limit caffeine and alcohol, which can worsen anxiety symptoms</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-teal-900 mb-2">Understanding Anxiety vs. Stress:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Normal stress: Response to specific external events, usually temporary</li>
                    <li>• Anxiety disorders: Persistent worry even without clear trigger</li>
                    <li>• Physical symptoms: Rapid heartbeat, muscle tension, digestive issues</li>
                    <li>• Cognitive symptoms: Catastrophic thinking, difficulty concentrating</li>
                    <li>• Behavioral symptoms: Avoidance, safety behaviors, seeking reassurance</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-teal-900 mb-2">Long-term Anxiety Management:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Regular mindfulness meditation (10-20 minutes daily)</li>
                    <li>• Consistent exercise routine (30 minutes, 3-5 times weekly)</li>
                    <li>• Sleep hygiene: 7-9 hours consistent sleep schedule</li>
                    <li>• Balanced diet with regular meals to stabilize blood sugar</li>
                    <li>• Limit news and social media exposure if it increases anxiety</li>
                    <li>• Develop supportive relationships and social connections</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stress Scale Specific Information */}
        {tool === 'stress' && (
          <Card className="mb-8 bg-orange-50 border-orange-200">
            <CardHeader>
              <CardTitle className="text-orange-900">Understanding Your Perceived Stress Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h4 className="font-semibold text-orange-900 mb-2">What Your Score Means:</h4>
                  <p className="text-sm leading-relaxed">
                    The Perceived Stress Scale measures your subjective experience of stress over the past month.
                    It assesses how often you feel unable to control important things, confident in handling problems,
                    that things are going your way, that difficulties are piling up, and how effectively you manage stress.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-orange-900 mb-2">About Stress Management:</h4>
                  <p className="text-sm leading-relaxed">
                    Chronic stress affects physical health, mental wellbeing, and cognitive function. While some stress
                    is normal and even beneficial, chronic perceived stress requires management strategies.
                    Effective approaches include stress-reduction techniques, lifestyle modifications, cognitive reframing,
                    and social support. Stress management skills can be learned and improved with practice.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-orange-900 mb-2">Why Managing Stress Matters:</h4>
                  <p className="text-sm leading-relaxed">
                    Chronic stress contributes to cardiovascular disease, immune dysfunction, digestive problems,
                    anxiety, depression, and cognitive impairment. It accelerates aging and reduces quality of life.
                    Effective stress management prevents health complications and improves resilience to future challenges.
                  </p>
                </div>

                {score >= 30 && (
                  <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
                    <h4 className="font-semibold text-red-900 mb-2">For High Perceived Stress:</h4>
                    <p className="text-sm text-red-800 leading-relaxed">
                      Your score indicates high perceived stress requiring immediate attention. High stress levels
                      significantly impact physical and mental health, increasing risk for burnout, anxiety, depression,
                      and stress-related illnesses. Consider stress management techniques, workload adjustment,
                      lifestyle changes, and professional support this week.
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-orange-900 mb-2">Immediate Stress Reduction Techniques:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Box breathing: 4-4-4-4 pattern to quickly calm nervous system</li>
                    <li>• Progressive muscle relaxation: Systematic tension and release</li>
                    <li>• Quick meditation: 3-5 minutes of focused breathing or guided imagery</li>
                    <li>• Physical movement: Quick walk, stretching, or shaking out tension</li>
                    <li>• Nature exposure: Even 5 minutes outdoors can reduce stress hormones</li>
                    <li>• Expressive writing: 10 minutes journaling about stressors</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-orange-900 mb-2">Building Stress Resilience:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Regular exercise: Most effective long-term stress reducer</li>
                    <li>• Quality sleep: 7-9 hours with consistent schedule</li>
                    <li>• Social connections: Strong relationships buffer stress effects</li>
                    <li>• Mindfulness practice: Changes brain's stress response over time</li>
                    <li>• Time management: Prioritize tasks, set realistic boundaries</li>
                    <li>• Healthy diet: Limit processed foods, caffeine, and alcohol</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-orange-900 mb-2">Workplace Stress Management:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Take regular breaks: 5 minutes every hour for movement or breathing</li>
                    <li>• Set boundaries: Learn to say no to additional commitments</li>
                    <li>• Prioritize tasks: Focus on high-impact activities</li>
                    <li>• Delegate or ask for help when overwhelmed</li>
                    <li>• Disconnect from work after hours: No emails or calls</li>
                    <li>• Create a comfortable, organized workspace</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Wellbeing Assessment Specific Information */}
        {tool === 'wellbeing' && (
          <Card className="mb-8 bg-emerald-50 border-emerald-200">
            <CardHeader>
              <CardTitle className="text-emerald-900">Understanding Your Wellbeing Assessment Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h4 className="font-semibold text-emerald-900 mb-2">What Your Score Means:</h4>
                  <p className="text-sm leading-relaxed">
                    This comprehensive wellbeing assessment evaluates multiple dimensions of your mental health and life satisfaction.
                    It covers emotional wellbeing, psychological functioning, social relationships, physical health,
                    purpose and meaning, work-life balance, and resilience. Your overall score reflects your current
                    state of mental health and quality of life across these key areas.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-900 mb-2">About Mental Health and Wellbeing:</h4>
                  <p className="text-sm leading-relaxed">
                    Mental health exists on a continuum from optimal functioning to serious illness. Wellbeing encompasses
                    positive emotions, engagement, relationships, meaning, and accomplishment (PERMA model). Improving
                    wellbeing involves strengthening protective factors, building resilience, developing healthy habits,
                    and addressing mental health challenges early through various therapeutic approaches and lifestyle modifications.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-900 mb-2">Why Prioritizing Wellbeing Matters:</h4>
                  <p className="text-sm leading-relaxed">
                    Good mental health and wellbeing are foundations for physical health, relationship satisfaction,
                    work performance, and overall life satisfaction. Mental wellbeing protects against mental illness,
                    enhances immune function, improves cognitive performance, and increases life expectancy.
                    Investing in your mental health provides returns across all areas of your life.
                  </p>
                </div>

                {score <= 30 && (
                  <div className="mt-4 p-4 bg-yellow-100 rounded-lg border border-yellow-300">
                    <h4 className="font-semibold text-yellow-900 mb-2">For Low Wellbeing Scores:</h4>
                    <p className="text-sm text-yellow-800 leading-relaxed">
                      Your score suggests areas for improvement in your mental health and life satisfaction.
                      Consider this an opportunity for growth and positive change. Many people experience periods
                      of lower wellbeing, and there are effective strategies to improve your mental health.
                      Consider professional support to develop a personalized wellbeing improvement plan.
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="font-semibold text-emerald-900 mb-2">Building Mental Wellbeing:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Positive emotions: Practice gratitude, savor positive experiences, find meaning</li>
                    <li>• Engagement: Pursue activities that create flow and absorption</li>
                    <li>• Relationships: Invest in meaningful connections and social support</li>
                    <li>• Meaning: Connect with values, purpose, and contribution to others</li>
                    <li>• Accomplishment: Set and achieve meaningful goals</li>
                    <li>• Physical health: Exercise, sleep, nutrition, and healthcare</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-900 mb-2">Developing Emotional Resilience:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Emotional awareness: Identify and label emotions accurately</li>
                    <li>• Acceptance: Allow difficult emotions without judgment</li>
                    <li>• Cognitive flexibility: Challenge negative thought patterns</li>
                    <li>• Problem-solving skills: Break challenges into manageable steps</li>
                    <li>• Self-compassion: Treat yourself with kindness during difficulties</li>
                    <li>• Support seeking: Reach out for help when needed</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-900 mb-2">Work-Life Integration Strategies:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Set clear boundaries between work and personal time</li>
                    <li>• Schedule regular self-care activities and protect this time</li>
                    <li>• Develop transition rituals between work and home life</li>
                    <li>• Create a workspace that supports focus and comfort</li>
                    <li>• Take regular breaks to prevent burnout and maintain productivity</li>
                    <li>• Align your work with personal values when possible</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-900 mb-2">Long-term Wellbeing Practices:</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Regular mental health check-ins: Monitor mood, energy, and satisfaction</li>
                    <li>• Lifelong learning: Maintain curiosity and personal growth</li>
                    <li>• Creative expression: Engage in art, music, writing, or other creative activities</li>
                    <li>• Nature connection: Spend regular time in natural environments</li>
                    <li>• Community involvement: Participate in groups or volunteer activities</li>
                    <li>• Digital wellbeing: Balance technology use with offline activities</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start">
                  <svg className="h-5 w-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-700">{recommendation}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Resources */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Helpful Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {resources.map((resource, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">{resource.title}</h3>
                  <p className="text-sm text-gray-600 mb-3">{resource.description}</p>
                  <div className="flex space-x-2">
                    {resource.phone && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(`tel:${resource.phone.replace(/[^\d]/g, '')}`)}
                      >
                        Call
                      </Button>
                    )}
                    {resource.link && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(resource.link!)}
                      >
                        Learn More
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI-Enhanced Wellness Plan */}
        <Card className="mb-8 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-purple-900">AI-Powered Wellness Plan</CardTitle>
              <div className="flex items-center space-x-2">
                <div className="animate-pulse h-2 w-2 bg-green-500 rounded-full"></div>
                <span className="text-xs text-green-600">Generated by AI Engine</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Personalized Summary */}
              <div className="bg-white p-4 rounded-lg border border-purple-100">
                <h4 className="font-semibold text-purple-900 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  Your Personalized Insights
                </h4>
                <div className="text-sm text-gray-700 leading-relaxed">
                  <p className="mb-3">
                    Based on your {tool?.toUpperCase()} assessment results, our AI engine has analyzed your responses
                    across multiple dimensions to provide targeted recommendations. Your score of {score} suggests
                    {severity?.label.toLowerCase()} level symptoms that can be effectively managed with the right strategies.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
                    <div className="flex items-center space-x-2 text-purple-700">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                        <path fillRule="evenodd" d="M4 5a2 2 0 012-2 1 1 0 000 2H6a2 2 0 100 4h2a2 2 0 100-4h-.5a1 1 0 000-2H8a2 2 0 012-2h2a2 2 0 012 2v9a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                      </svg>
                      <span>{recommendations.length} Evidence-based strategies</span>
                    </div>
                    <div className="flex items-center space-x-2 text-purple-700">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                      </svg>
                      <span>Daily implementation plan</span>
                    </div>
                    <div className="flex items-center space-x-2 text-purple-700">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                      </svg>
                      <span>Progress tracking enabled</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI-Generated Action Plan */}
              <div>
                <h4 className="font-semibold text-purple-900 mb-3">Your 30-Day Action Plan</h4>
                <div className="space-y-3">
                  {recommendations.slice(0, 3).map((recommendation, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-white rounded-lg border border-purple-100">
                      <div className="flex-shrink-0 w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-700">{recommendation}</p>
                        <div className="mt-2 text-xs text-gray-500">
                          <span className="font-medium">Timeline:</span> {index === 0 ? 'Immediate' : index === 1 ? 'Week 1-2' : 'Week 3-4'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Wellness Categories */}
              <div>
                <h4 className="font-semibold text-purple-900 mb-3">Wellness Focus Areas</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-4 rounded-lg border border-purple-100">
                    <h5 className="font-medium text-purple-800 mb-2">🧠 Mental Strategies</h5>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• Daily mindfulness practice (5-10 minutes)</li>
                      <li>• Cognitive reframing techniques</li>
                      <li>• Stress management breathing exercises</li>
                      <li>• Progressive muscle relaxation</li>
                    </ul>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-purple-100">
                    <h5 className="font-medium text-purple-800 mb-2">🏃 Physical Wellness</h5>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• Regular exercise (30 minutes, 3x/week)</li>
                      <li>• Sleep hygiene optimization</li>
                      <li>• Nutrition for mental health</li>
                      <li>• Outdoor time and sunlight exposure</li>
                    </ul>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-purple-100">
                    <h5 className="font-medium text-purple-800 mb-2">👥 Social Connection</h5>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• Regular social interaction scheduling</li>
                      <li>• Support network cultivation</li>
                      <li>• Communication skills practice</li>
                      <li>• Community engagement activities</li>
                    </ul>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-purple-100">
                    <h5 className="font-medium text-purple-800 mb-2">🎯 Purpose & Goals</h5>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• SMART goal setting framework</li>
                      <li>• Values clarification exercises</li>
                      <li>• Meaningful activity scheduling</li>
                      <li>• Progress monitoring system</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Progress Tracking */}
              <div className="bg-white p-4 rounded-lg border border-purple-100">
                <h4 className="font-semibold text-purple-900 mb-3">Progress Tracking & Reminders</h4>
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    <p className="mb-1">📊 Track your daily progress and symptoms</p>
                    <p className="text-xs text-gray-500">Get personalized insights based on your improvement patterns</p>
                  </div>
                  <Button size="sm" variant="outline">
                    Set Up Tracking
                  </Button>
                </div>
              </div>

              {/* AI Disclaimer */}
              <div className="text-xs text-gray-500 italic">
                <p>
                  This wellness plan is generated by our AI engine based on your assessment results and evidence-based practices.
                  It's designed to complement, not replace, professional medical advice. Please consult with your healthcare provider
                  before starting any new wellness program.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 justify-center">
          <Button
            onClick={handleShareWithProvider}
            variant="outline"
          >
            Share with Provider
          </Button>
          <Button
            onClick={handleSaveResults}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Results'}
          </Button>
          <Button
            onClick={handleRetakeAssessment}
            variant="outline"
          >
            Retake Assessment
          </Button>
          <Button
            onClick={() => navigate('/clinical-assessments')}
          >
            Take Another Assessment
          </Button>
        </div>

        {/* Disclaimer */}
        <Alert variant="info" className="mt-8">
          <AlertTitle>Important Disclaimer</AlertTitle>
          <p className="mt-2 text-sm">
            This screening tool is not a diagnostic instrument. It's designed to help you identify
            symptoms that may be associated with certain mental health conditions. Please discuss
            your results with a qualified healthcare provider for proper diagnosis and treatment planning.
          </p>
        </Alert>
      </div>
    </div>
  );
};

export default ClinicalResults;