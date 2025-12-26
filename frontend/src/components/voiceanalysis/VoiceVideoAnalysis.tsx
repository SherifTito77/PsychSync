import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  ComposedChart,
} from 'recharts';
import {
  Mic,
  Video,
  Camera,
  Upload,
  Download,
  Play,
  Pause,
  Square,
  RefreshCw,
  Settings,
  FileText,
  Volume2,
  Waveform,
  Face,
  Smile,
  Frown,
  Meh,
  Heart,
  Brain,
  Eye,
  Clock,
  Calendar,
  CheckCircle,
  AlertTriangle,
  Info,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  PieChartIcon,
  Target,
  Zap,
  Shield,
  Radio,
  Film,
  Music,
  MessageSquare,
  User,
  Users,
  Award,
  Star,
  ChevronRight,
  ChevronDown,
  Maximize2,
  Volume,
  Volume1,
  Volume2 as Volume2Icon,
  VolumeX,
} from 'lucide-react';

interface AnalysisResult {
  analysis_id: string;
  user_id: string;
  video_path: string;
  duration: number;
  transcription: {
    text: string;
    language: string;
    confidence: number;
    word_timestamps: Array<[number, number, string]>;
    processing_time: number;
  };
  facial_analysis: Array<{
    timestamp: number;
    primary_emotion: string;
    emotion_confidence: number;
    attention_score: number;
    eye_contact: boolean;
    engagement_indicators: string[];
  }>;
  voice_sentiment: Array<{
    timestamp: number;
    sentiment: string;
    sentiment_confidence: number;
    confidence_score: number;
    speech_rate: number;
    clarity_score: number;
    stress_indicators: string[];
  }>;
  overall_sentiment: string;
  overall_confidence: number;
  engagement_score: number;
  authenticity_score: number;
  recommendations: string[];
  insights: string[];
  risk_assessment: {
    risk_level: string;
    risk_factors: string[];
  };
}

interface RecordingConfig {
  maxDuration: number;
  quality: string;
  format: string;
  includeAudio: boolean;
  autoTranscription: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const VoiceVideoAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('recording');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisResult | null>(null);
  const [recordingConfig, setRecordingConfig] = useState<RecordingConfig>({
    maxDuration: 300,
    quality: 'high',
    format: 'mp4',
    includeAudio: true,
    autoTranscription: true,
  });

  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Mock data
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>([
    {
      analysis_id: 'analysis_001',
      user_id: 'user_001',
      video_path: '/videos/analysis_001.mp4',
      duration: 45.2,
      transcription: {
        text: 'I believe that my leadership style focuses on empowering team members through clear communication and setting achievable goals. I find that when people understand the vision and their role in achieving it, they become more motivated and engaged.',
        language: 'en-US',
        confidence: 0.94,
        word_timestamps: [[0, 0.5, 'I'], [0.5, 1.2, 'believe'], [1.2, 1.8, 'that']],
        processing_time: 2.3,
      },
      facial_analysis: [
        {
          timestamp: 0,
          primary_emotion: 'happy',
          emotion_confidence: 0.85,
          attention_score: 0.92,
          eye_contact: true,
          engagement_indicators: ['maintains_eye_contact', 'high_attention'],
        },
        {
          timestamp: 15,
          primary_emotion: 'engaged',
          emotion_confidence: 0.78,
          attention_score: 0.88,
          eye_contact: true,
          engagement_indicators: ['clear_expressions', 'focused'],
        },
        {
          timestamp: 30,
          primary_emotion: 'neutral',
          emotion_confidence: 0.72,
          attention_score: 0.85,
          eye_contact: true,
          engagement_indicators: ['steady_gaze', 'composed'],
        },
      ],
      voice_sentiment: [
        {
          timestamp: 0,
          sentiment: 'positive',
          sentiment_confidence: 0.87,
          confidence_score: 0.91,
          speech_rate: 145,
          clarity_score: 0.89,
          stress_indicators: [],
        },
        {
          timestamp: 20,
          sentiment: 'positive',
          sentiment_confidence: 0.82,
          confidence_score: 0.88,
          speech_rate: 152,
          clarity_score: 0.91,
          stress_indicators: [],
        },
      ],
      overall_sentiment: 'positive',
      overall_confidence: 0.86,
      engagement_score: 0.89,
      authenticity_score: 0.79,
      recommendations: [
        'Excellent eye contact and engagement throughout',
        'Consider varying pace slightly for better emphasis',
        'Strong vocal confidence and clarity detected',
      ],
      insights: [
        'High engagement level detected throughout the response',
        'Strong vocal confidence and clarity detected',
        'Emotional consistency shows authentic communication',
      ],
      risk_assessment: {
        risk_level: 'low',
        risk_factors: [],
      },
    }
  ]);

