import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, RefreshControl
} from 'react-native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const API_URL = 'http://127.0.0.1:8000/api';

export default function JobsScreen({ navigation }) {
  const [jobs, setJobs] = useState([]);
  const [search, setSearch] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const token = await import('expo-secure-store').then(m => m.getItemAsync('authToken'));
      const response = await axios.get(`${API_URL}/jobs/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJobs(response.data.jobs || []);
    } catch (error) {
      console.log('Error fetching jobs:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchJobs();
    setRefreshing(false);
  };

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = job.title.toLowerCase().includes(search.toLowerCase()) ||
                          job.company?.toLowerCase().includes(search.toLowerCase());
    if (filter === 'all') return matchesSearch;
    return matchesSearch && job.employment_type === filter;
  });

  const renderJob = ({ item }) => (
    <TouchableOpacity style={styles.jobCard} onPress={() => navigation.navigate('JobDetail', { job: item })}>
      <View style={styles.jobHeader}>
        <View style={styles.jobIcon}>
          <Text style={styles.jobIconText}>{item.company?.charAt(0) || 'J'}</Text>
        </View>
        <View style={styles.jobInfo}>
          <Text style={styles.jobTitle} numberOfLines={1}>{item.title}</Text>
          <Text style={styles.jobCompany}>{item.company}</Text>
        </View>
      </View>
      <Text style={styles.jobDescription} numberOfLines={2}>{item.description}</Text>
      <View style={styles.jobMeta}>
        <View style={styles.metaItem}>
          <Ionicons name="location-outline" size={14} color="#6B7280" />
          <Text style={styles.metaText}>{item.location}</Text>
        </View>
        <View style={styles.metaItem}>
          <Ionicons name="briefcase-outline" size={14} color="#6B7280" />
          <Text style={styles.metaText}>{item.employment_type}</Text>
        </View>
      </View>
      {item.skills_required && (
        <View style={styles.skillsContainer}>
          {item.skills_required.split(',').slice(0, 3).map((skill, i) => (
            <View key={i} style={styles.skillBadge}>
              <Text style={styles.skillText}>{skill.trim()}</Text>
            </View>
          ))}
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color="#9CA3AF" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search jobs..."
            value={search}
            onChangeText={setSearch}
            placeholderTextColor="#9CA3AF"
          />
        </View>
      </View>

      <View style={styles.filtersContainer}>
        {['all', 'full-time', 'part-time', 'internship'].map(f => (
          <TouchableOpacity
            key={f}
            style={[styles.filterButton, filter === f && styles.filterActive]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f && styles.filterTextActive]}>
              {f === 'all' ? 'All' : f}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={filteredJobs}
        renderItem={renderJob}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="search-outline" size={48} color="#9CA3AF" />
            <Text style={styles.emptyText}>No jobs found</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  searchContainer: { padding: 16, backgroundColor: '#fff' },
  searchBar: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F9FAFB', borderRadius: 12, paddingHorizontal: 12 },
  searchInput: { flex: 1, paddingVertical: 12, paddingHorizontal: 8, fontSize: 16 },
  filtersContainer: { flexDirection: 'row', paddingHorizontal: 16, paddingBottom: 12, gap: 8 },
  filterButton: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#fff' },
  filterActive: { backgroundColor: '#3B82F6' },
  filterText: { fontSize: 14, color: '#6B7280', textTransform: 'capitalize' },
  filterTextActive: { color: '#fff' },
  list: { padding: 16 },
  jobCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 12 },
  jobHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  jobIcon: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center' },
  jobIconText: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  jobInfo: { marginLeft: 12, flex: 1 },
  jobTitle: { fontSize: 16, fontWeight: '600', color: '#1F2937' },
  jobCompany: { fontSize: 14, color: '#6B7280', marginTop: 2 },
  jobDescription: { fontSize: 14, color: '#6B7280', marginBottom: 12, lineHeight: 20 },
  jobMeta: { flexDirection: 'row', gap: 16 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaText: { fontSize: 12, color: '#6B7280' },
  skillsContainer: { flexDirection: 'row', marginTop: 12, gap: 8, flexWrap: 'wrap' },
  skillBadge: { backgroundColor: '#EEF2FF', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  skillText: { fontSize: 12, color: '#3B82F6' },
  emptyState: { alignItems: 'center', padding: 48 },
  emptyText: { fontSize: 16, color: '#6B7280', marginTop: 16 },
});