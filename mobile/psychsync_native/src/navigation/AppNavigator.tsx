/**
 * App Navigation Structure
 *
 * Implements:
 * - Stack navigation for main flow
 * - Tab navigation for main sections
 * - Auth flow (login/signup)
 * - Assessment flow
 * - Telehealth flow
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Auth Screens
import LoginScreen from '@screens/auth/LoginScreen';
import SignupScreen from '@screens/auth/SignupScreen';

// Main Screens
import DashboardScreen from '@screens/DashboardScreen';
import AssessmentsScreen from '@screens/AssessmentsScreen';
import TelehealthScreen from '@screens/TelehealthScreen';
import ProfileScreen from '@screens/ProfileScreen';

// Assessment Screens
import LSASScreen from '@screens/assessments/LSASScreen';
import EAT26Screen from '@screens/assessments/EAT26Screen';
import YBOCSScreen from '@screens/assessments/YBOCSScreen';
import PHQ9Screen from '@screens/assessments/PHQ9Screen';
import GAD7Screen from '@screens/assessments/GAD7Screen';

// Telehealth Screens
import VideoConsultationScreen from '@screens/telehealth/VideoConsultationScreen';
import SessionDetailScreen from '@screens/telehealth/SessionDetailScreen';

// AI Chatbot
import ChatbotScreen from '@screens/ChatbotScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const MainTabs: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Dashboard':
              iconName = 'dashboard';
              break;
            case 'Assessments':
              iconName = 'assignment';
              break;
            case 'Telehealth':
              iconName = 'videocam';
              break;
            case 'Chatbot':
              iconName = 'chat';
              break;
            case 'Profile':
              iconName = 'person';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#6C63FF',
        tabBarInactiveTintColor: '#9E9E9E',
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ tabBarLabel: 'Home' }}
      />
      <Tab.Screen name="Assessments" component={AssessmentsScreen} />
      <Tab.Screen name="Telehealth" component={TelehealthScreen} />
      <Tab.Screen name="Chatbot" component={ChatbotScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
};

const AppNavigator: React.FC = () => {
  // TODO: Integrate with AuthContext to show auth stack if not logged in
  const isAuthenticated = true; // Placeholder

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: '#6C63FF',
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      {!isAuthenticated ? (
        // Auth Stack
        <>
          <Stack.Screen
            name="Login"
            component={LoginScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Signup"
            component={SignupScreen}
            options={{ title: 'Create Account' }}
          />
        </>
      ) : (
        // Main App Stack
        <>
          <Stack.Screen
            name="MainTabs"
            component={MainTabs}
            options={{ headerShown: false }}
          />

          {/* Assessment Screens */}
          <Stack.Screen
            name="LSAS"
            component={LSASScreen}
            options={{ title: 'Social Anxiety Assessment' }}
          />
          <Stack.Screen
            name="EAT26"
            component={EAT26Screen}
            options={{ title: 'Eating Attitudes Test' }}
          />
          <Stack.Screen
            name="YBOCS"
            component={YBOCSScreen}
            options={{ title: 'OCD Assessment' }}
          />
          <Stack.Screen
            name="PHQ9"
            component={PHQ9Screen}
            options={{ title: 'Depression Screening' }}
          />
          <Stack.Screen
            name="GAD7"
            component={GAD7Screen}
            options={{ title: 'Anxiety Screening' }}
          />

          {/* Telehealth Screens */}
          <Stack.Screen
            name="VideoConsultation"
            component={VideoConsultationScreen}
            options={{ title: 'Video Consultation' }}
          />
          <Stack.Screen
            name="SessionDetail"
            component={SessionDetailScreen}
            options={{ title: 'Session Details' }}
          />
        </>
      )}
    </Stack.Navigator>
  );
};

export default AppNavigator;
