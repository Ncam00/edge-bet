import React, { useEffect, useRef, Component, ErrorInfo, ReactNode, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, View, Platform, Text } from 'react-native';

import { HomeScreen } from './src/screens/HomeScreen';
import { PickDetailScreen } from './src/screens/PickDetailScreen';
import { DashboardScreen } from './src/screens/DashboardScreen';
import { SportsScreen } from './src/screens/SportsScreen';
import { RacingScreen } from './src/screens/RacingScreen';
import { colors } from './src/utils/theme';

// Error Boundary for catching runtime errors
class ErrorBoundary extends Component<{children: ReactNode}, {hasError: boolean, error: Error | null}> {
  constructor(props: {children: ReactNode}) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('App Error:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a2e', padding: 20 }}>
          <Text style={{ color: '#ff6b6b', fontSize: 18, fontWeight: 'bold' }}>Something went wrong</Text>
          <Text style={{ color: '#fff', marginTop: 10, textAlign: 'center' }}>{this.state.error?.message}</Text>
        </View>
      );
    }
    return this.props.children;
  }
}

// Web-safe icon component
const TabIcon = ({ name, color, size }: { name: string; color: string; size: number }) => {
  const icons: Record<string, string> = {
    flash: '⚡',
    'flash-outline': '⚡',
    'bar-chart': '📊',
    'bar-chart-outline': '📊',
    'football': '🎯',
    'football-outline': '🎯',
    'horse': '🏇',
    'horse-outline': '🏇',
  };
  return <Text style={{ fontSize: size, color }}>{icons[name] || '•'}</Text>;
};

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const PicksStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: colors.surface },
      headerTintColor: colors.textPrimary,
      headerTitleStyle: { fontWeight: '600' },
    }}
  >
    <Stack.Screen name="Home" component={HomeScreen} options={{ title: "Today's Picks" }} />
    <Stack.Screen name="PickDetail" component={PickDetailScreen} options={{ title: 'Pick Detail' }} />
  </Stack.Navigator>
);

export default function App() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simple hydration without expo-secure-store issues
    const hydrate = async () => {
      try {
        // On web, just check localStorage
        if (Platform.OS === 'web') {
          const token = localStorage.getItem('access_token');
          console.log('Token found:', !!token);
        }
      } catch (e) {
        console.warn('Hydration error:', e);
      } finally {
        setIsLoading(false);
      }
    };
    hydrate();
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator color={colors.accent} size="large" />
        <Text style={{ color: colors.textSecondary, marginTop: 16 }}>Loading EdgeBet...</Text>
      </View>
    );
  }

  return (
    <ErrorBoundary>
      <View style={{ flex: 1, height: '100%' }}>
        <NavigationContainer>
          <StatusBar style="light" />
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color, size }) => {
                const icons: Record<string, any> = {
                  Picks: focused ? 'flash' : 'flash-outline',
                  Sports: focused ? 'football' : 'football-outline',
                  Racing: focused ? 'horse' : 'horse-outline',
                  Dashboard: focused ? 'bar-chart' : 'bar-chart-outline',
                };
                return <TabIcon name={icons[route.name]} size={size} color={color} />;
              },
              tabBarActiveTintColor: colors.accent,
              tabBarInactiveTintColor: colors.textMuted,
              tabBarStyle: {
                backgroundColor: colors.surface,
                borderTopColor: colors.border,
                borderTopWidth: 1,
              },
              headerShown: false,
            })}
          >
            <Tab.Screen name="Picks" component={PicksStack} />
            <Tab.Screen
              name="Sports"
              component={SportsScreen}
              options={{
                headerShown: true,
                headerStyle: { backgroundColor: colors.surface },
                headerTintColor: colors.textPrimary,
                title: 'All Sports',
              }}
            />
            <Tab.Screen
              name="Racing"
              component={RacingScreen}
              options={{
                headerShown: true,
                headerStyle: { backgroundColor: colors.surface },
                headerTintColor: colors.textPrimary,
              }}
            />
            <Tab.Screen
              name="Dashboard"
              component={DashboardScreen}
              options={{
                headerShown: true,
                headerStyle: { backgroundColor: colors.surface },
                headerTintColor: colors.textPrimary,
              }}
            />
          </Tab.Navigator>
        </NavigationContainer>
      </View>
    </ErrorBoundary>
  );
}
