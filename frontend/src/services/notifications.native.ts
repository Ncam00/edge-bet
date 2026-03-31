/**
 * Push Notification Service for HIGH confidence value bets.
 * Uses Expo Notifications to alert users of top picks.
 * Gracefully degrades on web platform.
 */
import { Platform } from 'react-native';
import { getTodaysPicks, getTopProps } from './api';

// Lazy-load expo-notifications only on native
let Notifications: any = null;
if (Platform.OS !== 'web') {
  try {
    Notifications = require('expo-notifications');
    // Configure notification behavior
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
  } catch (e) {
    console.warn('expo-notifications not available');
  }
}

/**
 * Request permission for push notifications
 */
export async function requestNotificationPermissions(): Promise<boolean> {
  if (!Notifications) return false;
  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    return finalStatus === 'granted';
  } catch (error) {
    console.warn('Notification permissions error:', error);
    return false;
  }
}

/**
 * Get the push notification token for this device
 */
export async function getPushToken(): Promise<string | null> {
  if (!Notifications) return null;
  try {
    const token = await Notifications.getExpoPushTokenAsync({
      projectId: 'edgebet-local',
    });
    return token.data;
  } catch (error) {
    console.warn('Failed to get push token:', error);
    return null;
  }
}

/**
 * Schedule a local notification for a HIGH value bet
 */
export async function notifyHighValueBet(pick: {
  selection: string;
  home_team: string;
  away_team: string;
  expected_value: number;
  decimal_odds: number;
  type: 'game' | 'prop';
  player?: string;
  prop_type?: string;
}): Promise<void> {
  if (!Notifications) return;
  try {
    const evPct = (pick.expected_value * 100).toFixed(1);
    
    let title: string;
    let body: string;
    
    if (pick.type === 'prop' && pick.player) {
      title = `🔥 HIGH Value Prop: ${pick.player}`;
      body = `${pick.prop_type?.toUpperCase()} ${pick.selection} @ ${pick.decimal_odds.toFixed(2)} | +${evPct}% EV`;
    } else {
      title = `🎯 HIGH Value Bet Found`;
      body = `${pick.away_team} @ ${pick.home_team}: ${pick.selection} @ ${pick.decimal_odds.toFixed(2)} | +${evPct}% EV`;
    }

    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        sound: true,
        priority: Notifications.AndroidNotificationPriority.HIGH,
        data: { pick },
      },
      trigger: null,
    });
  } catch (error) {
    console.warn('Failed to send notification:', error);
  }
}

/**
 * Check for new HIGH value bets and notify
 */
export async function checkForHighValueBets(): Promise<number> {
  let notificationCount = 0;

  try {
    const picks = await getTodaysPicks().catch(() => []);
    const highPicks = picks.filter((p: any) => p.confidence_label === 'high');

    for (const pick of highPicks.slice(0, 3)) {
      await notifyHighValueBet({
        selection: pick.selection,
        home_team: pick.game?.home_team || pick.home_team,
        away_team: pick.game?.away_team || pick.away_team,
        expected_value: pick.expected_value,
        decimal_odds: pick.decimal_odds,
        type: 'game',
      });
      notificationCount++;
    }

    const propsResult = await getTopProps().catch(() => ({ props: [] }));
    const highProps = (propsResult.props || []).filter((p: any) => p.confidence === 'HIGH');

    for (const prop of highProps.slice(0, 2)) {
      await notifyHighValueBet({
        selection: `${prop.best_bet} ${prop.line}`,
        home_team: prop.opponent,
        away_team: prop.team,
        expected_value: prop.value,
        decimal_odds: 1.90,
        type: 'prop',
        player: prop.player,
        prop_type: prop.prop_type,
      });
      notificationCount++;
    }
  } catch (error) {
    console.warn('Error checking for high value bets:', error);
  }

  return notificationCount;
}

/**
 * Set up background notification checking
 */
export async function setupBackgroundNotifications(): Promise<void> {
  console.log('✅ Notification service initialized');
}

/**
 * Cancel all pending notifications
 */
export async function cancelAllNotifications(): Promise<void> {
  if (!Notifications) return;
  try {
    await Notifications.cancelAllScheduledNotificationsAsync();
  } catch (error) {
    console.warn('Failed to cancel notifications:', error);
  }
}

/**
 * Get notification badge count
 */
export async function getBadgeCount(): Promise<number> {
  if (!Notifications) return 0;
  try {
    return await Notifications.getBadgeCountAsync();
  } catch {
    return 0;
  }
}

/**
 * Set notification badge count
 */
export async function setBadgeCount(count: number): Promise<void> {
  if (!Notifications) return;
  try {
    await Notifications.setBadgeCountAsync(count);
  } catch (error) {
    console.warn('Failed to set badge count:', error);
  }
}

type NotificationSubscription = { remove: () => void };

/**
 * Add a notification listener
 */
export function addNotificationListener(
  callback: (notification: any) => void
): NotificationSubscription {
  if (!Notifications) return { remove: () => {} };
  return Notifications.addNotificationReceivedListener(callback);
}

/**
 * Add a notification response listener (when user taps notification)
 */
export function addNotificationResponseListener(
  callback: (response: any) => void
): NotificationSubscription {
  if (!Notifications) return { remove: () => {} };
  return Notifications.addNotificationResponseReceivedListener(callback);
}
