/**
 * Phishing Awareness Banner Component
 *
 * Displays educational security warnings to users about common threats.
 * Designed to improve security awareness without being intrusive.
 *
 * Usage:
 * <PhishingAwarenessBanner variant="reset-password" />
 * <PhishingAwarenessBanner variant="login-warning" />
 *
 * Author: Security Team
 * Date: 2025-12-24
 */

import React, { useState, useEffect } from 'react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/common/Button';
import { X, Shield, AlertTriangle, Info, CheckCircle } from 'lucide-react';

type BannerVariant = 'reset-password' | 'login-warning' | 'suspicious-activity' | 'general-tip';

interface PhishingAwarenessBannerProps {
  variant?: BannerVariant;
  onDismiss?: () => void;
  className?: string;
}

interface SecurityTip {
  icon: React.ReactNode;
  title: string;
  message: string;
  tips: string[];
  severity: 'warning' | 'info' | 'success';
}

const SECURITY_TIPS: Record<BannerVariant, SecurityTip> = {
  'reset-password': {
    icon: <Shield className="h-5 w-5" />,
    title: '🔐 Password Reset Security',
    message: 'Protecting your account during password reset',
    severity: 'warning',
    tips: [
      '✅ We will NEVER ask for your current password',
      '✅ We will NEVER ask you to provide your verification code to anyone',
      '✅ Verify you are on psychsync.com (check the URL bar)',
      '✅ Check that the email is actually from PsychSync (view headers/details)',
      '⚠️ If you did not request this reset, ignore this email',
      '⚠️ Never share verification codes with support staff or anyone else',
    ],
  },
  'login-warning': {
    icon: <AlertTriangle className="h-5 w-5" />,
    title: '🛡️ Login Security Tips',
    message: 'Keep your account secure',
    severity: 'warning',
    tips: [
      '✅ Always check the URL before entering your password',
      '✅ Use a password manager to detect phishing sites',
      '✅ Enable two-factor authentication (2FA)',
      '⚠️ PsychSync will never ask for your password via email or phone',
      '⚠️ Be suspicious of urgent security warnings demanding immediate action',
      '⚠️ Verify the sender email address carefully (scammers often use similar addresses)',
    ],
  },
  'suspicious-activity': {
    icon: <AlertTriangle className="h-5 w-5" />,
    title: '⚠️ Suspicious Activity Detected',
    message: 'We detected some unusual activity on your account',
    severity: 'warning',
    tips: [
      '🔍 Recent login from a new device or location',
      '🔍 Multiple failed password attempts',
      '🔍 Password reset was initiated',
      '✅ If this was you, no action is needed',
      '⚠️ If this was NOT you, change your password immediately',
      '⚠️ Contact support if you notice any unauthorized activity',
    ],
  },
  'general-tip': {
    icon: <Info className="h-5 w-5" />,
    title: '💡 Security Awareness Tip',
    message: 'Stay safe online',
    severity: 'info',
    tips: [
      '✅ Use unique passwords for each account',
      '✅ Enable two-factor authentication everywhere',
      '✅ Keep your software and browser updated',
      '✅ Be cautious of emails creating urgency or fear',
      '✅ Verify links before clicking (hover to see real URL)',
      '✅ When in doubt, contact support through official channels',
    ],
  },
};

