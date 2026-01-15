/**
 * Telehealth Video Consultation Component
 *
 * Secure video consultations with clinicians using Twilio Video
 * HIPAA-compliant with encrypted recordings
 *
 * Features:
 * - Video/audio controls
 * - Session timer
 * - Recording indicator
 * - Clinical notes (for clinicians)
 * - Emergency resources
 */

import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, Video, VideoOff, Mic, MicOff, PhoneOff, Shield, Clock, AlertTriangle } from 'lucide-react';
import api from '@/services/api';

interface VideoConsultationProps {
  sessionId: string;
  userRole: 'patient' | 'clinician';
  onEnd?: (data: { duration: number; notes?: string }) => void;
}

interface Participant {
  identity: string;
  videoEnabled: boolean;
  audioEnabled: boolean;
}

function VideoConsultation({ sessionId, userRole, onEnd }: VideoConsultationProps) {
  const [room, setRoom] = useState<any>(null);
  const [localVideoTrack, setLocalVideoTrack] = useState<any>(null);
  const [localAudioTrack, setLocalAudioTrack] = useState<any>(null);
  const [remoteParticipants, setRemoteParticipants] = useState<Map<string, any>>(new Map());
  const [connecting, setConnecting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionNotes, setSessionNotes] = useState('');
  const [showNotes, setShowNotes] = useState(userRole === 'clinician');
  const [ending, setEnding] = useState(false);

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Join video room
  useEffect(() => {
    initializeRoom();

    return () => {
      cleanup();
    };
  }, [sessionId]);

  // Session timer
  useEffect(() => {
    if (room && !sessionStartTime) {
      setSessionStartTime(new Date());
    }

    if (sessionStartTime && !timerRef.current) {
      timerRef.current = setInterval(() => {
        // Timer updates handled by getDuration()
      }, 1000);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [room, sessionStartTime]);

  const initializeRoom = async () => {
    try {
      setConnecting(true);
      setError(null);

      // Get access token from backend
      const response = await api.get(`/api/v1/telehealth/join/${sessionId}`);
      const { access_token, room_name, session_type, recording_enabled } = response.data;

      // Load Twilio Video dynamically
      const Video = require('twilio-video').default;

      // Connect to room
      const videoRoom = await Video.connect(access_token, {
        name: room_name,
        audio: true,
        video: { width: 640, height: 480, facingMode: 'user' },
        networkQuality: { local: 1, remote: 1 },
      });

      setRoom(videoRoom);
      setIsRecording(recording_enabled);
      setConnecting(false);

      // Handle local tracks
      const localParticipant = videoRoom.localParticipant;
      const localVideoPublication = Array.from(localParticipant.videoTracks.values())[0];
      const localAudioPublication = Array.from(localParticipant.audioTracks.values())[0];

      if (localVideoPublication) {
        setLocalVideoTrack(localVideoPublication.track);
        const videoTrack = localVideoPublication.track;
        if (videoTrack && localVideoRef.current) {
          videoTrack.attach(localVideoRef.current);
        }
      }

      if (localAudioPublication) {
        setLocalAudioTrack(localAudioPublication.track);
      }

      // Handle remote participants
      videoRoom.on('participantConnected', (participant: any) => {
        setRemoteParticipants((prev) => new Map(prev).set(participant.identity, participant));

        participant.on('trackSubscribed', (track: any) => {
          if (track.kind === 'video' && remoteVideoRef.current) {
            track.attach(remoteVideoRef.current);
          }
        });
      });

      // Check if anyone is already in the room
      videoRoom.participants.forEach((participant: any) => {
        setRemoteParticipants((prev) => new Map(prev).set(participant.identity, participant));

        participant.on('trackSubscribed', (track: any) => {
          if (track.kind === 'video' && remoteVideoRef.current) {
            track.attach(remoteVideoRef.current);
          }
        });

        // Subscribe to existing tracks
        participant.tracks.forEach((publication: any) => {
          if (publication.isSubscribed) {
            if (publication.track.kind === 'video' && remoteVideoRef.current) {
              publication.track.attach(remoteVideoRef.current);
            }
          }
        });
      });

      // Handle participant disconnection
      videoRoom.on('participantDisconnected', (participant: any) => {
        setRemoteParticipants((prev) => {
          const newMap = new Map(prev);
          newMap.delete(participant.identity);
          return newMap;
        });
      });

      // Handle disconnection
      videoRoom.on('disconnected', (room: any) => {
        setRoom(null);
        setLocalVideoTrack(null);
        setLocalAudioTrack(null);
        setRemoteParticipants(new Map());
      });

    } catch (err: any) {
      console.error('Failed to join video room:', err);
      setError(err.message || 'Failed to connect to video room. Please try again.');
      setConnecting(false);
    }
  };

  const toggleVideo = () => {
    if (localVideoTrack) {
      localVideoTrack.isEnabled = !localVideoTrack.isEnabled;
      setLocalVideoTrack({ ...localVideoTrack });
    }
  };

  const toggleAudio = () => {
    if (localAudioTrack) {
      localAudioTrack.isEnabled = !localAudioTrack.isEnabled;
      setLocalAudioTrack({ ...localAudioTrack });
    }
  };

  const endCall = async () => {
    if (!room || ending) return;

    setEnding(true);

    try {
      const duration = sessionStartTime
        ? Math.floor((Date.now() - sessionStartTime.getTime()) / 1000 / 60)
        : 0;

      // If clinician, save clinical notes
      if (userRole === 'clinician' && sessionNotes) {
        await api.post(`/api/v1/telehealth/end/${sessionId}`, {
          session_notes: sessionNotes,
          patient_satisfaction: null, // To be collected separately
        });
      } else {
        await api.post(`/api/v1/telehealth/end/${sessionId}`, {});
      }

      cleanup();

      if (onEnd) {
        onEnd({ duration, notes: sessionNotes });
      }
    } catch (err: any) {
      console.error('Failed to end session:', err);
      setError('Failed to end session properly. Please try again.');
      setEnding(false);
    }
  };

  const cleanup = () => {
    if (room) {
      room.disconnect();
      setRoom(null);
    }

    if (localVideoTrack && localVideoRef.current) {
      localVideoTrack.detach(localVideoRef.current);
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    setLocalVideoTrack(null);
    setLocalAudioTrack(null);
    setRemoteParticipants(new Map());
    setSessionStartTime(null);
  };

  const getDuration = () => {
    if (!sessionStartTime) return '0:00';
    const seconds = Math.floor((Date.now() - sessionStartTime.getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (connecting) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mb-4" />
            <h2 className="text-xl font-semibold mb-2">Connecting to Video Room...</h2>
            <p className="text-gray-600">Please wait while we establish a secure connection.</p>
            <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
              <Shield className="h-4 w-4" />
              <span>HIPAA-compliant encrypted connection</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong className="block mb-2">Connection Error</strong>
            {error}
            <div className="mt-4">
              <Button onClick={initializeRoom} variant="outline" size="sm">
                Try Again
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const remoteParticipantCount = remoteParticipants.size;
  const hasRemoteParticipant = remoteParticipantCount > 0;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Video className="h-6 w-6 text-blue-600" />
          <div>
            <h1 className="text-xl font-bold">
              {userRole === 'clinician' ? 'Consultation with Patient' : 'Consultation with Clinician'}
            </h1>
            <p className="text-sm text-gray-600 flex items-center gap-2">
              <Shield className="h-4 w-4" />
              HIPAA-compliant secure connection
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Session Timer */}
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg">
            <Clock className="h-4 w-4 text-gray-600" />
            <span className="font-mono text-lg">{getDuration()}</span>
          </div>

          {/* Recording Indicator */}
          {isRecording && (
            <Badge variant="destructive" className="animate-pulse">
              <span className="w-2 h-2 bg-white rounded-full mr-2" />
              Recording
            </Badge>
          )}

          {/* Participant Count */}
          <Badge variant={hasRemoteParticipant ? 'default' : 'secondary'}>
            {remoteParticipantCount + 1} / 2 participants
          </Badge>
        </div>
      </div>

      {/* Video Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Remote Video (Large) */}
        <Card className={`relative ${hasRemoteParticipant ? 'bg-black' : 'bg-gray-900'}`}>
          <CardContent className="p-0">
            <div className="aspect-video bg-gray-900 flex items-center justify-center">
              {hasRemoteParticipant ? (
                <video
                  ref={remoteVideoRef}
                  autoPlay
                  playsInline
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center text-white">
                  <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">Waiting for {userRole === 'clinician' ? 'patient' : 'clinician'}...</p>
                  <p className="text-sm opacity-75 mt-2">They will appear here when they join</p>
                </div>
              )}
            </div>

            {/* Remote participant label */}
            {hasRemoteParticipant && (
              <div className="absolute bottom-4 left-4 bg-black bg-opacity-70 text-white px-3 py-1 rounded">
                {userRole === 'clinician' ? 'Patient' : 'Clinician'}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Local Video (Small) */}
        <Card className="bg-black">
          <CardContent className="p-0">
            <div className="aspect-video bg-gray-900 flex items-center justify-center">
              <video
                ref={localVideoRef}
                autoPlay
                muted
                playsInline
                className="w-full h-full object-cover"
                style={{ transform: 'scaleX(-1)' }} // Mirror effect
              />
            </div>

            {/* Local participant label */}
            <div className="absolute bottom-4 left-4 bg-black bg-opacity-70 text-white px-3 py-1 rounded">
              You ({userRole})
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-center gap-4">
            {/* Toggle Video */}
            <Button
              onClick={toggleVideo}
              variant={localVideoTrack?.isEnabled ? 'default' : 'destructive'}
              size="lg"
              className="rounded-full w-14 h-14"
            >
              {localVideoTrack?.isEnabled ? (
                <Video className="h-6 w-6" />
              ) : (
                <VideoOff className="h-6 w-6" />
              )}
            </Button>

            {/* Toggle Audio */}
            <Button
              onClick={toggleAudio}
              variant={localAudioTrack?.isEnabled ? 'default' : 'destructive'}
              size="lg"
              className="rounded-full w-14 h-14"
            >
              {localAudioTrack?.isEnabled ? (
                <Mic className="h-6 w-6" />
              ) : (
                <MicOff className="h-6 w-6" />
              )}
            </Button>

            {/* End Call */}
            <Button
              onClick={endCall}
              disabled={ending}
              variant="destructive"
              size="lg"
              className="rounded-full w-14 h-14"
            >
              {ending ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : (
                <PhoneOff className="h-6 w-6" />
              )}
            </Button>
          </div>

          <p className="text-center text-sm text-gray-600 mt-3">
            {localAudioTrack?.isEnabled ? (
              <span className="text-green-600">● Microphone active</span>
            ) : (
              <span className="text-red-600">● Microphone muted</span>
            )}
            {' • '}
            {localVideoTrack?.isEnabled ? (
              <span className="text-green-600">Camera active</span>
            ) : (
              <span className="text-red-600">Camera off</span>
            )}
          </p>
        </CardContent>
      </Card>

      {/* Clinical Notes (Clinician Only) */}
      {userRole === 'clinician' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Clinical Notes</CardTitle>
            <CardDescription>
              Document the consultation for future reference
            </CardDescription>
          </CardHeader>
          <CardContent>
            <textarea
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
              placeholder="Enter session notes, observations, diagnosis codes, treatment plan..."
              className="w-full h-32 p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-600 mt-2">
              <Shield className="h-3 w-3 inline mr-1" />
              Notes are encrypted and stored securely (HIPAA-compliant)
            </p>
          </CardContent>
        </Card>
      )}

      {/* Emergency Resources */}
      <Alert className="border-red-500 bg-red-50">
        <AlertTriangle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-900">
          <strong>Emergency Protocol:</strong> If the patient expresses immediate harm intent,
          call 911 and stay on the line until emergency services arrive.
          <div className="mt-3 flex gap-3">
            <Button variant="destructive" size="sm" asChild>
              <a href="tel:911">Call 911</a>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <a href="tel:988">Call 988 Crisis Line</a>
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
export default VideoConsultation;
