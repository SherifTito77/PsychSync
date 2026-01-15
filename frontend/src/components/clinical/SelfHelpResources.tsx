import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Resource {
  title: string;
  category: string;
  description: string;
  techniques: string[];
  estimatedTime: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

const SelfHelpResources: React.FC = () => {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  const resources: Resource[] = [
    {
      title: 'Deep Breathing Exercises',
      category: 'Stress Management',
      description: 'Simple breathing techniques to calm your nervous system and reduce anxiety',
      techniques: [
        '4-7-8 Breathing: Inhale for 4, hold for 7, exhale for 8',
        'Box Breathing: Inhale, hold, exhale, hold - 4 seconds each',
        'Diaphragmatic Breathing: Deep belly breathing for relaxation',
      ],
      estimatedTime: '5-10 minutes',
      difficulty: 'beginner',
    },
    {
      title: 'Progressive Muscle Relaxation',
      category: 'Stress Management',
      description: 'Systematically tense and relax muscle groups to release physical tension',
      techniques: [
        'Lie comfortably in a quiet place',
        'Start with toes, work your way up to your head',
        'Tense each muscle group for 5 seconds, then relax for 10 seconds',
        'Focus on the difference between tension and relaxation',
      ],
      estimatedTime: '15-20 minutes',
      difficulty: 'beginner',
    },
    {
      title: 'Mindfulness Meditation',
      category: 'Mindfulness',
      description: 'Practice present-moment awareness to reduce stress and anxiety',
      techniques: [
        'Find a quiet, comfortable space',
        'Focus on your breath without trying to change it',
        'Notice thoughts without judgment',
        'Return your focus to your breath when your mind wanders',
        'Start with 5 minutes and gradually increase',
      ],
      estimatedTime: '5-20 minutes',
      difficulty: 'intermediate',
    },
    {
      title: 'Grounding Techniques',
      category: 'Crisis Management',
      description: 'Use your senses to stay present during overwhelming emotions',
      techniques: [
        '5-4-3-2-1 Method: Name 5 things you see, 4 things you can touch, 3 things you hear, 2 things you smell, 1 thing you taste',
        'Hold an ice cube in your hand',
        'Splash cold water on your face',
        'Focus on the feeling of your feet on the ground',
        'Name objects around you and describe them in detail',
      ],
      estimatedTime: '2-5 minutes',
      difficulty: 'beginner',
    },
    {
      title: 'Thought Recording',
      category: 'Cognitive Techniques',
      description: 'Challenge and reframe negative thought patterns',
      techniques: [
        'Write down the situation and automatic thoughts',
        'Identify cognitive distortions (all-or-nothing, catastrophizing, etc.)',
        'Challenge the evidence for and against your thoughts',
        'Develop a more balanced, realistic perspective',
        'Practice this regularly to build the skill',
      ],
      estimatedTime: '10-15 minutes',
      difficulty: 'intermediate',
    },
    {
      title: 'Sleep Hygiene',
      category: 'Lifestyle',
      description: 'Improve sleep quality for better mental health',
      techniques: [
        'Stick to a consistent sleep schedule',
        'Create a relaxing bedtime routine',
        'Avoid screens 1 hour before bed',
        'Keep your bedroom cool, dark, and quiet',
        'Avoid caffeine and alcohol close to bedtime',
        'Get natural sunlight exposure during the day',
      ],
      estimatedTime: 'Ongoing habit',
      difficulty: 'beginner',
    },
    {
      title: 'Physical Activity',
      category: 'Lifestyle',
      description: 'Use exercise to boost mood and reduce stress',
      techniques: [
        'Aim for 30 minutes of moderate activity most days',
        'Try walking, jogging, cycling, or swimming',
        'Include both cardio and strength training',
        'Practice yoga or stretching for flexibility',
        'Listen to your body and don\'t overexert',
        'Find activities you genuinely enjoy',
      ],
      estimatedTime: '30 minutes daily',
      difficulty: 'beginner',
    },
    {
      title: 'Journaling',
      category: 'Emotional Regulation',
      description: 'Express thoughts and feelings to process emotions',
      techniques: [
        'Write freely for 10-15 minutes without judgment',
        'Use prompts: "What am I grateful for today?"',
        'Track your mood and identify patterns',
        'Write letters you don\'t send to express difficult emotions',
        'Include both positive and negative experiences',
      ],
      estimatedTime: '10-20 minutes',
      difficulty: 'beginner',
    },
  ];

  const categories = Array.from(new Set(resources.map(r => r.category)));

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredResources = expandedCategory
    ? resources.filter(r => r.category === expandedCategory)
    : resources;

  const handlePracticeStart = (resource: Resource) => {
    // Log that user started practicing this technique
    fetch('/api/v1/clinical/self-help-practice', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        resource_title: resource.title,
        category: resource.category,
        started_at: new Date().toISOString(),
      }),
    }).catch(error => {
      console.error('Error logging practice:', error);
    });
  };

  return (
    <div className="space-y-6">
      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={!expandedCategory ? 'default' : 'outline'}
          size="sm"
          onClick={() => setExpandedCategory(null)}
        >
          All Resources ({resources.length})
        </Button>
        {categories.map(category => (
          <Button
            key={category}
            variant={expandedCategory === category ? 'default' : 'outline'}
            size="sm"
            onClick={() => setExpandedCategory(category)}
          >
            {category}
          </Button>
        ))}
      </div>

      {/* Resources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredResources.map((resource, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{resource.title}</CardTitle>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs font-medium rounded ${getDifficultyColor(resource.difficulty)}`}>
                    {resource.difficulty}
                  </span>
                  <span className="text-xs text-gray-500">
                    {resource.estimatedTime}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-500">{resource.category}</p>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 mb-4">{resource.description}</p>

              {/* Techniques */}
              <div className="mb-4">
                <h4 className="font-medium text-gray-900 mb-2">How to Practice:</h4>
                <ol className="space-y-1">
                  {resource.techniques.map((technique, techIndex) => (
                    <li key={techIndex} className="text-sm text-gray-600 flex items-start">
                      <span className="text-blue-500 mr-2 mt-0.5">{techIndex + 1}.</span>
                      <span>{technique}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Action Button */}
              <Button
                onClick={() => handlePracticeStart(resource)}
                className="w-full"
                size="sm"
              >
                Start Practice
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Important Note */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-6">
          <div className="flex items-start space-x-3">
            <svg className="h-6 w-6 text-blue-600 mt-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Self-Help Guidelines
              </h3>
              <div className="text-sm text-blue-800 space-y-2">
                <p>
                  <strong>Be consistent:</strong> Regular practice builds skills more effectively than occasional intense sessions.
                </p>
                <p>
                  <strong>Start small:</strong> Begin with shorter sessions and gradually increase duration as you become more comfortable.
                </p>
                <p>
                  <strong>Be patient:</strong> Some techniques take time to master. Don't get discouraged if it doesn't work immediately.
                </p>
                <p>
                  <strong>Combine approaches:</strong> Different techniques work for different situations. Build a toolkit of strategies.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Emergency Resources */}
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-red-900 mb-4">
              Need More Immediate Support?
            </h3>
            <p className="text-red-800 mb-6">
              If self-help techniques aren't enough, professional support is available 24/7.
            </p>
            <div className="flex justify-center space-x-4">
              <Button
                variant="destructive"
                onClick={() => window.open('tel:988')}
              >
                Call 988
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.href = '/clinical/emergency'}
                className="border-red-300 text-red-700 hover:bg-red-100"
              >
                Emergency Resources
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SelfHelpResources;