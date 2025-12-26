// src/pages/QuickAssessment.tsx
// Quick assessment page for instant value demonstration
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import onboardingService from '../services/onboardingService';

interface AssessmentOption {
  id: string;
  text: string;
  icon: string;
}

const QuickAssessment: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const questions = [
    {
      id: 1,
      text: "When working on team projects, I prefer to:",
      options: [
        { id: 'a', text: "Take the lead and organize the work", icon: "👑" },
        { id: 'b', text: "Focus on the details and ensure everything is perfect", icon: "🔍" },
        { id: 'c', text: "Come up with creative ideas and possibilities", icon: "💡" },
        { id: 'd', text: "Make sure everyone feels included and heard", icon: "🤝" }
      ]
    },
    {
      id: 2,
      text: "When facing a problem, I typically:",
      options: [
        { id: 'a', text: "Analyze the facts and find the most logical solution", icon: "🧠" },
        { id: 'b', text: "Trust my intuition and go with what feels right", icon: "🎯" },
        { id: 'c', text: "Look for practical solutions that have worked before", icon: "⚙️" },
        { id: 'd', text: "Consider how the solution will affect everyone involved", icon: "👥" }
      ]
    },
    {
      id: 3,
      text: "In meetings, I usually:",
      options: [
        { id: 'a', text: "Speak up with my opinions and ideas", icon: "📢" },
        { id: 'b', text: "Listen carefully and ask clarifying questions", icon: "👂" },
        { id: 'c', text: "Focus on the agenda and keep things on track", icon: "📋" },
        { id: 'd', text: "Help build consensus and find common ground", icon: "🤝" }
      ]
    }
  ];

  const handleAnswer = (answerId: string) => {
    const newAnswers = { ...answers, [currentQuestion]: answerId };
    setAnswers(newAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Generate results
      generateResults(newAnswers);
    }
  };

  const generateResults = async (finalAnswers: Record<number, string>) => {
    setIsGenerating(true);

    try {
      // Simulate assessment analysis
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Generate mock results based on answers
      const personalityType = analyzePersonality(finalAnswers);
      const insights = await onboardingService.generateQuickInsights({
        role: user?.role === 'user' ? 'member' : user?.role || 'member', // Convert user role to onboarding role
        challenge: 'communication',
        team_size: '5-10'
      });

      setResults({
        personalityType,
        insights: insights.insights,
        recommendations: generateRecommendations(finalAnswers, personalityType)
      });
    } catch (error) {
      console.error('Failed to generate results:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const analyzePersonality = (answers: Record<number, string>) => {
    // Simple personality analysis based on answers
    const score = {
      leader: 0,
      detail: 0,
      creative: 0,
      collaborative: 0
    };

    Object.values(answers).forEach((answer, index) => {
      if (index === 0) {
        if (answer === 'a') score.leader += 2;
        if (answer === 'b') score.detail += 2;
        if (answer === 'c') score.creative += 2;
        if (answer === 'd') score.collaborative += 2;
      }
      // Add more complex analysis logic here
    });

    const maxScore = Math.max(...Object.values(score));
    const personalityType = Object.keys(score).find(key => score[key] === maxScore);

    const types: Record<string, string> = {
      leader: 'Leader',
      detail: 'Analyst',
      creative: 'Innovator',
      collaborative: 'Collaborator'
    };

    return types[personalityType] || 'Balanced';
  };

  const generateRecommendations = (answers: Record<number, string>, personalityType: string) => {
    const recommendations = [];

    if (personalityType === 'Leader') {
      recommendations.push({
        title: "Leverage Your Natural Leadership",
        description: "Consider taking on more project management roles",
        priority: "high"
      });
    }

    if (personalityType === 'Collaborator') {
      recommendations.push({
        title: "Focus on Team Building",
        description: "Your collaborative style is perfect for team cohesion",
        priority: "high"
      });
    }

    return recommendations;
  };

  const restartAssessment = () => {
    setCurrentQuestion(0);
    setAnswers({});
    setResults(null);
    setIsGenerating(false);
  };

  const saveToProfile = async () => {
    if (!user) return;

    setLoading(true);
    try {
      // Here you would save assessment results to user profile
      await new Promise(resolve => setTimeout(resolve, 1000));
      navigate('/profile');
    } catch (error) {
      console.error('Failed to save results:', error);
    } finally {
      setLoading(false);
    }
  };

  if (isGenerating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="large" color="indigo" className="mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Analyzing Your Responses...
          </h2>
          <p className="text-gray-600">
            Generating personalized insights based on your answers
          </p>
        </div>
      </div>
    );
  }

  if (results) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Your Personality Type: {results.personalityType}
              </h2>
              <p className="text-gray-600 mb-4">
                Based on your responses, here are your personalized insights
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-blue-50 rounded-lg p-6">
                <h3 className="font-semibold text-blue-900 mb-3">Your Strengths</h3>
                <ul className="space-y-2 text-blue-800">
                  <li className="flex items-start">
                    <svg className="w-5 h-5 mr-2 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    {results.personalityType} leadership style
                  </li>
                  <li className="flex items-start">
                    <svg className="w-5 h-5 mr-2 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Team-oriented approach
                  </li>
                </ul>
              </div>

              <div className="bg-green-50 rounded-lg p-6">
                <h3 className="font-semibold text-green-900 mb-3">Team Impact</h3>
                <ul className="space-y-2 text-green-800">
                  <li className="flex items-start">
                    <svg className="w-5 h-5 mr-2 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Improves team cohesion by 35%
                  </li>
                  <li className="flex items-start">
                    <svg className="w-5 h-5 mr-2 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Reduces meeting conflicts by 25%
                  </li>
                </ul>
              </div>
            </div>

            <div className="mb-8">
              <h3 className="font-semibold text-gray-900 mb-3">Personalized Recommendations</h3>
              <div className="space-y-4">
                {results.recommendations?.map((rec: any, index: number) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900">{rec.title}</h4>
                    <p className="text-gray-600 text-sm mt-1">{rec.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex space-x-4 justify-center">
              <Button onClick={restartAssessment} variant="secondary">
                Retake Assessment
              </Button>
              <Button onClick={saveToProfile} disabled={loading}>
                {loading ? 'Saving...' : 'Save to Profile'}
              </Button>
              <Button onClick={() => navigate('/dashboard')}>
                Go to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const question = questions[currentQuestion];
  const progress = ((currentQuestion + 1) / questions.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-2xl font-bold text-gray-900">Quick Assessment</h2>
              <span className="text-sm text-gray-500">
                Question {currentQuestion + 1} of {questions.length}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Question */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">
              {question.text}
            </h3>

            <div className="space-y-3">
              {question.options.map((option) => (
                <button
                  key={option.id}
                  onClick={() => handleAnswer(option.id)}
                  className="w-full text-left p-4 rounded-lg border-2 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
                >
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">{option.icon}</div>
                    <div className="flex-1">
                      <span className="text-gray-900 font-medium">{option.text}</span>
                    </div>
                    <div className="w-6 h-6 rounded-full border-2 border-gray-300 mr-3 flex items-center justify-center">
                      {answers[currentQuestion] === option.id && (
                        <div className="w-3 h-3 rounded-full bg-indigo-600" />
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center">
            <Button
              variant="secondary"
              onClick={() => {
                if (currentQuestion > 0) {
                  setCurrentQuestion(currentQuestion - 1);
                  const newAnswers = { ...answers };
                  delete newAnswers[currentQuestion];
                  setAnswers(newAnswers);
                }
              }}
              disabled={currentQuestion === 0}
            >
              Previous
            </Button>

            <div className="text-sm text-gray-500">
              Progress: {Math.round(progress)}%
            </div>

            <Button
              variant="secondary"
              onClick={() => navigate('/dashboard')}
            >
              Save for Later
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickAssessment;