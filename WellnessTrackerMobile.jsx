import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Alert, Dimensions, Animated, Platform, Vibration
} from 'react-native';
import {
  Activity, Heart, Brain, Users, Moon, Sun, Smartphone,
  Bell, Calendar, TrendingUp, Award, Target, Battery,
  Droplets, Wind, Cloud, Zap, ArrowUp, Settings, Plus,
  Check, X, AlertCircle, Info
} from 'lucide-react-native';

const { width, height } = Dimensions.get('window');

const WellnessTrackerMobile = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [todayProgress, setTodayProgress] = useState({});
  const [recommendations, setRecommendations] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [quickActions, setQuickActions] = useState([]);

  useEffect(() => {
    loadUserProgress();
    loadRecommendations();
    scheduleNotifications();
    setupQuickActions();
  }, []);

  const loadUserProgress = useCallback(() => {
    // Simulate loading today's progress data
    const progress = {
      steps: {
        water: { current: 5, target: 8, icon: Droplets, unit: 'glasses' },
        exercise: { current: 15, target: 30, icon: Activity, unit: 'minutes' },
        mindfulness: { current: 5, target: 10, icon: Brain, unit: 'minutes' },
        sleep: { current: 7, target: 8, icon: Moon, unit: 'hours' },
        nutrition: { current: 2, target: 3, icon: Heart, unit: 'meals' }
      },
      wellnessScore: 75,
      streakDays: 12
    };
    setTodayProgress(progress);
  }, []);

  const loadRecommendations = useCallback(() => {
    // Load personalized recommendations
    const recs = [
      {
        id: 1,
        type: 'immediate',
        title: 'Take a mindful walk',
        description: '15-minute walk outside to reduce stress and boost mood',
        difficulty: 1,
        timeRequired: '15 min',
        icon: Activity,
        color: '#10b981',
        status: 'pending'
      },
      {
        id: 2,
        type: 'wellness',
        title: 'Practice deep breathing',
        description: '5-minute breathing exercise to calm your nervous system',
        difficulty: 1,
        timeRequired: '5 min',
        icon: Wind,
        color: '#3b82f6',
        status: 'pending'
      },
      {
        id: 3,
        type: 'lifestyle',
        title: 'Plan healthy lunch',
        description: 'Prepare a balanced meal with protein and vegetables',
        difficulty: 3,
        timeRequired: '20 min',
        icon: Heart,
        color: '#f59e0b',
        status: 'pending'
      }
    ];
    setRecommendations(recs);
  }, []);

  const scheduleNotifications = useCallback(() => {
    // Schedule wellness reminders
    const reminders = [
      {
        id: 'hydration',
        title: 'Time for water!',
        message: 'Stay hydrated throughout the day',
        time: '09:00',
        type: 'daily',
        icon: Droplets
      },
      {
        id: 'movement',
        title: 'Move your body',
        message: 'Time for a quick stretch or walk',
        time: '14:00',
        type: 'daily',
        icon: Activity
      },
      {
        id: 'mindfulness',
        title: 'Mindful moment',
        message: 'Take a 3-minute mindful break',
        time: '16:00',
        type: 'daily',
        icon: Brain
      }
    ];
    setNotifications(reminders);
  }, []);

  const setupQuickActions = useCallback(() => {
    // Quick action buttons for common wellness activities
    const actions = [
      {
        id: 'water',
        title: 'Log Water',
        icon: Droplets,
        color: '#3b82f6',
        onPress: () => logWaterIntake()
      },
      {
        id: 'mood',
        title: 'Check Mood',
        icon: Heart,
        color: '#ef4444',
        onPress: () => checkMood()
      },
      {
        id: 'meditation',
        title: 'Quick Meditation',
        icon: Brain,
        color: '#8b5cf6',
        onPress: () => startQuickMeditation()
      },
      {
        id: 'exercise',
        title: 'Log Activity',
        icon: Activity,
        color: '#10b981',
        onPress: () => logActivity()
      }
    ];
    setQuickActions(actions);
  }, []);

  const updateProgress = useCallback((step, value) => {
    setTodayProgress(prev => ({
      ...prev,
      steps: {
        ...prev.steps,
        [step]: { ...prev.steps[step], current: Math.min(value, prev.steps[step].target) }
      },
      wellnessScore: calculateWellnessScore({ ...todayProgress.steps, [step]: value })
    }));

    // Show success feedback
    if (value >= todayProgress.steps[step].target) {
      showAchievementNotification(step);
    }
  }, [todayProgress]);

  const calculateWellnessScore = (steps) => {
    const scores = Object.values(steps).map(step =>
      Math.min((step.current / step.target) * 20, 20) // 20 points max per category
    );
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  const showAchievementNotification = (step) => {
    Vibration.vibrate(1); // 1 second vibration
    Alert.alert(
      '🎉 Great job!',
      `You've completed your ${step.replace('_', ' ')} goal for today!`,
      [{ text: 'OK', style: 'default' }]
    );
  };

  const logWaterIntake = () => {
    // Vibration feedback
    Vibration.vibrate(1);

    // Update progress
    const current = todayProgress.steps.water.current + 1;
    updateProgress('water', current);

    // Show feedback
    Alert.alert(
      '💧 Water logged!',
      `${current} of ${todayProgress.steps.water.target} glasses completed today.`,
      [{ text: 'Keep it up!', style: 'default' }]
    );
  };

  const checkMood = () => {
    // Show mood selection modal
    // This would open a modal for mood rating
    showMoodModal();
  };

  const showMoodModal = () => {
    // Implementation would show a modal with mood options
    // For now, just show a simple rating
    const moods = ['😊', '😐', '😌', '😐', '😊'];
    const selectedMood = '😊'; // Would be selected by user
    Alert.alert(
      'Mood logged',
      `Your mood: ${selectedMood}`,
      [{ text: 'OK', style: 'default' }]
    );
  };

  const startQuickMeditation = () => {
    Vibration.vibrate(1);
    // This would start a short guided meditation
    Alert.alert(
      '🧘 Meditation started',
      '3-minute mindful breathing exercise',
      [{ text: 'I\'m done', style: 'default' }]
    );
  };

  const logActivity = () => {
    // Show activity logging modal
    showActivityModal();
  };

  const showActivityModal = () => {
    // Implementation would show modal for activity selection
    const activities = ['Walking', 'Running', 'Yoga', 'Cycling', 'Swimming', 'Weight Training'];
    const selectedActivity = 'Walking';

    // Update progress (simplified - would log actual duration)
    const currentMinutes = todayProgress.steps.exercise.current + 5;
    updateProgress('exercise', currentMinutes);

    Alert.alert(
      '🏃 Activity logged!',
      `Added 5 minutes of ${selectedActivity}`,
      [{ text: 'Great work!', style: 'default' }]
    );
  };

  const renderDashboard = () => (
    <ScrollView style={styles.dashboardContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Welcome back!</Text>
        <Text style={styles.headerSubtitle}>Let\'s see how you\'re doing today</Text>
        <View style={styles.headerDate}>
          <Text style={styles.headerDateText}>
            {new Date().toLocaleDateString('en-US', { weekday: 'long' })}
          </Text>
          <Text style={styles.headerScoreText}>
            Score: {todayProgress.wellnessScore}
          </Text>
        </View>
      </View>

      {/* Wellness Score Overview */}
      <Animated.View
        style={styles.scoreCard}
        entering={{ opacity: 1, scale: 1.05 }}
        exiting={{ opacity: 1, scale: 1 }}
      >
        <View style={styles.scoreHeader}>
          <Activity size={32} color="#10b981" />
          <Text style={styles.scoreTitle}>Overall Wellness</Text>
          <Text style={styles.scoreValue}>{todayProgress.wellnessScore}/100</Text>
        </View>
        <View style={styles.scoreDetails}>
          <Text style={styles.scoreTrend}>
            {todayProgress.wellnessScore >= 75 ? '📈 Excelling' :
             todayProgress.wellnessScore >= 50 ? '📈 Good' :
             todayProgress.wellnessScore >= 25 ? '📈 Fair' : '📈 Getting Started'}
          </Text>
          <Text style={styles.scoreSubtrend}>
            {todayProgress.streakDays} day streak
          </Text>
        </View>
      </Animated.View>

      {/* Daily Progress */}
      <View style={styles.progressSection}>
        <Text style={styles.sectionTitle}>Today\'s Progress</Text>
        <View style={styles.progressCards}>
          {Object.entries(todayProgress.steps).map(([step, data]) => (
            <Animated.View
              key={step}
              style={[styles.progressCard, {
                borderColor: data.current === data.target ? '#10b981' : '#e5e7eb'
              }]}
              entering={{ opacity: 1, translateY: 0 }}
              exiting={{ opacity: 1, translateY: 10 }}
            >
              <View style={styles.progressHeader}>
                <View style={styles.progressIcon}>
                  {data.icon({ size: 24, color: data.current === data.target ? '#10b981' : '#9ca3af' })}
                </View>
                <View style={styles.progressText}>
                  <Text style={styles.progressTitle}>
                    {step.replace('_', ' ').charAt(0).toUpperCase() + step.slice(1)}
                  </Text>
                  <Text style={progressValue}>
                    {data.current}/{data.target}
                  </Text>
                </View>
              </View>
              <View style={styles.progressBar}>
                <Animated.View
                  style={[
                    styles.progressBarFill,
                    { width: `${(data.current / data.target) * 100}%` },
                    { backgroundColor: data.current === data.target ? '#10b981' : '#e5e7eb'}
                  ]}
                  entering={{ width: `${(data.current / data.target) * 100}%` }}
                />
              </View>
              <TouchableOpacity
                style={[
                  styles.addButton,
                  data.current === data.target ? styles.buttonSuccess : styles.buttonPrimary
                ]}
                onPress={() => quickActionForStep(step, data)}
              >
                <Plus size={16} color="white" />
              </TouchableOpacity>
            </Animated.View>
          ))}
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.quickActionsSection}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActionButtons}>
          {quickActions.map((action) => (
            <TouchableOpacity
              key={action.id}
              style={[styles.quickActionButton, { backgroundColor: action.color }]}
              onPress={action.onPress}
              activeOpacity={0.8}
            >
              <action.icon size={24} color="white" />
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Today's Recommendations */}
      <View style={styles.recommendationsSection}>
        <View style={styles.sectionHeader}>
          <Target size={20} color="#3b82f6" />
          <Text style={styles.sectionTitle}>Today\'s Recommendations</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.recommendationsScroll}>
          {recommendations.slice(0, 3).map((rec) => (
            <View key={rec.id} style={styles.recommendationCard}>
              <View style={[styles.recommendationHeader, { backgroundColor: rec.color }]}>
                <rec.icon size={20} color="white" />
                <Text style={styles.recommendationTitle}>{rec.title}</Text>
              </View>
              <Text style={styles.recommendationDescription}>{rec.description}</Text>
              <View style={styles.recommendationMeta}>
                <Text style={styles.recommendationTime}>{rec.timeRequired}</Text>
                <Text style={[styles.recommendationDifficulty, { backgroundColor: rec.color }]}>
                  {rec.difficulty === 1 ? 'Easy' : rec.difficulty === 2 ? 'Medium' : 'Challenging'}
                </Text>
              </View>
              <TouchableOpacity
                style={[styles.startButton, { backgroundColor: rec.color }]}
                onPress={() => startRecommendation(rec)}
              >
                <ArrowUp size={16} color="white" />
              </TouchableOpacity>
            </View>
          ))}
        </ScrollView>
      </View>

      {/* Notifications */}
      <View style={styles.notificationsSection}>
        <View style={styles.sectionHeader}>
          <Bell size={20} color="#6b7280" />
          <Text style={styles.sectionTitle}>Reminders</Text>
        </View>
        <ScrollView style={styles.notificationsScroll}>
          {notifications.map((notification) => (
            <View key={notification.id} style={styles.notificationCard}>
              <View style={styles.notificationHeader}>
                <notification.icon size={18} color="#3b82f6" />
                <View style={styles.notificationText}>
                  <Text style={styles.notificationTitle}>{notification.title}</Text>
                  <Text style={notificationMessage}>{notification.message}</Text>
                  <Text style={notificationTime}>{notification.time}</Text>
                </View>
              </View>
            </View>
          ))}
        </ScrollView>
      </View>
    </ScrollView>
  );

  const renderRecommendations = () => (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Recommendations</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        {recommendations.map((rec, index) => (
          <Animated.View
            key={rec.id}
            entering={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exiting={{ opacity: 0, y: -20 }}
            style={styles.recommendationFullCard}
          >
            <View style={[styles.recommendationFullHeader, { backgroundColor: rec.color }]}>
              <rec.icon size={24} color="white" />
              <View style={styles.recommendationFullText}>
                <Text style={styles.recommendationFullTitle}>{rec.title}</Text>
                <Text style={styles.recommendationFullDescription}>{rec.description}</Text>
              </View>
            </View>

            <View style={styles.recommendationDetails}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Time Required</Text>
                <Text style={styles.detailValue}>{rec.timeRequired}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={detailLabel => `Difficulty`}>
                  {rec.difficulty === 1 ? 'Easy' : rec.difficulty === 2 ? 'Medium' : 'Challenging'}
                </Text>
                <Text style={styles.detailValue}>
                  {rec.difficulty === 1 ? '•○○○' : rec.difficulty === 2 ? '•●○○' : '•●●●'}
                </Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Impact</Text>
                <Text style={styles.detailValue}>{rec.impact}</Text>
              </View>
            </View>

            <View style={styles.recommendationActions}>
              <TouchableOpacity
                style={[styles.actionButton, styles.dismissButton]}
                onPress={() => dismissRecommendation(rec.id)}
              >
                <X size={16} color="#6b7280" />
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionButton, styles.completeButton, styles.completeSuccessButton]}
                onPress={() => completeRecommendation(rec.id)}
              >
                <Check size={16} color="white" />
              </TouchableOpacity>
            </View>
          </Animated.View>
        ))}
      </ScrollView>
    </ScrollView>
  );
  };

  const renderNotifications = () => (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Bell size={20} color="#6b7280" />
        <Text style={styles.headerTitle}>Wellness Reminders</Text>
      </View>

      <View style={styles.notificationsContainer}>
        {notifications.map((notification) => (
          <View key={notification.id} style={styles.notificationCard}>
            <View style={styles.notificationHeader}>
              <notification.icon size={18} color="#3b82f6" />
              <View style={styles.notificationContent}>
                <Text style={styles.notificationTitle}>{notification.title}</Text>
                <Text style={notificationMessage}>{notification.message}</Text>
                <Text style={notificationTime}>{notification.time}</Text>
              </View>
            </View>
            <View style={styles.notificationActions}>
              <TouchableOpacity style={[styles.notificationButton, styles.dismissButton]}>
                <Text>Dismiss</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.notificationButton, styles.completeButton]}>
                <Text>Complete</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  </ScrollView>
  );

  const renderProfile = () => (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Settings size={20} color="#6b7280" />
        <Text style={styles.headerTitle}>Profile Settings</Text>
      </View>

      <View style={styles.profileContent}>
        <View style={styles.profileSection}>
          <Text style={styles.sectionTitle}>Personal Information</Text>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Name</Text>
              <Text style={styles.profileValue}>Jane Doe</Text>
            </View>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Email</Text>
              <Text style={styles.profileValue}>jane.doe@example.com</Text>
            </View>
          <View style={profileRow}>
            <Text style={profileLabel}>Age</Text>
              <Text style={profileValue}>32 years</Text>
            </View>
        </View>

        <View style={styles.profileSection}>
          <Text style={styles.sectionTitle}>Wellness Goals</Text>
          <View style={styles.profileRow}>
            <Text style={styles.profileLabel}>Primary Focus</Text>
            <Text style={styles.profileValue}>Energy Management</Text>
          </View>
          <View style={profileRow}>
            <Text style={profileLabel}>Secondary Goals</Text>
          </View>
        </View>

        <View style={styles.profileSection}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          <View style={styles.preferencesList}>
            <View style={styles.preferenceItem}>
              <Text style={styles.preferenceLabel}>Daily Reminders</Text>
              <View style={styles.preferenceToggle}>
                <TouchableOpacity
                  style={[styles.toggleButton, styles.toggleActive]}
                  onPress={() => togglePreference('dailyReminders')}
                >
                  <View style={styles.toggleSlider} />
                </TouchableOpacity>
              </View>
            </View>
            <View style={styles.preferenceItem}>
              <Text style={styles.preferencesLabel}>Weekend Insights</Text>
              <View style={styles.preferenceToggle}>
                <TouchableOpacity
                  style={[styles.toggleButton, styles.toggleActive]}
                  onPress={() => togglePreference('weekendInsights')}
                >
                  <View style={styles.toggleSlider} />
                </TouchableOpacity>
              </View>
            </View>
            <View style={preferencesList[0]}>
              <Text style={preferencesLabel}>Smart Notifications</Text>
              <View style={preferencesToggle}>
                <TouchableOpacity
                  style={[styles.toggleButton, styles.toggleActive]}
                  onPress={() => togglePreference('smartNotifications')}
                >
                  <View style={styles.toggleSlider} />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.profileSection}>
          <Text style={styles.sectionTitle}>Connected Services</Text>
          <View style={styles.connectedServices}>
            <View style={styles.serviceItem}>
              <Activity size={20} color="#10b981" />
              <Text style={styles.serviceName}>Apple Health</Text>
              <Text style={styles.serviceStatus}>Connected</Text>
            </View>
            <View style={styles.serviceItem}>
              <Heart size={20} color="#ef4444" />
              <Text style={serviceName}>Fitbit</Text>
              <Text style={serviceStatus}>Connected</Text>
            </View>
            <View style={styles.serviceItem}>
              <Brain size={20} color="#8b5cf6" />
              <Text style={serviceName}>Calm</Text>
              <View style={[styles.serviceStatus, styles.serviceDisconnected]}>
                <Text style={styles.statusText}>Not Connected</Text>
              </View>
            </View>
          </View>
          <TouchableOpacity style={styles.connectServiceButton}>
            <Plus size={16} color="white" />
            <Text style={styles.connectServiceButtonText}>Add Service</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.profileSection}>
        <Text style={styles.sectionTitle}>Privacy & Data</Text>
        <TouchableOpacity style={styles.privacyButton}>
          <Info size={16} color="#6b7280" />
          <Text style={styles.privacyButtonText}>Privacy Policy</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  </ScrollView>
  );

  const quickActionForStep = (step, data) => {
    switch (step) {
      case 'water':
        logWaterIntake();
        break;
      case 'exercise':
        showActivityModal();
        break;
      case 'sleep':
        showSleepModal();
        break;
      case 'nutrition':
        showNutritionModal();
        break;
      case 'mindfulness':
        startQuickMeditation();
        break;
    }
  };

  const dismissRecommendation = (recId) => {
      setRecommendations(prev => prev.filter(rec => rec.id !== recId));
      showFeedbackOptions(recId, 'dismissed');
  };

  const completeRecommendation = (recId) => {
    // Update recommendation status
    setRecommendations(prev =>
      prev.map(rec =>
        rec.id === recId ? { ...rec, status: 'completed' } : rec
      )
    );
    showFeedbackOptions(recId, 'completed');

    // Update progress if applicable
    const rec = recommendations.find(r => r.id === recId);
    if (rec && rec.action) {
      updateProgressForAction(rec.action);
    }
  };

  const showFeedbackOptions = (recId, type) => {
    const feedback = {
      recommendation_id: recId,
      type,
      timestamp: new Date().toISOString(),
      rating: null,
      comments: null
    };

    // Show feedback modal
    Alert.alert(
      'Share Feedback',
      `How did you find this ${type === 'completed' ? 'completed' : 'dismissed'} recommendation?`,
      [
        {
          text: 'Rate 1-5',
          onPress: () => {
            feedback.rating = 5;
            submitFeedback(feedback);
          }
        },
        {
          text: 'Add comment',
          onPress: () => {
            Alert.prompt(
              'Add Comment',
              'Share your thoughts about this recommendation',
              [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Submit', style: 'default' }
              ],
              (buttonIndex) => {
                if (buttonIndex === 1) {
                  feedback.comments = 'Great recommendation!';
                  submitFeedback(feedback);
                }
              }
            );
          }
        },
        {
          text: 'Skip',
          onPress: () => {
            // Just log feedback without storing
            console.log('Feedback skipped');
          }
        }
      ],
      [{ text: 'Cancel', style: 'cancel' }]
    );
  };

  const submitFeedback = (feedback) => {
    // Submit feedback to analytics
    console.log('Feedback submitted:', feedback);
    // In real app, this would send to your backend
  };

  const togglePreference = (preference) => {
    // Handle preference toggle
    console.log(`Toggled ${preference}`);
  };

  const showSleepModal = () => {
    Alert.alert(
      'Sleep Tracker',
      'How would you rate your sleep last night?',
      [
        {
          text: 'Excellent - 8+ hours, restful',
          onPress: () => logSleepRating(5)
        },
        {
          text: 'Good - 6-8 hours, mostly restful',
          onPress: () => logSleepRating(4)
        },
        {
          text: 'Fair - 4-6 hours, some unrest',
          onPress: () => logSleepRating(3)
        },
        {
          text: 'Poor - < 4 hours, very restless',
          onPress: () => logSleepRating(2)
        },
        {
          text: 'Terrible - < 2 hours, very poor quality',
          onPress: () => logSleepRating(1)
        }
      ]
    );
  };

  const logSleepRating = (rating) => {
    // Update sleep data
    const current = rating >= 8 ? 8 : rating; // Cap at 8 hours
    updateProgress('sleep', current);

    Alert.alert(
      '💤 Sleep logged',
      `${current} hours of sleep recorded`,
      [{ text: 'Good job prioritizing rest!', style: 'default' }]
    );
  };

  const showNutritionModal = () => {
    Alert.alert(
      'Nutrition Tracker',
      'How many healthy meals did you have today?',
      [
        { text: '3+ meals', onPress: () => logNutritionMeals(3) },
        { text: '2 meals', onPress: => logNutritionMeals(2) },
        { text: '1 meal', onPress: => logNutritionMeals(1) },
        { text: '0 meals', onPress: () => logNutritionMeals(0) }
      ]
    );
  };

  const logNutritionMeals = (count) => {
    updateProgress('nutrition', count);

    Alert.alert(
      '🥗 Nutrition logged',
      `${count} healthy meals today`,
      [{ text: 'Keep fueling your body!', style: 'default' }]
    );
  };

  const startRecommendation = (recommendation) => {
    // Start the recommendation activity
    showRecommendationModal(recommendation);
  };

  const showRecommendationModal = (recommendation) => {
    Alert.alert(
      recommendation.title,
      `Starting: ${recommendation.description}\n\nTime: ${recommendation.timeRequired}`,
      [
        { text: 'Begin Activity', style: 'default', onPress: () => completeRecommendation(recommendation.id) },
        { text: 'View Details', style: 'cancel', onPress: () => {} }
      ]
    );
  };

  const TabButton = ({ title, icon: Icon, isActive, onPress }) => (
    <TouchableOpacity
      style={[
        styles.tabButton,
        isActive ? styles.activeTab : styles.inactiveTab,
        activeOpacity: isActive ? 1 : 0.7
      ]}
      onPress={onPress}
    >
      <Icon size={20} color={isActive ? '#10b981' : '#6b7280'} />
      <Text style={isActive ? styles.activeTabText : styles.inactiveTabText}>
        {title}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header Tabs */}
      <View style={styles.tabsContainer}>
        <TabButton
          title="Dashboard"
          icon={Activity}
          isActive={activeTab === 'dashboard'}
          onPress={() => setActiveTab('dashboard')}
        />
        <TabButton
          title="Recommendations"
          icon={Target}
          isActive={activeTab === 'recommendations'}
          onPress={() => setActiveTab('recommendations')}
        />
        <TabButton
          title="Reminders"
          icon={Bell}
          isActive={activeTab === 'notifications'}
          onPress={() => setActiveTab('notifications')}
        />
        <TabButton
          title="Profile"
          icon={Settings}
          isActive={activeTab === 'profile'}
          onPress={() => setActiveTab('profile')}
        />
      </View>

      {/* Content based on active tab */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'recommendations' && renderRecommendations()}
      {activeTab === 'notifications' && renderNotifications()}
      {activeTab === 'profile' && renderProfile()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },

  // Header styles
  header: {
    backgroundColor: 'white',
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6b7280',
  },
  headerDate: {
    alignItems: 'flex-start'
  },
  headerDateText: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500'
  },
  headerScoreText: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500'
  },

  // Score card
  scoreCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginHorizontal: 20,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 2
  },
  scoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12
  },
  scoreTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginLeft: 12
  },
  scoreValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#111827',
    marginLeft: 8
  },
  scoreDetails: {
    alignItems: 'center'
  },
  scoreTrend: {
    fontSize: 16,
    color: '#10b981',
    fontWeight: '500'
  },
  scoreSubtrend: {
    fontSize: 14,
    color: '#6b7280'
  },

  // Progress section
  progressSection: {
    marginBottom: 24
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16
  },
  progressCards: {
    gap: 12
  },
  progressCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1
  },
  progressHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8
  },
  progressIcon: {
    justifyContent: 'center'
  },
  progressText: {
    flex: 1,
    marginLeft: 12
  },
  progressTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151'
  },
  progressValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827'
  },
  progressBar: {
    height: 8,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
    marginBottom: 8
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
    width: 0, // Will be animated
  },
  addButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#10b981',
    marginLeft: 8
  },

  // Quick actions
  quickActionsSection: {
    marginBottom: 24
  },
  quickActionButtons: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 20
  },
  quickActionButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6
  },

  // Recommendations
  recommendationsSection: {
    marginBottom: 24
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12
  },
  recommendationsScroll: {
    paddingLeft: 20
  },
  recommendationCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    width: 280,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2
  },
  recommendationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
    flex: 1
  },
  recommendationDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 12
  },
  recommendationMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  recommendationTime: {
    fontSize: 12,
    color: '#6b7280'
  },
  recommendationDifficulty: {
    fontSize: 12,
    color: '#6b7280',
    fontWeight: '500',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    paddingVertical: 8,
    borderRadius: 8,
    elevation: 2
  },

  // Full recommendation card
  recommendationFullCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginHorizontal: 20,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4
  },
  recommendationFullHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16
  },
  recommendationFullText: {
    flex: 1,
    marginLeft: 12
  },
  recommendationFullTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginBottom: 4
  },
  recommendationFullDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)'
  },
  },
  recommendationDetails: {
    marginBottom: 16
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8
  },
  detailLabel: {
    fontSize: 14,
    color: '#6b7280',
    flex: 1
  },
  detailValue: {
    fontSize: 14,
    color: '#111827'
  },
  recommendationActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12
  },
  actionButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    alignItems: 'center',
    justifyContent: 'center'
  },
  dismissButton: {
    backgroundColor: '#ef4444',
    borderWidth: 1,
    borderColor: '#ef4444'
  },
  completeButton: {
    backgroundColor: '#10b981',
    borderWidth: 1,
    borderColor: '#10b981'
  },
  buttonSuccessButton: {
    backgroundColor: '#059669'
  },

  // Notifications
  notificationsSection: {
    marginBottom: 24
  },
  notificationsContainer: {
    gap: 12
  },
  notificationsScroll: {
    paddingLeft: 20
  },
  notificationCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8
  },
  notificationContent: {
    flex: 1,
    marginLeft: 12
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4
  },
  notificationMessage: {
      fontSize: 14,
      color: '#6b7280',
      marginBottom: 4
  },
  notificationTime: {
    fontSize: 12,
    color: '#6b7280'
  },
  notificationActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12
  },
  notificationButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb'
  },
  dismissButton: {
    backgroundColor: '#6b7280',
    borderWidth: 1,
    borderColor: '#6b7280'
  },
  completeButton: {
    backgroundColor: '#10b981',
    borderWidth: 1,
    borderColor: '#10b981'
  },

  // Profile styles
  profileContent: {
    gap: 24
    paddingHorizontal: 20
  },
  profileSection: {
    marginBottom: 24
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16
  },
  profileRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  profileLabel: {
    fontSize: 14,
    color: '#6b7280',
    flex: 1
  },
  profileValue: {
    fontSize: 16,
    color: '#111827',
    textAlign: 'right'
  },
  preferencesList: {
    gap: 16
  },
  preferenceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  preferenceLabel: {
    fontSize: 14,
    color: '#6b7280',
    flex: 1
  },
  preferenceToggle: {
    marginLeft: 'auto'
  },
  toggleButton: {
    width: 48,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#e5e7eb',
    borderWidth: 1,
    borderColor: '#d1d5db',
    alignItems: 'center',
    justifyContent: 'center'
  },
  toggleSlider: {
    width: 24,
    height: 12,
    backgroundColor: '#3b82f6',
    borderRadius: 6,
  },
  toggleActive: {
    backgroundColor: '#3b82f6'
  },
  toggleInactive: {
    backgroundColor: '#e5e7eb'
  },
  toggleSliderActive: {
    backgroundColor: '#3b82f6'
  },

  // Connected services
  connectedServices: {
    marginBottom: 24
  },
  serviceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    padding: 16,
    backgroundColor: 'white',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb'
  },
  serviceName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginLeft: 12,
    flex: 1
  },
  serviceStatus: {
    fontSize: 12,
    color: '#6b7280'
  },
  serviceDisconnected: {
      color: '#ef4444'
  },
  connectServiceButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#10b981',
    borderRadius: 8,
    gap: 4
  },
  connectServiceButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '500'
  },

  // Privacy
  privacyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    backgroundColor: 'white',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb'
  },
  privacyButtonText: {
    color: '#6b7280',
    fontSize: 14,
    fontWeight: '500'
  },

  // Tab navigation
  tabsContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    backgroundColor: 'white',
    paddingHorizontal: 20
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
      borderBottomColor: '#10b981'
  },
  inactiveTab: {
      borderBottomColor: 'transparent'
  },
  activeTabText: {
    color: '#10b981',
    fontWeight: '600'
  },
  inactiveTabText: {
    color: '#6b7280'
  },
  activeOpacity: 1,
  inactiveOpacity: 0.7
  },

  // Button styles
  buttonPrimary: {
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    color: 'white',
    fontWeight: '500'
  },
  buttonSuccess: {
    backgroundColor: '#10b981',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    color: 'white',
    fontWeight: '500'
  }
});

export default WellnessTrackerMobile;