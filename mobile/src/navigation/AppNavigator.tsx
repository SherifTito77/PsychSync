/**
 * Navigation structure for PsychSync Mobile App
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialIcons } from '@expo/vector-icons';
import { DashboardScreen } from '../screens/DashboardScreen';
import { ConnectionsScreen } from '../screens/ConnectionsScreen';
import { SettingsScreen } from '../screens/SettingsScreen';

export type RootTabParamList = {
  Dashboard: undefined;
  Connections: undefined;
  Settings: undefined;
};

interface Props {
  onLogout?: () => void;
}

const Tab = createBottomTabNavigator<RootTabParamList>();

export const AppNavigator: React.FC<Props> = ({ onLogout }) => {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          tabBarActiveTintColor: '#3b82f6',
          tabBarInactiveTintColor: '#9ca3af',
          headerShown: false,
        }}
      >
        <Tab.Screen
          name="Dashboard"
          component={DashboardScreen}
          options={{
            tabBarLabel: 'Dashboard',
            tabBarIcon: ({ color, size }) => (
              <MaterialIcons name="dashboard" color={color} size={size} />
            ),
          }}
        />
        <Tab.Screen
          name="Connections"
          component={ConnectionsScreen}
          options={{
            tabBarLabel: 'Connections',
            tabBarIcon: ({ color, size }) => (
              <MaterialIcons name="email" color={color} size={size} />
            ),
          }}
        />
        <Tab.Screen
          name="Settings"
          options={{
            tabBarLabel: 'Settings',
            tabBarIcon: ({ color, size }) => (
              <MaterialIcons name="settings" color={color} size={size} />
            ),
          }}
        >
          {(props) => <SettingsScreen {...props} onLogout={onLogout} />}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
  );
};
