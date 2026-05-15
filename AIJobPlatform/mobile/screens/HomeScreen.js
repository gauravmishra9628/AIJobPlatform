import React, { useContext, useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl
} from 'react-native';
import { AuthContext } from '../App';
import { useNavigation } from '@react-navigation/native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const API_URL = 'http://127.0.0.1:8000/api';

export default function HomeScreen() {
  const { user } = useContext(AuthContext);
  const navigation = useNavigation();
  const [recommendations, setRecommendations] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      const token = await import('expo-secure-store').then(m => m.getItemAsync('authToken'));
      const response = await axios.get(`${API_URL}/jobs/recommendations/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.log('Error fetching recommendations:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchRecommendations();
    setRefreshing(false);
  };

  const features = [
    { id: 'resume', icon: 'document-text', label: 'Resume Builder', color: '#3B82F6' },
    { id: 'coach', icon: 'chatbubbles', label: 'Career Coach', color: '#10B981' },
    { id: 'interview', icon: 'school', label: 'Interview Prep', color: '#8B5CF6' },
    { id: 'jobs', icon: 'search', label: 'Find Jobs', color: '#F59E0B' },
  ];

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Hello, {user?.first_name || 'User'}!</Text>
        <Text style={styles.subGreeting}>Find your dream job today</Text>
      </View>

      {/* Quick Actions */}
      <View style={styles.featuresGrid}>
        {features.map((feature) => (
          <TouchableOpacity key={feature.id} style={styles.featureCard} onPress={() => {
            if (feature.id === 'coach') navigation.navigate('ChatBot');
          }}>
            <View style={[styles.iconContainer, { backgroundColor: feature.color + '20' }]}>
              <Ionicons name={feature.icon} size={24} color={feature.color} />
            </View>
            <Text style={styles.featureLabel}>{feature.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Recommendations */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recommended for You</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Jobs')}>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        </View>

        {recommendations.length > 0 ? (
          recommendations.slice(0, 5).map((job) => (
            <TouchableOpacity key={job.id} style={styles.jobCard} onPress={() => {
              navigation.navigate('Jobs', { screen: 'JobDetail', params: { job } });
            }}>
              <View style={styles.jobHeader}>
                <View style={styles.jobIcon}>
                  <Text style={styles.jobIconText}>{job.company?.charAt(0) || 'J'}</Text>
                </View>
                <View style={styles.jobInfo}>
                  <Text style={styles.jobTitle} numberOfLines={1}>{job.title}</Text>
                  <Text style={styles.jobCompany}>{job.company}</Text>
                </View>
              </View>
              <View style={styles.jobMeta}>
                <View style={styles.metaItem}>
                  <Ionicons name="location-outline" size={14} color="#6B7280" />
                  <Text style={styles.metaText}>{job.location}</Text>
                </View>
                <View style={styles.metaItem}>
                  <Ionicons name="briefcase-outline" size={14} color="#6B7280" />
                  <Text style={styles.metaText}>{job.employment_type}</Text>
                </View>
              </View>
              {job.match_score > 0 && (
                <View style={styles.matchBadge}>
                  <Text style={styles.matchText}>{Math.round(job.match_score)}% Match</Text>
                </View>
              )}
            </TouchableOpacity>
          ))
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="briefcase-outline" size={48} color="#9CA3AF" />
            <Text style={styles.emptyText}>No recommendations yet</Text>
            <Text style={styles.emptySubtext}>Update your profile to get personalized job matches</Text>
          </View>
        )}
      </View>

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>12</Text>
          <Text style={styles.statLabel}>Applications</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>3</Text>
          <Text style={styles.statLabel}>Interviews</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>5</Text>
          <Text style={styles.statLabel}>Saved</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: { padding: 20, backgroundColor: '#fff' },
  greeting: { fontSize: 24, fontWeight: 'bold', color: '#1F2937' },
  subGreeting: { fontSize: 14, color: '#6B7280', marginTop: 4 },
  featuresGrid: { flexDirection: 'row', flexWrap: 'wrap', padding: 16, gap: 12 },
  featureCard: { width: '47%', backgroundColor: '#fff', borderRadius: 16, padding: 16, alignItems: 'center' },
  iconContainer: { width: 48, height: 48, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginBottom: 8 },
  featureLabel: { fontSize: 14, fontWeight: '500', color: '#1F2937' },
  section: { padding: 16 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: '#1F2937' },
  seeAll: { color: '#3B82F6', fontSize: 14 },
  jobCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12 },
  jobHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  jobIcon: { width: 40, height: 40, borderRadius: 10, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center' },
  jobIconText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  jobInfo: { marginLeft: 12, flex: 1 },
  jobTitle: { fontSize: 16, fontWeight: '600', color: '#1F2937' },
  jobCompany: { fontSize: 14, color: '#6B7280', marginTop: 2 },
  jobMeta: { flexDirection: 'row', gap: 16 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaText: { fontSize: 12, color: '#6B7280' },
  matchBadge: { marginTop: 12, backgroundColor: '#10B98120', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, alignSelf: 'flex-start' },
  matchText: { color: '#10B981', fontSize: 12, fontWeight: '600' },
  emptyState: { alignItems: 'center', padding: 32 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#6B7280', marginTop: 16 },
  emptySubtext: { fontSize: 14, color: '#9CA3AF', marginTop: 8, textAlign: 'center' },
  statsContainer: { flexDirection: 'row', padding: 16, gap: 12 },
  statCard: { flex: 1, backgroundColor: '#fff', borderRadius: 12, padding: 16, alignItems: 'center' },
  statValue: { fontSize: 24, fontWeight: 'bold', color: '#3B82F6' },
  statLabel: { fontSize: 12, color: '#6B7280', marginTop: 4 },
});