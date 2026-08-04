// frontend/src/components/dashboard/FeatureSearch.tsx
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../common/Icon';

export interface FeatureItem {
  id: string;
  title: string;
  description: string;
  icon: string;
  route: string;
  category: string;
  keywords?: string[];
  shortcut?: string;
}

// Comprehensive feature index - ALL 127+ APPLICATION ROUTES
// This index includes every route from App.tsx to ensure complete searchability
const FEATURE_INDEX: FeatureItem[] = [
  // ===== DASHBOARD & OVERVIEW =====
  {
    id: 'dashboard',
    title: 'Dashboard',
    description: 'Overview of teams, assessments, and analytics',
    icon: '🏠',
    route: '/dashboard',
    category: 'Overview',
    keywords: ['home', 'overview', 'main'],
  },
  {
    id: 'icon-gallery',
    title: 'Icon Gallery',
    description: 'Browse all available UI icons and emojis',
    icon: '🎨',
    route: '/icon-gallery',
    category: 'Overview',
    keywords: ['icons', 'emoji', 'symbols', 'gallery', 'palette'],
  },

  // ===== TEAMS (7 routes) =====
  {
    id: 'teams',
    title: 'Teams',
    description: 'Manage and view your teams',
    icon: '👥',
    route: '/teams',
    category: 'Teams',
    keywords: ['team', 'groups', 'members'],
  },
  {
    id: 'team-detail',
    title: 'Team Detail',
    description: 'View detailed team information',
    icon: '👥',
    route: '/teams/:teamId',
    category: 'Teams',
    keywords: ['team', 'detail', 'info'],
  },
  {
    id: 'team-optimizer',
    title: 'Team Optimizer',
    description: 'AI-powered team composition analysis',
    icon: '⚡',
    route: '/team-optimizer',
    category: 'Teams',
    keywords: ['optimize', 'optimization', 'ai', 'composition'],
  },
  {
    id: 'team-health',
    title: 'Team Health',
    description: 'Monitor team health and wellness metrics',
    icon: '💚',
    route: '/team-health',
    category: 'Teams',
    keywords: ['team', 'health', 'wellness', 'metrics'],
  },
  {
    id: 'team-composition',
    title: 'Team Composition Analytics',
    description: 'Analyze team composition dynamics',
    icon: '📊',
    route: '/team-composition',
    category: 'Teams',
    keywords: ['composition', 'dynamics', 'analytics'],
  },
  {
    id: 'team-dashboard',
    title: 'Team Dashboard',
    description: 'Team-specific performance dashboard',
    icon: '📈',
    route: '/team-dashboard',
    category: 'Teams',
    keywords: ['team', 'dashboard', 'performance'],
  },

  // ===== PERSONALITY ASSESSMENTS (12 routes) =====
  {
    id: 'personality-assessments',
    title: 'Personality Assessments',
    description: 'Browse all personality assessments',
    icon: '📊',
    route: '/personality-assessments',
    category: 'Assessments',
    keywords: ['personality', 'tests', 'evaluations'],
  },
  {
    id: 'assessments',
    title: 'Assessments',
    description: 'View and manage assessments',
    icon: '📋',
    route: '/assessments',
    category: 'Assessments',
    keywords: ['tests', 'evaluations', 'questionnaire'],
  },
  {
    id: 'assessment-detail',
    title: 'Assessment Detail',
    description: 'View assessment details',
    icon: '📄',
    route: '/assessments/:assessmentId',
    category: 'Assessments',
    keywords: ['assessment', 'detail', 'info'],
  },
  {
    id: 'take-assessment',
    title: 'Take Assessment',
    description: 'Start a new assessment',
    icon: '✏️',
    route: '/assessments/:assessmentId/take',
    category: 'Assessments',
    keywords: ['new', 'start', 'begin', 'take'],
  },
  {
    id: 'mbti',
    title: 'MBTI Assessment',
    description: 'Myers-Briggs Type Indicator',
    icon: '🔮',
    route: '/assessments/mbti',
    category: 'Assessments',
    keywords: ['myers', 'briggs', 'types', '16 personalities'],
  },
  {
    id: 'mbti-start',
    title: 'MBTI Start',
    description: 'Start MBTI assessment',
    icon: '🔮',
    route: '/assessments/mbti/start',
    category: 'Assessments',
    keywords: ['mbti', 'start', 'begin'],
  },
  {
    id: 'big-five',
    title: 'Big Five Assessment',
    description: 'Ocean personality traits assessment',
    icon: '🌊',
    route: '/assessments/big-five',
    category: 'Assessments',
    keywords: ['ocean', 'personality', 'traits'],
  },
  {
    id: 'big-five-start',
    title: 'Big Five Start',
    description: 'Start Big Five assessment',
    icon: '🌊',
    route: '/assessments/big-five/start',
    category: 'Assessments',
    keywords: ['big five', 'start', 'ocean'],
  },
  {
    id: 'enneagram',
    title: 'Enneagram Assessment',
    description: 'Nine personality types assessment',
    icon: '⭕',
    route: '/assessments/enneagram',
    category: 'Assessments',
    keywords: ['9 types', 'enneagram', 'personality types'],
  },
  {
    id: 'enneagram-start',
    title: 'Enneagram Start',
    description: 'Start Enneagram assessment',
    icon: '⭕',
    route: '/assessments/enneagram/start',
    category: 'Assessments',
    keywords: ['enneagram', 'start', 'begin'],
  },
  {
    id: 'disc',
    title: 'DISC Assessment',
    description: 'Dominance, Influence, Steadiness, Conscientiousness',
    icon: '💠',
    route: '/assessments/disc',
    category: 'Assessments',
    keywords: ['disc', 'behavioral', 'styles'],
  },
  {
    id: 'disc-start',
    title: 'DISC Start',
    description: 'Start DISC assessment',
    icon: '💠',
    route: '/assessments/disc/start',
    category: 'Assessments',
    keywords: ['disc', 'start', 'behavioral'],
  },
  {
    id: 'social-styles',
    title: 'Social Styles Assessment',
    description: 'Social styles personality assessment',
    icon: '🎭',
    route: '/assessments/social',
    category: 'Assessments',
    keywords: ['social', 'styles', 'behavioral'],
  },
  {
    id: 'social-start',
    title: 'Social Styles Start',
    description: 'Start Social Styles assessment',
    icon: '🎭',
    route: '/assessments/social/start',
    category: 'Assessments',
    keywords: ['social', 'start', 'styles'],
  },
  {
    id: 'strengthsfinder',
    title: 'StrengthsFinder Assessment',
    description: 'Discover your strengths',
    icon: '💪',
    route: '/assessments/strengthsfinder',
    category: 'Assessments',
    keywords: ['strengths', 'strengthsfinder', 'talents'],
  },
  {
    id: 'strengthsfinder-start',
    title: 'StrengthsFinder Start',
    description: 'Start StrengthsFinder assessment',
    icon: '💪',
    route: '/assessments/strengthsfinder/start',
    category: 'Assessments',
    keywords: ['strengths', 'start', 'talents'],
  },
  {
    id: 'predictive-index',
    title: 'Predictive Index Assessment',
    description: 'Behavioral assessment',
    icon: '📊',
    route: '/assessments/predictive-index',
    category: 'Assessments',
    keywords: ['predictive', 'behavioral', 'index'],
  },
  {
    id: 'predictive-index-start',
    title: 'Predictive Index Start',
    description: 'Start Predictive Index assessment',
    icon: '📊',
    route: '/assessments/predictive-index/start',
    category: 'Assessments',
    keywords: ['predictive', 'start', 'index'],
  },

  // ===== ANALYTICS (6 routes) =====
  {
    id: 'analytics',
    title: 'Analytics Overview',
    description: 'Performance insights and reports',
    icon: '📈',
    route: '/analytics',
    category: 'Analytics',
    keywords: ['reports', 'insights', 'data', 'statistics'],
  },
  {
    id: 'analytics-dashboard',
    title: 'Analytics Dashboard',
    description: 'Detailed analytics dashboard',
    icon: '📊',
    route: '/analytics/dashboard',
    category: 'Analytics',
    keywords: ['analytics', 'dashboard', 'reports'],
  },
  {
    id: 'kpi-dashboard',
    title: 'KPI Dashboard',
    description: 'Key performance indicators',
    icon: '🎯',
    route: '/analytics/kpi',
    category: 'Analytics',
    keywords: ['kpi', 'metrics', 'performance'],
  },
  {
    id: 'predictive-analytics',
    title: 'Predictive Analytics',
    description: 'AI-powered predictions',
    icon: '🔮',
    route: '/predictive-analytics',
    category: 'Analytics',
    keywords: ['predictions', 'forecasting', 'ai'],
  },
  {
    id: 'clinical-analytics',
    title: 'Clinical Analytics',
    description: 'Mental health analytics dashboard',
    icon: '🧠',
    route: '/analytics/clinical',
    category: 'Clinical',
    keywords: ['mental health', 'clinical', 'wellness'],
  },
  {
    id: 'population-health',
    title: 'Population Health Analytics',
    description: 'Population health metrics',
    icon: '🏥',
    route: '/analytics/population-health',
    category: 'Clinical',
    keywords: ['population', 'health', 'metrics'],
  },

  // ===== CLINICAL & SCREENING (30+ routes) =====
  {
    id: 'clinical-assessments',
    title: 'Clinical Assessments',
    description: 'Mental health screening tools',
    icon: '🏥',
    route: '/clinical-assessments',
    category: 'Clinical',
    keywords: ['clinical', 'mental health', 'screening'],
  },
  {
    id: 'enhanced-assessments',
    title: 'Enhanced Clinical Assessments',
    description: 'Advanced clinical screening tools',
    icon: '🏥',
    route: '/enhanced-assessments',
    category: 'Clinical',
    keywords: ['enhanced', 'clinical', 'advanced'],
  },
  {
    id: 'clinical',
    title: 'Clinical Dashboard',
    description: 'Clinical assessment dashboard',
    icon: '🧠',
    route: '/clinical',
    category: 'Clinical',
    keywords: ['clinical', 'dashboard', 'health'],
  },
  {
    id: 'clinical-consent',
    title: 'Clinical Consent',
    description: 'Clinical assessment consent form',
    icon: '📝',
    route: '/clinical/consent',
    category: 'Clinical',
    keywords: ['consent', 'clinical', 'agreement'],
  },
  {
    id: 'clinical-emergency',
    title: 'Clinical Emergency',
    description: 'Emergency resources and support',
    icon: '🚨',
    route: '/clinical/emergency',
    category: 'Clinical',
    keywords: ['emergency', 'crisis', 'help'],
  },
  {
    id: 'clinical-dashboard',
    title: 'Clinical Dashboard',
    description: 'Mental health dashboard',
    icon: '🧠',
    route: '/clinical/dashboard',
    category: 'Clinical',
    keywords: ['clinical', 'dashboard', 'mental health'],
  },
  {
    id: 'clinical-self-help',
    title: 'Clinical Self Help',
    description: 'Self-help resources',
    icon: '📚',
    route: '/clinical/self-help',
    category: 'Clinical',
    keywords: ['self help', 'resources', 'wellness'],
  },
  {
    id: 'clinical-resources',
    title: 'Clinical Resources',
    description: 'Clinical resources and tools',
    icon: '📋',
    route: '/clinical/resources',
    category: 'Clinical',
    keywords: ['resources', 'clinical', 'tools'],
  },
  // Screening Tools
  {
    id: 'screening',
    title: 'Screening Tools',
    description: 'Health screening assessments',
    icon: '🔍',
    route: '/screening',
    category: 'Clinical',
    keywords: ['screening', 'health', 'assessment'],
  },
  {
    id: 'phq9',
    title: 'PHQ-9 Depression Screening',
    description: 'Patient Health Questionnaire for depression',
    icon: '📋',
    route: '/screening/phq9',
    category: 'Clinical',
    keywords: ['depression', 'phq9', 'phq', 'mood'],
  },
  {
    id: 'gad7',
    title: 'GAD-7 Anxiety Screening',
    description: 'Generalized Anxiety Disorder assessment',
    icon: '😰',
    route: '/screening/gad7',
    category: 'Clinical',
    keywords: ['anxiety', 'gad7', 'gad', 'worry'],
  },
  {
    id: 'cssrs',
    title: 'C-SSRS Suicide Risk Screening',
    description: 'Columbia Suicide Severity Rating Scale',
    icon: '⚠️',
    route: '/screening/cssrs',
    category: 'Clinical',
    keywords: ['suicide', 'risk', 'cssrs', 'crisis'],
  },
  {
    id: 'crisis-resources',
    title: 'Crisis Resources',
    description: 'Emergency crisis resources',
    icon: '🚨',
    route: '/screening/crisis-resources',
    category: 'Clinical',
    keywords: ['crisis', 'emergency', 'help', 'resources'],
  },
  {
    id: 'lsas',
    title: 'LSAS Social Anxiety',
    description: 'Liebowitz Social Anxiety Scale',
    icon: '😰',
    route: '/screening/lsas',
    category: 'Clinical',
    keywords: ['social anxiety', 'lsas', 'anxiety'],
  },
  {
    id: 'eat26',
    title: 'EAT-26 Eating Disorder',
    description: 'Eating Attitudes Test',
    icon: '🍽️',
    route: '/screening/eat26',
    category: 'Clinical',
    keywords: ['eating', 'disorder', 'eat26'],
  },
  {
    id: 'ybocs',
    title: 'Y-BOCS OCD',
    description: 'Yale-Brown Obsessive Compulsive Scale',
    icon: '🔄',
    route: '/screening/ybocs',
    category: 'Clinical',
    keywords: ['ocd', 'ybocs', 'obsessive', 'compulsive'],
  },
  {
    id: 'bdi2',
    title: 'BDI-II Depression',
    description: 'Beck Depression Inventory',
    icon: '😔',
    route: '/screening/bdi2',
    category: 'Clinical',
    keywords: ['depression', 'bdi', 'beck'],
  },
  {
    id: 'bai',
    title: 'BAI Anxiety',
    description: 'Beck Anxiety Inventory',
    icon: '😰',
    route: '/screening/bai',
    category: 'Clinical',
    keywords: ['anxiety', 'bai', 'beck'],
  },
  {
    id: 'dass21',
    title: 'DASS-21 Stress',
    description: 'Depression Anxiety Stress Scales',
    icon: '📊',
    route: '/screening/dass21',
    category: 'Clinical',
    keywords: ['stress', 'depression', 'anxiety', 'dass'],
  },
  {
    id: 'pcl5',
    title: 'PCL-5 PTSD',
    description: 'PTSD Checklist for DSM-5',
    icon: '🎖️',
    route: '/screening/pcl5',
    category: 'Clinical',
    keywords: ['ptsd', 'pcl5', 'trauma'],
  },
  {
    id: 'audit',
    title: 'AUDIT Alcohol Use',
    description: 'Alcohol Use Disorders Identification Test',
    icon: '🍺',
    route: '/screening/audit',
    category: 'Clinical',
    keywords: ['alcohol', 'audit', 'substance', 'use'],
  },
  {
    id: 'pss10',
    title: 'PSS-10 Perceived Stress',
    description: 'Perceived Stress Scale',
    icon: '😫',
    route: '/screening/pss10',
    category: 'Clinical',
    keywords: ['stress', 'pss', 'perceived'],
  },
  {
    id: 'asrs',
    title: 'ASRS ADHD',
    description: 'ADHD Self-Report Scale',
    icon: '🧠',
    route: '/screening/asrs',
    category: 'Clinical',
    keywords: ['adhd', 'asrs', 'attention'],
  },
  {
    id: 'isi',
    title: 'ISI Insomnia',
    description: 'Insomnia Severity Index',
    icon: '😴',
    route: '/screening/isi',
    category: 'Clinical',
    keywords: ['insomnia', 'isi', 'sleep'],
  },
  {
    id: 'cbi',
    title: 'CBI Burnout',
    description: 'Copenhagen Burnout Inventory',
    icon: '🔥',
    route: '/screening/cbi',
    category: 'Clinical',
    keywords: ['burnout', 'cbi', 'copenhagen'],
  },
  {
    id: 'mdq',
    title: 'MDQ Bipolar',
    description: 'Mood Disorder Questionnaire',
    icon: '🎭',
    route: '/screening/mdq',
    category: 'Clinical',
    keywords: ['bipolar', 'mdq', 'mood'],
  },
  {
    id: 'dast10',
    title: 'DAST-10 Drug Use',
    description: 'Drug Abuse Screening Test',
    icon: '💊',
    route: '/screening/dast10',
    category: 'Clinical',
    keywords: ['drug', 'dast', 'substance', 'abuse'],
  },
  {
    id: 'aq10',
    title: 'AQ-10 Autism',
    description: 'Autism Spectrum Quotient',
    icon: '🧩',
    route: '/screening/aq10',
    category: 'Clinical',
    keywords: ['autism', 'aq10', 'spectrum'],
  },
  {
    id: 'ace',
    title: 'ACE Trauma',
    description: 'Adverse Childhood Experiences',
    icon: '👶',
    route: '/screening/ace',
    category: 'Clinical',
    keywords: ['trauma', 'ace', 'childhood', 'adverse'],
  },
  {
    id: 'iesr',
    title: 'IES-R Stress',
    description: 'Impact of Event Scale-Revised',
    icon: '💥',
    route: '/screening/iesr',
    category: 'Clinical',
    keywords: ['stress', 'iesr', 'trauma', 'impact'],
  },
  {
    id: 'iat',
    title: 'IAT Addiction',
    description: 'Internet Addiction Test',
    icon: '🌐',
    route: '/screening/iat',
    category: 'Clinical',
    keywords: ['addiction', 'iat', 'internet'],
  },
  {
    id: 'clinical-alerts',
    title: 'Clinical Alerts Center',
    description: 'Automated clinical alerts',
    icon: '🔔',
    route: '/clinical/alerts-center',
    category: 'Clinical',
    keywords: ['alerts', 'clinical', 'notifications'],
  },

  // ===== HEALTH & WELLNESS (5 routes) =====
  {
    id: 'health',
    title: 'Health Dashboard',
    description: 'Overall health monitoring',
    icon: '💚',
    route: '/health',
    category: 'Health',
    keywords: ['health', 'wellness', 'dashboard'],
  },
  {
    id: 'health-dashboard',
    title: 'Enhanced Health Dashboard',
    description: 'Advanced health monitoring',
    icon: '📊',
    route: '/health-dashboard',
    category: 'Health',
    keywords: ['health', 'dashboard', 'enhanced'],
  },
  {
    id: 'mental-health-wellness',
    title: 'Mental Health & Wellness',
    description: 'Mental health resources',
    icon: '🧠',
    route: '/mental-health-wellness',
    category: 'Health',
    keywords: ['mental', 'health', 'wellness'],
  },
  {
    id: 'burnout-prevention',
    title: 'Burnout Prevention',
    description: 'Prevent and manage burnout',
    icon: '🔥',
    route: '/burnout-prevention',
    category: 'Health',
    keywords: ['burnout', 'prevention', 'stress'],
  },
  {
    id: 'burnout-prediction',
    title: 'Burnout Prediction',
    description: 'AI-powered burnout prediction',
    icon: '🔮',
    route: '/burnout-prediction',
    category: 'Health',
    keywords: ['burnout', 'prediction', 'ai'],
  },
  {
    id: 'advanced-burnout',
    title: 'Advanced Burnout Analytics',
    description: 'Advanced burnout analysis',
    icon: '📊',
    route: '/advanced-burnout',
    category: 'Health',
    keywords: ['burnout', 'advanced', 'analytics'],
  },
  {
    id: 'executive-burnout',
    title: 'Executive Burnout Dashboard',
    description: 'CEO and executive burnout tracking',
    icon: '👔',
    route: '/executive/burnout',
    category: 'Health',
    keywords: ['executive', 'ceo', 'burnout'],
  },

  // ===== HRIS INTEGRATION (9 routes) =====
  {
    id: 'hris-connector',
    title: 'HRIS Connector',
    description: 'Connect your HR data source',
    icon: '🏢',
    route: '/hris-connector',
    category: 'Integrations',
    keywords: ['hris', 'hr', 'integration', 'workday', 'bamboohr'],
  },
  {
    id: 'hris-analytics',
    title: 'HRIS Analytics',
    description: 'HR data analytics',
    icon: '📊',
    route: '/hris-analytics',
    category: 'Integrations',
    keywords: ['hris', 'analytics', 'hr', 'data'],
  },
  {
    id: 'hris-analytics-dashboard',
    title: 'HRIS Analytics Dashboard',
    description: 'HR analytics dashboard',
    icon: '📈',
    route: '/hris-analytics-dashboard',
    category: 'Integrations',
    keywords: ['hris', 'analytics', 'dashboard', 'hr'],
  },
  {
    id: 'hris-demographics',
    title: 'Workforce Demographics',
    description: 'Employee demographics analysis',
    icon: '👥',
    route: '/hris/demographics',
    category: 'Integrations',
    keywords: ['demographics', 'workforce', 'hr'],
  },
  {
    id: 'hris-performance',
    title: 'Performance Analytics',
    description: 'Employee performance metrics',
    icon: '📊',
    route: '/hris/performance',
    category: 'Integrations',
    keywords: ['performance', 'hr', 'analytics'],
  },
  {
    id: 'hris-turnover',
    title: 'Turnover Analysis',
    description: 'Employee turnover analytics',
    icon: '📉',
    route: '/hris/turnover',
    category: 'Integrations',
    keywords: ['turnover', 'retention', 'hr'],
  },
  {
    id: 'hris-compensation',
    title: 'Compensation Analysis',
    description: 'Salary and compensation data',
    icon: '💰',
    route: '/hris/compensation',
    category: 'Integrations',
    keywords: ['compensation', 'salary', 'pay', 'hr'],
  },
  {
    id: 'hris-engagement',
    title: 'Engagement Analytics',
    description: 'Employee engagement metrics',
    icon: '💼',
    route: '/hris/engagement',
    category: 'Integrations',
    keywords: ['engagement', 'employee', 'hr'],
  },
  {
    id: 'hris-learning',
    title: 'Learning & Development',
    description: 'L&D analytics',
    icon: '📚',
    route: '/hris/learning',
    category: 'Integrations',
    keywords: ['learning', 'development', 'training', 'hr'],
  },
  {
    id: 'hris-succession',
    title: 'Succession Planning',
    description: 'Succession planning analytics',
    icon: '👔',
    route: '/hris/succession',
    category: 'Integrations',
    keywords: ['succession', 'planning', 'hr'],
  },

  // ===== EMAIL INTEGRATION (7 routes) =====
  {
    id: 'email-connector',
    title: 'Email Connector',
    description: 'Connect your email for analysis',
    icon: '📧',
    route: '/email-connector',
    category: 'Integrations',
    keywords: ['email', 'gmail', 'outlook', 'connection'],
  },
  {
    id: 'email-analytics',
    title: 'Email Analytics',
    description: 'Email communication analytics',
    icon: '📊',
    route: '/email-analytics',
    category: 'Integrations',
    keywords: ['email', 'analytics', 'communication'],
  },
  {
    id: 'email-oauth',
    title: 'Email OAuth Callback',
    description: 'Email authentication callback',
    icon: '🔐',
    route: '/email-oauth-callback',
    category: 'Integrations',
    keywords: ['email', 'oauth', 'auth'],
  },
  {
    id: 'email-monitoring',
    title: 'Email Monitoring Hub',
    description: 'Centralized email monitoring',
    icon: '📧',
    route: '/email-monitoring',
    category: 'Integrations',
    keywords: ['email', 'monitoring', 'hub'],
  },
  {
    id: 'scheduled-reports',
    title: 'Scheduled Reports',
    description: 'Automated email reporting',
    icon: '📅',
    route: '/scheduled-reports',
    category: 'Integrations',
    keywords: ['scheduled', 'reports', 'email', 'automation'],
  },
  {
    id: 'anomaly-detection',
    title: 'Anomaly Detection',
    description: 'Email anomaly visualization',
    icon: '🔍',
    route: '/anomaly-detection',
    category: 'Integrations',
    keywords: ['anomaly', 'detection', 'email'],
  },
  {
    id: 'sentiment-analysis',
    title: 'Sentiment Analysis',
    description: 'Email sentiment analysis',
    icon: '😊',
    route: '/sentiment-analysis',
    category: 'Integrations',
    keywords: ['sentiment', 'email', 'analysis'],
  },

  // ===== INTEGRATIONS (3 routes) =====
  {
    id: 'integrations',
    title: 'Integrations',
    description: 'Browse all integrations',
    icon: '🔗',
    route: '/integrations',
    category: 'Integrations',
    keywords: ['integrations', 'connect', 'apps'],
  },
  {
    id: 'corporate-integrations',
    title: 'Corporate Integrations',
    description: 'Enterprise integration options',
    icon: '🏢',
    route: '/integrations/corporate',
    category: 'Integrations',
    keywords: ['corporate', 'enterprise', 'integrations'],
  },
  {
    id: 'services',
    title: 'Services',
    description: 'Available services',
    icon: '🛠️',
    route: '/services',
    category: 'Overview',
    keywords: ['services', 'features', 'tools'],
  },

  // ===== TELEHEALTH & AI SUPPORT (3 routes) =====
  {
    id: 'telehealth-schedule',
    title: 'Telehealth Scheduling',
    description: 'Schedule video consultations',
    icon: '📅',
    route: '/telehealth/schedule',
    category: 'Clinical',
    keywords: ['telehealth', 'schedule', 'video', 'consultation'],
  },
  {
    id: 'telehealth-session',
    title: 'Telehealth Session',
    description: 'Video consultation session',
    icon: '📹',
    route: '/telehealth/session/:sessionId',
    category: 'Clinical',
    keywords: ['telehealth', 'video', 'session', 'consultation'],
  },
  {
    id: 'mental-health-chatbot',
    title: 'Mental Health Chatbot',
    description: 'AI-powered mental health support',
    icon: '🤖',
    route: '/support/chat',
    category: 'Clinical',
    keywords: ['chatbot', 'ai', 'support', 'chat'],
  },

  // ===== ANALYTICS & BEHAVIORAL (5 routes) =====
  {
    id: 'behavioral-analytics',
    title: 'Behavioral Analytics',
    description: 'Behavioral data analysis',
    icon: '📊',
    route: '/behavioral-analytics',
    category: 'Analytics',
    keywords: ['behavioral', 'analytics', 'patterns'],
  },
  {
    id: 'behavioral-analysis',
    title: 'Behavioral Analysis',
    description: 'Individual behavior analysis',
    icon: '🔍',
    route: '/behavioral-analysis',
    category: 'Analytics',
    keywords: ['behavioral', 'analysis', 'individual'],
  },
  {
    id: 'early-warning',
    title: 'Early Warning System',
    description: 'Risk early warning alerts',
    icon: '⚠️',
    route: '/early-warning',
    category: 'Analytics',
    keywords: ['early', 'warning', 'risk', 'alert'],
  },
  {
    id: 'toxic-behavior',
    title: 'Toxic Behavior Detection',
    description: 'Detect toxic workplace behavior',
    icon: '🚫',
    route: '/toxic-behavior-detection',
    category: 'Analytics',
    keywords: ['toxic', 'behavior', 'detection', 'workplace'],
  },
  {
    id: 'employee-safety',
    title: 'Employee Safety',
    description: 'Workplace safety monitoring',
    icon: '🦺',
    route: '/employee-safety',
    category: 'Analytics',
    keywords: ['safety', 'employee', 'workplace'],
  },

  // ===== OTHER FEATURES =====
  {
    id: 'templates',
    title: 'Assessment Templates',
    description: 'Browse assessment templates',
    icon: '📑',
    route: '/templates',
    category: 'Assessments',
    keywords: ['library', 'collection', 'catalog'],
  },
  {
    id: 'my-responses',
    title: 'My Responses',
    description: 'View your assessment responses',
    icon: '📝',
    route: '/responses/my-responses',
    category: 'Responses',
    keywords: ['results', 'answers', 'history'],
  },
  {
    id: 'response-results',
    title: 'Response Results',
    description: 'View assessment results',
    icon: '📊',
    route: '/responses/:responseId/results',
    category: 'Responses',
    keywords: ['results', 'response', 'outcome'],
  },
  {
    id: 'settings',
    title: 'Settings',
    description: 'Manage your preferences',
    icon: '⚙️',
    route: '/settings',
    category: 'Settings',
    keywords: ['preferences', 'config', 'options'],
  },
  {
    id: 'profile',
    title: 'Profile',
    description: 'Edit your profile information',
    icon: '👤',
    route: '/profile',
    category: 'Settings',
    keywords: ['account', 'user', 'edit'],
  },
  {
    id: 'reliability-validity',
    title: 'Reliability & Validity',
    description: 'Assessment reliability metrics',
    icon: '✅',
    route: '/reliability-validity',
    category: 'Analytics',
    keywords: ['reliability', 'validity', 'metrics'],
  },
  {
    id: 'multi-framework',
    title: 'Multi-Framework Synthesis',
    description: 'Combine multiple assessment frameworks',
    icon: '🔀',
    route: '/multi-framework-synthesis',
    category: 'Analytics',
    keywords: ['multi', 'framework', 'synthesis', 'combine'],
  },
  {
    id: 'anonymous-feedback',
    title: 'Anonymous Feedback',
    description: 'Submit anonymous feedback',
    icon: '📝',
    route: '/anonymous-feedback',
    category: 'Other',
    keywords: ['anonymous', 'feedback', 'survey'],
  },
  {
    id: 'feedback-status',
    title: 'Feedback Status',
    description: 'Check feedback submission status',
    icon: '📊',
    route: '/feedback-status',
    category: 'Other',
    keywords: ['feedback', 'status', 'check'],
  },
  {
    id: 'admin-security',
    title: 'Security Dashboard',
    description: 'Admin security monitoring',
    icon: '🔒',
    route: '/admin/security',
    category: 'Admin',
    keywords: ['security', 'admin', 'monitoring'],
  },
  {
    id: 'admin-corporate',
    title: 'Corporate Psychology Dashboard',
    description: 'Executive psychology analytics',
    icon: '🏢',
    route: '/admin/corporate-psychology',
    category: 'Admin',
    keywords: ['corporate', 'psychology', 'executive', 'admin'],
  },
  {
    id: 'legal-rights',
    title: 'Legal Rights Dashboard',
    description: 'Legal rights and compliance',
    icon: '⚖️',
    route: '/legal-rights',
    category: 'Other',
    keywords: ['legal', 'rights', 'compliance'],
  },
  {
    id: 'equity',
    title: 'Equity Dashboard',
    description: 'DEI and equity metrics',
    icon: '⚖️',
    route: '/equity',
    category: 'Other',
    keywords: ['equity', 'dei', 'diversity', 'inclusion'],
  },
];