  const emotionTimelineData = selectedAnalysis?.facial_analysis.map(point => ({
    time: point.timestamp,
    emotion: point.primary_emotion,
    confidence: point.emotion_confidence * 100,
    attention: point.attention_score * 100,
  })) || [];

  const sentimentTimelineData = selectedAnalysis?.voice_sentiment.map(point => ({
    time: point.timestamp,
    sentiment: point.sentiment,
    confidence: point.sentiment_confidence * 100,
    clarity: point.clarity_score * 100,
  })) || [];

  const emotionDistribution = selectedAnalysis?.facial_analysis.reduce((acc, point) => {
    acc[point.primary_emotion] = (acc[point.primary_emotion] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  const emotionChartData = Object.entries(emotionDistribution).map(([emotion, count]) => ({
    name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
    value: count,
    fill: COLORS[Object.keys(emotionDistribution).indexOf(emotion) % COLORS.length]
  }));

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return <Smile className="h-4 w-4 text-green-500" />;
      case 'negative': return <Frown className="h-4 w-4 text-red-500" />;
      case 'neutral': return <Meh className="h-4 w-4 text-gray-500" />;
      default: return <Meh className="h-4 w-4 text-gray-500" />;
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'high': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        },
        audio: true
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm'
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        await processRecording(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      startRecordingTimer();

    } catch (error) {
      console.error('Error accessing media devices:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsRecording(false);
    stopRecordingTimer();
  };

  const startRecordingTimer = () => {
    setRecordingTime(0);
    recordingTimerRef.current = setInterval(() => {
      setRecordingTime(prev => {
        if (prev >= recordingConfig.maxDuration) {
          stopRecording();
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
  };

  const stopRecordingTimer = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
  };

  const processRecording = async (blob: Blob) => {
    setIsProcessing(true);

    // In production, upload to server and process
    setTimeout(() => {
      const newAnalysis: AnalysisResult = {
        analysis_id: `analysis_${Date.now()}`,
        user_id: 'current_user',
        video_path: URL.createObjectURL(blob),
        duration: blob.size / 1000, // Mock duration
        transcription: {
          text: 'This is a sample transcription of the recorded response.',
          language: 'en-US',
          confidence: 0.92,
          word_timestamps: [],
          processing_time: 1.5,
        },
        facial_analysis: [
          {
            timestamp: 0,
            primary_emotion: 'happy',
            emotion_confidence: 0.85,
            attention_score: 0.90,
            eye_contact: true,
            engagement_indicators: ['maintains_eye_contact'],
          }
        ],
        voice_sentiment: [
          {
            timestamp: 0,
            sentiment: 'positive',
            sentiment_confidence: 0.88,
            confidence_score: 0.90,
            speech_rate: 150,
            clarity_score: 0.92,
            stress_indicators: [],
          }
        ],
        overall_sentiment: 'positive',
        overall_confidence: 0.87,
        engagement_score: 0.88,
        authenticity_score: 0.82,
        recommendations: ['Good performance overall'],
        insights: ['Clear communication detected'],
        risk_assessment: {
          risk_level: 'low',
          risk_factors: [],
        },
      };

      setAnalysisHistory([newAnalysis, ...analysisHistory]);
      setSelectedAnalysis(newAnalysis);
      setIsProcessing(false);
    }, 3000);
  };

  const uploadVideo = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    // Process uploaded video
    setTimeout(() => {
      setIsProcessing(false);
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Video className="h-8 w-8 text-blue-500" />
            Voice & Video Response Analysis
          </h1>
          <p className="text-muted-foreground">
            Advanced multimodal analysis with transcription, facial recognition, and sentiment analysis
          </p>
        </div>
        <div className="flex gap-4">
          <Button variant="outline" className="gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
          <Button className="gap-2">
            <FileText className="h-4 w-4" />
            View History
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Analyses</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{analysisHistory.length}</div>
            <p className="text-xs text-muted-foreground">
              Completed analyses
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Confidence</CardTitle>
            <Target className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {selectedAnalysis ? `${(selectedAnalysis.overall_confidence * 100).toFixed(0)}%` : '87%'}
            </div>
            <p className="text-xs text-muted-foreground">
              Analysis confidence
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Engagement Score</CardTitle>
            <Eye className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {selectedAnalysis ? `${(selectedAnalysis.engagement_score * 100).toFixed(0)}%` : '85%'}
            </div>
            <p className="text-xs text-muted-foreground">
              Average engagement
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Level</CardTitle>
            <Shield className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600 capitalize">
              {selectedAnalysis ? selectedAnalysis.risk_assessment.risk_level : 'Low'}
            </div>
            <p className="text-xs text-muted-foreground">
              Current risk assessment
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="recording" className="gap-2">
            <Video className="h-4 w-4" />
            Recording
          </TabsTrigger>
          <TabsTrigger value="analysis" className="gap-2">
            <Brain className="h-4 w-4" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="transcription" className="gap-2">
            <FileText className="h-4 w-4" />
            Transcription
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <Calendar className="h-4 w-4" />
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="recording" className="space-y-6">
          {/* Recording Interface */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Camera className="h-5 w-5 text-red-500" />
                  Video Recording
                </CardTitle>
                <CardDescription>
                  Record your response for comprehensive analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Video Preview */}
                <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
                  <video
                    ref={videoRef}
                    autoPlay
                    muted
                    className="w-full h-full object-cover"
                  />
                  {!isRecording && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-900/50">
                      <div className="text-center text-white">
                        <Camera className="h-12 w-12 mx-auto mb-2" />
                        <p>Camera preview will appear here</p>
                      </div>
                    </div>
                  )}
                  {/* Recording Indicator */}
                  {isRecording && (
                    <div className="absolute top-4 right-4 flex items-center gap-2 bg-red-500 text-white px-3 py-1 rounded-full">
                      <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                      <span className="text-sm font-medium">REC {formatTime(recordingTime)}</span>
                    </div>
                  )}
                </div>

                {/* Recording Controls */}
                <div className="flex justify-center gap-4">
                  {!isRecording ? (
                    <Button
                      onClick={startRecording}
                      size="lg"
                      className="gap-2 h-16 w-16 rounded-full"
                    >
                      <Video className="h-6 w-6" />
                    </Button>
                  ) : (
                    <Button
                      onClick={stopRecording}
                      size="lg"
                      variant="destructive"
                      className="gap-2 h-16 w-16 rounded-full"
                    >
                      <Square className="h-6 w-6" />
                    </Button>
                  )}
                </div>

                {/* Recording Settings */}
                <div className="space-y-4">
                  <h4 className="font-semibold">Recording Settings</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Quality</label>
                      <Select value={recordingConfig.quality} onValueChange={(value) =>
                        setRecordingConfig(prev => ({ ...prev, quality: value }))
                      }>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low (faster)</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High (recommended)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Max Duration</label>
                      <Select value={recordingConfig.maxDuration.toString()} onValueChange={(value) =>
                        setRecordingConfig(prev => ({ ...prev, maxDuration: parseInt(value) }))
                      }>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="60">1 minute</SelectItem>
                          <SelectItem value="180">3 minutes</SelectItem>
                          <SelectItem value="300">5 minutes</SelectItem>
                          <SelectItem value="600">10 minutes</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="autoTranscription"
                      checked={recordingConfig.autoTranscription}
                      onChange={(e) =>
                        setRecordingConfig(prev => ({ ...prev, autoTranscription: e.target.checked }))
                      }
                      className="rounded"
                    />
                    <label htmlFor="autoTranscription" className="text-sm">
                      Auto-transcribe audio
                    </label>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Upload className="h-5 w-5 text-blue-500" />
                  Upload Video
                </CardTitle>
                <CardDescription>
                  Upload an existing video file for analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-lg font-medium mb-2">Upload Video File</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Drag and drop or click to select
                  </p>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={uploadVideo}
                    className="hidden"
                    id="video-upload"
                  />
                  <Button asChild>
                    <label htmlFor="video-upload" className="cursor-pointer">
                      Select File
                    </label>
                  </Button>
                  <p className="text-xs text-muted-foreground mt-4">
                    Supported formats: MP4, WebM, MOV (Max 100MB)
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Processing Status */}
          {isProcessing && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
                  <div>
                    <h3 className="font-semibold">Processing Analysis</h3>
                    <p className="text-sm text-muted-foreground">
                      Analyzing video, transcribing audio, and generating insights...
                    </p>
                  </div>
                </div>
                <Progress value={66} className="mt-4" />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="analysis" className="space-y-6">
          {selectedAnalysis ? (
            <>
              {/* Analysis Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>Analysis Overview</CardTitle>
                  <CardDescription>
                    Comprehensive insights from multimodal analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="flex justify-center mb-2">
                        {getSentimentIcon(selectedAnalysis.overall_sentiment)}
                      </div>
                      <div className="text-2xl font-bold capitalize">
                        {selectedAnalysis.overall_sentiment}
                      </div>
                      <div className="text-sm text-muted-foreground">Overall Sentiment</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {(selectedAnalysis.overall_confidence * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Confidence Score</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {(selectedAnalysis.engagement_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Engagement</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {(selectedAnalysis.authenticity_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Authenticity</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Emotional Analysis */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-3">
                      <Face className="h-5 w-5 text-blue-500" />
                      Facial Expression Timeline
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={emotionTimelineData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" label="Time (s)" />
                        <YAxis label="Score (%)" />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="confidence"
                          stroke="#8884d8"
                          name="Emotion Confidence"
                          strokeWidth={2}
                        />
                        <Line
                          type="monotone"
                          dataKey="attention"
                          stroke="#82ca9d"
                          name="Attention Score"
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-3">
                      <Volume2 className="h-5 w-5 text-green-500" />
                      Voice Sentiment Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={sentimentTimelineData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" label="Time (s)" />
                        <YAxis label="Score (%)" />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="confidence"
                          stroke="#ff7300"
                          name="Sentiment Confidence"
                          strokeWidth={2}
                        />
                        <Line
                          type="monotone"
                          dataKey="clarity"
                          stroke="#00ff00"
                          name="Speech Clarity"
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>

              {/* Emotion Distribution */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Emotion Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={emotionChartData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {emotionChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Risk Assessment</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className={`p-4 rounded-lg ${getRiskColor(selectedAnalysis.risk_assessment.risk_level)}`}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold">Risk Level</span>
                          <Badge variant="outline" className={getRiskColor(selectedAnalysis.risk_assessment.risk_level)}>
                            {selectedAnalysis.risk_assessment.risk_level.toUpperCase()}
                          </Badge>
                        </div>
                        {selectedAnalysis.risk_assessment.risk_factors.length > 0 ? (
                          <div className="space-y-2">
                            <span className="text-sm font-medium">Identified Factors:</span>
                            {selectedAnalysis.risk_assessment.risk_factors.map((factor, index) => (
                              <div key={index} className="flex items-center gap-2 text-sm">
                                <AlertTriangle className="h-3 w-3" />
                                {factor.replace('_', ' ')}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm">No significant risk factors detected</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Recommendations and Insights */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-3">
                      <TrendingUp className="h-5 w-5 text-blue-500" />
                      Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {selectedAnalysis.recommendations.map((recommendation, index) => (
                        <div key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                          <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5" />
                          <span className="text-sm">{recommendation}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-3">
                      <Brain className="h-5 w-5 text-purple-500" />
                      Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {selectedAnalysis.insights.map((insight, index) => (
                        <div key={index} className="flex items-start gap-3 p-3 bg-purple-50 rounded-lg">
                          <Info className="h-4 w-4 text-purple-600 mt-0.5" />
                          <span className="text-sm">{insight}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Video className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Analysis Available</h3>
                <p className="text-muted-foreground">
                  Record or upload a video to see detailed analysis results
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="transcription" className="space-y-6">
          {selectedAnalysis ? (
            <>
              {/* Transcription Overview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-blue-500" />
                    Transcription Results
                  </CardTitle>
                  <CardDescription>
                    Automatic speech-to-text with confidence scoring
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {selectedAnalysis.transcription.language}
                        </div>
                        <div className="text-sm text-muted-foreground">Language</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {(selectedAnalysis.transcription.confidence * 100).toFixed(0)}%
                        </div>
                        <div className="text-sm text-muted-foreground">Confidence</div>
                      </div>
                      <div className="text-center p-4 border rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {selectedAnalysis.transcription.processing_time.toFixed(1)}s
                        </div>
                        <div className="text-sm text-muted-foreground">Processing Time</div>
                      </div>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-semibold mb-2">Transcribed Text</h4>
                      <p className="text-sm leading-relaxed">
                        {selectedAnalysis.transcription.text}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Word Timeline */}
              <Card>
                <CardHeader>
                  <CardTitle>Word Timeline</CardTitle>
                  <CardDescription>
                    Timestamped words from the transcription
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {selectedAnalysis.transcription.word_timestamps.map((timestamp, index) => (
                      <div key={index} className="flex items-center gap-3 text-sm p-2 hover:bg-gray-50 rounded">
                        <span className="text-xs text-muted-foreground font-mono">
                          {timestamp[0].toFixed(1)}s
                        </span>
                        <span className="flex-1">{timestamp[2]}</span>
                        <span className="text-xs text-gray-500">
                          → {timestamp[1].toFixed(1)}s
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <FileText className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Transcription Available</h3>
                <p className="text-muted-foreground">
                  Record or upload a video to see transcription results
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Analysis History</CardTitle>
              <CardDescription>
                Your previous voice and video analyses
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Sentiment</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Engagement</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {analysisHistory.map((analysis, index) => (
                    <TableRow key={analysis.analysis_id}>
                      <TableCell>
                        {new Date().toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {analysis.duration.toFixed(1)}s
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getSentimentIcon(analysis.overall_sentiment)}
                          <span className="capitalize">{analysis.overall_sentiment}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {(analysis.overall_confidence * 100).toFixed(0)}%
                      </TableCell>
                      <TableCell>
                        {(analysis.engagement_score * 100).toFixed(0)}%
                      </TableCell>
                      <TableCell>
                        <Badge className={getRiskColor(analysis.risk_assessment.risk_level)}>
                          {analysis.risk_assessment.risk_level}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedAnalysis(analysis)}
                        >
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VoiceVideoAnalysis;