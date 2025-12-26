import React, { useState, useEffect } from 'react';
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  LineChart,
  Line,
  AreaChart,
  Area,
  Treemap,
} from 'recharts';
import {
  Trophy,
  Target,
  Star,
  Crown,
  Award,
  Medal,
  Gift,
  Flag,
  Zap,
  Flame,
  TrendingUp,
  Users,
  Clock,
  CheckCircle,
  Lock,
  Unlock,
  Settings,
  Share2,
  Download,
  Calendar,
  Activity,
  BarChart3,
  PieChartIcon,
  Gem,
  Diamond,
  Sparkles,
  Heart,
  Brain,
  Rocket,
  BookOpen,
  Lightbulb,
  Handshake,
  Mountain,
  Flags,
  Shield,
  Sword,
  Crown as CrownIcon,
  Gem as GemIcon,
  Coins,
  Target as TargetIcon,
  Compass,
  Map,
  Navigation,
} from 'lucide-react';

interface Achievement {
  id: string;
  name: string;
  description: string;
  category: string;
  badge_tier: string;
  badge_emoji: string;
  points: number;
  progress: number;
  earned: boolean;
  earned_date?: string;
  repeat_count: number;
  hidden: boolean;
  prerequisites: string[];
}

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  score: number;
  level: number;
  badge_tier: string;
  avatar: string;
  change_from_previous: number;
  last_updated: string;
}

