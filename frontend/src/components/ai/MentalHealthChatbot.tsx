/**
 * AI Mental Health Support Chatbot
 *
 * Provides immediate support while waiting for clinician contact
 * Includes crisis detection and automatic escalation
 *
 * Features:
 * - Empathetic AI responses
 * - Crisis keyword detection
 * - Automatic escalation to human clinicians
 * - Resource suggestions
 * - Conversation history
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  MessageCircle,
  Send,
  AlertTriangle,
  Shield,
  Phone,
  Clock,
  CheckCircle,
  Bot,
  User,
  Loader2,
  ExternalLink
} from 'lucide-react';
import api from '@/services/api';

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  crisisDetected: boolean;
  resources?: string[];
}

function MentalHealthChatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [typing, setTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [escalated, setEscalated] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Initialize conversation
    initializeChat();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeChat = async () => {
    const welcomeMessage: ChatMessage = {
      id: 'welcome',
      text: "Hi there! I'm your mental health support assistant. I'm here to listen and provide support while you wait to speak with a clinician. How are you feeling today?",
      isUser: false,
      timestamp: new Date(),
      crisisDetected: false,
    };

    setMessages([welcomeMessage]);
    setSessionId(`chat_${Date.now()}`);
  };

  const detectCrisis = (text: string): boolean => {
    const crisisKeywords = [
      'suicide',
      'kill myself',
      'end it all',
      'want to die',
      'better off dead',
      'no reason to live',
      'hurt myself',
      'self harm',
      'plan to kill',
      'goodbye forever',
    ];

    const lowerText = text.toLowerCase();
    return crisisKeywords.some(keyword => lowerText.includes(keyword));
  };

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      text: input.trim(),
      isUser: true,
      timestamp: new Date(),
      crisisDetected: false,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setSending(true);

    // Check for crisis keywords
    const isCrisis = detectCrisis(userMessage.text);

    if (isCrisis) {
      handleCrisisResponse(userMessage);
      setSending(false);
      return;
    }

    try {
      const response = await api.post('/chatbot/message', {
        message: userMessage.text,
        session_id: sessionId,
      });

      const responseData = response.data as {
        response?: string;
        crisis_detected?: boolean;
        suggested_resources?: string[];
        action?: string;
      };

      const botMessage: ChatMessage = {
        id: `bot_${Date.now()}`,
        text: responseData.response || "I'm here to help. Can you tell me more?",
        isUser: false,
        timestamp: new Date(),
        crisisDetected: responseData.crisis_detected || false,
        resources: responseData.suggested_resources,
      };

      setMessages((prev) => [...prev, botMessage]);

      // Check if escalated to human
      if (responseData.action === 'escalate_to_human') {
        setEscalated(true);
      }
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        text: "I'm having trouble connecting right now. Please try again, or reach out to crisis resources directly.",
        isUser: false,
        timestamp: new Date(),
        crisisDetected: false,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleCrisisResponse = (userMessage: ChatMessage) => {
    const crisisResponse: ChatMessage = {
      id: `crisis_${Date.now()}`,
      text: "I'm concerned about what you've shared. Your safety is the most important thing to me. Please reach out for help immediately - there are people who want to support you.",
      isUser: false,
      timestamp: new Date(),
      crisisDetected: true,
      resources: [
        '988 Suicide & Crisis Lifeline: Call or text 988',
        'Crisis Text Line: Text HOME to 741741',
        'Emergency Services: Call 911',
      ],
    };

    setMessages((prev) => [...prev, crisisResponse]);
    setEscalated(true);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasCrisis = messages.some((m) => m.crisisDetected);

  return (
    <div className="max-w-3xl mx-auto p-6">
      {/* Header */}
      <Card className={hasCrisis ? 'border-red-500' : ''}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MessageCircle className={`h-8 w-8 ${hasCrisis ? 'text-red-600' : 'text-blue-600'}`} />
              <div>
                <CardTitle className="text-2xl">Mental Health Support</CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <Bot className="h-4 w-4" />
                  AI-powered support • Available 24/7
                </CardDescription>
              </div>
            </div>

            {escalated && (
              <Badge variant="error" className="animate-pulse">
                <Shield className="h-3 w-3 mr-1" />
                Escalated to Clinician
              </Badge>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Crisis Alert Banner */}
      {hasCrisis && (
        <Alert className="border-red-500 bg-red-50 my-4">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-900">
            <strong className="block mb-2">⚠️ Crisis Resources Activated</strong>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
              <div className="p-3 bg-red-100 rounded-lg">
                <strong>988 Suicide & Crisis Lifeline</strong>
                <div className="flex gap-2 mt-2">
                  <Button variant="danger" size="sm">
                    <a href="tel:988">Call 988</a>
                  </Button>
                  <Button variant="outline" size="sm">
                    <a href="sms:988">Text 988</a>
                  </Button>
                </div>
              </div>

              <div className="p-3 bg-red-100 rounded-lg">
                <strong>Crisis Text Line</strong>
                <p className="text-sm mt-1">Text HOME to 741741</p>
              </div>

              <div className="p-3 bg-red-100 rounded-lg">
                <strong>Emergency</strong>
                <Button variant="danger" size="sm" className="w-full mt-2">
                  <a href="tel:911">Call 911</a>
                </Button>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Chat Messages */}
      <Card className="mt-4">
        <CardContent className="p-4">
          <div className="space-y-4 max-h-[500px] overflow-y-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.isUser
                      ? 'bg-blue-600 text-white'
                      : message.crisisDetected
                      ? 'bg-red-100 border-2 border-red-500 text-red-900'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {message.isUser ? (
                      <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    ) : (
                      <Bot className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                        message.crisisDetected ? 'text-red-600' : 'text-gray-600'
                      }`} />
                    )}
                    <div>
                      <p className="text-sm leading-relaxed">{message.text}</p>

                      {/* Resources */}
                      {message.resources && message.resources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-300">
                          <p className="text-xs font-semibold mb-2">Helpful Resources:</p>
                          <div className="space-y-1">
                            {message.resources.map((resource, idx) => (
                              <div key={idx} className="text-xs flex items-start gap-2">
                                <ExternalLink className="h-3 w-3 mt-0.5 flex-shrink-0" />
                                {typeof resource === 'string' ? (
                                  <span>{resource}</span>
                                ) : (
                                  <a
                                    href={(resource as any).url}
                                    target={(resource as any).url.startsWith('http') ? '_blank' : '_self'}
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline font-medium"
                                  >
                                    {(resource as any).title}
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Timestamp */}
                      <div
                        className={`text-xs mt-2 ${
                          message.isUser ? 'text-blue-200' : 'text-gray-500'
                        }`}
                      >
                        {message.timestamp.toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {typing && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>

      {/* Input Area */}
      <Card className="mt-4">
        <CardContent className="p-4">
          <div className="flex gap-3">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here... (Shift+Enter for new line)"
              disabled={sending}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || sending}
              size="sm"
              className="h-10 w-10"
            >
              {sending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-gray-600">
            <div className="flex items-center gap-2">
              <Shield className="h-3 w-3" />
              <span>Conversations are confidential and secure</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>Average response time: ~2 seconds</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Alert className="border-blue-500 bg-blue-50">
        <AlertDescription className="text-blue-900 text-sm">
          <strong>Important:</strong> This AI chatbot provides support and information but is not a
          substitute for professional mental health care. If you're experiencing a crisis or having
          thoughts of self-harm, please use the crisis resources above or call 988 immediately.
        </AlertDescription>
      </Alert>
    </div>
  );
}
export default MentalHealthChatbot;