export const PhishingAwarenessBanner: React.FC<PhishingAwarenessBannerProps> = ({
  variant = 'general-tip',
  onDismiss,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const tip = SECURITY_TIPS[variant];

  // Auto-rotate through tips
  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      setSelectedIndex((prev) => (prev + 1) % tip.tips.length);
    }, 5000); // Change tip every 5 seconds

    return () => clearInterval(interval);
  }, [isVisible, tip.tips.length]);

  const handleDismiss = () => {
    setIsVisible(false);
    if (onDismiss) {
      onDismiss();
    }

    // Save dismissal to localStorage
    try {
      const dismissedBanners = JSON.parse(
        localStorage.getItem('dismissedSecurityBanners') || '{}'
      );
      dismissedBanners[variant] = Date.now();
      localStorage.setItem('dismissedSecurityBanners', JSON.stringify(dismissedBanners));
    } catch (e) {
      // Ignore localStorage errors
    }
  };

  // Check if this banner was recently dismissed
  useEffect(() => {
    try {
      const dismissedBanners = JSON.parse(
        localStorage.getItem('dismissedSecurityBanners') || '{}'
      );
      const dismissedTime = dismissedBanners[variant];

      // Show again if dismissed more than 7 days ago
      if (dismissedTime && Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        setIsVisible(false);
      }
    } catch (e) {
      // Show banner if localStorage fails
    }
  }, [variant]);

  if (!isVisible) return null;

  const alertVariant = {
    warning: 'default',
    info: 'default',
    success: 'default',
  }[tip.severity];

  return (
    <Alert
      variant={alertVariant as any}
      className={`relative border-l-4 ${
        tip.severity === 'warning' ? 'border-l-amber-500 bg-amber-50 dark:bg-amber-950' :
        tip.severity === 'info' ? 'border-l-blue-500 bg-blue-50 dark:bg-blue-950' :
        'border-l-green-500 bg-green-50 dark:bg-green-950'
      } ${className}`}
    >
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex items-start gap-3">
        <div className={`mt-0.5 ${
          tip.severity === 'warning' ? 'text-amber-600 dark:text-amber-400' :
          tip.severity === 'info' ? 'text-blue-600 dark:text-blue-400' :
          'text-green-600 dark:text-green-400'
        }`}>
          {tip.icon}
        </div>

        <div className="flex-1 space-y-2">
          <AlertTitle className="text-sm font-semibold">
            {tip.title}
          </AlertTitle>

          <AlertDescription className="text-sm text-gray-700 dark:text-gray-300">
            {tip.message}
          </AlertDescription>

          {/* Tips display */}
          <div className="mt-3 space-y-1.5">
            {tip.tips.map((tipText, index) => (
              <div
                key={index}
                className={`text-xs transition-all duration-300 ${
                  index === selectedIndex
                    ? 'text-gray-900 dark:text-gray-100 font-medium scale-[1.02]'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                {tipText}
              </div>
            ))}
          </div>

          {/* Learn more link */}
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="link"
              size="sm"
              className="h-auto p-0 text-xs"
              onClick={() => window.open('https://psychsync.com/security', '_blank')}
            >
              Learn more about account security →
            </Button>
          </div>
        </div>
      </div>
    </Alert>
  );
};

/**
 * Interactive Phishing Quiz Component
 *
 * Tests user's ability to identify phishing attempts
 */
export const PhishingQuiz: React.FC = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [answered, setAnswered] = useState(false);

  const questions = [
    {
      scenario: "You receive an email: 'URGENT: Your account will be deleted in 24 hours unless you verify your information. Click here to verify.'",
      options: [
        { text: "Click the link immediately to verify", correct: false },
        { text: "Check the sender email and verify through official channels", correct: true },
        { text: "Reply with your account information", correct: false },
        { text: "Forward to friends for advice", correct: false },
      ],
      explanation: "Urgency and threats are common phishing tactics. Always verify through official channels.",
    },
    {
      scenario: "You get a phone call: 'Hi, this is PsychSync support. We need your verification code to fix your account.'",
      options: [
        { text: "Provide the code to help them", correct: false },
        { text: "Hang up and contact support through the official website", correct: true },
        { text: "Ask for their employee ID", correct: false },
        { text: "Provide the code but ask for a callback number", correct: false },
      ],
      explanation: "Legitimate support will NEVER ask for your verification code. This is a social engineering attack.",
    },
    {
      scenario: "You receive a password reset email you didn't request. What should you do?",
      options: [
        { text: "Click the link to see what happens", correct: false },
        { text: "Ignore and delete the email", correct: true },
        { text: "Reply asking who sent it", correct: false },
        { text: "Click the link and change your password just in case", correct: false },
      ],
      explanation: "If you didn't request a reset, ignore it. Clicking links in suspicious emails can lead to phishing sites.",
    },
    {
      scenario: "The login page URL is: psychsync-secure-login.com instead of psychsync.com. Is this safe?",
      options: [
        { text: "Yes, it looks similar enough", correct: false },
        { text: "No, this is likely a phishing site", correct: true },
        { text: "Yes, if it has the lock icon", correct: false },
        { text: "Check with a friend first", correct: false },
      ],
      explanation: "Always verify the exact domain. Slight variations are common phishing techniques.",
    },
  ];

  const handleAnswer = (correct: boolean) => {
    if (answered) return;
    setAnswered(true);

    if (correct) {
      setScore(score + 1);
    }

    setTimeout(() => {
      if (currentQuestion < questions.length - 1) {
        setCurrentQuestion(currentQuestion + 1);
        setAnswered(false);
      } else {
        setShowResult(true);
      }
    }, 2000);
  };

  if (showResult) {
    const percentage = (score / questions.length) * 100;
    return (
      <Alert
        variant={
          percentage >= 75 ? 'default' : percentage >= 50 ? 'default' : 'destructive'
        }
        className={`border-l-4 ${
          percentage >= 75 ? 'border-l-green-500 bg-green-50 dark:bg-green-950' :
          percentage >= 50 ? 'border-l-amber-500 bg-amber-50 dark:bg-amber-950' :
          'border-l-red-500 bg-red-50 dark:bg-red-950'
        }`}
      >
        <CheckCircle className="h-5 w-5" />
        <AlertTitle>
          {percentage >= 75 ? '🎉 Great job!' : percentage >= 50 ? '📚 Good effort!' : '⚠️ Keep learning!'}
        </AlertTitle>
        <AlertDescription className="space-y-2">
          <p>
            You scored {score} out of {questions.length} ({percentage.toFixed(0)}%).
          </p>
          {percentage < 75 && (
            <p className="text-sm">
              Consider reviewing our security guidelines to learn more about protecting your account.
            </p>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setCurrentQuestion(0);
              setScore(0);
              setShowResult(false);
              setAnswered(false);
            }}
          >
            Try Again
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  const question = questions[currentQuestion];

  return (
    <Alert className="border-l-4 border-l-blue-500 bg-blue-50 dark:bg-blue-950">
      <Shield className="h-5 w-5 text-blue-600 dark:text-blue-400" />
      <AlertTitle>Security Quiz: Question {currentQuestion + 1}/{questions.length}</AlertTitle>
      <AlertDescription className="space-y-3">
        <p className="text-sm font-medium">{question.scenario}</p>

        <div className="grid grid-cols-1 gap-2">
          {question.options.map((option, index) => (
            <Button
              key={index}
              variant={answered ? (option.correct ? 'default' : 'outline') : 'outline'}
              size="sm"
              onClick={() => handleAnswer(option.correct)}
              disabled={answered}
              className={`justify-start text-left h-auto py-2 px-3 ${
                answered && option.correct ? 'bg-green-600 hover:bg-green-700' : ''
              }`}
            >
              <span className="flex-1">{option.text}</span>
              {answered && option.correct && <CheckCircle className="h-4 w-4 ml-2" />}
              {answered && !option.correct && <X className="h-4 w-4 ml-2" />}
            </Button>
          ))}
        </div>

        {answered && (
          <div className="text-xs p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
            <strong>Explanation:</strong> {question.explanation}
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
};

/**
 * Domain Verification Warning
 *
 * Shows a warning if the user is not on the official domain
 */
export const DomainVerificationWarning: React.FC = () => {
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    const currentDomain = window.location.hostname;
    const allowedDomains = [
      'psychsync.com',
      'app.psychsync.com',
      'localhost',
      '127.0.0.1',
    ];

    const isAllowedDomain = allowedDomains.some(domain =>
      currentDomain === domain || currentDomain.endsWith(`.${domain}`)
    );

    if (!isAllowedDomain) {
      setShowWarning(true);
    }
  }, []);

  if (!showWarning) return null;

  return (
    <Alert variant="destructive" className="border-l-4 border-l-red-500">
      <AlertTriangle className="h-5 w-5" />
      <AlertTitle>⚠️ Security Warning: Unrecognized Domain</AlertTitle>
      <AlertDescription className="space-y-2">
        <p>
          You may be on a fraudulent website. Always verify you are on{' '}
          <strong>psychsync.com</strong> before entering your credentials.
        </p>
        <div className="text-sm p-2 bg-white dark:bg-gray-800 rounded">
          <p><strong>Current domain:</strong> {window.location.hostname}</p>
          <p><strong>Expected domain:</strong> psychsync.com</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.location.href = 'https://psychsync.com'}
        >
          Go to Official Site
        </Button>
      </AlertDescription>
    </Alert>
  );
};

export default PhishingAwarenessBanner;
