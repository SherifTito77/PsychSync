// src/components/onboarding/QuickSetupWizard.tsx - Quick setup wizard for new users
import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTeam } from '../../contexts/TeamContext';
import Icon from '../common/Icon';

interface WizardStep {
  id: string;
  title: string;
  description: string;
  icon: string;
  required: boolean;
}

interface SetupData {
  displayName: string;
  jobTitle: string;
  department: string;
  teamChoice: 'create' | 'join' | 'skip';
  teamName?: string;
  teamCode?: string;
  takeAssessment: boolean;
  notifications: boolean;
}

const QuickSetupWizard: React.FC = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const { createTeam } = useTeam();

  const [currentStep, setCurrentStep] = useState(0);
  const [setupData, setSetupData] = useState<SetupData>({
    displayName: user?.full_name || '',
    jobTitle: '',
    department: '',
    teamChoice: 'skip',
    takeAssessment: false,
    notifications: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const steps: WizardStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to PsychSync!',
      description: 'Let\'s get you set up in 2 minutes',
      icon: '🎉',
      required: true,
    },
    {
      id: 'profile',
      title: 'Tell us about yourself',
      description: 'Help us personalize your experience',
      icon: '👤',
      required: false,
    },
    {
      id: 'team',
      title: 'Join or create a team',
      description: 'Connect with your colleagues',
      icon: '👥',
      required: false,
    },
    {
      id: 'assessment',
      title: 'Quick personality check',
      description: 'Optional - discover your strengths',
      icon: '🧠',
      required: false,
    },
    {
      id: 'preferences',
      title: 'Your preferences',
      description: 'Set up notifications and more',
      icon: '⚙️',
      required: false,
    },
    {
      id: 'complete',
      title: 'You\'re all set!',
      description: 'Ready to explore PsychSync',
      icon: '🚀',
      required: true,
    },
  ];

  const currentStepData = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  const handleNext = useCallback(async () => {
    setError('');

    // Validation for specific steps
    if (currentStep === 1) { // Profile step
      if (!setupData.displayName.trim()) {
        setError('Please enter your name');
        return;
      }
    }

    if (currentStep === 2) { // Team step
      if (setupData.teamChoice === 'create' && !setupData.teamName?.trim()) {
        setError('Please enter a team name');
        return;
      }
      if (setupData.teamChoice === 'join' && !setupData.teamCode?.trim()) {
        setError('Please enter a team code');
        return;
      }

      // Handle team creation/joining
      if (setupData.teamChoice === 'create') {
        setIsLoading(true);
        try {
          await createTeam({
            name: setupData.teamName!,
            description: `Created by ${setupData.displayName}`,
          });
        } catch (err) {
          setError('Failed to create team. Please try again.');
          setIsLoading(false);
          return;
        }
        setIsLoading(false);
      }
    }

    // Move to next step
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete setup
      handleComplete();
    }
  }, [currentStep, setupData, createTeam]);

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setError('');
    }
  };

  const handleSkip = () => {
    setError('');
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      // Update user profile if data provided
      if (setupData.displayName !== user?.full_name || setupData.jobTitle) {
        // Call API to update user
        // await updateUser({ full_name: setupData.displayName, job_title: setupData.jobTitle });
      }

      // Mark setup wizard as completed
      localStorage.setItem('setupWizardCompleted', 'true');
      localStorage.setItem('setupWizardDate', new Date().toISOString());

      // Navigate to dashboard
      navigate('/dashboard');
    } catch (err) {
      setError('Failed to save your preferences');
      setIsLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0: return renderWelcomeStep();
      case 1: return renderProfileStep();
      case 2: return renderTeamStep();
      case 3: return renderAssessmentStep();
      case 4: return renderPreferencesStep();
      case 5: return renderCompleteStep();
      default: return renderWelcomeStep();
    }
  };

  const renderWelcomeStep = () => (
    <div className="text-center py-8">
      <div className="text-6xl mb-6 animate-bounce">🎉</div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">
        Welcome to PsychSync!
      </h2>
      <p className="text-lg text-gray-600 mb-8">
        We're excited to have you! Let's set up your account in just a few steps.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto mb-8">
        <div className="bg-indigo-50 rounded-lg p-4">
          <div className="text-3xl mb-2">⏱️</div>
          <h3 className="font-semibold text-gray-900 mb-1">Takes 2 minutes</h3>
          <p className="text-sm text-gray-600">Quick and easy setup</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4">
          <div className="text-3xl mb-2">✨</div>
          <h3 className="font-semibold text-gray-900 mb-1">Personalized</h3>
          <p className="text-sm text-gray-600">Tailored to your needs</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="text-3xl mb-2">🎯</div>
          <h3 className="font-semibold text-gray-900 mb-1">Get Started</h3>
          <p className="text-sm text-gray-600">Ready to explore</p>
        </div>
      </div>
    </div>
  );

  const renderProfileStep = () => (
    <div className="py-8">
      <h3 className="text-2xl font-semibold text-gray-900 mb-6">Tell us about yourself</h3>

      <div className="space-y-4 max-w-md mx-auto">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Display Name *
          </label>
          <input
            type="text"
            value={setupData.displayName}
            onChange={(e) => setSetupData({ ...setupData, displayName: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="How should we call you?"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Job Title
          </label>
          <input
            type="text"
            value={setupData.jobTitle}
            onChange={(e) => setSetupData({ ...setupData, jobTitle: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g., Product Manager, Developer"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Department
          </label>
          <select
            value={setupData.department}
            onChange={(e) => setSetupData({ ...setupData, department: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Select department...</option>
            <option value="engineering">Engineering</option>
            <option value="product">Product</option>
            <option value="design">Design</option>
            <option value="marketing">Marketing</option>
            <option value="sales">Sales</option>
            <option value="hr">Human Resources</option>
            <option value="operations">Operations</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderTeamStep = () => (
    <div className="py-8">
      <h3 className="text-2xl font-semibold text-gray-900 mb-2">Join or create a team</h3>
      <p className="text-gray-600 mb-6">Connect with your colleagues to unlock team features</p>

      <div className="space-y-4 max-w-lg mx-auto">
        <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors">
          <input
            type="radio"
            name="teamChoice"
            value="create"
            checked={setupData.teamChoice === 'create'}
            onChange={(e) => setSetupData({ ...setupData, teamChoice: e.target.value as any })}
            className="mr-3"
          />
          <div>
            <div className="font-semibold text-gray-900">Create a new team</div>
            <div className="text-sm text-gray-600">Start fresh with your own team</div>
          </div>
        </label>

        {setupData.teamChoice === 'create' && (
          <div className="ml-8 mt-4">
            <input
              type="text"
              value={setupData.teamName}
              onChange={(e) => setSetupData({ ...setupData, teamName: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter team name"
            />
          </div>
        )}

        <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors">
          <input
            type="radio"
            name="teamChoice"
            value="join"
            checked={setupData.teamChoice === 'join'}
            onChange={(e) => setSetupData({ ...setupData, teamChoice: e.target.value as any })}
            className="mr-3"
          />
          <div>
            <div className="font-semibold text-gray-900">Join existing team</div>
            <div className="text-sm text-gray-600">Enter a team code from your admin</div>
          </div>
        </label>

        {setupData.teamChoice === 'join' && (
          <div className="ml-8 mt-4">
            <input
              type="text"
              value={setupData.teamCode}
              onChange={(e) => setSetupData({ ...setupData, teamCode: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter team code"
            />
          </div>
        )}

        <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors">
          <input
            type="radio"
            name="teamChoice"
            value="skip"
            checked={setupData.teamChoice === 'skip'}
            onChange={(e) => setSetupData({ ...setupData, teamChoice: e.target.value as any })}
            className="mr-3"
          />
          <div>
            <div className="font-semibold text-gray-900">Skip for now</div>
            <div className="text-sm text-gray-600">You can join a team later</div>
          </div>
        </label>
      </div>
    </div>
  );

  const renderAssessmentStep = () => (
    <div className="py-8">
      <h3 className="text-2xl font-semibold text-gray-900 mb-2">Discover your personality</h3>
      <p className="text-gray-600 mb-6">Take a quick assessment to unlock personalized insights</p>

      <div className="space-y-4 max-w-md mx-auto">
        <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors">
          <input
            type="radio"
            name="takeAssessment"
            checked={setupData.takeAssessment}
            onChange={() => setSetupData({ ...setupData, takeAssessment: true })}
            className="mr-3"
          />
          <div>
            <div className="font-semibold text-gray-900">Yes, take me to the assessment</div>
            <div className="text-sm text-gray-600">Takes about 10 minutes</div>
          </div>
        </label>

        <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:border-indigo-500 transition-colors">
          <input
            type="radio"
            name="takeAssessment"
            checked={!setupData.takeAssessment}
            onChange={() => setSetupData({ ...setupData, takeAssessment: false })}
            className="mr-3"
          />
          <div>
            <div className="font-semibold text-gray-900">Maybe later</div>
            <div className="text-sm text-gray-600">Find it in the dashboard anytime</div>
          </div>
        </label>
      </div>
    </div>
  );

  const renderPreferencesStep = () => (
    <div className="py-8">
      <h3 className="text-2xl font-semibold text-gray-900 mb-6">Your preferences</h3>

      <div className="space-y-4 max-w-md mx-auto">
        <label className="flex items-center justify-between p-4 border rounded-lg">
          <div>
            <div className="font-semibold text-gray-900">Email Notifications</div>
            <div className="text-sm text-gray-600">Get updates about your activity</div>
          </div>
          <input
            type="checkbox"
            checked={setupData.notifications}
            onChange={(e) => setSetupData({ ...setupData, notifications: e.target.checked })}
            className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
          />
        </label>

        <div className="bg-indigo-50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Icon size="sm" className="text-indigo-600 mt-1">💡</Icon>
            <p className="text-sm text-indigo-800">
              You can always change these settings later from the Settings page
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderCompleteStep = () => (
    <div className="text-center py-8">
      <div className="text-6xl mb-6">🚀</div>
      <h2 className="text-3xl font-bold text-gray-900 mb-4">
        You're all set, {setupData.displayName.split(' ')[0]}!
      </h2>
      <p className="text-lg text-gray-600 mb-8">
        Here's what you can do now:
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto mb-8">
        <div className="bg-blue-50 rounded-lg p-4 text-left">
          <div className="text-2xl mb-2">📊</div>
          <h4 className="font-semibold text-gray-900">View Dashboard</h4>
          <p className="text-sm text-gray-600">See your overview and activity</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4 text-left">
          <div className="text-2xl mb-2">🧠</div>
          <h4 className="font-semibold text-gray-900">Take Assessment</h4>
          <p className="text-sm text-gray-600">Discover your personality type</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 text-left">
          <div className="text-2xl mb-2">👥</div>
          <h4 className="font-semibold text-gray-900">Manage Team</h4>
          <p className="text-sm text-gray-600">Create or join teams</p>
        </div>
        <div className="bg-orange-50 rounded-lg p-4 text-left">
          <div className="text-2xl mb-2">⚙️</div>
          <h4 className="font-semibold text-gray-900">Explore Features</h4>
          <p className="text-sm text-gray-600">See all PsychSync has to offer</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-3xl w-full">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Progress Bar */}
          <div className="h-2 bg-gray-200">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Header */}
          <div className="px-8 py-6 border-b border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-indigo-600">
                Step {currentStep + 1} of {steps.length}
              </span>
              <span className="text-sm text-gray-500">
                {Math.round(progress)}% complete
              </span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">{currentStepData.title}</h1>
            <p className="text-gray-600">{currentStepData.description}</p>
          </div>

          {/* Content */}
          <div className="px-8 py-6">
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            {renderStep()}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={handleBack}
                disabled={currentStep === 0 || isLoading}
                className="px-6 py-2 text-gray-700 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                ← Back
              </button>

              <div className="flex gap-3">
                {!currentStepData.required && (
                  <button
                    onClick={handleSkip}
                    disabled={isLoading}
                    className="px-6 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Skip →
                  </button>
                )}

                <button
                  onClick={handleNext}
                  disabled={isLoading}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mobile-touch-target"
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Saving...
                    </span>
                  ) : currentStep === steps.length - 1 ? (
                    'Go to Dashboard →'
                  ) : (
                    'Next →'
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Step Indicators */}
          <div className="px-8 pb-6">
            <div className="flex items-center justify-center gap-2">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`h-2 rounded-full transition-all duration-300 ${
                    index === currentStep
                      ? 'w-8 bg-indigo-600'
                      : index < currentStep
                      ? 'w-2 bg-indigo-600'
                      : 'w-2 bg-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickSetupWizard;