interface LevelInfo {
  level: number;
  points_for_current_level: number;
  points_for_next_level: number;
  progress_percentage: number;
  badge_tier: string;
  unlocked_features: string[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658'];

const GamificationSystem: React.FC = () => {
  const [activeTab, setActiveTab] = useState('achievements');
  const [selectedAchievement, setSelectedAchievement] = useState<Achievement | null>(null);
  const [userStats, setUserStats] = useState<any>({});
  const [loading, setLoading] = useState(false);

  // Mock data
  const [achievements, setAchievements] = useState<Achievement[]>([
    {
      id: 'first_assessment',
      name: 'Assessment Pioneer',
      description: 'Complete your first psychological assessment',
      category: 'milestone',
      badge_tier: 'bronze',
      badge_emoji: '🎯',
      points: 100,
      progress: 1.0,
      earned: true,
      earned_date: '2024-01-15',
      repeat_count: 1,
      hidden: false,
      prerequisites: []
    },
    {
      id: 'week_warrior',
      name: 'Week Warrior',
      description: 'Maintain a 7-day activity streak',
      category: 'engagement',
      badge_tier: 'silver',
      badge_emoji: '🔥',
      points: 500,
      progress: 0.71,
      earned: false,
      repeat_count: 0,
      hidden: false,
      prerequisites: []
    },
    {
      id: 'team_leader',
      name: 'Team Leader',
      description: 'Lead a team to top performance ranking',
      category: 'leadership',
      badge_tier: 'gold',
      badge_emoji: '👑',
      points: 750,
      progress: 0.8,
      earned: false,
      repeat_count: 0,
      hidden: false,
      prerequisites: []
    },
    {
      id: 'skill_master',
      name: 'Skill Master',
      description: 'Achieve mastery in 5 different skills',
      category: 'skill_master',
      badge_tier: 'gold',
      badge_emoji: '🏅',
      points: 1000,
      progress: 0.6,
      earned: false,
      repeat_count: 0,
      hidden: false,
      prerequisites: []
    },
    {
      id: 'experimental_explorer',
      name: 'Innovation Explorer',
      description: 'Try experimental features and provide feedback',
      category: 'experimental',
      badge_tier: 'silver',
      badge_emoji: '🚀',
      points: 300,
      progress: 0.33,
      earned: false,
      repeat_count: 0,
      hidden: false,
      prerequisites: []
    },
    {
      id: 'polymath',
      name: 'Polymath',
      description: 'Achieve mastery in 10 different categories',
      category: 'skill_master',
      badge_tier: 'diamond',
      badge_emoji: '🧠',
      points: 5000,
      progress: 0.0,
      earned: false,
      repeat_count: 0,
      hidden: true,
      prerequisites: ['skill_master']
    }
  ]);

  const [levelInfo, setLevelInfo] = useState<LevelInfo>({
    level: 12,
    points_for_current_level: 7200,
    points_for_next_level: 8750,
    progress_percentage: 0.78,
    badge_tier: 'silver',
    unlocked_features: ['basic_analytics', 'advanced_analytics', 'priority_support']
  });

  const [leaderboardData, setLeaderboardData] = useState<LeaderboardEntry[]>([
    {
      rank: 1,
      user_id: 'user_001',
      display_name: 'Alex Chen',
      score: 15420,
      level: 25,
      badge_tier: 'platinum',
      avatar: '👤',
      change_from_previous: -1,
      last_updated: '2024-01-20T10:30:00Z'
    },
    {
      rank: 2,
      user_id: 'user_002',
      display_name: 'Sarah Johnson',
      score: 14200,
      level: 23,
      badge_tier: 'gold',
      avatar: '👤',
      change_from_previous: 1,
      last_updated: '2024-01-20T10:25:00Z'
    },
    {
      rank: 3,
      user_id: 'user_003',
      display_name: 'Mike Davis',
      score: 13800,
      level: 22,
      badge_tier: 'gold',
      avatar: '👤',
      change_from_previous: 0,
      last_updated: '2024-01-20T10:20:00Z'
    },
    {
      rank: 4,
      user_id: 'user_004',
      display_name: 'Emma Wilson',
      score: 12100,
      level: 20,
      badge_tier: 'gold',
      avatar: '👤',
      change_from_previous: 2,
      last_updated: '2024-01-20T10:15:00Z'
    },
    {
      rank: 5,
      user_id: 'user_005',
      display_name: 'James Brown',
      score: 11500,
      level: 19,
      badge_tier: 'silver',
      avatar: '👤',
      change_from_previous: -1,
      last_updated: '2024-01-20T10:10:00Z'
    }
  ]);

  const categoryData = achievements.reduce((acc, achievement) => {
    if (achievement.earned) {
      acc[achievement.category] = (acc[achievement.category] || 0) + 1;
    }
    return acc;
  }, {} as Record<string, number>);

  const categoryChartData = Object.entries(categoryData).map(([category, count]) => ({
    name: category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' '),
    value: count,
    fill: COLORS[Object.keys(categoryData).indexOf(category) % COLORS.length]
  }));

  const tierData = [
    { tier: 'Bronze', count: achievements.filter(a => a.badge_tier === 'bronze' && a.earned).length, color: '#CD7F32' },
    { tier: 'Silver', count: achievements.filter(a => a.badge_tier === 'silver' && a.earned).length, color: '#C0C0C0' },
    { tier: 'Gold', count: achievements.filter(a => a.badge_tier === 'gold' && a.earned).length, color: '#FFD700' },
    { tier: 'Platinum', count: achievements.filter(a => a.badge_tier === 'platinum' && a.earned).length, color: '#E5E4E2' },
    { tier: 'Diamond', count: achievements.filter(a => a.badge_tier === 'diamond' && a.earned).length, color: '#B9F2FF' }
  ];

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'bronze': return <Medal className="h-4 w-4" style={{ color: '#CD7F32' }} />;
      case 'silver': return <Award className="h-4 w-4" style={{ color: '#C0C0C0' }} />;
      case 'gold': return <Trophy className="h-4 w-4" style={{ color: '#FFD700' }} />;
      case 'platinum': return <Crown className="h-4 w-4" style={{ color: '#E5E4E2' }} />;
      case 'diamond': return <Diamond className="h-4 w-4" style={{ color: '#B9F2FF' }} />;
      default: return <Star className="h-4 w-4" />;
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'bronze': return 'bg-bronze-500 text-bronze-100';
      case 'silver': return 'bg-silver-500 text-silver-100';
      case 'gold': return 'bg-yellow-500 text-yellow-100';
      case 'platinum': return 'bg-gray-300 text-gray-800';
      case 'diamond': return 'bg-cyan-300 text-cyan-900';
      default: return 'bg-gray-500 text-gray-100';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'milestone': return <Flag className="h-4 w-4" />;
      case 'engagement': return <Flame className="h-4 w-4" />;
      case 'leadership': return <Crown className="h-4 w-4" />;
      case 'skill_master': return <Brain className="h-4 w-4" />;
      case 'experimental': return <Rocket className="h-4 w-4" />;
      case 'social': return <Users className="h-4 w-4" />;
      case 'learning': return <BookOpen className="h-4 w-4" />;
      case 'challenge': return <Target className="h-4 w-4" />;
      default: return <Star className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Trophy className="h-8 w-8 text-yellow-500" />
            Gamification System
          </h1>
          <p className="text-muted-foreground">
            Track your progress, earn achievements, and climb the leaderboards
          </p>
        </div>
        <div className="flex gap-4">
          <Button variant="outline" className="gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </Button>
          <Button className="gap-2">
            <Target className="h-4 w-4" />
            Active Challenges
          </Button>
        </div>
      </div>

      {/* User Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Level</CardTitle>
            <Crown className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">{levelInfo.level}</div>
            <p className="text-xs text-muted-foreground">
              Level {levelInfo.badge_tier.charAt(0).toUpperCase() + levelInfo.badge_tier.slice(1)} Tier
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Points</CardTitle>
            <Coins className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{levelInfo.points_for_current_level.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Next level at {levelInfo.points_for_next_level.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Achievements</CardTitle>
            <Award className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {achievements.filter(a => a.earned).length}/{achievements.length}
            </div>
            <p className="text-xs text-muted-foreground">
              {((achievements.filter(a => a.earned).length / achievements.length) * 100).toFixed(0)}% completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Leaderboard Rank</CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">#42</div>
            <p className="text-xs text-muted-foreground">
              Top 5% of all users
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Level Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-purple-500" />
            Level Progress
          </CardTitle>
          <CardDescription>
            Your progress to the next level and unlocked features
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Level {levelInfo.level} Progress</span>
              <span>{(levelInfo.progress_percentage * 100).toFixed(0)}%</span>
            </div>
            <Progress value={levelInfo.progress_percentage * 100} className="h-3" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{levelInfo.points_for_current_level.toLocaleString()} points</span>
              <span>{levelInfo.points_for_next_level.toLocaleString()} points</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-semibold">Unlocked Features</h4>
              <div className="space-y-1">
                {levelInfo.unlocked_features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm p-2 bg-green-50 rounded">
                    <Unlock className="h-3 w-3 text-green-600" />
                    {feature.replace('_', ' ').charAt(0).toUpperCase() + feature.replace('_', ' ').slice(1)}
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold">Next Level Rewards</h4>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm p-2 bg-gray-50 rounded">
                  <Lock className="h-3 w-3 text-gray-600" />
                  Advanced Analytics Dashboard
                </div>
                <div className="flex items-center gap-2 text-sm p-2 bg-gray-50 rounded">
                  <Lock className="h-3 w-3 text-gray-600" />
                  Custom Achievement Badges
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="achievements" className="gap-2">
            <Trophy className="h-4 w-4" />
            Achievements
          </TabsTrigger>
          <TabsTrigger value="leaderboards" className="gap-2">
            <Target className="h-4 w-4" />
            Leaderboards
          </TabsTrigger>
          <TabsTrigger value="progress" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Progress Analytics
          </TabsTrigger>
          <TabsTrigger value="rewards" className="gap-2">
            <Gift className="h-4 w-4" />
            Rewards
          </TabsTrigger>
        </TabsList>

        <TabsContent value="achievements" className="space-y-6">
          {/* Achievement Categories */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Achievement Categories</CardTitle>
                <CardDescription>
                  Distribution of earned achievements by category
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryChartData.map((entry, index) => (
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
                <CardTitle>Badge Tier Collection</CardTitle>
                <CardDescription>
                  Your achievement collection by tier
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {tierData.map((tier) => (
                    <div key={tier.tier} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-4 h-4 rounded-full" style={{ backgroundColor: tier.color }} />
                        <span className="font-medium capitalize">{tier.tier}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold">{tier.count}</span>
                        {getTierIcon(tier.tier.toLowerCase())}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Achievements List */}
          <Card>
            <CardHeader>
              <CardTitle>All Achievements</CardTitle>
              <CardDescription>
                Track your progress on all available achievements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {achievements.map((achievement) => (
                  <div key={achievement.id} className={`border rounded-lg p-4 space-y-3 ${
                    achievement.earned ? 'bg-green-50 border-green-200' : 'bg-gray-50'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">{achievement.badge_emoji}</div>
                        <div>
                          <h3 className="font-semibold flex items-center gap-2">
                            {achievement.name}
                            {getTierIcon(achievement.badge_tier)}
                          </h3>
                          <p className="text-sm text-muted-foreground">{achievement.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant={achievement.earned ? "default" : "secondary"}>
                          {achievement.badge_tier.charAt(0).toUpperCase() + achievement.badge_tier.slice(1)}
                        </Badge>
                        <div className="text-right">
                          <div className="font-bold text-blue-600">+{achievement.points}</div>
                          <div className="text-xs text-muted-foreground">points</div>
                        </div>
                      </div>
                    </div>

                    {!achievement.earned && achievement.progress > 0 && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Progress</span>
                          <span>{(achievement.progress * 100).toFixed(0)}%</span>
                        </div>
                        <Progress value={achievement.progress * 100} className="h-2" />
                      </div>
                    )}

                    {achievement.earned && (
                      <div className="flex items-center justify-between text-sm text-green-700">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4" />
                          Earned on {achievement.earned_date}
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Share2 className="h-3 w-3" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    )}

                    {achievement.prerequisites.length > 0 && (
                      <div className="text-xs text-muted-foreground">
                        Prerequisites: {achievement.prerequisites.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leaderboards" className="space-y-6">
          {/* Main Leaderboard */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Target className="h-5 w-5 text-orange-500" />
                Points Leaderboard
              </CardTitle>
              <CardDescription>
                Top performers this week
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rank</TableHead>
                    <TableHead>Player</TableHead>
                    <TableHead>Level</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Change</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaderboardData.map((entry) => (
                    <TableRow key={entry.user_id} className={entry.display_name === 'You' ? 'bg-blue-50' : ''}>
                      <TableCell>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                          entry.rank === 1 ? 'bg-yellow-500' :
                          entry.rank === 2 ? 'bg-gray-400' :
                          entry.rank === 3 ? 'bg-orange-600' :
                          'bg-gray-300'
                        }`}>
                          {entry.rank}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{entry.avatar}</span>
                          <span className="font-medium">{entry.display_name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">Level {entry.level}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="font-bold">{entry.score.toLocaleString()}</div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getTierColor(entry.badge_tier)}>
                          {entry.badge_tier.charAt(0).toUpperCase() + entry.badge_tier.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className={`flex items-center gap-1 font-medium ${
                          entry.change_from_previous > 0 ? 'text-green-600' :
                          entry.change_from_previous < 0 ? 'text-red-600' :
                          'text-gray-600'
                        }`}>
                          {entry.change_from_previous > 0 ? '↑' :
                           entry.change_from_previous < 0 ? '↓' : '→'}
                          {Math.abs(entry.change_from_previous)}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Leaderboard Categories */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Flame className="h-4 w-4 text-red-500" />
                  Streak Masters
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { name: 'Sarah Johnson', streak: 45, avatar: '👤' },
                    { name: 'Mike Davis', streak: 32, avatar: '👤' },
                    { name: 'Emma Wilson', streak: 28, avatar: '👤' }
                  ].map((user, index) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center gap-2">
                        <span>{user.avatar}</span>
                        <span className="text-sm font-medium">{user.name}</span>
                      </div>
                      <div className="flex items-center gap-1 text-red-600">
                        <Flame className="h-3 w-3" />
                        <span className="text-sm font-bold">{user.streak}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-purple-500" />
                  Achievement Hunters
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { name: 'Alex Chen', achievements: 47, avatar: '👤' },
                    { name: 'Sarah Johnson', achievements: 42, avatar: '👤' },
                    { name: 'Mike Davis', achievements: 38, avatar: '👤' }
                  ].map((user, index) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center gap-2">
                        <span>{user.avatar}</span>
                        <span className="text-sm font-medium">{user.name}</span>
                      </div>
                      <div className="flex items-center gap-1 text-purple-600">
                        <Trophy className="h-3 w-3" />
                        <span className="text-sm font-bold">{user.achievements}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Rocket className="h-4 w-4 text-blue-500" />
                  Innovation Leaders
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { name: 'Emma Wilson', score: 892, avatar: '👤' },
                    { name: 'Alex Chen', score: 756, avatar: '👤' },
                    { name: 'James Brown', score: 634, avatar: '👤' }
                  ].map((user, index) => (
                    <div key={index} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center gap-2">
                        <span>{user.avatar}</span>
                        <span className="text-sm font-medium">{user.name}</span>
                      </div>
                      <div className="flex items-center gap-1 text-blue-600">
                        <Zap className="h-3 w-3" />
                        <span className="text-sm font-bold">{user.score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="progress" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Points Progression</CardTitle>
                <CardDescription>
                  Your points earned over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={[
                    { month: 'Jan', points: 1200 },
                    { month: 'Feb', points: 2800 },
                    { month: 'Mar', points: 4200 },
                    { month: 'Apr', points: 5800 },
                    { month: 'May', points: 7200 }
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="points"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Activity Heatmap</CardTitle>
                <CardDescription>
                  Your daily activity patterns
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-7 gap-1 text-xs">
                  {Array.from({ length: 35 }, (_, i) => (
                    <div
                      key={i}
                      className={`aspect-square rounded ${
                        Math.random() > 0.7 ? 'bg-green-500' :
                        Math.random() > 0.4 ? 'bg-green-300' :
                        Math.random() > 0.2 ? 'bg-gray-200' : 'bg-gray-100'
                      }`}
                      title={`${i + 1} activities`}
                    />
                  ))}
                </div>
                <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                  <span>Less</span>
                  <div className="flex gap-1">
                    <div className="w-3 h-3 bg-gray-100 rounded" />
                    <div className="w-3 h-3 bg-gray-200 rounded" />
                    <div className="w-3 h-3 bg-green-300 rounded" />
                    <div className="w-3 h-3 bg-green-500 rounded" />
                  </div>
                  <span>More</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rewards" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Gift className="h-5 w-5 text-purple-500" />
                  Unlocked Rewards
                </CardTitle>
                <CardDescription>
                  Features and benefits you've earned
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {levelInfo.unlocked_features.map((reward, index) => (
                    <div key={index} className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <Unlock className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">{reward.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Lock className="h-5 w-5 text-gray-500" />
                  Upcoming Rewards
                </CardTitle>
                <CardDescription>
                  Rewards you can unlock at the next level
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <Lock className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium">Custom Profile Themes</span>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <Lock className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium">Priority Support Access</span>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <Lock className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium">Beta Feature Access</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Sparkles className="h-5 w-5 text-yellow-500" />
                  Special Badges
                </CardTitle>
                <CardDescription>
                  Exclusive badges for special achievements
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <span className="text-xl">👑</span>
                    <div>
                      <div className="font-medium">Team Leader</div>
                      <div className="text-xs text-muted-foreground">Led team to #1 ranking</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <span className="text-xl">🚀</span>
                    <div>
                      <div className="font-medium">Early Adopter</div>
                      <div className="text-xs text-muted-foreground">First 100 users</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GamificationSystem;