// Fuzzy search function
const fuzzyMatch = (text: string, query: string): boolean => {
  const queryLower = query.toLowerCase();
  const textLower = text.toLowerCase();

  // Exact match
  if (textLower.includes(queryLower)) {
    return true;
  }

  // Fuzzy match - characters in order
  let queryIndex = 0;
  for (let i = 0; i < textLower.length && queryIndex < queryLower.length; i++) {
    if (textLower[i] === queryLower[queryIndex]) {
      queryIndex++;
    }
  }

  return queryIndex === queryLower.length;
};

// Calculate relevance score
const calculateScore = (item: FeatureItem, query: string): number => {
  const queryLower = query.toLowerCase();
  const titleLower = item.title.toLowerCase();
  const descLower = item.description.toLowerCase();
  const keywordsLower = (item.keywords || []).map((k) => k.toLowerCase());

  let score = 0;

  // Exact title match gets highest score
  if (titleLower === queryLower) score += 100;
  else if (titleLower.startsWith(queryLower)) score += 80;
  else if (titleLower.includes(queryLower)) score += 60;

  // Description match
  if (descLower.includes(queryLower)) score += 20;

  // Keyword match
  if (keywordsLower.some((k) => k.includes(queryLower))) score += 30;

  return score;
};

interface FeatureSearchProps {
  isOpen: boolean;
  onClose: () => void;
}

