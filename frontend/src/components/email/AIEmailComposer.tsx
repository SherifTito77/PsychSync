/**
 * AI Email Composer Component
 * Demonstrates AI-powered email personalization based on personality insights
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/common/Button';
import { api } from '@/services/api';

interface PersonalizationLevel {
  value: string;
  label: string;
  description: string;
}

interface EmailType {
  value: string;
  label: string;
  description: string;
}

interface AIEmailContent {
  subject: string;
  body: string;
  call_to_action: string;
  personalization_level: string;
  personality_adaptations: {
    extraversion_level: string;
    openness_level: string;
    conscientiousness_level: string;
    mbti_type: string;
    tone_adjustment: string;
  };
  optimal_send_time?: string;
  engagement_prediction?: number;
  tone: string;
}

interface UserPersona {
  user_id: string;
  name: string;
  role: string;
  experience_level: string;
  communication_preference: string;
  predicted_persona: string;
}

export const AIEmailComposer: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [emailType, setEmailType] = useState<string>('notification');
  const [personalizationLevel, setPersonalizationLevel] = useState<string>('personality');
  const [baseContent, setBaseContent] = useState({
    subject: 'Important Platform Update',
    body: 'We have exciting new features and improvements to share with you.',
    call_to_action: 'Learn More'
  });

  const [aiContent, setAIContent] = useState<AIEmailContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock user data - in real app this would come from API
  const mockUsers: UserPersona[] = [
    {
      user_id: 'user1',
      name: 'Sarah Chen',
      role: 'Team Lead',
      experience_level: 'Senior',
      communication_preference: 'Collaborative',
      predicted_persona: 'social_connector'
    },
    {
      user_id: 'user2',
      name: 'Michael Rodriguez',
      role: 'Software Engineer',
      experience_level: 'Senior',
      communication_preference: 'Independent',
      predicted_persona: 'analytical_achiever'
    },
    {
      user_id: 'user3',
      name: 'Emily Johnson',
      role: 'HR Manager',
      experience_level: 'Intermediate',
      communication_preference: 'Team-focused',
      predicted_persona: 'team_player'
    }
  ];

  const personalizationLevels: PersonalizationLevel[] = [
    {
      value: 'basic',
      label: 'Basic',
      description: 'Simple name replacement and basic formatting'
    },
    {
      value: 'behavioral',
      label: 'Behavioral',
      description: 'Based on observed behavioral patterns'
    },
    {
      value: 'personality',
      label: 'Personality-Based',
      description: 'Tailored to personality assessment results'
    },
    {
      value: 'predictive',
      label: 'Predictive AI',
      description: 'AI-optimized content and timing predictions'
    }
  ];

  const emailTypes: EmailType[] = [
    {
      value: 'notification',
      label: 'Notification',
      description: 'General updates and announcements'
    },
    {
      value: 'reminder',
      label: 'Reminder',
      description: 'Assessment deadlines and important dates'
    },
    {
      value: 'assessment_invitation',
      label: 'Assessment Invitation',
      description: 'Invitations to complete assessments'
    },
    {
      value: 'results_delivery',
      label: 'Results Delivery',
      description: 'Personal assessment results delivery'
    },
    {
      value: 'development_recommendation',
      label: 'Development Recommendation',
      description: 'Personalized growth suggestions'
    }
  ];

  const generateAIEmail = async () => {
    if (!selectedUser) {
      setError('Please select a user first');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const payload = {
        user_id: selectedUser,
        email_type: emailType,
        base_content: baseContent,
        personalization_level: personalizationLevel
      };

      // In a real implementation, this would call the AI email service
      // For now, we'll simulate the AI response based on persona
      const selectedUserPersona = mockUsers.find(u => u.user_id === selectedUser);
      const simulatedResponse = simulateAIEmailGeneration(payload, selectedUserPersona);

      setAIContent(simulatedResponse);
    } catch (err: any) {
      console.error('Error generating AI email:', err);
      setError(err.response?.data?.message || 'Failed to generate AI email');
    } finally {
      setLoading(false);
    }
  };

  const simulateAIEmailGeneration = (payload: any, userPersona?: UserPersona): AIEmailContent => {
    const baseSubject = payload.base_content.subject;
    const baseBody = payload.base_content.body;
    const baseCTA = payload.base_content.call_to_action;

    // Simulate AI personalization based on persona
    let subject = baseSubject;
    let body = baseBody;
    let callToAction = baseCTA;
    let tone = 'professional';
    let engagementPrediction = 0.65;

    if (userPersona) {
      switch (userPersona.predicted_persona) {
        case 'social_connector':
          subject = `Team Update: ${baseSubject}`;
          body = `${baseBody}\n\nJoin your colleagues who are already benefiting from these insights! Let's discuss how this can strengthen our team collaboration.`;
          callToAction = 'Connect & Discuss';
          tone = 'warm_friendly';
          engagementPrediction = 0.85;
          break;

        case 'analytical_achiever':
          subject = `Data-Driven Analysis: ${baseSubject}`;
          body = `${baseBody}\n\nKey performance indicators show significant impact potential. Detailed metrics and implementation strategy are available in your personalized dashboard.`;
          callToAction = 'View Detailed Analysis';
          tone = 'structured_formal';
          engagementPrediction = 0.75;
          break;

        case 'team_player':
          subject = `Team Success Update: ${baseSubject}`;
          body = `${baseBody}\n\nThese improvements will help us work better together and achieve our team goals more effectively.`;
          callToAction = 'Support Team Goals';
          tone = 'supportive';
          engagementPrediction = 0.80;
          break;
      }
    }

    return {
      subject,
      body,
      call_to_action: callToAction,
      personalization_level: payload.personalization_level,
      personality_adaptations: {
        extraversion_level: userPersona?.predicted_persona === 'social_connector' ? 'high' : 'medium',
        openness_level: 'medium',
        conscientiousness_level: userPersona?.predicted_persona === 'analytical_achiever' ? 'high' : 'medium',
        mbti_type: 'unknown',
        tone_adjustment: tone
      },
      optimal_send_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
      engagement_prediction: engagementPrediction,
      tone
    };
  };

  const getPersonaColor = (persona: string) => {
    switch (persona) {
      case 'social_connector': return 'bg-purple-100 text-purple-800';
      case 'analytical_achiever': return 'bg-blue-100 text-blue-800';
      case 'team_player': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getEngagementColor = (prediction: number) => {
    if (prediction > 0.8) return 'text-green-600';
    if (prediction > 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Email Composer</h1>
          <p className="text-gray-600 mt-2">
            Create AI-personalized emails based on personality insights and behavioral patterns
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-6">
          {/* User Selection */}
          <Card className="p-4">
            <h3 className="font-semibold mb-3">1. Select Recipient</h3>
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">Choose a user...</option>
              {mockUsers.map(user => (
                <option key={user.user_id} value={user.user_id}>
                  {user.name} - {user.role}
                </option>
              ))}
            </select>

            {selectedUser && (
              <div className="mt-3 p-3 bg-gray-50 rounded">
                <div className="text-sm">
                  <div className="font-medium">{mockUsers.find(u => u.user_id === selectedUser)?.name}</div>
                  <div className="text-gray-600">{mockUsers.find(u => u.user_id === selectedUser)?.role}</div>
                  <div className="mt-1">
                    <span className={`inline-block px-2 py-1 rounded text-xs ${getPersonaColor(mockUsers.find(u => u.user_id === selectedUser)?.predicted_persona || '')}`}>
                      {mockUsers.find(u => u.user_id === selectedUser)?.predicted_persona?.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </Card>

          {/* Email Type */}
          <Card className="p-4">
            <h3 className="font-semibold mb-3">2. Email Type</h3>
            <select
              value={emailType}
              onChange={(e) => setEmailType(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              {emailTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {emailTypes.find(t => t.value === emailType)?.description}
            </p>
          </Card>

          {/* Personalization Level */}
          <Card className="p-4">
            <h3 className="font-semibold mb-3">3. AI Personalization</h3>
            <div className="space-y-2">
              {personalizationLevels.map(level => (
                <label key={level.value} className="flex items-start">
                  <input
                    type="radio"
                    value={level.value}
                    checked={personalizationLevel === level.value}
                    onChange={(e) => setPersonalizationLevel(e.target.value)}
                    className="mt-1 mr-2"
                  />
                  <div>
                    <div className="font-medium text-sm">{level.label}</div>
                    <div className="text-xs text-gray-500">{level.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </Card>

          {/* Base Content */}
          <Card className="p-4">
            <h3 className="font-semibold mb-3">4. Base Content</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  value={baseContent.subject}
                  onChange={(e) => setBaseContent({...baseContent, subject: e.target.value})}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Body
                </label>
                <textarea
                  value={baseContent.body}
                  onChange={(e) => setBaseContent({...baseContent, body: e.target.value})}
                  rows={4}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Call to Action
                </label>
                <input
                  type="text"
                  value={baseContent.call_to_action}
                  onChange={(e) => setBaseContent({...baseContent, call_to_action: e.target.value})}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
              </div>
            </div>
          </Card>

          {/* Generate Button */}
          <Button
            onClick={generateAIEmail}
            disabled={!selectedUser || loading}
            className="w-full"
          >
            {loading ? '🤖 Generating AI Email...' : '🚀 Generate AI-Personalized Email'}
          </Button>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <Card className="p-4 border-red-200 bg-red-50">
              <div className="text-red-600">⚠️ {error}</div>
            </Card>
          )}

          {aiContent && (
            <>
              {/* AI Email Preview */}
              <Card className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold">📧 AI-Generated Email</h3>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      Engagement Prediction:
                    </span>
                    <span className={`font-bold ${getEngagementColor(aiContent.engagement_prediction || 0)}`}>
                      {Math.round((aiContent.engagement_prediction || 0) * 100)}%
                    </span>
                  </div>
                </div>

                {/* Email Preview */}
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                    <div className="text-sm">
                      <strong>Subject:</strong> {aiContent.subject}
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="whitespace-pre-wrap text-sm">
                      {aiContent.body}
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <Button className="w-full">
                        {aiContent.call_to_action}
                      </Button>
                    </div>
                  </div>
                </div>

                {/* AI Insights */}
                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-2">🧠 AI Adaptations</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Tone:</span>
                        <span className="font-medium capitalize">{aiContent.tone.replace('_', ' ')}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Extraversion:</span>
                        <span className="font-medium capitalize">{aiContent.personality_adaptations.extraversion_level}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Conscientiousness:</span>
                        <span className="font-medium capitalize">{aiContent.personality_adaptations.conscientiousness_level}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">⏰ Optimal Timing</h4>
                    {aiContent.optimal_send_time && (
                      <div className="text-sm">
                        <div className="text-gray-600">Best send time:</div>
                        <div className="font-medium">
                          {new Date(aiContent.optimal_send_time).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </Card>

              {/* Comparison */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">📊 AI vs Original Comparison</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-600 mb-3">Original Email</h4>
                    <div className="border border-gray-200 rounded p-3 bg-gray-50">
                      <div className="text-sm font-medium mb-2">{baseContent.subject}</div>
                      <div className="text-sm text-gray-600 mb-3">{baseContent.body}</div>
                      <div className="text-sm italic text-gray-500">
                        Standard messaging - no personalization
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-green-600 mb-3">AI-Enhanced Email</h4>
                    <div className="border border-green-200 rounded p-3 bg-green-50">
                      <div className="text-sm font-medium mb-2">{aiContent.subject}</div>
                      <div className="text-sm text-gray-700 mb-3">{aiContent.body}</div>
                      <div className="text-sm text-green-600">
                        ✓ Personalized for {personalizationLevels.find(l => l.value === personalizationLevel)?.label} level
                      </div>
                      <div className="text-sm text-green-600">
                        ✓ Optimized for {aiContent.personality_adaptations.tone_adjustment} tone
                      </div>
                      <div className="text-sm text-green-600">
                        ✓ {Math.round(((aiContent.engagement_prediction || 0) - 0.5) * 100)}% higher predicted engagement
                      </div>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Action Buttons */}
              <div className="flex space-x-3">
                <Button variant="outline" className="flex-1">
                  📤 Test Send
                </Button>
                <Button variant="outline" className="flex-1">
                  💾 Save Template
                </Button>
                <Button className="flex-1">
                  📈 Schedule Campaign
                </Button>
              </div>
            </>
          )}

          {!aiContent && !loading && (
            <Card className="p-12 text-center">
              <div className="text-gray-400 text-6xl mb-4">🤖</div>
              <h3 className="text-lg font-medium text-gray-600 mb-2">
                Ready to Create AI-Personalized Emails
              </h3>
              <p className="text-gray-500 text-sm">
                Select a recipient and click "Generate AI-Personalized Email" to see the power of AI-driven personalization
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};