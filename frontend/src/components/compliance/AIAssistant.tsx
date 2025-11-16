import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  Send,
  User,
  Sparkles,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Clock,
  ChevronDown,
  Mic,
  MicOff,
  Search
} from 'lucide-react';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import { useNotification } from '../../contexts/NotificationContext';
interface AIAssistantProps {
  className?: string;
}
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type?: 'text' | 'recommendation' | 'warning' | 'check';
}
const AIAssistant: React.FC<AIAssistantProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your AI compliance assistant. I can help you understand regulations, assess compliance gaps, and provide recommendations for improving your organization's compliance posture. What would you like to know?",
      timestamp: new Date().toISOString(),
      type: 'text'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([
    'What are the most common compliance gaps for tech companies?',
    'How do I improve our training completion rates?',
    'What GDPR requirements apply to our business?',
    'How can we reduce workplace safety incidents?',
    'What is the best way to handle anonymous feedback?',
    'Help me understand employee privacy rights'
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  const generateResponse = async (userMessage: string): Promise<string> => {
    // Simulate AI processing delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    const lowerMessage = userMessage.toLowerCase();
    // Simulated AI responses based on keywords
    if (lowerMessage.includes('training') && lowerMessage.includes('completion')) {
      return `Based on best practices, here are proven strategies to improve training completion rates:
**Immediate Actions:**
1. **Automated Reminders** - Set up smart reminder sequences (7 days before due, 3 days before, day of due)
2. **Make Training Mobile-Friendly** - 65% of employees prefer mobile access
3. **Break into Micro-Learning** - 15-20 minute modules instead of 2-hour sessions
**Incentive Programs:**
- Gamification: Points, badges, leaderboards
- Recognition programs for early completers
- Department competitions with prizes
**Technical Solutions:**
- Integrate with existing workflow tools (Slack, Teams)
- Offline access for field employees
- Progress tracking dashboards for managers
**Communication Strategy:**
- Explain "why" training matters (not just "what")
- Share success stories from other departments
- Manager-led training discussions
Most organizations see completion rates jump from 45% to 85% within 60 days using this approach.`;
    }
    if (lowerMessage.includes('gdpr') || lowerMessage.includes('data privacy')) {
      return `Here's a comprehensive overview of GDPR compliance requirements:
**Core GDPR Principles:**
1. **Lawfulness, Fairness, and Transparency** - Process data lawfully and be open about it
2. **Purpose Limitation** - Only collect data for specified, explicit purposes
3. **Data Minimization** - Collect only what's necessary
4. **Accuracy** - Keep data accurate and up-to-date
5. **Storage Limitation** - Don't keep data longer than needed
6. **Integrity & Confidentiality** - Protect data with appropriate security
7. **Accountability** - Be responsible for GDPR compliance
**Key Requirements:**
- **Data Protection Officer (DPO)** - Required for companies processing large amounts of data
- **Data Protection Impact Assessments (DPIAs)** - Required for high-risk processing
- **Breach Notification** - Report data breaches within 72 hours
- **Record of Processing Activities** - Document all data processing
- **Privacy by Design** - Build privacy into systems from the start
**Employee Training Mandates:**
- All staff handling personal data need GDPR training
- Refresher training annually
- Role-specific training for marketing, HR, IT teams
- Documentation of completion records
**Recommended Timeline:**
- Week 1-2: Data mapping and gap analysis
- Week 3-4: Policy updates and DPO appointment
- Week 5-6: Staff training and documentation
- Week 7-8: Technical implementations and testing
Would you like me to elaborate on any specific area?`;
    }
    if (lowerMessage.includes('workplace safety') || lowerMessage.includes('osha')) {
      return `**Workplace Safety Best Practices:**
**Immediate Safety Improvements:**
1. **Regular Safety Walkthroughs** - Weekly documented inspections
2. **Employee Reporting System** - Easy, anonymous incident reporting
3. **Safety Training** - Job-specific and refresh training
4. **Emergency Preparedness** - Drills and clear evacuation plans
**OSHA Compliance Essentials:**
- **Display Required Posters** - OSHA Job Safety & Health poster (or state equivalent)
- **Maintain OSHA 300 Log** - Record injuries and illnesses
- **Provide PPE** - Personal protective equipment at no cost
- **Medical Attention** - Access to medical care for work-related injuries
**High-Impact Safety Programs:**
- **Behavior-Based Safety** - Focus on safe behaviors, not just conditions
- **Safety Committees** - Include employee representatives
- **Recognition Programs** - Reward safe behaviors
- **Near-Miss Reporting** - Track and address potential incidents
**Technology Solutions:**
- Mobile incident reporting apps
- Digital safety management systems
- Real-time monitoring for high-risk areas
- Automated compliance tracking
**Key Metrics to Track:**
- Total Recordable Incident Rate (TRIR)
- Days Away, Restricted, or Transferred (DART)
- Near-miss reporting frequency
- Training completion rates
- Inspection completion rates
Most organizations see 40-60% reduction in incidents within the first year implementing these practices.`;
    }
    if (lowerMessage.includes('anonymous feedback') || lowerMessage.includes('feedback system')) {
      return `**Anonymous Feedback Best Practices:**
**Creating Psychological Safety:**
1. **Multiple Reporting Channels** - Phone, web form, mobile app, in-person
2. **Zero-Retaliation Policy** - Clearly state and enforce anti-retaliation
3. **Anonymous Tracking** - Secure tracking IDs known only to submitter
4. **Third-Party Hotlines** - External reporting options
5. **Regular Communication** - Updates on actions taken (without revealing sources)
**System Design Requirements:**
- **No IP Logging** - Don't collect any identifying information
- **Encrypted Storage** - Protect all submission data
- **Limited Access** - Only authorized HR personnel can review
- **No Timing Analysis** - Prevent pattern identification
- **Salted Hashing** - For any target information
**Response Framework:**
**Critical Issues** (Harassment, Safety, Discrimination):
- Immediate HR notification
- 24-hour initial assessment
- 48-hour investigation start
- Weekly updates (without revealing sources)
**Standard Issues:**
- 5-day acknowledgment
- 10-day assessment
- 30-day resolution target
- Monthly status checks
**Legal Protection:**
- Follow EEOC, OSHA, and state-specific guidelines
- Maintain chain of custody
- Document all actions taken
- Consult legal counsel for serious issues
**Success Metrics:**
- Trust index scores
- Reporting frequency trends
- Resolution time improvements
- Employee satisfaction surveys
**Implementation Timeline:**
- Week 1: Policy review and system setup
- Week 2: Staff training and communication
- Week 3: Launch with multiple feedback channels
- Week 4: Review first submissions and refine process
The key is building trust through consistent, transparent responses while maintaining complete anonymity.`;
    }
    // Default response for other questions
    return `I understand you're asking about compliance. Here are some key areas I can help with:
**🔍 Compliance Analysis**
- Gap assessments across different regulations
- Risk scoring and prioritization
- Compliance audit preparation
- Regulatory requirement mapping
**📋 Policy Development**
- Employee handbook creation
- Code of conduct development
- Privacy policy drafting
- Safety procedure documentation
**📚 Training Programs**
- Compliance training curriculum
- Role-specific training paths
- Engagement strategies
- Completion tracking systems
**🛡️ Risk Management**
- Risk assessment methodologies
- Mitigation strategy development
- Incident response planning
- Regulatory monitoring
**Could you be more specific about which compliance area you'd like help with? I can provide detailed guidance on any of these topics or help you assess your current compliance posture.`;
  };
  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    try {
      const response = await generateResponse(input);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
        type: response.includes('⚠️') ? 'warning' : response.includes('✓') ? 'recommendation' : 'text'
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI response error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again or contact support for assistance.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };
  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };
  const toggleVoiceInput = () => {
    if (!isListening) {
      // Start voice recognition
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInput(transcript);
          setIsListening(false);
        };
        recognition.onerror = () => {
          setIsListening(false);
        };
        recognition.onend = () => {
          setIsListening(false);
        };
        recognition.start();
        setIsListening(true);
      } else {
        alert('Voice recognition is not supported in your browser');
      }
    } else {
      setIsListening(false);
    }
  };
  const getTypeIcon = (type?: string) => {
    switch (type) {
      case 'recommendation':
        return <Lightbulb className="w-4 h-4 text-yellow-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'check':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      default:
        return <Bot className="w-4 h-4 text-blue-500" />;
    }
  };
  return (
    <div className={`max-w-4xl mx-auto p-6 ${className}`}>
      <Card className="h-[600px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">AI Compliance Assistant</h2>
              <p className="text-sm text-gray-500">Get expert compliance guidance</p>
            </div>
          </div>
          <Badge color="blue" variant="outline">
            <Sparkles className="w-3 h-3 mr-1" />
            AI Powered
          </Badge>
        </div>
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex space-x-2 max-w-[80%] ${
                message.role === 'user' ? 'flex-row-reverse' : ''
              }`}>
                <div className={`flex-shrink-0 ${
                  message.role === 'user' ? 'bg-blue-500' : 'bg-gray-200'
                } rounded-full p-2`}>
                  {message.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    getTypeIcon(message.type)
                  )}
                </div>
                <div
                  className={`rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex space-x-2">
                <div className="flex-shrink-0 bg-gray-200 rounded-full p-2">
                  <Bot className="w-4 h-4 text-gray-600" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        {/* Suggestions */}
        {messages.length === 1 && (
          <div className="p-4 border-t border-gray-200">
            <p className="text-sm text-gray-600 mb-3">Popular questions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.slice(0, 3).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full hover:bg-blue-100 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
        {/* Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me anything about compliance..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isTyping}
            />
            <Button
              onClick={toggleVoiceInput}
              variant="outline"
              size="small"
              icon={isListening ? <MicOff className="w-4 h-4 text-red-500" /> : <Mic className="w-4 h-4" />}
              className={isListening ? 'animate-pulse bg-red-50 border-red-200' : ''}
            >
              {isListening ? 'Mute' : 'Voice'}
            </Button>
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || isTyping}
              icon={<Send className="w-4 h-4" />}
              loading={isTyping}
            >
              Send
            </Button>
          </div>
        </div>
      </Card>
      {/* Usage Tips */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">💡 Tips for Better Results:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Be specific about your industry and company size</li>
          <li>• Ask about specific regulations (GDPR, OSHA, EEOC, etc.)</li>
          <li>• Include details about your current compliance challenges</li>
          <li>• Request practical, actionable advice rather than theoretical</li>
          <li>• Ask for step-by-step implementation guidance</li>
        </ul>
      </div>
    </div>
  );
};