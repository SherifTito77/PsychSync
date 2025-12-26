import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface PCL5Question {
  id: number;
  text: string;
  cluster: 'B' | 'C' | 'D' | 'E';
}

const PCL5Assessment: React.FC = () => {
  const navigate = useNavigate();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState<Record<number, number>>({});

  const pcl5Questions: PCL5Question[] = [
    // Cluster B (Intrusion)
    { id: 1, text: "Repeated, disturbing, and unwanted memories of the stressful experience?", cluster: 'B' },
    { id: 2, text: "Repeated, disturbing dreams of the stressful experience?", cluster: 'B' },
    { id: 3, text: "Suddenly feeling or acting as if the stressful experience were actually happening again (as if you were reliving it)?", cluster: 'B' },
    { id: 4, text: "Feeling very upset when something reminded you of the stressful experience?", cluster: 'B' },
    { id: 5, text: "Having strong physical reactions when something reminded you of the stressful experience?", cluster: 'B' },
    // Cluster C (Avoidance)
    { id: 6, text: "Avoiding memories, thoughts, or feelings related to the stressful experience?", cluster: 'C' },
    { id: 7, text: "Avoiding external reminders of the stressful experience (e.g., people, places, conversations, activities, objects, or situations)?", cluster: 'C' },
    // Cluster D (Negative alterations in cognitions and mood)
    { id: 8, text: "Not being able to remember important parts of the stressful experience?", cluster: 'D' },
    { id: 9, text: "Having strong negative beliefs about yourself, other people, or the world (e.g., \"I am bad,\" \"No one can be trusted,\" \"The world is completely dangerous\")?", cluster: 'D' },
    { id: 10, text: "Blaming yourself or someone else for the stressful experience or what happened after it?", cluster: 'D' },
    { id: 11, text: "Having strong negative feelings such as fear, horror, anger, guilt, or shame?", cluster: 'D' },
    { id: 12, text: "Loss of interest in activities that you used to enjoy?", cluster: 'D' },
    { id: 13, text: "Feeling distant or cut off from other people?", cluster: 'D' },
    { id: 14, text: "Trouble experiencing positive feelings (e.g., happiness, love, joy, or satisfaction)?", cluster: 'D' },
    // Cluster E (Alterations in arousal and reactivity)
    { id: 15, text: "Irritable behavior, angry outbursts, or acting aggressively?", cluster: 'E' },
    { id: 16, text: "Taking too many risks or doing things that could cause you harm?", cluster: 'E' },
    { id: 17, text: "Being \"superalert\" or watchful or on guard?", cluster: 'E' },
    { id: 18, text: "Feeling jumpy or easily startled?", cluster: 'E' },
    { id: 19, text: "Having difficulty concentrating?", cluster: 'E' },
    { id: 20, text: "Trouble falling or staying asleep?", cluster: 'E' },
  ];

  const responseOptions = [
    { value: 0, text: "Not at all" },
    { value: 1, text: "A little bit" },
    { value: 2, text: "Moderately" },
    { value: 3, text: "Quite a bit" },
    { value: 4, text: "Extremely" },
  ];

  const getClusterColor = (cluster: string) => {
    const colors = {
      'B': 'bg-purple-100 text-purple-800',
      'C': 'bg-blue-100 text-blue-800',
      'D': 'bg-green-100 text-green-800',
      'E': 'bg-orange-100 text-orange-800'
    };
    return colors[cluster] || 'bg-gray-100 text-gray-800';
  };

  const getClusterName = (cluster: string) => {
    const names = {
      'B': 'Intrusion',
      'C': 'Avoidance',
      'D': 'Negative Cognitions',
      'E': 'Arousal'
    };
    return names[cluster] || '';
  };

  const handleResponse = (value: number) => {
    setResponses({ ...responses, [currentQuestion + 1]: value });

    if (currentQuestion < pcl5Questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Calculate scores and show results
      calculateAndShowResults();
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const getPCL5SeverityLevel = (totalScore: number): string => {
    if (totalScore <= 20) return 'Minimal';
    if (totalScore <= 40) return 'Mild';
    if (totalScore <= 60) return 'Moderate';
    if (totalScore <= 80) return 'Severe';
    return 'Severe'; // Very Severe maps to Severe for the ClinicalResults component
  };

  const calculateAndShowResults = () => {
    // Calculate cluster scores
    const clusterBScore = [1, 2, 3, 4, 5].reduce((sum, id) => sum + (responses[id] || 0), 0);
    const clusterCScore = [6, 7].reduce((sum, id) => sum + (responses[id] || 0), 0);
    const clusterDScore = [8, 9, 10, 11, 12, 13, 14].reduce((sum, id) => sum + (responses[id] || 0), 0);
    const clusterEScore = [15, 16, 17, 18, 19, 20].reduce((sum, id) => sum + (responses[id] || 0), 0);

    const totalScore = Object.values(responses).reduce((sum, val) => sum + val, 0);

    const results = {
      score: totalScore,
      severity_level: getPCL5SeverityLevel(totalScore),
      clusters: {
        B: clusterBScore,
        C: clusterCScore,
        D: clusterDScore,
        E: clusterEScore
      }
    };

    navigate('/clinical/assessment/pcl5/complete', { state: { assessmentType: 'pcl5', result: results } });
  };

  const question = pcl5Questions[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            PCL-5 Assessment
          </h1>
          <div className="flex items-center justify-between mb-4">
            <p className="text-lg text-gray-600">
              PTSD Symptom Assessment
            </p>
            <div className="text-sm text-gray-500">
              Question {currentQuestion + 1} of {pcl5Questions.length}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / pcl5Questions.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <span className={`${getClusterColor(question.cluster)} px-3 py-1 rounded-full text-sm mr-3`}>
                Cluster {question.cluster}: {getClusterName(question.cluster)}
              </span>
              Question {currentQuestion + 1}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg text-gray-800 mb-2 leading-relaxed">
              {question.text}
            </p>
            <p className="text-sm text-gray-500 mb-8 italic">
              In the past month, how much were you bothered by:
            </p>

            {/* Response Options */}
            <div className="space-y-3">
              {responseOptions.map((option) => (
                <Button
                  key={option.value}
                  variant="outline"
                  className="w-full text-left justify-start h-auto p-4 whitespace-normal"
                  onClick={() => handleResponse(option.value)}
                >
                  <div>
                    <span className="font-medium">{option.value}.</span> {option.text}
                  </div>
                </Button>
              ))}
            </div>

            {/* Navigation */}
            <div className="flex justify-between mt-8">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentQuestion === 0}
              >
                Previous
              </Button>
              <div className="text-sm text-gray-500">
                Please select the response that best describes how much you were bothered by each symptom in the past month.
              </div>
              <Button
                variant="outline"
                onClick={() => navigate('/clinical/assessments')}
              >
                Exit Assessment
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">🧠 About PCL-5</h3>
              <p className="text-sm text-gray-600">
                20-item questionnaire assessing PTSD symptoms across 4 clusters based on DSM-5 criteria.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">📊 Reliability</h3>
              <p className="text-sm text-gray-600">
                Excellent reliability (α = 0.94) for PTSD symptom assessment.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">⏱️ Time</h3>
              <p className="text-sm text-gray-600">
                Takes approximately 10-15 minutes to complete.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Emergency Alert */}
        <div className="mt-6 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                <strong>Important:</strong> This assessment is for screening purposes only. If you're experiencing severe symptoms or thoughts of harm, please contact emergency services or a crisis hotline immediately.
              </p>
              <div className="mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open('tel:988')}
                  className="text-red-700 border-red-300 hover:bg-red-100"
                >
                  Call 988 (Crisis Line)
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PCL5Assessment;