/**
 * Crisis Resources Component
 *
 * Displays immediate crisis support resources
 * Should be shown when risk indicators are detected
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Phone, MessageCircle, AlertTriangle } from 'lucide-react';

interface CrisisResource {
  name: string;
  contact: string;
  available: string;
  description: string;
}

const CRISIS_RESOURCES: CrisisResource[] = [
  {
    name: '988 Suicide & Crisis Lifeline',
    contact: 'Call or Text 988',
    available: '24/7',
    description: 'Free, confidential support for people in distress',
  },
  {
    name: 'Crisis Text Line',
    contact: 'Text "HOME" to 741741',
    available: '24/7',
    description: 'Text with a trained Crisis Counselor',
  },
  {
    name: 'Emergency Services',
    contact: 'Call 911',
    available: '24/7',
    description: 'For immediate medical emergencies',
  },
];

interface CrisisResourcesProps {
  severity?: 'low' | 'moderate' | 'high' | 'critical';
  showMessage?: boolean;
}

export function CrisisResources({ severity = 'moderate', showMessage = true }: CrisisResourcesProps) {
  const isCritical = severity === 'critical' || severity === 'high';

  return (
    <Card className="border-destructive">
      <CardHeader className="bg-destructive/10">
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="h-5 w-5" />
          Crisis Resources
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        {/* Critical warning */}
        {isCritical && (
          <Alert variant="destructive">
            <AlertDescription>
              <div className="space-y-2">
                <div className="font-semibold text-lg">
                  🚨 You Deserve Support Right Now
                </div>
                <p className="text-sm">
                  If you are in immediate danger, please call emergency services
                  or go to the nearest emergency room. You are not alone, and help
                  is available 24/7.
                </p>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Message */}
        {showMessage && (
          <div className="text-sm">
            <p className="font-medium mb-2">
              These resources are available 24/7, free, and confidential:
            </p>
          </div>
        )}

        {/* Resource list */}
        <div className="space-y-3">
          {CRISIS_RESOURCES.map((resource, idx) => (
            <Alert key={idx} variant={idx === 2 ? 'destructive' : 'default'}>
              <AlertDescription>
                <div className="flex items-start gap-3">
                  <div className="mt-1">
                    {idx === 2 ? (
                      <Phone className="h-5 w-5" />
                    ) : (
                      <MessageCircle className="h-5 w-5" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold">{resource.name}</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {resource.description}
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold">
                        {resource.contact}
                      </span>
                      <span className="text-xs bg-secondary px-2 py-1 rounded">
                        {resource.available}
                      </span>
                    </div>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          ))}
        </div>

        {/* International resources */}
        <div className="border-t pt-4">
          <p className="text-sm font-medium mb-2">Outside the United States?</p>
          <a
            href="https://findahelpline.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary hover:underline"
          >
            Find a helpline near you →
          </a>
        </div>

        {/* Safety tips */}
        {isCritical && (
          <div className="bg-muted p-4 rounded-lg space-y-2">
            <div className="font-semibold text-sm">While You Wait for Help:</div>
            <ul className="text-xs space-y-1">
              <li>• Stay in a safe, public place if possible</li>
              <li>• Contact a trusted friend or family member</li>
              <li>• Remove access to any means of harm</li>
              <li>• Remember: this feeling is temporary</li>
            </ul>
          </div>
        )}

        {/* Additional resources */}
        <div className="border-t pt-4 space-y-2 text-xs text-muted-foreground">
          <p>
            <strong>Additional Resources:</strong>
          </p>
          <ul className="space-y-1">
            <li>• National Alliance on Mental Illness (NAMI): 1-800-950-NAMI</li>
            <li>• Substance Abuse and Mental Health Services Administration (SAMHSA): 1-800-662-4357</li>
            <li>• Veterans Crisis Line: Call 988, then press 1</li>
            <li>• Trevor Project (LGBTQ+): 1-866-488-7386</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

// Default export for React.lazy()
export default CrisisResources;

/**
 * Quick Crisis Banner
 * Lightweight version for displaying in modals or drawers
 */
export function CrisisBanner({ message }: { message?: string }) {
  return (
    <Alert variant="destructive" className="border-2 border-destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1">
            <div className="font-semibold mb-1">Help is Available</div>
            <p className="text-sm">
              {message || 'If you need support, please reach out:'}
            </p>
            <div className="mt-2 flex flex-wrap gap-4 text-sm font-mono">
              <span>📞 988</span>
              <span>💬 Text HOME to 741741</span>
              <span>🚨 911 (Emergency)</span>
            </div>
          </div>
        </div>
      </AlertDescription>
    </Alert>
  );
}

/**
 * Safety Plan Component
 * Helps users create a personal safety plan
 */
export function SafetyPlan() {
  const handlePrint = () => {
    window.print();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Safety Plan</CardTitle>
        <div className="text-sm text-muted-foreground">
          Having a plan in place can help during difficult moments
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <AlertDescription className="text-sm">
            <strong>Complete this plan with a trusted person or mental health professional.</strong>
            Keep it somewhere easily accessible.
          </AlertDescription>
        </Alert>

        <div className="space-y-6">
          {/* Warning signs */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                1
              </span>
              Warning Signs
            </h3>
            <p className="text-sm text-muted-foreground mb-2">
              What thoughts, feelings, or behaviors might indicate a crisis is developing?
            </p>
            <textarea
              className="w-full p-3 border rounded-md text-sm"
              rows={3}
              placeholder="e.g., Feeling hopeless, withdrawing from friends, changes in sleep..."
            />
          </div>

          {/* Coping strategies */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                2
              </span>
              Coping Strategies
            </h3>
            <p className="text-sm text-muted-foreground mb-2">
              What can I do by myself to help myself stay safe?
            </p>
            <textarea
              className="w-full p-3 border rounded-md text-sm"
              rows={3}
              placeholder="e.g., Call a friend, go for a walk, listen to music, practice deep breathing..."
            />
          </div>

          {/* Distractions */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                3
              </span>
              Distractions
            </h3>
            <p className="text-sm text-muted-foreground mb-2">
              What activities can I do to take my mind off things?
            </p>
            <textarea
              className="w-full p-3 border rounded-md text-sm"
              rows={3}
              placeholder="e.g., Watch a movie, exercise, read, cook..."
            />
          </div>

          {/* Support people */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                4
              </span>
              People I Can Contact
            </h3>
            <p className="text-sm text-muted-foreground mb-2">
              Who can I call for support?
            </p>
            <div className="space-y-2">
              <input
                type="text"
                className="w-full p-3 border rounded-md text-sm"
                placeholder="Name 1 - Phone number"
              />
              <input
                type="text"
                className="w-full p-3 border rounded-md text-sm"
                placeholder="Name 2 - Phone number"
              />
              <input
                type="text"
                className="w-full p-3 border rounded-md text-sm"
                placeholder="Name 3 - Phone number"
              />
            </div>
          </div>

          {/* Professionals */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                5
              </span>
              Professionals
            </h3>
            <p className="text-sm text-muted-foreground mb-2">
              Mental health professionals or services I can contact
            </p>
            <div className="space-y-2">
              <input
                type="text"
                className="w-full p-3 border rounded-md text-sm"
                placeholder="Therapist name - Phone number"
              />
              <input
                type="text"
                className="w-full p-3 border rounded-md text-sm"
                placeholder="Clinic/Counseling service - Phone number"
              />
            </div>
          </div>

          {/* Make environment safe */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                6
              </span>
              Making My Environment Safe
            </h3>
            <p className="text-sm text-muted-foreground mb-2">
              What can I do to make my environment safe?
            </p>
            <textarea
              className="w-full p-3 border rounded-md text-sm"
              rows={3}
              placeholder="e.g., Remove medications from easy access, give car keys to trusted person..."
            />
          </div>

          {/* Reasons for living */}
          <div>
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                7
              </span>
              My Reasons for Living
            </h3>
            <p className="text-sm text-muted-foreground mb-2">
              What gives my life meaning or purpose?
            </p>
            <textarea
              className="w-full p-3 border rounded-md text-sm"
              rows={3}
              placeholder="e.g., My family, my pets, my goals, my faith..."
            />
          </div>
        </div>

        <div className="flex gap-2">
          <Button onClick={handlePrint} variant="outline">
            Print Safety Plan
          </Button>
          <Button variant="default">
            Save Plan
          </Button>
        </div>

        <Alert>
          <AlertDescription className="text-xs">
            This safety plan is NOT a substitute for professional help.
            If you are in crisis, please call 988 or 911 immediately.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}
