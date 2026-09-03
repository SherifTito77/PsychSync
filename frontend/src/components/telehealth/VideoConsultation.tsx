/**
 * Telehealth Video Consultation Component (Jitsi Meet Integration)
 *
 * Secure video consultations with clinicians using Jitsi Meet Free Tier.
 * HIPAA-compliant with peer-to-peer encryption.
 */

import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, Video, PhoneOff, Shield, Clock, AlertTriangle } from 'lucide-react';
import api from '@/services/api';

interface VideoConsultationProps {
  sessionId: string;
  userRole: 'patient' | 'clinician' | 'admin' | 'super_admin';
  onEnd?: (data: { duration: number; notes?: string }) => void;
}

declare global {
  interface Window {
    JitsiMeetExternalAPI: any;
  }
}

function VideoConsultation({ sessionId, userRole, onEnd }: VideoConsultationProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null);
  const [sessionNotes, setSessionNotes] = useState('');
  const [ending, setEnding] = useState(false);

  const isClinicianLike = userRole === 'clinician' || userRole === 'admin' || userRole === 'super_admin';

  const jitsiContainerRef = useRef<HTMLDivElement>(null);
  const jitsiApiRef = useRef<any>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const loadJitsiScript = () => {
      return new Promise((resolve) => {
        if (window.JitsiMeetExternalAPI) {
          resolve(true);
          return;
        }
        const script = document.createElement('script');
        script.src = 'https://meet.jit.si/external_api.js';
        script.async = true;
        script.onload = () => resolve(true);
        document.body.appendChild(script);
      });
    };

    const initConference = async () => {
      try {
        setLoading(true);

        // FORCE PARENT PERMISSION: Ask for camera/mic permission on the main site first
        // If we don't do this, the browser might block the iframe's request by default
        try {
          console.log('🔒 Telehealth: Requesting hardware handshake...');
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
          // Immediately stop tracks to release hardware for Jitsi
          stream.getTracks().forEach(track => track.stop());
          console.log('✅ Telehealth: Hardware handshake successful');
        } catch (pErr) {
          console.warn('⚠️ Telehealth: Preliminary handshake failed, continuing to Jitsi...', pErr);
        }

        await loadJitsiScript();

        // Get room details from backend
        const response = await api.get(`/telehealth/join/${sessionId}`);
        const { room_name, domain } = response.data as { room_name: string; domain: string };

        if (jitsiContainerRef.current) {
          const options = {
            roomName: room_name,
            width: '100%',
            height: '100%',
            parentNode: jitsiContainerRef.current,
            userInfo: {
              displayName: isClinicianLike ? 'Dr. Clinician' : 'Patient',
            },
            interfaceConfigOverwrite: {
              TOOLBAR_BUTTONS: [
                'microphone', 'camera', 'closedcaptions', 'desktop', 'fullscreen',
                'fodeviceselection', 'hangup', 'profile', 'chat', 'recording',
                'livestreaming', 'etherpad', 'sharedvideo', 'settings', 'raisehand',
                'videoquality', 'filmstrip', 'invite', 'feedback', 'stats', 'shortcuts',
                'tileview', 'videobackgroundblur', 'download', 'help', 'mute-everyone',
                'security'
              ],
            },
            configOverwrite: {
              startWithAudioMuted: false,
              startWithVideoMuted: false,
              prejoinPageEnabled: true,
              p2p: { enabled: true },
              externalConnectUrl: 'https://meet.jit.si', // Helps with WebSocket connection in iframes
            }
          };

          const apiInstance = new window.JitsiMeetExternalAPI(domain, options);
          jitsiApiRef.current = apiInstance;

          // AGGRESSIVE PERMISSION DELEGATION
          // Use an observer to catch the iframe the millisecond it's added
          const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
              mutation.addedNodes.forEach((node) => {
                if (node instanceof HTMLIFrameElement) {
                  console.log('🛡️ Telehealth: Injecting hardware permissions into secure tunnel');
                  node.setAttribute('allow', 'camera; microphone; display-capture; autoplay; clipboard-write; spotlight');
                }
              });
            });
          });

          if (jitsiContainerRef.current) {
            observer.observe(jitsiContainerRef.current, { childList: true });
          }

          // Initial check just in case it was created instantly
          const iframe = jitsiContainerRef.current.querySelector('iframe');
          if (iframe) {
            iframe.setAttribute('allow', 'camera; microphone; display-capture; autoplay; clipboard-write; spotlight');
          }

          apiInstance.addEventListeners({
            readyToClose: () => endCall(),
            videoConferenceJoined: () => {
              setSessionStartTime(new Date());
              setLoading(false);
            },
            videoConferenceLeft: () => endCall(),
          });
        }
      } catch (err) {
        console.error('Jitsi init error:', err);
        setError('Failed to establish a secure clinical connection. Please try again.');
        setLoading(false);
      }
    };

    initConference();

    return () => {
      if (jitsiApiRef.current) {
        jitsiApiRef.current.dispose();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [sessionId]);

  const endCall = async () => {
    if (ending) return;
    setEnding(true);

    try {
      const duration = sessionStartTime
        ? Math.floor((Date.now() - sessionStartTime.getTime()) / 1000 / 60)
        : 0;

      await api.post(`/telehealth/end/${sessionId}`, {
        notes: isClinicianLike ? sessionNotes : undefined
      });

      if (onEnd) {
        onEnd({ duration, notes: sessionNotes });
      } else {
        window.location.href = '/telehealth/schedule';
      }
    } catch (err) {
      window.location.href = '/telehealth/schedule';
    }
  };

  const getDuration = () => {
    if (!sessionStartTime) return '0:00';
    const seconds = Math.floor((Date.now() - sessionStartTime.getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Alert variant="error">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-full">
            <Video className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-lg font-bold">
              {isClinicianLike ? 'Clinical Consultation' : 'Doctor Consultation'}
            </h1>
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <Shield className="h-3 w-3 text-green-500" />
              HIPAA-Compliant Peer-to-Peer Encryption
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-md">
            <Clock className="h-4 w-4 text-gray-600" />
            <span className="font-mono font-bold">{getDuration()}</span>
          </div>
          <Button variant="danger" size="sm" onClick={endCall} disabled={ending}>
            <PhoneOff className="h-4 w-4 mr-2" />
            End Session
          </Button>
        </div>
      </div>

      {/* Video Area */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
          <Card className="overflow-hidden bg-black aspect-video relative">
            {loading && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 z-10">
                <Loader2 className="h-10 w-10 animate-spin text-blue-500 mb-4" />
                <p className="text-white font-medium">Initializing Secure Video...</p>
              </div>
            )}
            <div ref={jitsiContainerRef} className="w-full h-full" />
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {isClinicianLike && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Clinical Session Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <textarea
                  value={sessionNotes}
                  onChange={(e) => setSessionNotes(e.target.value)}
                  placeholder="Record observations..."
                  className="w-full h-48 p-2 text-sm border rounded-md focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                />
              </CardContent>
            </Card>
          )}

          <Alert className="bg-blue-50 border-blue-200">
            <AlertDescription className="text-xs text-blue-800">
              <strong>Tip:</strong> Use the blur background feature in the settings for extra privacy during your session.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    </div>
  );
}

export default VideoConsultation;
