import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

// PSS-10 Questions (Perceived Stress Scale)
const PSS_QUESTIONS = [
  { id: 'pss_1', text: 'In the last month, how often have you been upset because of something that happened unexpectedly?' },
  { id: 'pss_2', text: 'In the last month, how often have you felt that you were unable to control the important things in your life?' },
  { id: 'pss_3', text: 'In the last month, how often have you felt nervous and "stressed"?' },
  { id: 'pss_4', text: 'In the last month, how often have you felt confident about your ability to handle your personal problems?' },
  { id: 'pss_5', text: 'In the last month, how often have you felt that things were going your way?' },
  { id: 'pss_6', text: 'In the last month, how often have you found that you could not cope with all the things that you had to do?' },
  { id: 'pss_7', text: 'In the last month, how often have you been able to control irritations in your life?' },
  { id: 'pss_8', text: 'In the last month, how often have you felt that you were on top of things?' },
  { id: 'pss_9', text: 'In the last month, how often have you been angered because of things that were outside of your control?' },
  { id: 'pss_10', text: 'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?' },
];

const OPTIONS = ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'];

const StressAssessmentTest: React.FC = () => {
  const navigate = useNavigate();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [showResults, setShowResults] = useState(false);

  const handleResponse = (option: string) => {
    setResponses(prev => ({ ...prev, [PSS_QUESTIONS[currentQuestion].id]: option }));

    if (currentQuestion < PSS_QUESTIONS.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    } else {
      setShowResults(true);
    }
  };

  const calculateScore = () => {
    // PSS-10 scoring: Reverse items 4, 5, 7, 8
    const reverseItems = ['pss_4', 'pss_5', 'pss_7', 'pss_8'];
    const optionScores = { 'Never': 0, 'Almost never': 1, 'Sometimes': 2, 'Fairly often': 3, 'Very often': 4 };

    let totalScore = 0;
    PSS_QUESTIONS.forEach(q => {
      const response = responses[q.id];
      if (response) {
        let score = optionScores[response as keyof typeof optionScores];
        if (reverseItems.includes(q.id)) {
          score = 4 - score; // Reverse scoring
        }
        totalScore += score;
      }
    });

    return totalScore;
  };

  const getSeverityLevel = (score: number) => {
    if (score <= 13) return {
      label: 'Low Stress',
      color: 'green',
      description: 'You appear to be managing stress well. You have effective coping strategies and feel in control of your life.',
      recommendations: [
        'Continue using your current stress management techniques',
        'Maintain your healthy work-life balance',
        'Keep up with regular exercise and social activities',
        'Practice preventive self-care to maintain your resilience'
      ],
      copingStrategies: [
        { title: 'Maintain Healthy Habits', description: 'Continue with regular exercise, adequate sleep, and balanced nutrition.' },
        { title: 'Social Connection', description: 'Stay connected with friends and family who provide support.' },
        { title: 'Mindfulness Practice', description: 'Consider meditation or yoga to maintain your current stress resilience.' },
        { title: 'Time Management', description: 'Keep organizing your tasks effectively to maintain control.' }
      ]
    };
    if (score <= 20) return {
      label: 'Moderate Stress',
      color: 'yellow',
      description: 'You experience some stress that may be affecting your daily life. Consider implementing additional coping strategies.',
      recommendations: [
        'Identify your main stress triggers and work to address them',
        'Practice relaxation techniques like deep breathing or progressive muscle relaxation',
        'Set realistic goals and prioritize tasks',
        'Consider talking to a counselor or therapist for additional support'
      ],
      copingStrategies: [
        { title: 'Deep Breathing', description: 'Practice 4-7-8 breathing: Inhale for 4, hold for 7, exhale for 8 seconds.' },
        { title: 'Progressive Muscle Relaxation', description: 'Tense and relax each muscle group from toes to head.' },
        { title: 'Time Management', description: 'Break large tasks into smaller, manageable steps.' },
        { title: 'Physical Activity', description: 'Even 10 minutes of walking can reduce stress hormones.' },
        { title: 'Journaling', description: 'Write down your thoughts and feelings to process stress.' }
      ]
    };
    return {
      label: 'High Stress',
      color: 'red',
      description: 'You are experiencing significant stress that may be impacting your health and daily functioning. Professional support is recommended.',
      recommendations: [
        'Consider speaking with a mental health professional',
        'Practice immediate stress reduction techniques daily',
        'Evaluate your workload and seek support in managing responsibilities',
        'Reach out to your support network - don\'t face this alone'
      ],
      copingStrategies: [
        { title: 'Immediate Relief', description: 'Try box breathing: 4 counts in, 4 hold, 4 out, 4 hold. Repeat 4 times.' },
        { title: 'Grounding Technique', description: 'Use 5-4-3-2-1 method: 5 things you see, 4 touch, 3 hear, 2 smell, 1 taste.' },
        { title: 'Professional Help', description: 'A therapist can provide personalized strategies and support.' },
        { title: 'Support Network', description: 'Connect with trusted friends, family, or support groups.' },
        { title: 'Self-Compassion', description: 'Be kind to yourself - high stress is not a personal failure.' },
        { title: 'Crisis Resources', description: 'If overwhelmed, contact crisis hotlines for immediate support.' }
      ]
    };
  };

  if (showResults) {
    const score = calculateScore();
    const severity = getSeverityLevel(score);

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-3xl">Perceived Stress Scale Results</CardTitle>
              <p className="text-gray-600 mt-2">Based on your responses to the PSS-10 assessment</p>
            </CardHeader>
            <CardContent>
              {/* Score Display */}
              <div className="text-center mb-8">
                <div className={`inline-block px-8 py-4 rounded-full text-white text-3xl font-bold mb-4 ${
                  severity.color === 'green' ? 'bg-green-600' :
                  severity.color === 'yellow' ? 'bg-yellow-600' : 'bg-red-600'
                }`}>
                  Score: {score} / 40
                </div>
                <p className={`text-2xl font-bold mt-4 ${
                  severity.color === 'green' ? 'text-green-700' :
                  severity.color === 'yellow' ? 'text-yellow-700' : 'text-red-700'
                }`}>
                  {severity.label}
                </p>
              </div>

              {/* What Your Score Means */}
              <div className="mb-8 p-6 bg-blue-50 rounded-lg border-l-4 border-blue-600">
                <h3 className="font-bold text-lg mb-3 flex items-center">
                  <span className="mr-2">💭</span> What Your Score Means
                </h3>
                <p className="text-gray-700 leading-relaxed">{severity.description}</p>
              </div>

              {/* Score Interpretation */}
              <div className="mb-8 p-6 bg-gray-50 rounded-lg">
                <h3 className="font-bold text-lg mb-3">Understanding PSS-10 Scores:</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className={`p-4 rounded-lg ${score <= 13 ? 'ring-2 ring-green-500' : 'opacity-60'}`}>
                    <div className="font-semibold text-green-700">0-13</div>
                    <div className="text-sm text-gray-600">Low Stress</div>
                  </div>
                  <div className={`p-4 rounded-lg ${score > 13 && score <= 20 ? 'ring-2 ring-yellow-500' : 'opacity-60'}`}>
                    <div className="font-semibold text-yellow-700">14-20</div>
                    <div className="text-sm text-gray-600">Moderate Stress</div>
                  </div>
                  <div className={`p-4 rounded-lg ${score > 20 ? 'ring-2 ring-red-500' : 'opacity-60'}`}>
                    <div className="font-semibold text-red-700">21-40</div>
                    <div className="text-sm text-gray-600">High Stress</div>
                  </div>
                </div>
              </div>

              {/* Personalized Recommendations */}
              <div className="mb-8 p-6 bg-indigo-50 rounded-lg border-l-4 border-indigo-600">
                <h3 className="font-bold text-lg mb-4 flex items-center">
                  <span className="mr-2">💡</span> Recommendations For You
                </h3>
                <ul className="space-y-3">
                  {severity.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-indigo-600 mr-3 mt-1">✓</span>
                      <span className="text-gray-700">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Coping Strategies */}
              <div className="mb-8 p-6 bg-green-50 rounded-lg border-l-4 border-green-600">
                <h3 className="font-bold text-lg mb-4 flex items-center">
                  <span className="mr-2">🛠️</span> Coping Strategies & Techniques
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {severity.copingStrategies.map((strategy, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg shadow-sm">
                      <h4 className="font-semibold text-gray-800 mb-2">{strategy.title}</h4>
                      <p className="text-sm text-gray-600">{strategy.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Important Note */}
              <div className="mb-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  <strong>Important:</strong> This assessment is a screening tool, not a diagnostic instrument.
                  If you're experiencing significant distress, please consider consulting with a mental health professional.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  onClick={() => {
                    setCurrentQuestion(0);
                    setResponses({});
                    setShowResults(false);
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  Retake Assessment
                </Button>
                <Button
                  onClick={() => navigate('/clinical-assessments')}
                  className="flex-1"
                >
                  More Assessments
                </Button>
                <Button
                  onClick={() => navigate('/')}
                  variant="ghost"
                  className="flex-1"
                >
                  Back to Home
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const progress = ((currentQuestion + 1) / PSS_QUESTIONS.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <Button onClick={() => navigate('/')} variant="ghost">
            ← Back
          </Button>
        </div>

        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentQuestion + 1} of {PSS_QUESTIONS.length}</span>
            <span>{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Perceived Stress Scale (PSS-10)</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg text-gray-900 mb-6">
              {PSS_QUESTIONS[currentQuestion].text}
            </p>

            <div className="space-y-3">
              {OPTIONS.map((option) => (
                <button
                  key={option}
                  onClick={() => handleResponse(option)}
                  className="w-full text-left p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {option}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> This is a clinical screening tool. Your responses are confidential.
          </p>
        </div>
      </div>
    </div>
  );
};

export default StressAssessmentTest;
