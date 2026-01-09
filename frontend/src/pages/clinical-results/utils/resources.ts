/**
 * Resources Generator Utility
 *
 * Generates appropriate resources (hotlines, websites, support groups) based on
 * assessment type and severity level. Includes crisis resources for severe cases.
 */

import { Resource } from '../types';

/**
 * Get resources based on assessment tool, severity level, and crisis status
 *
 * @param toolType - The assessment tool (e.g., 'phq9', 'gad7', 'pcl5')
 * @param severityLevel - The severity level
 * @param crisisAlert - Whether crisis resources should be prioritized
 * @param score - The assessment score (used for some threshold logic)
 * @returns Array of Resource objects
 *
 * @example
 * ```typescript
 * const resources = getResources('phq9', 'Severe', true, 25);
 * // Returns: Array of crisis resources and helplines
 * ```
 */
export function getResources(
  toolType: string,
  severityLevel: string,
  crisisAlert: boolean,
  score?: number
): Resource[] {
  // PCL-5 PTSD specific resources
  if (toolType === 'pcl5') {
    const crisisResources: Resource[] = [
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

    const pcl5GeneralResources: Resource[] = [
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
    const alcoholResources: Resource[] = [
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
    const dass21Resources: Resource[] = [
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

    const severeResources: Resource[] = [
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

    const isSevere = severityLevel === 'Severe' || severityLevel === 'Moderately Severe';
    return isSevere ? severeResources : dass21Resources;
  }

  // PHQ-9 specific resources
  if (toolType === 'phq9') {
    const depressionResources: Resource[] = [
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

    const severeDepressionResources: Resource[] = [
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

    // Score threshold for PHQ-9 severe case is 20+
    return (score !== undefined && score >= 20) ? severeDepressionResources : depressionResources;
  }

  // GAD-7 specific resources
  if (toolType === 'gad7') {
    const anxietyResources: Resource[] = [
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

    const severeAnxietyResources: Resource[] = [
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

    // Score threshold for GAD-7 severe case is 15+
    return (score !== undefined && score >= 15) ? severeAnxietyResources : anxietyResources;
  }

  // Stress Scale specific resources
  if (toolType === 'stress') {
    const stressResources: Resource[] = [
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
    const wellbeingResources: Resource[] = [
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

    const lowWellbeingResources: Resource[] = [
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

    // Score threshold for low wellbeing is 30 or below
    return (score !== undefined && score <= 30) ? lowWellbeingResources : wellbeingResources;
  }

  // General mental health resources for other assessments (fallback)
  const baseResources: Resource[] = [
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

  const additionalResources: Resource[] = [
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
}
