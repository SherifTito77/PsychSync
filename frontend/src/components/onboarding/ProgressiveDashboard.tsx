// src/components/onboarding/ProgressiveDashboard.tsx
// Dashboard that reveals features progressively
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  component: React.ReactNode;
  estimatedTime: string;
  isCompleted: boolean;
  isSkippable: boolean;
}

interface ProgressiveDashboardProps {
  initialRole: string;
  initialChallenge: string;
  isSocialSignup?: boolean;
}

const ProgressiveDashboard: React.FC<ProgressiveDashboardProps> = ({
  initialRole,
  initialChallenge,
  isSocialSignup = false
}) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);
  const [dashboardData, setDashboardData] = useState({
    teams: [],
    assessments: [],
    insights: null,
    setupProgress: 0
  });

  const onboardingSteps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to PsychSync!',
      description: 'Let\'s set up your behavioral intelligence dashboard',
      component: null, // Custom component will be rendered
      estimatedTime: '30 seconds',
      isCompleted: true,
      isSkippable: false
    },
    {
      id: 'team_setup',
      title: 'Set Up Your First Team',
      description: 'Create or import your team to get personalized insights',
      component: null,
      estimatedTime: '2 minutes',
      isCompleted: false,
      isSkippable: true
    },
    {
      id: 'quick_assessment',
      title: 'Quick Personality Assessment',
      description: 'Take a 2-minute assessment to unlock team insights',
      component: null,
      estimatedTime: '2 minutes',
      isCompleted: false,
      isSkippable: true
    },
    {
      id: 'first_insights',
      title: 'Your First Insights',
      description: 'See your personalized team behavioral analysis',
      component: null,
      estimatedTime: '1 minute',
      isCompleted: false,
      isSkippable: false
    }
  ];

  useEffect(() => {
    // Animate progress when step changes
    setIsAnimating(true);
    const timer = setTimeout(() => setIsAnimating(false), 300);
    return () => clearTimeout(timer);
  }, [currentStep]);

  const nextStep = () => {
    if (currentStep < onboardingSteps.length - 1) {
      setCurrentStep(currentStep + 1);
      updateStepCompletion(currentStep, true);
    }
  };

  const skipStep = () => {
    if (currentStep < onboardingSteps.length - 1) {
      setCurrentStep(currentStep + 1);
      updateStepCompletion(currentStep, false);
    }
  };

  const goToDashboard = () => {
    setShowConfetti(true);
    setTimeout(() => {
      navigate('/dashboard');
    }, 2000);
  };

  const updateStepCompletion = (stepIndex: number, completed: boolean) => {
    const updatedSteps = [...onboardingSteps];
    updatedSteps[stepIndex].isCompleted = completed;
    const progress = (updatedSteps.filter(s => s.isCompleted).length / updatedSteps.length) * 100;
    setDashboardData(prev => ({ ...prev, setupProgress: progress }));
  };

  const currentStepData = onboardingSteps[currentStep];

  const renderStepContent = () => {
    switch (currentStepData.id) {
      case 'welcome':
        return <WelcomeStep user={user} role={initialRole} challenge={initialChallenge} />;
      case 'team_setup':
        return <TeamSetupStep onComplete={nextStep} onSkip={skipStep} />;
      case 'quick_assessment':
        return <QuickAssessmentStep role={initialRole} onComplete={nextStep} onSkip={skipStep} />;
      case 'first_insights':
        return <FirstInsightsStep onComplete={goToDashboard} />;
      default:
        return null;
    }
  };

  const progressPercentage = ((currentStep + 1) / onboardingSteps.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Progress */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">PsychSync Setup</h1>
              <p className="text-sm text-gray-600">{currentStepData.description}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">
                  Step {currentStep + 1} of {onboardingSteps.length}
                </div>
                <div className="text-xs text-gray-500">
                  {currentStepData.estimatedTime}
                </div>
              </div>
              <div className="w-32">
                <div className="flex space-x-1">
                  {onboardingSteps.map((step, index) => (
                    <div
                      key={step.id}
                      className={`flex-1 h-2 rounded-full transition-colors ${
                        index < currentStep
                          ? 'bg-green-500'
                          : index === currentStep
                          ? 'bg-indigo-500'
                          : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className={`transition-all duration-300 ${isAnimating ? 'opacity-0 transform translate-x-4' : 'opacity-100 transform translate-x-0'}`}>
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {currentStepData.title}
            </h2>

            {/* Step Content */}
            <div className="mt-6">
              {renderStepContent()}
            </div>
          </div>
        </div>

        {/* Quick Actions Sidebar */}
        {currentStep > 0 && (
          <div className="mt-8 flex justify-center space-x-4">
            {currentStep > 0 && (
              <Button variant="secondary" onClick={() => setCurrentStep(currentStep - 1)}>
                Previous
              </Button>
            )}

            {currentStepData.isSkippable && currentStep < onboardingSteps.length - 1 && (
              <Button variant="secondary" onClick={skipStep}>
                Skip this step
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Success Confetti */}
      {showConfetti && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white rounded-xl p-8 text-center">
            <div className="mb-4">
              <svg className="w-16 h-16 text-green-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              Setup Complete! 🎉
            </h3>
            <p className="text-gray-600 mb-4">
              Your behavioral intelligence dashboard is ready
            </p>
            <LoadingSpinner size="medium" color="indigo" />
          </div>
        </div>
      )}
    </div>
  );
};

// Welcome Step Component
const WelcomeStep: React.FC<{ user: any; role: string; challenge: string }> = ({ user, role, challenge }) => {
  const roleMessages: Record<string, string> = {
    manager: 'As a team manager, you\'ll get insights to improve team performance and communication.',
    hr: 'As an HR professional, you\'ll get organizational behavior insights and retention analytics.',
    lead: 'As a team lead, you\'ll get tools to build more cohesive and productive teams.',
    member: 'As a team member, you\'ll understand your work style and improve collaboration.',
    executive: 'As an executive, you\'ll get leadership intelligence and organizational insights.'
  };

  return (
    <div className="text-center">
      <div className="mb-6">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-indigo-100 rounded-full mb-4">
          <svg className="w-10 h-10 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
      </div>

      <h3 className="text-xl font-semibold text-gray-900 mb-4">
        Welcome, {user?.full_name || 'to PsychSync'}!
      </h3>

      <p className="text-lg text-gray-600 mb-6 max-w-2xl mx-auto">
        {roleMessages[role] || roleMessages.manager}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
        <div className="text-center p-4 bg-blue-50 rounded-lg">
          <div className="text-2xl mb-2">📊</div>
          <h4 className="font-semibold text-gray-900">Behavioral Insights</h4>
          <p className="text-sm text-gray-600 mt-1">Understand team dynamics</p>
        </div>
        <div className="text-center p-4 bg-green-50 rounded-lg">
          <div className="text-2xl mb-2">🚀</div>
          <h4 className="font-semibold text-gray-900">Performance Optimization</h4>
          <p className="text-sm text-gray-600 mt-1">Improve team productivity</p>
        </div>
        <div className="text-center p-4 bg-purple-50 rounded-lg">
          <div className="text-2xl mb-2">🎯</div>
          <h4 className="font-semibold text-gray-900">Targeted Actions</h4>
          <p className="text-sm text-gray-600 mt-1">Get specific recommendations</p>
        </div>
      </div>
    </div>
  );
};

// Team Setup Step Component
const TeamSetupStep: React.FC<{ onComplete: () => void; onSkip: () => void }> = ({ onComplete, onSkip }) => {
  const [teamName, setTeamName] = useState('');
  const [teamSize, setTeamSize] = useState('5-10');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateTeam = async () => {
    setIsCreating(true);
    // Simulate team creation
    setTimeout(() => {
      setIsCreating(false);
      onComplete();
    }, 1500);
  };

  return (
    <div>
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 mb-2">Create your first team</h4>
        <p className="text-gray-600">
          Start with a basic team setup. You can always edit details and add members later.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Team Name
          </label>
          <input
            type="text"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="e.g., Marketing Team, Engineering Squad"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Team Size
          </label>
          <select
            value={teamSize}
            onChange={(e) => setTeamSize(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="2-5">2-5 members</option>
            <option value="5-10">5-10 members</option>
            <option value="10-20">10-20 members</option>
            <option value="20+">20+ members</option>
          </select>
        </div>
      </div>

      <div className="mt-6 flex space-x-4">
        <Button
          onClick={handleCreateTeam}
          disabled={!teamName.trim() || isCreating}
          className="flex-1"
        >
          {isCreating ? (
            <>
              <LoadingSpinner size="small" color="white" className="mr-2" />
              Creating team...
            </>
          ) : (
            'Create Team'
          )}
        </Button>
        <Button variant="secondary" onClick={onSkip}>
          Skip for now
        </Button>
      </div>
    </div>
  );
};

// Quick Assessment Step Component
const QuickAssessmentStep: React.FC<{ role: string; onComplete: () => void; onSkip: () => void }> = ({ role, onComplete, onSkip }) => {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const questions = [
    {
      id: 1,
      text: "When working on a team project, I prefer to:",
      options: [
        "Take the lead and organize the work",
        "Focus on the details and make sure everything is perfect",
        "Come up with creative ideas and possibilities",
        "Make sure everyone feels included and heard"
      ]
    },
    {
      id: 2,
      text: "When facing a problem, I typically:",
      options: [
        "Analyze the facts and find the most logical solution",
        "Trust my intuition and go with what feels right",
        "Look for practical solutions that have worked before",
        "Consider how the solution will affect everyone involved"
      ]
    },
    {
      id: 3,
      text: "In meetings, I usually:",
      options: [
        "Speak up with my opinions and ideas",
        "Listen carefully and ask clarifying questions",
        "Focus on the agenda and keep things on track",
        "Help build consensus and find common ground"
      ]
    }
  ];

  const handleAnswer = (answer: string) => {
    const newAnswers = { ...answers, [currentQuestion]: answer };
    setAnswers(newAnswers);

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      setTimeout(() => {
        onComplete();
      }, 1000);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h4 className="font-semibold text-gray-900">
            Quick Personality Assessment
          </h4>
          <span className="text-sm text-gray-500">
            Question {currentQuestion + 1} of {questions.length}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
          />
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-6">
          {questions[currentQuestion].text}
        </h3>

        <div className="space-y-3">
          {questions[currentQuestion].options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswer(option)}
              className="w-full text-left p-4 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
            >
              <div className="flex items-center">
                <div className="w-6 h-6 rounded-full border-2 border-gray-300 mr-3 flex items-center justify-center">
                  {answers[currentQuestion] === option && (
                    <div className="w-3 h-3 rounded-full bg-indigo-500" />
                  )}
                </div>
                <span className="text-gray-700">{option}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-between">
        {currentQuestion > 0 && (
          <Button variant="secondary" onClick={() => setCurrentQuestion(currentQuestion - 1)}>
            Previous
          </Button>
        )}
        <Button variant="secondary" onClick={onSkip}>
          Skip assessment
        </Button>
      </div>
    </div>
  );
};

// First Insights Step Component
const FirstInsightsStep: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  const [isGenerating, setIsGenerating] = useState(true);

  useEffect(() => {
    // Simulate insight generation
    setTimeout(() => {
      setIsGenerating(false);
    }, 2000);
  }, []);

  if (isGenerating) {
    return (
      <div className="text-center py-8">
        <LoadingSpinner size="large" color="indigo" className="mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Analyzing your responses...
        </h3>
        <p className="text-gray-600">
          Generating your personalized behavioral insights
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Your Behavioral Profile is Ready!
        </h3>
        <p className="text-gray-600">
          Here's what we discovered about your team approach
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-blue-50 rounded-lg p-6">
          <h4 className="font-semibold text-blue-900 mb-2">Your Strengths</h4>
          <ul className="space-y-2 text-blue-800">
            <li className="flex items-start">
              <svg className="w-5 h-5 mr-2 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Strong analytical thinking
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 mr-2 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Natural team leadership
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 mr-2 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Goal-oriented approach
            </li>
          </ul>
        </div>

        <div className="bg-green-50 rounded-lg p-6">
          <h4 className="font-semibold text-green-900 mb-2">Team Impact</h4>
          <ul className="space-y-2 text-green-800">
            <li className="flex items-start">
              <svg className="w-5 h-5 mr-2 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Improves team productivity by 25%
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 mr-2 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Reduces team conflicts by 40%
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 mr-2 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Increases team satisfaction scores
            </li>
          </ul>
        </div>
      </div>

      <div className="text-center">
        <Button size="lg" onClick={onComplete}>
          View My Full Dashboard
        </Button>
        <p className="text-sm text-gray-500 mt-3">
          Continue exploring your team insights and recommendations
        </p>
      </div>
    </div>
  );
};

export default ProgressiveDashboard;
