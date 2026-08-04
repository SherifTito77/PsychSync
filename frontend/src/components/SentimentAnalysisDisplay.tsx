/**
 * Sentiment Analysis Display Component
 * Shows emotional tone analysis of emails
 */

import React, { useState, useEffect } from 'react';
import {
  FaceSmileIcon,
  FaceFrownIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  EnvelopeIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';

interface SentimentData {
  sentiment: {
    polarity: 'positive' | 'negative' | 'neutral';
    confidence: number;
    positive_score: number;
    negative_score: number;
    breakdown: {
      positive: { strong: number; moderate: number; weak: number };
      negative: { strong: number; moderate: number; weak: number };
    };
  };
  emotional_tones: {
    primary_tone: string;
    tones: Array<{ tone: string; count: number; intensity: string }>;
    has_emotional_content: boolean;
  };
  stress_analysis: {
    stress_level: string;
    stress_score: number;
    indicators: Array<{ indicator: string; count: number; severity: string }>;
    requires_attention: boolean;
  };
  key_phrases: string[];
  insights: string[];
}

interface EmailData {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
  body?: string;
}

interface AnalyzedEmail {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
  is_new: boolean;
  analysis: SentimentData;
}

interface AnalyzedEmails {
  emails_analyzed: number;
  new_emails: number;
  total_emails: number;
  analyses: AnalyzedEmail[];
}

interface SentimentAnalysisDisplayProps {
  emailContent?: string;
  emailSubject?: string;
  autoAnalyze?: boolean;
  standalone?: boolean; // If true, fetch emails from backend
  autoAnalyzeNew?: boolean; // If true, automatically analyze new emails on mount
}

export const SentimentAnalysisDisplay: React.FC<SentimentAnalysisDisplayProps> = ({
  emailContent = '',
  emailSubject = '',
  autoAnalyze = true,
  standalone = false,
  autoAnalyzeNew = false,
}) => {
  console.log('🔍 SentimentAnalysisDisplay component rendering!');
  const [analysis, setAnalysis] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [emails, setEmails] = useState<EmailData[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailData | null>(null);
  const [view, setView] = useState<'list' | 'analyze' | 'results'>('list');
  const [loadingEmails, setLoadingEmails] = useState(false);
  const [analyzedEmails, setAnalyzedEmails] = useState<AnalyzedEmail[]>([]);
  const [autoAnalyzedCount, setAutoAnalyzedCount] = useState(0);
  const [newEmailsCount, setNewEmailsCount] = useState(0);
  const [previousView, setPreviousView] = useState<'list' | 'results'>('list');

  // Fetch emails when in standalone mode
  useEffect(() => {
    if (standalone && !emailContent) {
      if (autoAnalyzeNew) {
        autoAnalyzeNewEmails();
      } else {
        fetchEmails();
      }
    }
  }, [standalone, autoAnalyzeNew]);

  const fetchEmails = async () => {
    setLoadingEmails(true);
    try {
      // Try both token keys for compatibility
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');

      if (!token) {
        console.error('❌ No auth token found in localStorage');
        setEmails([]);
        setLoadingEmails(false);
        return;
      }

      console.log('🔍 Fetching emails from API...');
      console.log('🔑 Using token:', token.substring(0, 20) + '...');

      // Fetch emails from the sentiment analysis emails endpoint
      const response = await fetch('http://localhost:8000/api/v1/sentiment-analysis/emails?page=1&limit=30', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log('📡 API Response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Received data from API:', data);
        // Transform API response to match our EmailData interface
        const transformedEmails = (data.emails || []).map((email: any) => ({
          id: email.id,
          subject: email.subject,
          from: email.from,
          date: email.date,
          snippet: email.snippet,
          body: email.body
        }));
        console.log(`📧 Transformed ${transformedEmails.length} emails`);
        setEmails(transformedEmails);
      } else {
        // If API fails, show mock data for demo
        const errorText = await response.text();
        console.error('❌ API Error:', response.status, errorText);
        setEmails(getMockEmails());
      }
    } catch (err) {
      console.error('❌ Failed to fetch emails:', err);
      // Show mock data on error
      setEmails(getMockEmails());
    } finally {
      setLoadingEmails(false);
    }
  };

  const clearCacheAndRefresh = async () => {
    setLoadingEmails(true);
    setError('');

    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');

      if (!token) {
        console.error('❌ No auth token found!');
        setError('Authentication required.');
        setLoadingEmails(false);
        return;
      }

      console.log('🗑️ Clearing email cache...');

      const response = await fetch('http://localhost:8000/api/v1/sentiment-analysis/clear-cache', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Cache cleared:', result.message);

        // Now fetch fresh emails
        await fetchEmails();
      } else {
        setError('Failed to clear cache.');
        setLoadingEmails(false);
      }
    } catch (err) {
      console.error('❌ Failed to clear cache:', err);
      setError('Failed to clear cache.');
      setLoadingEmails(false);
    }
  };

  const autoAnalyzeNewEmails = async () => {
    setLoadingEmails(true);
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');

      if (!token) {
        console.error('❌ No auth token found!');
        setError('Authentication required. Please login again.');
        setLoadingEmails(false);
        setLoading(false);
        return;
      }

      console.log('🔍 Auto-analyzing new emails...');

      const response = await fetch('http://localhost:8000/api/v1/sentiment-analysis/auto-analyze-new?limit=30&days_back=7', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log('📡 Auto-analyze response status:', response.status);

      if (response.ok) {
        const data: AnalyzedEmails = await response.json();
        console.log('✅ Auto-analysis complete:', data);

        setAnalyzedEmails(data.analyses);
        setAutoAnalyzedCount(data.emails_analyzed);
        setNewEmailsCount(data.new_emails);

        // Also populate the emails list for manual selection
        const transformedEmails = data.analyses.map((item: AnalyzedEmail) => ({
          id: item.id,
          subject: item.subject,
          from: item.from,
          date: item.date,
          snippet: item.snippet,
          body: '' // Body is not included in the analysis response
        }));
        setEmails(transformedEmails);

        // If we have analyzed emails, show the results view
        if (data.analyses.length > 0) {
          setView('results');
        }
      } else {
        const errorText = await response.text();
        console.error('❌ Auto-analysis API Error:', response.status, errorText);
        setError('Failed to auto-analyze emails. Please try again.');
      }
    } catch (err) {
      console.error('❌ Auto-analysis error:', err);
      setError('Failed to connect to analysis service.');
    } finally {
      setLoadingEmails(false);
      setLoading(false);
    }
  };

  const getMockEmails = (): EmailData[] => {
    return [
      {
        id: '1',
        subject: 'Quarterly Performance Review',
        from: 'manager@company.com',
        date: '2025-01-20',
        snippet: 'I wanted to discuss your performance over the last quarter...',
        body: 'I wanted to discuss your performance over the last quarter. You have shown excellent dedication and your team collaboration skills have improved significantly. However, there are some areas where we need to focus on time management and meeting deadlines. Let us schedule a meeting to discuss this further and create an action plan for your development.'
      },
      {
        id: '2',
        subject: 'Urgent: Project Deadline',
        from: 'client@business.com',
        date: '2025-01-19',
        snippet: 'We need to move up the deadline by two weeks...',
        body: 'We need to move up the deadline by two weeks due to changing market conditions. I understand this is short notice and may cause stress, but we need your team to prioritize the critical features. Please let me know if this is feasible and what support you need.'
      },
      {
        id: '3',
        subject: 'Team Appreciation',
        from: 'hr@company.com',
        date: '2025-01-18',
        snippet: 'Congratulations on the successful project launch!',
        body: 'Congratulations on the successful project launch! The entire team did an outstanding job. Your hard work, dedication, and collaborative spirit made this possible. We are proud to have such an amazing team and look forward to celebrating together at the upcoming team event.'
      },
      {
        id: '4',
        subject: 'Budget Concerns',
        from: 'finance@company.com',
        date: '2025-01-17',
        snippet: 'We need to discuss the department budget cuts...',
        body: 'We need to discuss the department budget cuts. Unfortunately, we are facing financial constraints and need to reduce expenses by 15%. This is difficult news and I know it will impact the team. We should explore options together to minimize the impact on critical operations and team morale.'
      }
    ];
  };

  const analyzeSentiment = async (content?: string, subject?: string) => {
    const contentToAnalyze = content || emailContent;
    const subjectToUse = subject || emailSubject;

    if (!contentToAnalyze || contentToAnalyze.length < 10) {
      setError('Email content too short for analysis');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');

      if (!token) {
        console.error('❌ No auth token found!');
        setError('Authentication required. Please login again.');
        setLoading(false);
        return;
      }

      console.log('🔍 Sending analysis request for:', subjectToUse.substring(0, 50));
      console.log('📧 Content length:', contentToAnalyze.length);
      console.log('🔑 Token:', token.substring(0, 30) + '...');

      const response = await fetch('http://localhost:8000/api/v1/sentiment-analysis/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          content: contentToAnalyze,
          subject: subjectToUse,
        }),
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response OK:', response.ok);

      const data = await response.json();
      console.log('📦 Response data:', data);

      if (response.ok) {
        console.log('✅ Setting analysis from API:', data.email_analysis);
        setAnalysis(data.email_analysis);
      } else {
        console.error('❌ API Error:', response.status, data);
        // If API fails, show mock analysis for demo
        setAnalysis(getMockAnalysis());
      }
    } catch (err) {
      console.error('❌ Sentiment analysis error:', err);
      // Show mock analysis on error
      setAnalysis(getMockAnalysis());
    } finally {
      setLoading(false);
    }
  };

  const getMockAnalysis = (): SentimentData => {
    return {
      sentiment: {
        polarity: 'neutral',
        confidence: 0.75,
        positive_score: 6,
        negative_score: 4,
        breakdown: {
          positive: { strong: 2, moderate: 3, weak: 1 },
          negative: { strong: 1, moderate: 2, weak: 1 }
        }
      },
      emotional_tones: {
        primary_tone: 'professional',
        tones: [
          { tone: 'professional', count: 5, intensity: 'moderate' },
          { tone: 'concerned', count: 3, intensity: 'moderate' },
          { tone: 'supportive', count: 2, intensity: 'weak' }
        ],
        has_emotional_content: true
      },
      stress_analysis: {
        stress_level: 'moderate',
        stress_score: 5.5,
        indicators: [
          { indicator: 'deadline_pressure', count: 3, severity: 'moderate' },
          { indicator: 'workload', count: 2, severity: 'low' }
        ],
        requires_attention: false
      },
      key_phrases: [
        'need to discuss',
        'deadline',
        'team collaboration',
        'support',
        'concerns'
      ],
      insights: [
        'The email shows professional communication with balanced emotional tone',
        'Moderate stress indicators related to deadlines and workload',
        'Supportive language suggests positive team dynamics',
        'Clear action-oriented communication style'
      ]
    };
  };

  useEffect(() => {
    if (autoAnalyze && emailContent && !standalone) {
      analyzeSentiment();
    }
  }, [emailContent, emailSubject, autoAnalyze]);

  const handleSelectEmail = (email: EmailData) => {
    // Remember which view we came from
    setPreviousView(view);

    // Check if we already have analysis for this email from auto-analysis
    const existingAnalysis = analyzedEmails.find(item => item.id === email.id);

    setSelectedEmail(email);
    setView('analyze');

    if (existingAnalysis) {
      // Use existing analysis instead of re-analyzing
      console.log('✅ Using existing analysis for email:', email.id);
      setAnalysis(existingAnalysis.analysis);
    } else if (email.body && email.body.length > 0) {
      // Only analyze if we have body content
      analyzeSentiment(email.body, email.subject);
    } else {
      // Fetch full email content and then analyze
      fetchEmailAndAnalyze(email.id);
    }
  };

  const fetchEmailAndAnalyze = async (emailId: string) => {
    setLoading(true);
    setError('Fetching email content...');

    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');

      if (!token) {
        setError('Authentication required.');
        setLoading(false);
        return;
      }

      // Fetch all emails to get the body
      const response = await fetch('http://localhost:8000/api/v1/sentiment-analysis/emails?page=1&limit=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const fullEmail = (data.emails || []).find((e: any) => e.id === emailId);

        if (fullEmail && fullEmail.body) {
          // Update the selected email with full content
          setSelectedEmail({
            id: fullEmail.id,
            subject: fullEmail.subject,
            from: fullEmail.from,
            date: fullEmail.date,
            snippet: fullEmail.snippet,
            body: fullEmail.body
          });

          // Analyze the full email
          await analyzeSentiment(fullEmail.body, fullEmail.subject);
        } else {
          setError('Could not fetch email content. Please try again.');
        }
      } else {
        setError('Failed to fetch email content.');
      }
    } catch (err) {
      console.error('Failed to fetch email:', err);
      setError('Failed to fetch email content.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToList = () => {
    // Go back to the previous view (results or list)
    setView(previousView);
    setSelectedEmail(null);
    setAnalysis(null);
  };

  const getSentimentIcon = () => {
    if (!analysis) return <FaceFrownIcon className="w-8 h-8 text-gray-400" />;

    switch (analysis.sentiment.polarity) {
      case 'positive':
        return <FaceSmileIcon className="w-8 h-8 text-green-500" />;
      case 'negative':
        return <FaceFrownIcon className="w-8 h-8 text-red-500" />;
      default:
        return <FaceFrownIcon className="w-8 h-8 text-gray-500" />;
    }
  };

  const getSentimentColor = () => {
    if (!analysis) return 'gray';

    switch (analysis.sentiment.polarity) {
      case 'positive':
        return 'green';
      case 'negative':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStressColor = () => {
    if (!analysis) return 'gray';

    switch (analysis.stress_analysis.stress_level) {
      case 'very high':
        return 'red';
      case 'high':
        return 'orange';
      case 'moderate':
        return 'yellow';
      default:
        return 'green';
    }
  };

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="text-gray-600">Analyzing email sentiment...</p>
        </div>
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="bg-red-50 p-4 rounded-lg border border-red-200">
        <p className="text-red-700">{error}</p>
        <button
          onClick={() => {
            if (autoAnalyzeNew) {
              autoAnalyzeNewEmails();
            } else {
              fetchEmails();
            }
          }}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  // Standalone mode: Show auto-analysis results
  if (standalone && view === 'results') {
    return (
      <div className="space-y-4">
        {/* Header */}
        <div key="header" className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
          <h1 className="text-3xl font-bold mb-2">😊 Sentiment Analysis</h1>
          <p className="text-purple-100">
            Analyzed {autoAnalyzedCount} emails ({newEmailsCount} new)
          </p>
        </div>

        {/* Action Buttons */}
        <div key="actions" className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setView('list')}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 font-medium"
            >
              View All Emails
            </button>
            <button
              onClick={autoAnalyzeNewEmails}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-medium"
            >
              Refresh Analysis
            </button>
            <button
              onClick={clearCacheAndRefresh}
              disabled={loadingEmails}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loadingEmails ? 'Refreshing...' : '🔄 Clear Cache & Refresh'}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Clear cache to fetch your latest 30 emails from connected accounts
          </p>
        </div>

        {/* Results List */}
        {analyzedEmails.length === 0 ? (
          <div key="no-results" className="bg-white p-6 rounded-lg shadow border border-gray-200">
            <p className="text-gray-500">No analyzed emails found.</p>
          </div>
        ) : (
          <div key="results-list" className="space-y-4">
            {analyzedEmails.map((item, index) => (
              <div
                key={`${item.id}-${index}`}
                onClick={() => {
                  // We already have the analysis! Use it directly.
                  const emailData: EmailData = {
                    id: item.id,
                    subject: item.subject,
                    from: item.from,
                    date: item.date,
                    snippet: item.snippet,
                    body: '' // Body not needed since we have analysis
                  };

                  // Set the selected email and use the existing analysis
                  setSelectedEmail(emailData);
                  setView('analyze');
                  setAnalysis(item.analysis); // Use the analysis we already have!
                  setPreviousView('results');
                }}
                className={`bg-white rounded-lg shadow border-2 overflow-hidden cursor-pointer hover:shadow-lg transition-shadow ${
                  item.is_new ? 'border-green-300' : 'border-gray-200'
                }`}
              >
                {/* Email Header */}
                <div className={`p-4 ${
                  item.is_new ? 'bg-green-50' : 'bg-gray-50'
                } border-b border-gray-200`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-semibold text-gray-900 truncate">
                          {item.subject}
                        </h3>
                        {item.is_new && (
                          <span className="px-2 py-1 bg-green-500 text-white text-xs font-medium rounded-full">
                            NEW
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        From: {item.from}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {item.date}
                      </p>
                      <p className="text-xs text-purple-600 mt-1 flex items-center">
                        Click for details →
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                    {item.snippet}
                  </p>
                </div>

                {/* Analysis Summary */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      {item.analysis.sentiment.polarity === 'positive' ? (
                        <FaceSmileIcon className="w-6 h-6 text-green-500" />
                      ) : item.analysis.sentiment.polarity === 'negative' ? (
                        <FaceFrownIcon className="w-6 h-6 text-red-500" />
                      ) : (
                        <FaceFrownIcon className="w-6 h-6 text-gray-500" />
                      )}
                      <div>
                        <p className="text-lg font-bold capitalize text-gray-900">
                          {item.analysis.sentiment.polarity}
                        </p>
                        <p className="text-xs text-gray-500">
                          {Math.round(item.analysis.sentiment.confidence * 100)}% confidence
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Stress Level</p>
                      <p className={`text-sm font-bold capitalize ${
                        item.analysis.stress_analysis.stress_level === 'very high' ? 'text-red-600' :
                        item.analysis.stress_analysis.stress_level === 'high' ? 'text-orange-600' :
                        item.analysis.stress_analysis.stress_level === 'moderate' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {item.analysis.stress_analysis.stress_level}
                      </p>
                    </div>
                  </div>

                  {/* Emotional Tones */}
                  {item.analysis.emotional_tones.has_emotional_content && (
                    <div className="mb-3">
                      <div className="flex flex-wrap gap-1">
                        {item.analysis.emotional_tones.tones.slice(0, 3).map((tone) => (
                          <span
                            key={`${tone.tone}-${tone.count}`}
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              tone.intensity === 'high'
                                ? 'bg-red-100 text-red-800'
                                : tone.intensity === 'moderate'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}
                          >
                            {tone.tone}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Key Insights */}
                  {item.analysis.insights.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-600">
                        💡 {item.analysis.insights[0]}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Standalone mode: Show email list
  if (standalone && view === 'list') {
    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
          <h1 className="text-3xl font-bold mb-2">😊 Sentiment Analysis</h1>
          <p className="text-purple-100">
            Analyze the emotional tone and sentiment of your emails
          </p>
        </div>

        {/* Action Button */}
        <div className="flex justify-end">
          <button
            onClick={clearCacheAndRefresh}
            disabled={loadingEmails}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
          >
            {loadingEmails ? 'Refreshing...' : '🔄 Clear Cache & Refresh Latest Emails'}
          </button>
        </div>

        {/* Email List */}
        {loadingEmails ? (
          <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
            <div className="flex items-center justify-center space-x-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <p className="text-gray-600">Loading your emails...</p>
            </div>
          </div>
        ) : emails.length === 0 ? (
          <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
            <p className="text-gray-500">No emails found. Connect your email account first.</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
            <div className="p-4 bg-gray-50 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <EnvelopeIcon className="w-5 h-5 mr-2" />
                Select an Email to Analyze
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {emails.length} emails available
              </p>
            </div>
            <div className="divide-y divide-gray-200">
              {emails.map((email, index) => (
                <button
                  key={`${email.id}-${index}`}
                  onClick={() => handleSelectEmail(email)}
                  className="w-full p-4 hover:bg-purple-50 transition-colors text-left"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {email.subject}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        From: {email.from}
                      </p>
                      <p className="text-xs text-gray-500 mt-1 truncate">
                        {email.snippet}
                      </p>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      <p className="text-xs text-gray-500">{email.date}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  if (!analysis && !standalone) {
    return (
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <p className="text-gray-500 mb-4">No analysis available</p>
        <button
          onClick={() => analyzeSentiment()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Analyze Sentiment
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Back Button and Email Info (standalone mode) */}
      {standalone && selectedEmail && (
        <>
          <button
            onClick={handleBackToList}
            className="flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-medium"
          >
            <ArrowLeftIcon className="w-5 h-5" />
            <span>Back to Email List</span>
          </button>

          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h3 className="font-semibold text-gray-900">{selectedEmail.subject}</h3>
            <p className="text-sm text-gray-600 mt-1">From: {selectedEmail.from}</p>
            <p className="text-sm text-gray-500 mt-1">{selectedEmail.date}</p>
          </div>
        </>
      )}

      {/* Overall Sentiment */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <ChartBarIcon className="w-5 h-5 mr-2" />
          Sentiment Analysis
        </h3>

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            {getSentimentIcon()}
            <div>
              <p className="text-2xl font-bold text-gray-900 capitalize">
                {analysis.sentiment.polarity}
              </p>
              <p className="text-sm text-gray-500">
                Confidence: {Math.round(analysis.sentiment.confidence * 100)}%
              </p>
            </div>
          </div>

          <div className="text-right">
            <p className="text-sm text-gray-500">Scores</p>
            <p className="text-green-600 font-semibold">
              +{analysis.sentiment.positive_score}
            </p>
            <p className="text-red-600 font-semibold">
              -{analysis.sentiment.negative_score}
            </p>
          </div>
        </div>

        {/* Sentiment Bar */}
        <div className="mb-6">
          <div className="flex h-4 rounded-full overflow-hidden bg-gray-200">
            <div
              className="bg-green-500 flex items-center justify-center text-xs font-bold text-white"
              style={{
                width: `${(analysis.sentiment.positive_score /
                  (analysis.sentiment.positive_score + analysis.sentiment.negative_score)) * 100}%`,
              }}
            >
              {analysis.sentiment.positive_score > 0 && (
                <span className="px-1">{analysis.sentiment.positive_score}</span>
              )}
            </div>
            <div
              className="bg-red-500 flex items-center justify-center text-xs font-bold text-white"
              style={{
                width: `${(analysis.sentiment.negative_score /
                  (analysis.sentiment.positive_score + analysis.sentiment.negative_score)) * 100}%`,
              }}
            >
              {analysis.sentiment.negative_score > 0 && (
                <span className="px-1">{analysis.sentiment.negative_score}</span>
              )}
            </div>
          </div>
        </div>

        {/* Emotional Tones */}
        {analysis.emotional_tones.has_emotional_content && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Emotional Tones</h4>
            <div className="flex flex-wrap gap-2">
              {analysis.emotional_tones.tones.map((tone) => (
                <span
                  key={`${tone.tone}-${tone.count}`}
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    tone.intensity === 'high'
                      ? 'bg-red-100 text-red-800'
                      : tone.intensity === 'moderate'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  {tone.tone} ({tone.count})
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Stress Analysis */}
        <div className={`p-4 rounded-lg border-2 ${
          analysis.stress_analysis.requires_attention
            ? 'bg-orange-50 border-orange-300'
            : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-gray-700">Stress Level</h4>
            {analysis.stress_analysis.requires_attention && (
              <div className="flex items-center text-orange-600">
                <ExclamationTriangleIcon className="w-4 h-4 mr-1" />
                <span className="text-xs font-medium">Requires Attention</span>
              </div>
            )}
          </div>

          <p className="text-lg font-bold capitalize mb-2" style={{
            color: getStressColor() === 'red' ? '#dc2626' :
                   getStressColor() === 'orange' ? '#ea580c' :
                   getStressColor() === 'yellow' ? '#ca8a04' : '#16a34a'
          }}>
            {analysis.stress_analysis.stress_level}
          </p>

          {analysis.stress_analysis.indicators.length > 0 && (
            <div className="space-y-1">
              {analysis.stress_analysis.indicators.map((indicator, index) => (
                <div key={`indicator-${index}`} className="text-xs text-gray-600">
                  • {indicator.indicator.replace('_', ' ')} ({indicator.count})
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Key Phrases */}
      {analysis.key_phrases.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Key Phrases Detected</h4>
          <div className="flex flex-wrap gap-2">
            {analysis.key_phrases.map((phrase, index) => (
              <span
                key={`phrase-${index}`}
                className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium"
              >
                {phrase}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Insights */}
      {analysis.insights.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Insights</h4>
          <ul className="space-y-2">
            {analysis.insights.map((insight, index) => (
              <li key={`insight-${index}`} className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span className="text-sm text-gray-600">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Re-analyze Button */}
      <button
        onClick={() => analyzeSentiment()}
        className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 font-medium"
      >
        Re-analyze
      </button>
    </div>
  );
};

export default SentimentAnalysisDisplay;
