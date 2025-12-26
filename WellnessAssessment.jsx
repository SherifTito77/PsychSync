import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, SkipForward, Activity, Heart, Users, Brain, Sparkles } from 'lucide-react';

const WellnessAssessment = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [assessmentData, setAssessmentData] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Domain configurations
  const domains = [
    {
      id: 'physical',
      name: 'Physical Wellness',
      icon: Activity,
      color: '#10b981',
      description: 'Energy, sleep, movement, and nutrition'
    },
    {
      id: 'mental',
      name: 'Mental Wellness',
      icon: Brain,
      color: '#3b82f6',
      description: 'Stress, focus, and mental clarity'
    },
    {
      id: 'emotional',
      name: 'Emotional Wellness',
      icon: Heart,
      color: '#ef4444',
      description: 'Emotional awareness and regulation'
    },
    {
      id: 'social',
      name: 'Social Wellness',
      icon: Users,
      color: '#8b5cf6',
      description: 'Relationships and community connection'
    },
    {
      id: 'spiritual',
      name: 'Spiritual Wellness',
      icon: Sparkles,
      color: '#f59e0b',
      description: 'Purpose, meaning, and inner peace'
    }
  ];

  // Sample question data - in production, this would come from your API
  const sampleQuestions = {
    physical: [
      {
        id: 'phys_focus_area',
        type: 'multiple_choice',
        text: 'Which aspect of your physical wellness matters most to you right now?',
        description: 'This helps us personalize your recommendations',
        options: [
          {
            value: 'energy',
            text: '⚡ Energy & Vitality',
            subtext: 'Feeling energized throughout the day'
          },
          {
            value: 'sleep',
            text: '😴 Sleep Quality',
            subtext: 'Getting restful, sufficient sleep'
          },
          {
            value: 'exercise',
            text: '🏃 Physical Activity',
            subtext: 'Regular movement and exercise'
          },
          {
            value: 'nutrition',
            text: '🥗 Nutrition Habits',
            subtext: 'Balanced eating patterns'
          }
        ]
      },
      {
        id: 'sleep_quality',
        type: 'scale',
        text: 'How would you describe your typical sleep?',
        scale: {
          min: 1,
          max: 5,
          labels: {
            1: '💤 Consistently poor - difficulty falling/staying asleep',
            2: '😕 Often restless - wake up tired most days',
            3: '😐 Fair - some good nights, some bad nights',
            4: '🙂 Generally good - most nights are restful',
            5: '⭐ Excellent - consistently deep, restorative sleep'
          }
        }
      },
      {
        id: 'exercise_frequency',
        type: 'range',
        text: 'How many days per week do you get at least 30 minutes of moderate physical activity?',
        description: 'Moderate activity includes brisk walking, cycling, swimming, dancing, etc.',
        range: {
          min: 0,
          max: 7,
          labels: { 0: 'Never', 7: 'Daily' }
        }
      }
    ]
  };

  useEffect(() => {
    // Load assessment data
    setAssessmentData(sampleQuestions);
  }, []);

  const handleAnswer = (questionId, answer) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleNext = () => {
    if (currentQuestion < getTotalQuestions() - 1) {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentQuestion(prev => prev + 1);
        setIsTransitioning(false);
      }, 300);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentQuestion(prev => prev - 1);
        setIsTransitioning(false);
      }, 300);
    }
  };

  const handleSkip = () => {
    handleNext();
  };

  const getTotalQuestions = () => {
    if (!assessmentData?.physical) return 0;
    return assessmentData.physical.length;
  };

  const getCurrentQuestion = () => {
    if (!assessmentData?.physical) return null;
    return assessmentData.physical[currentQuestion];
  };

  const getProgress = () => {
    return ((currentQuestion + 1) / getTotalQuestions()) * 100;
  };

  const renderQuestion = (question) => {
    switch (question.type) {
      case 'multiple_choice':
        return <MultipleChoiceQuestion question={question} onAnswer={handleAnswer} />;
      case 'scale':
        return <ScaleQuestion question={question} onAnswer={handleAnswer} />;
      case 'range':
        return <RangeQuestion question={question} onAnswer={handleAnswer} />;
      default:
        return <div>Unknown question type</div>;
    }
  };

  if (!assessmentData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading wellness assessment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="h-6 w-6 text-green-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Physical Wellness Assessment</h1>
                <p className="text-sm text-gray-600">Understanding your health habits and lifestyle patterns</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Est. Time</div>
              <div className="font-medium">3-4 minutes</div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Question {currentQuestion + 1} of {getTotalQuestions()}
            </span>
            <span className="text-sm text-gray-500">{Math.round(getProgress())}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${getProgress()}%` }}
              transition={{ duration: 0.5, ease: "easeInOut" }}
            />
          </div>
        </div>
      </div>

      {/* Question Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentQuestion}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="bg-white rounded-2xl shadow-lg p-8"
          >
            {renderQuestion(getCurrentQuestion())}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <div className="max-w-4xl mx-auto px-4 pb-8">
        <div className="flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            className="flex items-center space-x-2 px-6 py-3 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Previous</span>
          </button>

          <button
            onClick={handleSkip}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            Skip for now
          </button>

          <button
            onClick={handleNext}
            className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <span>{currentQuestion === getTotalQuestions() - 1 ? 'Complete' : 'Next'}</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Multiple Choice Question Component
const MultipleChoiceQuestion = ({ question, onAnswer }) => {
  const [selectedOption, setSelectedOption] = useState(null);

  const handleSelect = (option) => {
    setSelectedOption(option.value);
    onAnswer(question.id, option.value);
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{question.text}</h2>
        {question.description && (
          <p className="text-gray-600">{question.description}</p>
        )}
      </div>

      <div className="grid gap-3">
        {question.options.map((option) => (
          <motion.div
            key={option.value}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <label
              className={`
                flex items-center p-4 rounded-xl border-2 cursor-pointer transition-all
                ${selectedOption === option.value
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <input
                type="radio"
                name={question.id}
                value={option.value}
                checked={selectedOption === option.value}
                onChange={() => handleSelect(option)}
                className="sr-only"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900">{option.text}</div>
                {option.subtext && (
                  <div className="text-sm text-gray-600 mt-1">{option.subtext}</div>
                )}
              </div>
              <div className={`
                w-5 h-5 rounded-full border-2 flex items-center justify-center
                ${selectedOption === option.value
                  ? 'border-green-500 bg-green-500'
                  : 'border-gray-300'
                }
              `}>
                {selectedOption === option.value && (
                  <div className="w-2 h-2 bg-white rounded-full" />
                )}
              </div>
            </label>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// Scale Question Component
const ScaleQuestion = ({ question, onAnswer }) => {
  const [selectedValue, setSelectedValue] = useState(null);

  const handleSelect = (value) => {
    setSelectedValue(value);
    onAnswer(question.id, value);
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{question.text}</h2>
      </div>

      <div className="space-y-3">
        {Object.entries(question.scale.labels).map(([value, label]) => (
          <motion.div
            key={value}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <label
              className={`
                flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all
                ${selectedValue === parseInt(value)
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <input
                type="radio"
                name={question.id}
                value={value}
                checked={selectedValue === parseInt(value)}
                onChange={() => handleSelect(parseInt(value))}
                className="sr-only mt-1"
              />
              <div className="flex-1 ml-3">
                <div className="text-gray-900">{label}</div>
              </div>
              <div className={`
                w-5 h-5 rounded-full border-2 flex items-center justify-center mt-1
                ${selectedValue === parseInt(value)
                  ? 'border-green-500 bg-green-500'
                  : 'border-gray-300'
                }
              `}>
                {selectedValue === parseInt(value) && (
                  <div className="w-2 h-2 bg-white rounded-full" />
                )}
              </div>
            </label>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// Range Question Component
const RangeQuestion = ({ question, onAnswer }) => {
  const [value, setValue] = useState(question.range.min || 0);

  const handleChange = (newValue) => {
    setValue(newValue);
    onAnswer(question.id, newValue);
  };

  const getLabel = (val) => {
    if (val === question.range.min) return question.range.labels[question.range.min];
    if (val === question.range.max) return question.range.labels[question.range.max];
    if (val === 0) return 'Never';
    if (val === 1) return '1 day/week';
    if (val >= 2 && val <= 4) return `${val} days/week`;
    if (val === 5) return '5-6 days/week';
    if (val === 7) return 'Daily';
    return `${val} days/week`;
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{question.text}</h2>
        {question.description && (
          <p className="text-gray-600">{question.description}</p>
        )}
      </div>

      <div className="space-y-6">
        <div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-3xl font-bold text-green-600">{value}</span>
            <span className="text-gray-700 font-medium">{getLabel(value)}</span>
          </div>

          <div className="relative">
            <input
              type="range"
              min={question.range.min}
              max={question.range.max}
              value={value}
              onChange={(e) => handleChange(parseInt(e.target.value))}
              className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, #10b981 0%, #10b981 ${((value - question.range.min) / (question.range.max - question.range.min)) * 100}%, #e5e7eb ${((value - question.range.min) / (question.range.max - question.range.min)) * 100}%, #e5e7eb 100%)`
              }}
            />
            <div className="flex justify-between mt-2">
              <span className="text-xs text-gray-500">{question.range.labels[question.range.min]}</span>
              <span className="text-xs text-gray-500">{question.range.labels[question.range.max]}</span>
            </div>
          </div>
        </div>

        {/* Visual indicators */}
        <div className="grid grid-cols-4 gap-2">
          {[0, 2, 4, 6].map((val) => (
            <button
              key={val}
              onClick={() => handleChange(val)}
              className={`
                p-3 rounded-lg border-2 transition-all
                ${value === val
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <div className="font-medium">{val}</div>
              <div className="text-xs">{getLabel(val)}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WellnessAssessment;