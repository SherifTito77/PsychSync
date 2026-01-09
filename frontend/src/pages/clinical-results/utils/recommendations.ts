/**
 * Recommendations Generator Utility
 *
 * Generates evidence-based recommendations based on assessment type and severity level.
 * Each assessment tool has specific recommendations tailored to that condition.
 */

/**
 * Generate recommendations based on assessment tool and severity level
 *
 * @param toolType - The assessment tool (e.g., 'phq9', 'gad7', 'pcl5')
 * @param severityLevel - The severity level (e.g., 'Minimal', 'Mild', 'Moderate', 'Severe')
 * @returns Array of recommendation strings
 *
 * @example
 * ```typescript
 * const recs = getRecommendations('phq9', 'Moderate');
 * // Returns: ['Seek evaluation from a mental health professional...', ...]
 * ```
 */
export function getRecommendations(toolType: string, severityLevel: string): string[] {
  // PCL-5 PTSD specific recommendations
  if (toolType === 'pcl5') {
    const pcl5Recommendations: Record<string, string[]> = {
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
    const auditRecommendations: Record<string, string[]> = {
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
    const dass21Recommendations: Record<string, string[]> = {
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
    const phq9Recommendations: Record<string, string[]> = {
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
    const gad7Recommendations: Record<string, string[]> = {
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
    const stressRecommendations: Record<string, string[]> = {
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
    const wellbeingRecommendations: Record<string, string[]> = {
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
}
