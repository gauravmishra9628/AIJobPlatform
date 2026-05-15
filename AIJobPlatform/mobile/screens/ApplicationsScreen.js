import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const API_URL = 'http://127.0.0.1:8000/api';

const statusColors = {
  pending: '#F59E0B',
  reviewed: '#3B82F6',
  interview: '#8B5CF6',
  accepted: '#10B981',
  rejected: '#EF4444',
};

export default function ApplicationsScreen() {
  const [applications, setApplications] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const token = await import('expo-secure-store').then(m => m.getItemAsync('authToken'));
      const response = await axios.get(`${API_URL}/jobs/applications/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setApplications(response.data.applications || []);
    } catch (error) {
      console.log('Error fetching applications:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchApplications();
    setRefreshing(false);
  };

  const renderApplication = ({ item }) => (
    <View style={styles.appCard}>
      <View style={styles.appHeader}>
        <View style={styles.appIcon}>
          <Text style={styles.appIconText}>{item.job?.title?.charAt(0) || 'J'}</Text>
        </View>
        <View style={styles.appInfo}>
          <Text style={styles.appTitle}>{item.job?.title}</Text>
          <Text style={styles.appCompany}>{item.job?.company}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: statusColors[item.status] + '20' }]}>
          <Text style={[styles.statusText, { color: statusColors[item.status] }]}>
            {item.status}
          </Text>
        </View>
      </View>
      <View style={styles.appMeta}>
        <View style={styles.metaItem}>
          <Ionicons name="calendar-outline" size={14} color="#9CA3AF" />
          <Text style={styles.metaText}>
            {new Date(item.created_at).toLocaleDateString()}
          </Text>
        </View>
        {item.match_score && (
          <View style={styles.metaItem}>
            <Ionicons name="trending-up" size={14} color="#9CA3AF" />
            <Text style={styles.metaText}>{Math.round(item.match_score)}% Match</Text>
          </View>
        )}
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={applications}
        renderItem={renderApplication}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={64} color="#9CA3AF" />
            <Text style={styles.emptyTitle}>No Applications Yet</Text>
            <Text style={styles.emptySubtitle}>Start applying to jobs to see your applications here</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  list: { padding: 16 },
  appCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12 },
  appHeader: { flexDirection: 'row', alignItems: 'center' },
  appIcon: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center' },
  appIconText: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  appInfo: { flex: 1, marginLeft: 12 },
  appTitle: { fontSize: 16, fontWeight: '600', color: '#1F2937' },
  appCompany: { fontSize: 14, color: '#6B7280', marginTop: 2 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  statusText: { fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  appMeta: { flexDirection: 'row', marginTop: 12, gap: 16 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaText: { fontSize: 12, color: '#9CA3AF' },
  emptyState: { alignItems: 'center', paddingTop: 80 },
  emptyTitle: { fontSize: 18, fontWeight: '600', color: '#6B7280', marginTop: 16 },
  emptySubtitle: { fontSize: 14, color: '#9CA3AF', marginTop: 8, textAlign: 'center', paddingHorizontal: 40 },
});