const FeatureSearch: React.FC<FeatureSearchProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query,setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Filter and sort features based on query
  const filteredFeatures = useMemo(() => {
    if (!query.trim()) {
      // Show featured/recent items when no query
      return FEATURE_INDEX.filter((item) =>
        ['dashboard', 'teams', 'assessments', 'analytics'].includes(item.id)
      );
    }

    const matches = FEATURE_INDEX.filter(
      (item) =>
        fuzzyMatch(item.title, query) ||
        fuzzyMatch(item.description, query) ||
        (item.keywords || []).some((k) => fuzzyMatch(k, query))
    );

    return matches
      .map((item) => ({ item, score: calculateScore(item, query) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 8)
      .map((x) => x.item);
  }, [query]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((i) =>
            i < filteredFeatures.length - 1 ? i + 1 : i
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((i) => (i > 0 ? i - 1 : 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredFeatures[selectedIndex]) {
            navigate(filteredFeatures[selectedIndex].route);
            onClose();
          }
          break;
        case 'Escape':
          onClose();
          break;
      }
    },
    [filteredFeatures, selectedIndex, navigate, onClose]
  );

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 sm:pt-32"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Search Modal */}
      <div
        className="relative w-full max-w-2xl mx-4 bg-white rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 p-4 border-b border-gray-200">
          <Icon size="md" className="text-gray-400">🔍</Icon>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search features, assessments, pages..."
            className="flex-1 text-lg outline-none placeholder-gray-400"
            aria-label="Search features"
            aria-autocomplete="list"
            aria-controls="search-results"
            aria-activedescendant={`search-item-${selectedIndex}`}
          />
          <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 border border-gray-300 rounded text-gray-500">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div
          ref={listRef}
          id="search-results"
          className="max-h-[60vh] overflow-y-auto p-2"
          role="listbox"
        >
          {filteredFeatures.length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              <Icon size="lg" className="mb-2">🔍</Icon>
              <p>No results found for "{query}"</p>
              <p className="text-sm mt-1">Try different keywords</p>
            </div>
          ) : (
            filteredFeatures.map((feature, index) => (
              <button
                key={feature.id}
                id={`search-item-${index}`}
                role="option"
                aria-selected={index === selectedIndex}
                onClick={() => {
                  navigate(feature.route);
                  onClose();
                }}
                className={`
                  w-full flex items-start gap-3 p-3 rounded-lg
                  transition-all duration-150
                  ${
                    index === selectedIndex
                      ? 'bg-indigo-50 border-2 border-indigo-500'
                      : 'hover:bg-gray-50 border-2 border-transparent'
                  }
                  focus:outline-none focus:bg-indigo-50 focus:border-indigo-500
                  mobile-touch-target
                `}
              >
                <div className="p-2 bg-gray-100 rounded-lg flex-shrink-0">
                  <Icon size="sm">{feature.icon}</Icon>
                </div>

                <div className="flex-1 min-w-0 text-left">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">
                      {feature.title}
                    </span>
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                      {feature.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-0.5 line-clamp-1">
                    {feature.description}
                  </p>
                </div>

                {feature.shortcut && (
                  <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 border border-gray-300 rounded text-gray-500 flex-shrink-0">
                    {feature.shortcut}
                  </kbd>
                )}
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white border rounded">↑↓</kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white border rounded">↵</kbd>
              Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white border rounded">ESC</kbd>
              Close
            </span>
          </div>
          <span>{filteredFeatures.length} results</span>
        </div>
      </div>
    </div>
  );
};

export default FeatureSearch;
export { FEATURE_INDEX };
