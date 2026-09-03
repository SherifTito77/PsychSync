/**
 * Theme Context for Dark/Light Mode
 * Provides theme management throughout the app
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Appearance, ColorSchemeName } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const THEME_KEY = '@psychsync_theme';

interface ThemeColors {
  // Primary colors
  primary: string;
  primaryLight: string;
  primaryDark: string;

  // Background colors
  background: string;
  backgroundSecondary: string;
  backgroundCard: string;

  // Text colors
  text: string;
  textSecondary: string;
  textTertiary: string;

  // Border colors
  border: string;
  borderLight: string;

  // Status colors
  success: string;
  warning: string;
  error: string;
  info: string;

  // UI elements
  tabBar: string;
  tabBarActive: string;
  tabBarInactive: string;

  // Shadows
  shadow: string;
  shadowLight: string;
}

const lightTheme: ThemeColors = {
  primary: '#3b82f6',
  primaryLight: '#60a5fa',
  primaryDark: '#2563eb',

  background: '#f9fafb',
  backgroundSecondary: '#ffffff',
  backgroundCard: '#ffffff',

  text: '#111827',
  textSecondary: '#6b7280',
  textTertiary: '#9ca3af',

  border: '#e5e7eb',
  borderLight: '#f3f4f6',

  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',

  tabBar: '#ffffff',
  tabBarActive: '#3b82f6',
  tabBarInactive: '#9ca3af',

  shadow: '#000000',
  shadowLight: 'rgba(0, 0, 0, 0.05)',
};

const darkTheme: ThemeColors = {
  primary: '#60a5fa',
  primaryLight: '#93c5fd',
  primaryDark: '#3b82f6',

  background: '#111827',
  backgroundSecondary: '#1f2937',
  backgroundCard: '#1f2937',

  text: '#f9fafb',
  textSecondary: '#d1d5db',
  textTertiary: '#9ca3af',

  border: '#374151',
  borderLight: '#4b5563',

  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',

  tabBar: '#1f2937',
  tabBarActive: '#60a5fa',
  tabBarInactive: '#6b7280',

  shadow: '#000000',
  shadowLight: 'rgba(0, 0, 0, 0.3)',
};

interface ThemeContextType {
  colorScheme: ColorSchemeName;
  theme: ThemeColors;
  isDark: boolean;
  setColorScheme: (scheme: ColorSchemeName) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface Props {
  children: ReactNode;
}

export const ThemeProvider: React.FC<Props> = ({ children }) => {
  const [colorScheme, setColorSchemeState] = useState<ColorSchemeName>('light');

  // Load saved theme preference on mount
  useEffect(() => {
    loadThemePreference();
  }, []);

  const loadThemePreference = async () => {
    try {
      const savedScheme = await AsyncStorage.getItem(THEME_KEY);
      if (savedScheme) {
        setColorSchemeState(savedScheme as ColorSchemeName);
      } else {
        // Use system preference if no saved preference
        const systemScheme = Appearance.getColorScheme();
        setColorSchemeState(systemScheme || 'light');
      }
    } catch (error) {
      console.error('Error loading theme preference:', error);
    }
  };

  const setColorScheme = async (scheme: ColorSchemeName) => {
    try {
      setColorSchemeState(scheme);
      await AsyncStorage.setItem(THEME_KEY, scheme || 'light');
    } catch (error) {
      console.error('Error saving theme preference:', error);
    }
  };

  const toggleTheme = () => {
    setColorScheme(colorScheme === 'light' ? 'dark' : 'light');
  };

  const theme = colorScheme === 'dark' ? darkTheme : lightTheme;
  const isDark = colorScheme === 'dark';

  return (
    <ThemeContext.Provider value={{ colorScheme, theme, isDark, setColorScheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
