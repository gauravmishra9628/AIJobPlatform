// AI Job Platform - Mobile App
// Built with React Native + Expo

import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Ionicons } from '@expo/vector-icons';
import * as SecureStore from 'expo-secure-store';

// Screens
import LoginScreen from './screens/LoginScreen';
import JobsScreen from './screens/JobsScreen';
import JobDetailScreen from './screens/JobDetailScreen';
import ApplicationsScreen from './screens/ApplicationsScreen';
import ProfileScreen from './screens/ProfileScreen';
import HomeScreen from './screens/HomeScreen';
import ChatBotScreen from './screens/ChatBotScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Auth Context
export const AuthContext = React.createContext();

function App() {
  const [userToken, setUserToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await SecureStore.getItemAsync('authToken');
      const userData = await SecureStore.getItemAsync('userData');
      if (token && userData) {
        setUserToken(token);
        setUser(JSON.parse(userData));
      }
    } catch (e) {
      console.log('Auth error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (token, userData) => {
    await SecureStore.setItemAsync('authToken', token);
    await SecureStore.setItemAsync('userData', JSON.stringify(userData));
    setUserToken(token);
    setUser(userData);
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync('authToken');
    await SecureStore.deleteItemAsync('userData');
    setUserToken(null);
    setUser(null);
  };

  const authContext = {
    userToken,
    user,
    login,
    logout,
    isLoading,
  };

  return (
    <SafeAreaProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <AuthContext.Provider value={authContext}>
          <NavigationContainer>
            <StatusBar style="auto" />
            {userToken ? <MainApp /> : <AuthStack />}
          </NavigationContainer>
        </AuthContext.Provider>
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}

function AuthStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
    </Stack.Navigator>
  );
}

function MainApp() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;
          if (route.name === 'Home') iconName = focused ? 'home' : 'home-outline';
          else if (route.name === 'Jobs') iconName = focused ? 'briefcase' : 'briefcase-outline';
          else if (route.name === 'Applications') iconName = focused ? 'document-text' : 'document-text-outline';
          else if (route.name === 'Profile') iconName = focused ? 'person' : 'person-outline';
          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#3B82F6',
        tabBarInactiveTintColor: '#9CA3AF',
        headerStyle: { backgroundColor: '#fff' },
        headerTintColor: '#1F2937',
      })}
    >
      <Tab.Screen name="Home" component={HomeStack} options={{ headerShown: false }} />
      <Tab.Screen name="Jobs" component={JobsStack} options={{ headerShown: false }} />
      <Tab.Screen name="Applications" component={ApplicationsScreen} />
      <Tab.Screen name="Profile" component={ProfileStack} options={{ headerShown: false }} />
    </Tab.Navigator>
  );
}

function HomeStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="HomeMain" component={HomeScreen} options={{ title: 'AI Job Platform' }} />
      <Stack.Screen name="ChatBot" component={ChatBotScreen} options={{ title: 'Career Coach' }} />
    </Stack.Navigator>
  );
}

function JobsStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="JobsList" component={JobsScreen} options={{ title: 'Opportunities' }} />
      <Stack.Screen name="JobDetail" component={JobDetailScreen} options={{ title: 'Job Details' }} />
    </Stack.Navigator>
  );
}

function ProfileStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="ProfileMain" component={ProfileScreen} options={{ title: 'Profile' }} />
    </Stack.Navigator>
  );
}

export default App;