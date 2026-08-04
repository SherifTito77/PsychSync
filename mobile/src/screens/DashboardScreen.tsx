/**
 * Email Monitoring Dashboard Screen for Mobile
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { apiService } from '../services/api';
import { notificationService } from '../services/notifications';
import { MonitoringStats, CategoryData } from '../types';

const { width } = Dimensions.get('window');

export const DashboardScreen: React.FC = () => {
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [unreadAlerts, setUnreadAlerts] = useState(0);

  const fetchData = useCallback(async () => {
    try {
      const response = await apiService.getMonitoringStats();

      if (response.success && response.data) {
        setStats(response.data);

        // Count unread alerts
        const unread = response.data.alerts?.filter((a) => !a.read).length || 0;
        setUnreadAlerts(unread);

        // Show notification for critical alerts
        const criticalAlerts = response.data.alerts?.filter(
          (a) => !a.read && a.severity === 'critical'
        );

        if (criticalAlerts && criticalAlerts.length > 0) {
          await notificationService.showLocalNotification(
            'Critical Email Alert',
            criticalAlerts[0].message
          );
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to fetch monitoring data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchData();
  }, [fetchData]);

  const getCategoryData = (): CategoryData[] => {
    if (!stats || !stats.categories) return [];

    const total = Object.values(stats.categories).reduce((a, b) => a + b, 0);
    const colors = {
      security: '#ef4444',
      financial: '#22c55e',
      professional: '#3b82f6',
      social: '#f59e0b',
      promotional: '#8b5cf6',
      other: '#6b7280',
    };

    return Object.entries(stats.categories)
      .map(([category, count]) => ({
        category,
        count,
        percentage: total > 0 ? (count / total) * 100 : 0,
        color: colors[category as keyof typeof colors] || colors.other,
      }))
      .sort((a, b) => b.count - a.count);
  };

  const getSecurityLevelColor = (level: string): string => {
    switch (level) {
      case 'high':
        return '#22c55e';
      case 'medium':
        return '#f59e0b';
      case 'low':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <Text style={styles.loadingText}>Loading email analytics...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!stats) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <Text style={styles.errorText}>No data available</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchData}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const categoryData = getCategoryData();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.headerTitle}>Email Monitoring</Text>
            <Text style={styles.headerSubtitle}>
              Last updated: {new Date(stats.generated_at).toLocaleTimeString()}
            </Text>
          </View>
          {unreadAlerts > 0 && (
            <View style={styles.alertBadge}>
              <Text style={styles.alertBadgeText}>{unreadAlerts}</Text>
            </View>
          )}
        </View>

        {/* Main Stats */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.total_emails.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Total Emails</Text>
          </View>

          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.emails_last_24h}</Text>
            <Text style={styles.statLabel}>Last 24h</Text>
          </View>

          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.emails_last_week}</Text>
            <Text style={styles.statLabel}>Last 7 Days</Text>
          </View>

          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.emails_last_hour}</Text>
            <Text style={styles.statLabel}>Last Hour</Text>
          </View>
        </View>

        {/* Categories */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Email Categories</Text>
          <View style={styles.categoryList}>
            {categoryData.map((cat) => (
              <View key={cat.category} style={styles.categoryItem}>
                <View style={styles.categoryInfo}>
                  <View
                    style={[
                      styles.categoryIndicator,
                      { backgroundColor: cat.color },
                    ]}
                  />
                  <Text style={styles.categoryName}>
                    {cat.category.charAt(0).toUpperCase() + cat.category.slice(1)}
                  </Text>
                </View>
                <View style={styles.categoryStats}>
                  <Text style={styles.categoryCount}>{cat.count}</Text>
                  <Text style={styles.categoryPercentage}>
                    {cat.percentage.toFixed(1)}%
                  </Text>
                </View>
                <View style={styles.categoryBar}>
                  <View
                    style={[
                      styles.categoryBarFill,
                      {
                        backgroundColor: cat.color,
                        width: `${cat.percentage}%`,
                      },
                    ]}
                  />
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* Behavioral Insights */}
        {stats.behavioral_insights && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Behavioral Insights</Text>
            <View style={styles.insightsGrid}>
              <View style={styles.insightCard}>
                <Text style={styles.insightLabel}>Security</Text>
                <Text
                  style={[
                    styles.insightValue,
                    {
                      color: getSecurityLevelColor(
                        stats.behavioral_insights.security_consciousness || 'medium'
                      ),
                    },
                  ]}
                >
                  {(stats.behavioral_insights.security_consciousness || 'medium').toUpperCase()}
                </Text>
              </View>

              <View style={styles.insightCard}>
                <Text style={styles.insightLabel}>Financial</Text>
                <Text
                  style={[
                    styles.insightValue,
                    {
                      color: getSecurityLevelColor(
                        stats.behavioral_insights.financial_activity || 'medium'
                      ),
                    },
                  ]}
                >
                  {(stats.behavioral_insights.financial_activity || 'medium').toUpperCase()}
                </Text>
              </View>

              <View style={styles.insightCard}>
                <Text style={styles.insightLabel}>Professional</Text>
                <Text
                  style={[
                    styles.insightValue,
                    {
                      color: getSecurityLevelColor(
                        stats.behavioral_insights.professional_engagement || 'medium'
                      ),
                    },
                  ]}
                >
                  {(stats.behavioral_insights.professional_engagement || 'medium').toUpperCase()}
                </Text>
              </View>

              <View style={styles.insightCard}>
                <Text style={styles.insightLabel}>Social</Text>
                <Text
                  style={[
                    styles.insightValue,
                    {
                      color: getSecurityLevelColor(
                        stats.behavioral_insights.social_activity || 'medium'
                      ),
                    },
                  ]}
                >
                  {(stats.behavioral_insights.social_activity || 'medium').toUpperCase()}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Recent Alerts */}
        {stats.alerts && stats.alerts.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recent Alerts</Text>
            {stats.alerts.slice(0, 3).map((alert) => (
              <View
                key={alert.id}
                style={[
                  styles.alertCard,
                  {
                    borderLeftColor:
                      alert.severity === 'critical'
                        ? '#ef4444'
                        : alert.severity === 'high'
                        ? '#f59e0b'
                        : '#3b82f6',
                  },
                ]}
              >
                <View style={styles.alertHeader}>
                  <Text style={styles.alertType}>{alert.type}</Text>
                  <Text style={styles.alertSeverity}>{alert.severity}</Text>
                </View>
                <Text style={styles.alertMessage}>{alert.message}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Recommendations */}
        {stats.behavioral_insights?.recommendations && stats.behavioral_insights.recommendations.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recommendations</Text>
            {stats.behavioral_insights.recommendations.map((rec, idx) => (
              <View key={idx} style={styles.recommendationItem}>
                <Text style={styles.bullet}>•</Text>
                <Text style={styles.recommendationText}>{rec}</Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
  },
  errorText: {
    fontSize: 16,
    color: '#ef4444',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  alertBadge: {
    backgroundColor: '#ef4444',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    minWidth: 24,
    alignItems: 'center',
  },
  alertBadgeText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  statCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  categoryList: {
    gap: 12,
  },
  categoryItem: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  categoryInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryIndicator: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginRight: 8,
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  categoryStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  categoryCount: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  categoryPercentage: {
    fontSize: 14,
    color: '#6b7280',
  },
  categoryBar: {
    height: 8,
    backgroundColor: '#f3f4f6',
    borderRadius: 4,
    overflow: 'hidden',
  },
  categoryBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  insightsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  insightCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    width: (width - 56) / 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  insightLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  insightValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  alertCard: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  alertType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  alertSeverity: {
    fontSize: 12,
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  alertMessage: {
    fontSize: 12,
    color: '#4b5563',
  },
  recommendationItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  bullet: {
    fontSize: 16,
    color: '#3b82f6',
    marginRight: 8,
  },
  recommendationText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
});
