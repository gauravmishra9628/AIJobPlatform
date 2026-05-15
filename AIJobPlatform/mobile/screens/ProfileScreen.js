import React, { useContext } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { AuthContext } from '../App';
import { Ionicons } from '@expo/vector-icons';

export default function ProfileScreen() {
  const { user, logout } = useContext(AuthContext);

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: logout },
    ]);
  };

  const menuItems = [
    { icon: 'person-outline', label: 'Edit Profile', onPress: () => {} },
    { icon: 'document-text-outline', label: 'My Resume', onPress: () => {} },
    { icon: 'bookmark-outline', label: 'Saved Jobs', onPress: () => {} },
    { icon: 'notifications-outline', label: 'Notifications', onPress: () => {} },
    { icon: 'settings-outline', label: 'Settings', onPress: () => {} },
    { icon: 'help-circle-outline', label: 'Help & Support', onPress: () => {} },
    { icon: 'shield-checkmark-outline', label: 'Privacy Policy', onPress: () => {} },
  ];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {user?.first_name?.charAt(0) || 'U'}{user?.last_name?.charAt(0) || ''}
          </Text>
        </View>
        <Text style={styles.name}>{user?.first_name} {user?.last_name}</Text>
        <Text style={styles.email}>{user?.email}</Text>
        <View style={styles.roleBadge}>
          <Text style={styles.roleText}>{user?.role}</Text>
        </View>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>12</Text>
          <Text style={styles.statLabel}>Applications</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statValue}>5</Text>
          <Text style={styles.statLabel}>Saved</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statValue}>3</Text>
          <Text style={styles.statLabel}>Interviews</Text>
        </View>
      </View>

      <View style={styles.menuContainer}>
        {menuItems.map((item, index) => (
          <TouchableOpacity key={index} style={styles.menuItem} onPress={item.onPress}>
            <View style={styles.menuIcon}>
              <Ionicons name={item.icon} size={22} color="#6B7280" />
            </View>
            <Text style={styles.menuLabel}>{item.label}</Text>
            <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={22} color="#EF4444" />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>

      <Text style={styles.version}>Version 1.0.0</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: { backgroundColor: '#fff', padding: 24, alignItems: 'center' },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  avatarText: { color: '#fff', fontSize: 28, fontWeight: 'bold' },
  name: { fontSize: 22, fontWeight: 'bold', color: '#1F2937' },
  email: { fontSize: 14, color: '#6B7280', marginTop: 4 },
  roleBadge: { marginTop: 12, backgroundColor: '#EEF2FF', paddingHorizontal: 16, paddingVertical: 6, borderRadius: 16 },
  roleText: { color: '#3B82F6', fontSize: 14, fontWeight: '600', textTransform: 'capitalize' },
  statsContainer: { flexDirection: 'row', backgroundColor: '#fff', marginTop: 8, padding: 16 },
  statItem: { flex: 1, alignItems: 'center' },
  statValue: { fontSize: 24, fontWeight: 'bold', color: '#3B82F6' },
  statLabel: { fontSize: 12, color: '#6B7280', marginTop: 4 },
  statDivider: { width: 1, backgroundColor: '#E5E7EB' },
  menuContainer: { backgroundColor: '#fff', marginTop: 8, paddingVertical: 8 },
  menuItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, paddingHorizontal: 16 },
  menuIcon: { width: 36, height: 36, borderRadius: 10, backgroundColor: '#F3F4F6', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  menuLabel: { flex: 1, fontSize: 16, color: '#1F2937' },
  logoutButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', margin: 16, padding: 16, backgroundColor: '#FEF2F2', borderRadius: 12 },
  logoutText: { color: '#EF4444', fontSize: 16, fontWeight: '600', marginLeft: 8 },
  version: { textAlign: 'center', color: '#9CA3AF', fontSize: 12, paddingBottom: 32 },
});