/**
 * PHQ-9 Educational Content Component
 *
 * Displays detailed educational information about PHQ-9 assessment results.
 * This includes information about depression, treatment options, and coping strategies.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { SeverityInfo } from '../../types';

interface PHQ9EducationProps {
  score: number;
  severity: SeverityInfo | undefined;
}

export const PHQ9Education: React.FC<PHQ9EducationProps> = ({ score, severity }) => {
  return (
    <Card className="mb-8 bg-indigo-50 border-indigo-200">
      <CardHeader>
        <CardTitle className="text-indigo-900">Understanding Your PHQ-9 Results</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4 text-gray-700">
          <div>
            <h4 className="font-semibold text-indigo-900 mb-2">What Your Score Means:</h4>
            <p className="text-sm leading-relaxed">
              The PHQ-9 (Patient Health Questionnaire-9) assesses depression symptoms based on DSM-5 criteria.
              It evaluates how often you've been bothered by problems like low mood, loss of interest, sleep issues,
              energy changes, appetite changes, self-worth, concentration, and thoughts of self-harm over the past two weeks.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-indigo-900 mb-2">About Depression Treatment:</h4>
            <p className="text-sm leading-relaxed">
              Depression is a highly treatable medical condition affecting brain chemistry and function.
              Evidence-based treatments include antidepressant medications, cognitive-behavioral therapy (CBT),
              interpersonal therapy, exercise, and lifestyle modifications. With proper treatment, 80-90% of people
              experience significant improvement.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-indigo-900 mb-2">Why Treating Depression Matters:</h4>
            <p className="text-sm leading-relaxed">
              Untreated depression can affect physical health, relationships, work performance, and overall quality of life.
              It increases risk for other medical conditions and can lead to serious complications. Early treatment
              prevents worsening symptoms and helps restore your ability to enjoy life and function effectively.
            </p>
          </div>

          {(score >= 20 || severity?.label?.includes('Severe')) && (
            <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
              <h4 className="font-semibold text-red-900 mb-2">For Severe Depression Symptoms:</h4>
              <p className="text-sm text-red-800 leading-relaxed">
                Your score indicates severe depression requiring immediate professional attention. Severe depression
                can impair daily functioning and carries significant health risks, including suicide risk.
                Please contact a mental health professional or crisis services immediately. Effective treatment
                can provide rapid relief and prevent serious complications.
              </p>
              <div className="mt-3 p-3 bg-yellow-50 rounded border border-yellow-200">
                <p className="text-sm text-yellow-800 font-medium">
                  <strong>Suicide Risk:</strong> If you have thoughts of self-harm, call 988 immediately.
                  Your life is valuable, and help is available 24/7.
                </p>
              </div>
            </div>
          )}

          <div>
            <h4 className="font-semibold text-indigo-900 mb-2">Immediate Coping Strategies:</h4>
            <ul className="text-sm space-y-1">
              <li>• Behavioral activation: Schedule pleasant activities even when you don't feel like it</li>
              <li>• Physical activity: Even 15 minutes of walking can improve mood within hours</li>
              <li>• Social connection: Contact friends or family, even briefly</li>
              <li>• Sleep hygiene: Consistent sleep schedule, limit screen time before bed</li>
              <li>• Nutrition: Regular meals with protein, fruits, and vegetables</li>
              <li>• Sunlight exposure: 15 minutes daily can help regulate mood</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-indigo-900 mb-2">Treatment Success Indicators:</h4>
            <ul className="text-sm space-y-1">
              <li>• Antidepressants typically show improvement in 4-6 weeks</li>
              <li>• CBT can be as effective as medication for mild-moderate depression</li>
              <li>• Combined treatment (medication + therapy) often works best</li>
              <li>• Exercise provides similar benefits to some medications for mild depression</li>
              <li>• 60-70% of people respond to first treatment attempt</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-indigo-900 mb-2">Support Someone with Depression:</h4>
            <ul className="text-sm space-y-1">
              <li>• Listen without judgment - avoid "just cheer up" comments</li>
              <li>• Offer specific help: "Can I drive you to your appointment?"</li>
              <li>• Encourage treatment while respecting their autonomy</li>
              <li>• Take threats of self-harm seriously - seek immediate help</li>
              <li>• Be patient - recovery takes time and has ups and downs</li>
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
