/**
 * Telehealth Scheduler Component
 *
 * Schedule video consultations with clinicians
 * View upcoming sessions
 * Cancel/reschedule appointments
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Calendar, Clock, Video, CheckCircle, XCircle, Loader2, User } from 'lucide-react';
import api from '@/services/api';

interface TelehealthSession {
  id: string;
  session_type: string;
  scheduled_time: string;
  duration_minutes: number;
  status: string;
  recording_enabled: boolean;
  clinician_id?: string;
  user_id?: string;
}

function TelehealthScheduler() {
  const [upcomingSessions, setUpcomingSessions] = useState<TelehealthSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [scheduling, setScheduling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Scheduling form
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [sessionType, setSessionType] = useState('initial');
  const [duration, setDuration] = useState(60);
  const [recordingEnabled, setRecordingEnabled] = useState(false);

  useEffect(() => {
    loadUpcomingSessions();
  }, []);

  const loadUpcomingSessions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/telehealth/upcoming?role=patient');
      setUpcomingSessions(response.data.data || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load upcoming sessions');
    } finally {
      setLoading(false);
    }
  };

  const handleSchedule = async () => {
    if (!selectedDate || !selectedTime) {
      setError('Please select date and time for your consultation');
      return;
    }

    setScheduling(true);
    setError(null);
    setSuccess(null);

    try {
      const scheduledTime = new Date(`${selectedDate}T${selectedTime}`);

      // For demo, use a mock clinician ID
      const clinicianId = '00000000-0000-0000-0000-000000000001';

      const response = await api.post('/api/v1/telehealth/schedule', {
        clinician_id: clinicianId,
        scheduled_time: scheduledTime.toISOString(),
        session_type: sessionType,
        duration_minutes: duration,
        recording_enabled: recordingEnabled,
      });

      setSuccess('Consultation scheduled successfully! You will receive a reminder before the session.');
      await loadUpcomingSessions();

      // Reset form
      setSelectedDate('');
      setSelectedTime('');
      setSessionType('initial');
      setDuration(60);
      setRecordingEnabled(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to schedule consultation');
    } finally {
      setScheduling(false);
    }
  };

  const handleCancel = async (sessionId: string) => {
    if (!confirm('Are you sure you want to cancel this consultation?')) return;

    try {
      await api.post(`/api/v1/telehealth/cancel/${sessionId}`, {
        cancellation_reason: 'Cancelled by patient',
      });

      setSuccess('Consultation cancelled successfully');
      await loadUpcomingSessions();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel consultation');
    }
  };

  const handleJoin = (session: TelehealthSession) => {
    // Navigate to video consultation
    window.location.href = `/telehealth/session/${session.id}`;
  };

  const getSessionTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      initial: 'Initial Consultation',
      follow_up: 'Follow-up',
      crisis: 'Crisis Intervention',
      group: 'Group Therapy',
    };
    return labels[type] || type;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Video className="h-8 w-8 text-blue-600" />
            <div>
              <CardTitle className="text-2xl">Telehealth Consultations</CardTitle>
              <CardDescription>
                Schedule and manage video consultations with licensed clinicians
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Success Message */}
      {success && (
        <Alert className="border-green-500 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-900">{success}</AlertDescription>
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Schedule New Session */}
      <Card>
        <CardHeader>
          <CardTitle>Schedule a Consultation</CardTitle>
          <CardDescription>
            Choose a convenient time for your video consultation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Date Selection */}
            <div className="space-y-2">
              <Label htmlFor="date">Date</Label>
              <Input
                id="date"
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
              />
            </div>

            {/* Time Selection */}
            <div className="space-y-2">
              <Label htmlFor="time">Time</Label>
              <Input
                id="time"
                type="time"
                value={selectedTime}
                onChange={(e) => setSelectedTime(e.target.value)}
              />
            </div>
          </div>

          {/* Session Type */}
          <div className="space-y-2">
            <Label>Session Type</Label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { value: 'initial', label: 'Initial Consultation' },
                { value: 'follow_up', label: 'Follow-up' },
                { value: 'crisis', label: 'Crisis Intervention' },
                { value: 'group', label: 'Group Therapy' },
              ].map((type) => (
                <button
                  key={type.value}
                  onClick={() => setSessionType(type.value)}
                  className={`p-3 border rounded-lg text-left transition-all ${
                    sessionType === type.value
                      ? 'border-blue-500 bg-blue-50 text-blue-900'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="font-medium">{type.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div className="space-y-2">
            <Label>Duration</Label>
            <div className="flex gap-3">
              {[30, 45, 60, 90].map((mins) => (
                <button
                  key={mins}
                  onClick={() => setDuration(mins)}
                  className={`px-4 py-2 border rounded-lg transition-all ${
                    duration === mins
                      ? 'border-blue-500 bg-blue-500 text-white'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  {mins} min
                </button>
              ))}
            </div>
          </div>

          {/* Recording Consent */}
          <div className="flex items-start space-x-3 p-4 border rounded-lg">
            <input
              type="checkbox"
              id="recording"
              checked={recordingEnabled}
              onChange={(e) => setRecordingEnabled(e.target.checked)}
              className="mt-1"
            />
            <div className="flex-1">
              <Label htmlFor="recording" className="font-semibold cursor-pointer">
                Enable Session Recording
              </Label>
              <p className="text-sm text-gray-600 mt-1">
                Record the consultation for clinical documentation. Recordings are encrypted and stored securely.
                You can withdraw consent at any time.
              </p>
            </div>
          </div>

          {/* Schedule Button */}
          <Button
            onClick={handleSchedule}
            disabled={scheduling || !selectedDate || !selectedTime}
            size="lg"
            className="w-full"
          >
            {scheduling ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Scheduling...
              </>
            ) : (
              <>
                <Calendar className="h-4 w-4 mr-2" />
                Schedule Consultation
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Upcoming Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Consultations</CardTitle>
          <CardDescription>
            Your scheduled video consultations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : upcomingSessions.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">No upcoming consultations</p>
              <p className="text-sm">Schedule your first consultation using the form above</p>
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingSessions.map((session) => (
                <div key={session.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <Badge variant="outline">
                          {getSessionTypeLabel(session.session_type)}
                        </Badge>
                        <Badge variant={session.recording_enabled ? 'default' : 'secondary'}>
                          {session.recording_enabled ? 'Recording' : 'Not Recording'}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-gray-600" />
                          <span className="text-sm">{formatDate(session.scheduled_time)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-gray-600" />
                          <span className="text-sm">{formatTime(session.scheduled_time)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-600" />
                          <span className="text-sm">{session.duration_minutes} minutes</span>
                        </div>
                      </div>

                      <div className="text-sm text-gray-600">
                        Status: <span className="font-medium capitalize">{session.status}</span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        onClick={() => handleJoin(session)}
                        size="sm"
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Video className="h-4 w-4 mr-2" />
                        Join
                      </Button>
                      <Button
                        onClick={() => handleCancel(session.id)}
                        variant="outline"
                        size="sm"
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Information Card */}
      <Alert className="border-blue-500 bg-blue-50">
        <AlertDescription className="text-blue-900">
          <strong className="block mb-2">What to Expect:</strong>
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>Join the session 5 minutes early to test your camera and microphone</li>
            <li>Use a stable internet connection for best video quality</li>
            <li>Find a quiet, private space for your consultation</li>
            <li>Sessions are encrypted and HIPAA-compliant</li>
            <li>You can cancel or reschedule up to 24 hours before the appointment</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
}
export default TelehealthScheduler;
