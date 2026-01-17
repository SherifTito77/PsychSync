/**
 * API wrapper for Wellness Recommendation Engine
 * Provides RESTful endpoints for generating and managing wellness recommendations
 */

const express = require('express');
const cors = require('cors');
const WellnessRecommendationEngine = require('./WellnessRecommendationEngine');

class RecommendationEngineAPI {
  constructor() {
    this.app = express();
    this.engine = new WellnessRecommendationEngine();
    this.setupMiddleware();
    this.setupRoutes();
    this.userRecommendations = new Map(); // In-memory storage (use database in production)
  }

  setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
      next();
    });

    // Error handling
    this.app.use((err, req, res, next) => {
      console.error('Error:', err);
      res.status(500).json({
        success: false,
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
      });
    });
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'Wellness Recommendation Engine',
        version: '1.0.0'
      });
    });

    // Generate recommendations based on assessment data
    this.app.post('/recommendations/generate', this.generateRecommendations.bind(this));

    // Get user's current recommendations
    this.app.get('/recommendations/:userId', this.getUserRecommendations.bind(this));

    // Update recommendation feedback
    this.app.post('/recommendations/:userId/feedback', this.updateRecommendationFeedback.bind(this));

    // Track recommendation progress
    this.app.post('/recommendations/:userId/progress', this.trackRecommendationProgress.bind(this));

    // Get recommendation analytics
    this.app.get('/recommendations/:userId/analytics', this.getRecommendationAnalytics.bind(this));

    // Update user profile
    this.app.put('/users/:userId/profile', this.updateUserProfile.bind(this));

    // Get domain-specific recommendations
    this.app.get('/recommendations/:userId/domain/:domain', this.getDomainRecommendations.bind(this));

    // Get recommendation categories
    this.app.get('/recommendations/:userId/category/:category', this.getCategoryRecommendations.bind(this));

    // Search recommendations
    this.app.get('/recommendations/search', this.searchRecommendations.bind(this));
  }

  async generateRecommendations(req, res) {
    try {
      const { assessmentData, userProfile = {}, userId } = req.body;

      if (!assessmentData) {
        return res.status(400).json({
          success: false,
          error: 'Assessment data is required'
        });
      }

      // Generate personalized recommendations
      const recommendations = this.engine.generateRecommendations(assessmentData, userProfile);

      // Store recommendations if userId provided
      if (userId) {
        this.userRecommendations.set(userId, {
          recommendations,
          generatedAt: new Date().toISOString(),
          assessmentData: this.sanitizeAssessmentData(assessmentData),
          userProfile: userProfile,
          feedback: {},
          progress: {}
        });
      }

      res.json({
        success: true,
        data: {
          recommendations,
          personalizedInsights: recommendations.personalizedInsights,
          successFactors: recommendations.successFactors,
          potentialBarriers: recommendations.potentialBarriers,
          expectedTimeline: recommendations.expectedTimeline
        }
      });
    } catch (error) {
      console.error('Error generating recommendations:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to generate recommendations'
      });
    }
  }

  async getUserRecommendations(req, res) {
    try {
      const { userId } = req.params;
      const userRecs = this.userRecommendations.get(userId);

      if (!userRecs) {
        return res.status(404).json({
          success: false,
          error: 'No recommendations found for this user'
        });
      }

      res.json({
        success: true,
        data: {
          recommendations: userRecs.recommendations,
          generatedAt: userRecs.generatedAt,
          personalizedInsights: userRecs.recommendations.personalizedInsights,
          feedback: userRecs.feedback,
          progress: userRecs.progress
        }
      });
    } catch (error) {
      console.error('Error getting user recommendations:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve recommendations'
      });
    }
  }

  async updateRecommendationFeedback(req, res) {
    try {
      const { userId } = req.params;
      const { recommendationId, feedback, rating, comments } = req.body;

      const userRecs = this.userRecommendations.get(userId);
      if (!userRecs) {
        return res.status(404).json({
          success: false,
          error: 'No recommendations found for this user'
        });
      }

      // Store feedback
      userRecs.feedback[recommendationId] = {
        feedback,
        rating,
        comments,
        timestamp: new Date().toISOString()
      };

      // Update recommendations based on feedback (adaptive learning)
      const updatedRecommendations = this.adaptRecommendationsBasedOnFeedback(
        userRecs.recommendations,
        recommendationId,
        feedback
      );

      userRecs.recommendations = updatedRecommendations;

      res.json({
        success: true,
        message: 'Feedback recorded successfully',
        data: {
          updatedRecommendations: updatedRecommendations
        }
      });
    } catch (error) {
      console.error('Error updating feedback:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to update feedback'
      });
    }
  }

  async trackRecommendationProgress(req, res) {
    try {
      const { userId } = req.params;
      const { recommendationId, status, progress, notes } = req.body;

      const userRecs = this.userRecommendations.get(userId);
      if (!userRecs) {
        return res.status(404).json({
          success: false,
          error: 'No recommendations found for this user'
        });
      }

      // Track progress
      if (!userRecs.progress[recommendationId]) {
        userRecs.progress[recommendationId] = [];
      }

      userRecs.progress[recommendationId].push({
        status, // 'started', 'completed', 'skipped', 'paused'
        progress, // 0-100
        notes,
        timestamp: new Date().toISOString()
      });

      // Generate adaptive next steps based on progress
      const nextSteps = this.generateNextSteps(userRecs.recommendations, userRecs.progress);

      res.json({
        success: true,
        message: 'Progress tracked successfully',
        data: {
          nextSteps,
          overallProgress: this.calculateOverallProgress(userRecs.progress)
        }
      });
    } catch (error) {
      console.error('Error tracking progress:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to track progress'
      });
    }
  }

  async getRecommendationAnalytics(req, res) {
    try {
      const { userId } = req.params;
      const { timeRange = '30days' } = req.query;

      const userRecs = this.userRecommendations.get(userId);
      if (!userRecs) {
        return res.status(404).json({
          success: false,
          error: 'No recommendations found for this user'
        });
      }

      const analytics = {
        completionRate: this.calculateCompletionRate(userRecs.progress),
        categoryEngagement: this.calculateCategoryEngagement(userRecs),
        timeSpent: this.calculateTimeSpent(userRecs.progress),
        favoriteDomains: this.getFavoriteDomains(userRecs.feedback),
        improvementAreas: this.getImprovementAreas(userRecs.progress, userRecs.feedback),
        predictedSuccess: this.predictSuccessProbability(userRecs),
        trends: this.calculateRecommendationTrends(userRecs, timeRange)
      };

      res.json({
        success: true,
        data: analytics
      });
    } catch (error) {
      console.error('Error getting analytics:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to generate analytics'
      });
    }
  }

  async updateUserProfile(req, res) {
    try {
      const { userId } = req.params;
      const userProfile = req.body;

      const userRecs = this.userRecommendations.get(userId);
      if (userRecs) {
        userRecs.userProfile = { ...userRecs.userProfile, ...userProfile };
      }

      // Re-generate recommendations with updated profile
      const updatedRecommendations = this.engine.generateRecommendations(
        userRecs.assessmentData,
        userRecs.userProfile
      );

      if (userRecs) {
        userRecs.recommendations = updatedRecommendations;
      }

      res.json({
        success: true,
        message: 'Profile updated successfully',
        data: {
          updatedRecommendations
        }
      });
    } catch (error) {
      console.error('Error updating profile:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to update profile'
      });
    }
  }

  async getDomainRecommendations(req, res) {
    try {
      const { userId, domain } = req.params;
      const { limit = 10 } = req.query;

      const userRecs = this.userRecommendations.get(userId);
      if (!userRecs) {
        return res.status(404).json({
          success: false,
          error: 'No recommendations found for this user'
        });
      }

      const domainRecommendations = userRecs.recommendations[domain] || [];
      const limitedRecommendations = domainRecommendations.slice(0, parseInt(limit));

      res.json({
        success: true,
        data: {
          domain,
          recommendations: limitedRecommendations,
          total: domainRecommendations.length
        }
      });
    } catch (error) {
      console.error('Error getting domain recommendations:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get domain recommendations'
      });
    }
  }

  async getCategoryRecommendations(req, res) {
    try {
      const { userId, category } = req.params;

      const userRecs = this.userRecommendations.get(userId);
      if (!userRecs) {
        return res.status(404).json({
          success: false,
          error: 'No recommendations found for this user'
        });
      }

      const categoryRecommendations = Object.values(userRecs.recommendations)
        .flat()
        .filter(rec => rec.category === category);

      res.json({
        success: true,
        data: {
          category,
          recommendations: categoryRecommendations
        }
      });
    } catch (error) {
      console.error('Error getting category recommendations:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to get category recommendations'
      });
    }
  }

  async searchRecommendations(req, res) {
    try {
      const { query, userId, category, domain, difficulty } = req.query;

      let recommendations = [];

      if (userId) {
        const userRecs = this.userRecommendations.get(userId);
        if (userRecs) {
          recommendations = Object.values(userRecs.recommendations).flat();
        }
      } else {
        // Return all available recommendations
        recommendations = this.getAllAvailableRecommendations();
      }

      // Apply filters
      if (category) {
        recommendations = recommendations.filter(rec => rec.category === category);
      }
      if (domain) {
        recommendations = recommendations.filter(rec => rec.domain === domain);
      }
      if (difficulty) {
        recommendations = recommendations.filter(rec => rec.difficulty <= parseInt(difficulty));
      }
      if (query) {
        recommendations = recommendations.filter(rec =>
          rec.action.toLowerCase().includes(query.toLowerCase()) ||
          rec.why.toLowerCase().includes(query.toLowerCase())
        );
      }

      res.json({
        success: true,
        data: {
          query: req.query,
          recommendations,
          total: recommendations.length
        }
      });
    } catch (error) {
      console.error('Error searching recommendations:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to search recommendations'
      });
    }
  }

  // Helper methods
  sanitizeAssessmentData(assessmentData) {
    // Remove sensitive information and clean up assessment data
    const sanitized = {};
    Object.keys(assessmentData).forEach(key => {
      if (typeof assessmentData[key] === 'number') {
        sanitized[key] = Math.min(100, Math.max(0, assessmentData[key])); // Ensure 0-100 range
      } else if (typeof assessmentData[key] === 'object') {
        sanitized[key] = assessmentData[key];
      }
    });
    return sanitized;
  }

  adaptRecommendationsBasedOnFeedback(recommendations, recommendationId, feedback) {
    // Adaptive learning based on user feedback
    const adapted = { ...recommendations };

    // If user disliked a recommendation, remove or replace similar ones
    if (feedback === 'disliked' || (feedback.rating && feedback.rating < 3)) {
      adapted.immediate = adapted.immediate.filter(rec => rec.id !== recommendationId);
      adapted.weekly = adapted.weekly.filter(rec => rec.id !== recommendationId);
      adapted.monthly = adapted.monthly.filter(rec => rec.id !== recommendationId);
    }

    return adapted;
  }

  generateNextSteps(recommendations, progress) {
    const nextSteps = [];
    const completed = Object.keys(progress).filter(key =>
      progress[key].some(p => p.status === 'completed')
    );

    if (completed.length >= 3) {
      nextSteps.push({
        type: 'milestone',
        title: 'Great progress!',
        message: 'You\'ve completed several recommendations. Consider moving to more advanced habits.',
        action: 'Review and update your wellness goals'
      });
    }

    // Add more next step logic...
    return nextSteps;
  }

  calculateOverallProgress(progress) {
    const totalActions = Object.keys(progress).length;
    if (totalActions === 0) return 0;

    const completedActions = Object.values(progress).filter(actions =>
      actions.some(p => p.status === 'completed')
    ).length;

    return Math.round((completedActions / totalActions) * 100);
  }

  calculateCompletionRate(progress) {
    return this.calculateOverallProgress(progress);
  }

  calculateCategoryEngagement(recommendations) {
    // Calculate engagement by recommendation category
    const engagement = {};

    ['immediate', 'weekly', 'monthly'].forEach(category => {
      const categoryRecs = Object.values(recommendations).flat()
        .filter(rec => rec.category === category);

      engagement[category] = {
        total: categoryRecs.length,
        attempted: 0,
        completed: 0,
        rate: 0
      };
    });

    return engagement;
  }

  calculateTimeSpent(progress) {
    // Estimate time spent based on progress tracking
    let totalTime = 0;

    Object.values(progress).forEach(actions => {
      actions.forEach(action => {
        if (action.status === 'completed') {
          totalTime += 10; // Assume 10 minutes per completed action
        }
      });
    });

    return totalTime;
  }

  getFavoriteDomains(feedback) {
    // Analyze feedback to determine favorite domains
    const domainRatings = {};

    Object.entries(feedback).forEach(([recId, feedback]) => {
      if (feedback.domain) {
        if (!domainRatings[feedback.domain]) {
          domainRatings[feedback.domain] = { ratings: [], total: 0 };
        }
        domainRatings[feedback.domain].ratings.push(feedback.rating || 5);
        domainRatings[feedback.domain].total++;
      }
    });

    // Calculate average ratings and return sorted domains
    Object.keys(domainRatings).forEach(domain => {
      const domainData = domainRatings[domain];
      domainData.average = domainData.ratings.reduce((a, b) => a + b, 0) / domainData.ratings.length;
    });

    return Object.entries(domainRatings)
      .sort(([, a], [, b]) => b.average - a.average)
      .slice(0, 3)
      .map(([domain, data]) => ({
        domain,
        averageRating: data.average,
        totalRatings: data.total
      }));
  }

  getImprovementAreas(progress, feedback) {
    // Identify areas where user is struggling or not making progress
    const improvementAreas = [];

    Object.entries(progress).forEach(([recId, actions]) => {
      const skipped = actions.filter(a => a.status === 'skipped');
      const failed = actions.filter(a => a.status === 'paused');

      if (skipped.length > 0 || failed.length > 0) {
        improvementAreas.push({
          recommendationId: recId,
          skippedCount: skipped.length,
          failedCount: failed.length,
          totalAttempts: actions.length
        });
      }
    });

    return improvementAreas;
  }

  predictSuccessProbability(userRecs) {
    // Predict likelihood of success based on current patterns
    let probability = 70; // Base probability

    // Adjust based on completion rate
    const completionRate = this.calculateCompletionRate(userRecs.progress);
    probability += (completionRate - 50) * 0.5;

    // Adjust based on feedback sentiment
    const averageRating = this.calculateAverageFeedbackRating(userRecs.feedback);
    probability += (averageRating - 3) * 10;

    return Math.min(95, Math.max(25, Math.round(probability)));
  }

  calculateAverageFeedbackRating(feedback) {
    const ratings = Object.values(feedback)
      .map(f => f.rating)
      .filter(r => r !== undefined);

    if (ratings.length === 0) return 3;
    return ratings.reduce((a, b) => a + b, 0) / ratings.length;
  }

  calculateRecommendationTrends(userRecs, timeRange) {
    // Calculate trends over time
    // Implementation would analyze historical data
    return {
      improvementTrend: 'increasing',
      categoryTrends: {
        immediate: 'stable',
        weekly: 'increasing',
        monthly: 'stable'
      }
    };
  }

  getAllAvailableRecommendations() {
    // Return all available recommendation templates
    return this.engine.getAllRecommendationTemplates();
  }

  startServer(port = 3000) {
    this.app.listen(port, () => {
      console.log(`Wellness Recommendation Engine API running on port ${port}`);
      console.log(`Health check: http://localhost:${port}/health`);
    });
  }
}

module.exports = RecommendationEngineAPI;
