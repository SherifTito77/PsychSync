/**
 * Email Connections Management Screen
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { apiService } from '../services/api';
import { EmailConnection } from '../types';
import { AddEmailConnectionModal } from '../components/AddEmailConnectionModal';

export const ConnectionsScreen: React.FC = () => {
  const [connections, setConnections] = useState<EmailConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await apiService.getEmailConnections();
      if (response.success && response.data) {
        // Ensure response.data is an array before setting
        setConnections(Array.isArray(response.data) ? response.data : []);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to fetch connections');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (connectionId: number) => {
    setSyncing(connectionId);
    try {
      const response = await apiService.syncEmailConnection(connectionId);
      if (response.success) {
        Alert.alert('Success', 'Email sync completed');
        await fetchConnections();
      } else {
        Alert.alert('Error', response.error || 'Sync failed');
      }
    } catch (error) {
      Alert.alert('Error', 'Sync failed');
    } finally {
      setSyncing(null);
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'ACTIVE':
        return '#22c55e';
      case 'ERROR':
        return '#ef4444';
      case 'INACTIVE':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const getProviderIcon = (provider: string): string => {
    switch (provider) {
      case 'GMAIL':
        return '📧';
      case 'IMAP':
        return '📨';
      case 'OUTLOOK':
        return '🔷';
      default:
        return '📬';
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text style={styles.loadingText}>Loading connections...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Email Connections</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setShowAddModal(true)}>
          <Text style={styles.addButtonText}>+ Add New</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView}>
        {!Array.isArray(connections) || connections.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📧</Text>
            <Text style={styles.emptyTitle}>No Connections</Text>
            <Text style={styles.emptyText}>
              Connect your email accounts to start monitoring
            </Text>
          </View>
        ) : (
          connections.map((connection) => (
            <View key={connection.id} style={styles.connectionCard}>
              <View style={styles.connectionHeader}>
                <View style={styles.connectionInfo}>
                  <Text style={styles.providerIcon}>
                    {getProviderIcon(connection.provider)}
                  </Text>
                  <View>
                    <Text style={styles.emailAddress}>
                      {connection.email_address}
                    </Text>
                    <Text style={styles.providerText}>
                      {connection.provider}
                    </Text>
                  </View>
                </View>
                <View
                  style={[
                    styles.statusBadge,
                    { backgroundColor: getStatusColor(connection.connection_status) },
                  ]}
                >
                  <Text style={styles.statusText}>
                    {connection.connection_status}
                  </Text>
                </View>
              </View>

              <View style={styles.connectionDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Connected:</Text>
                  <Text style={styles.detailValue}>
                    {new Date(connection.created_at).toLocaleDateString()}
                  </Text>
                </View>
                {connection.last_sync && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>Last Sync:</Text>
                    <Text style={styles.detailValue}>
                      {new Date(connection.last_sync).toLocaleString()}
                    </Text>
                  </View>
                )}
              </View>

              <View style={styles.actions}>
                <TouchableOpacity
                  style={styles.syncButton}
                  onPress={() => handleSync(connection.id)}
                  disabled={syncing === connection.id}
                >
                  {syncing === connection.id ? (
                    <ActivityIndicator size="small" color="#ffffff" />
                  ) : (
                    <Text style={styles.syncButtonText}>Sync Now</Text>
                  )}
                </TouchableOpacity>
                <TouchableOpacity style={styles.settingsButton}>
                  <Text style={styles.settingsButtonText}>Settings</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </ScrollView>

      <AddEmailConnectionModal
        visible={showAddModal}
        onClose={() => setShowAddModal(false)}
        onConnectionAdded={fetchConnections}
      />
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
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
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
  addButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  connectionCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  connectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  connectionInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  providerIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  emailAddress: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  providerText: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  connectionDetails: {
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
    paddingTop: 12,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  detailLabel: {
    fontSize: 12,
    color: '#6b7280',
    width: 80,
  },
  detailValue: {
    fontSize: 12,
    color: '#111827',
    flex: 1,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  syncButton: {
    flex: 1,
    backgroundColor: '#3b82f6',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  syncButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14,
  },
  settingsButton: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  settingsButtonText: {
    color: '#374151',
    fontWeight: '600',
    fontSize: 14,
  },
});
