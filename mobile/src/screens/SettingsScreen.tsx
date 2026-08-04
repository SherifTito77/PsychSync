/**
 * Settings Screen for PsychSync Mobile
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Switch,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { notificationService } from '../services/notifications';
import { apiService } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';

interface Props {
  onLogout?: () => void;
}

export const SettingsScreen: React.FC<Props> = ({ onLogout }) => {
  const { isDark, toggleTheme, theme } = useTheme();
  const [notificationsEnabled, setNotificationsEnabled] = React.useState(false); // Disabled by default on web
  const [autoRefreshEnabled, setAutoRefreshEnabled] = React.useState(true);

  const handleNotificationToggle = async (value: boolean) => {
    // Skip notification setup on web platform
    if (Platform.OS === 'web') {
      console.log('Push notifications not supported on web');
      setNotificationsEnabled(false);
      return;
    }

    setNotificationsEnabled(value);
    if (value) {
      await notificationService.registerForPushNotifications();
    } else {
      await notificationService.cancelAllNotifications();
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await apiService.logout();
            onLogout?.();
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={[styles.header, { backgroundColor: theme.backgroundSecondary, borderBottomColor: theme.border }]}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Settings</Text>
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Notifications Section - Hide on web */}
        {Platform.OS !== 'web' && (
          <View style={[styles.section, { backgroundColor: theme.backgroundSecondary, borderTopColor: theme.border, borderBottomColor: theme.border }]}>
            <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Notifications</Text>

            <View style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Text style={[styles.settingLabel, { color: theme.text }]}>Push Notifications</Text>
                <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                  Receive alerts for critical email activity
                </Text>
              </View>
              <Switch
                value={notificationsEnabled}
                onValueChange={handleNotificationToggle}
                trackColor={{ false: theme.border, true: theme.primary }}
              />
            </View>

            <View style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <Text style={[styles.settingLabel, { color: theme.text }]}>Critical Alerts Only</Text>
                <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                  Only notify for high-severity events
                </Text>
              </View>
              <Switch
                value={false}
                onValueChange={() => {}}
                trackColor={{ false: theme.border, true: theme.primary }}
              />
            </View>
          </View>
        )}

        {/* Data Section */}
        <View style={[styles.section, { backgroundColor: theme.backgroundSecondary, borderTopColor: theme.border, borderBottomColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Data & Sync</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: theme.text }]}>Auto-Refresh</Text>
              <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                Automatically refresh data every 30 seconds
              </Text>
            </View>
            <Switch
              value={autoRefreshEnabled}
              onValueChange={setAutoRefreshEnabled}
              trackColor={{ false: theme.border, true: theme.primary }}
            />
          </View>

          <TouchableOpacity style={[styles.actionButton, { backgroundColor: theme.background, borderColor: theme.border }]}>
            <Text style={[styles.actionButtonText, { color: theme.primary }]}>Clear Cache</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.actionButton, { backgroundColor: theme.background, borderColor: theme.border }]}>
            <Text style={[styles.actionButtonText, { color: theme.primary }]}>Sync All Accounts</Text>
          </TouchableOpacity>
        </View>

        {/* Appearance Section */}
        <View style={[styles.section, { backgroundColor: theme.backgroundSecondary, borderTopColor: theme.border, borderBottomColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Appearance</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: theme.text }]}>Dark Mode</Text>
              <Text style={[styles.settingDescription, { color: theme.textSecondary }]}>
                Switch to dark theme
              </Text>
            </View>
            <Switch
              value={isDark}
              onValueChange={toggleTheme}
              trackColor={{ false: theme.border, true: theme.primary }}
            />
          </View>
        </View>

        {/* About Section */}
        <View style={[styles.section, { backgroundColor: theme.backgroundSecondary, borderTopColor: theme.border, borderBottomColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>About</Text>

          <View style={[styles.infoItem, { borderBottomColor: theme.borderLight }]}>
            <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Version</Text>
            <Text style={[styles.infoValue, { color: theme.text }]}>1.0.0</Text>
          </View>

          <View style={[styles.infoItem, { borderBottomColor: theme.borderLight }]}>
            <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Build</Text>
            <Text style={[styles.infoValue, { color: theme.text }]}>2026.01.23</Text>
          </View>

          <TouchableOpacity style={[styles.linkButton, { borderBottomColor: theme.borderLight }]}>
            <Text style={[styles.linkButtonText, { color: theme.primary }]}>Privacy Policy</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.linkButton, { borderBottomColor: theme.borderLight }]}>
            <Text style={[styles.linkButtonText, { color: theme.primary }]}>Terms of Service</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.linkButton, { borderBottomColor: theme.borderLight }]}>
            <Text style={[styles.linkButtonText, { color: theme.primary }]}>GitHub Repository</Text>
          </TouchableOpacity>
        </View>

        {/* Logout Button */}
        {onLogout && (
          <View style={styles.section}>
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
              <Text style={styles.logoutButtonText}>Sign Out</Text>
            </TouchableOpacity>
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
  header: {
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
  scrollView: {
    flex: 1,
  },
  section: {
    backgroundColor: '#ffffff',
    marginTop: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 1,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  settingInfo: {
    flex: 1,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#111827',
  },
  settingDescription: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  actionButton: {
    backgroundColor: '#f9fafb',
    marginHorizontal: 16,
    marginTop: 8,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  actionButtonText: {
    color: '#3b82f6',
    fontSize: 14,
    fontWeight: '600',
  },
  infoItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  infoLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  infoValue: {
    fontSize: 14,
    color: '#111827',
    fontWeight: '500',
  },
  linkButton: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  linkButtonText: {
    fontSize: 14,
    color: '#3b82f6',
  },
  logoutButton: {
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 16,
    backgroundColor: '#ef4444',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  logoutButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
