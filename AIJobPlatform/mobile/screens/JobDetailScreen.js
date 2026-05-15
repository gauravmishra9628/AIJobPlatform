import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const API_URL = 'http://127.0.0.1:8000/api';

export default function JobDetailScreen({ route, navigation }) {
  const { job } = route.params;
  const [applying, setApplying] = useState(false);

  const handleApply = async () => {
    setApplying(true);
    try {
      const token = await import('expo-secure-store').then(m => m.getItemAsync('authToken'));
      await axios.post(`${API_URL}/jobs/${job.id}/apply/`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      Alert.alert('Success', 'Application submitted successfully!');
    } catch (error) {
      Alert.alert('Error', 'Failed to apply. You may have already applied.');
    } finally {
      setApplying(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.companyIcon}>
          <Text style={styles.companyIconText}>{job.company?.charAt(0) || 'J'}</Text>
        </View>
        <Text style={styles.title}>{job.title}</Text>
        <Text style={styles.company}>{job.company}</Text>
      </View>

      <View style={styles.metaContainer}>
        <View style={styles.metaItem}>
          <Ionicons name="location" size={18} color="#6B7280" />
          <Text style={styles.metaText}>{job.location}</Text>
        </View>
        <View style={styles.metaItem}>
          <Ionicons name="briefcase" size={18} color="#6B7280" />
          <Text style={styles.metaText}>{job.employment_type}</Text>
        </View>
        {job.salary_min && (
          <View style={styles.metaItem}>
            <Ionicons name="cash" size={18} color="#6B7280" />
            <Text style={styles.metaText}>${job.salary_min} - ${job.salary_max || job.salary_min}</Text>
          </View>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Description</Text>
        <Text style={styles.sectionContent}>{job.description}</Text>
      </View>

      {job.skills_required && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Required Skills</Text>
          <View style={styles.skillsContainer}>
            {job.skills_required.split(',').map((skill, i) => (
              <View key={i} style={styles.skillBadge}>
                <Text style={styles.skillText}>{skill.trim()}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Requirements</Text>
        <Text style={styles.sectionContent}>
          • {job.required_experience_years || 0}+ years of experience{'\n'}
          {job.required_education && `• ${job.required_education}`}
        </Text>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity style={styles.applyButton} onPress={handleApply} disabled={applying}>
          <Text style={styles.applyButtonText}>{applying ? 'Applying...' : 'Apply Now'}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.saveButton}>
          <Ionicons name="bookmark-outline" size={24} color="#3B82F6" />
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: { backgroundColor: '#fff', padding: 20, alignItems: 'center' },
  companyIcon: { width: 64, height: 64, borderRadius: 16, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  companyIconText: { color: '#fff', fontSize: 28, fontWeight: 'bold' },
  title: { fontSize: 20, fontWeight: 'bold', color: '#1F2937', textAlign: 'center' },
  company: { fontSize: 16, color: '#6B7280', marginTop: 4 },
  metaContainer: { flexDirection: 'row', flexWrap: 'wrap', backgroundColor: '#fff', padding: 16, marginTop: 8, gap: 16 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaText: { fontSize: 14, color: '#6B7280' },
  section: { backgroundColor: '#fff', padding: 16, marginTop: 8 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#1F2937', marginBottom: 12 },
  sectionContent: { fontSize: 14, color: '#6B7280', lineHeight: 22 },
  skillsContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  skillBadge: { backgroundColor: '#EEF2FF', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  skillText: { fontSize: 14, color: '#3B82F6' },
  buttonContainer: { flexDirection: 'row', padding: 16, gap: 12 },
  applyButton: { flex: 1, backgroundColor: '#3B82F6', padding: 16, borderRadius: 12, alignItems: 'center' },
  applyButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  saveButton: { width: 56, backgroundColor: '#fff', borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#3B82F6' },
});