import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, View } from 'react-native';

import { HomeScreen } from './src/screens/HomeScreen';
import { PickDetailScreen } from './src/screens/PickDetailScreen';
import { DashboardScreen } from './src/screens/DashboardScreen';
import { useAuthStore } from './src/hooks/useAuth';
import { colors } from './src/utils/theme';

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
  const { hydrate, isLoading } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            const icons: Record<string, any> = {
              Picks: focused ? 'flash' : 'flash-outline',
              Dashboard: focused ? 'bar-chart' : 'bar-chart-outline',
            };
            return <Ionicons name={icons[route.name]} size={size} color={color} />;
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
  );
}
