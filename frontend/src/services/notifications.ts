/**
 * Web stub for notifications service.
 * expo-notifications is not supported on web, so all functions are no-ops.
 */

type NotificationSubscription = { remove: () => void };

export async function requestNotificationPermissions(): Promise<boolean> {
  return false;
}

export async function getPushToken(): Promise<string | null> {
  return null;
}

export async function notifyHighValueBet(_pick: any): Promise<void> {
  // No-op on web
}

export async function checkForHighValueBets(): Promise<number> {
  return 0;
}

export async function setupBackgroundNotifications(): Promise<void> {
  console.log('✅ Notification service (web stub)');
}

export async function cancelAllNotifications(): Promise<void> {
  // No-op on web
}

export async function getBadgeCount(): Promise<number> {
  return 0;
}

export async function setBadgeCount(_count: number): Promise<void> {
  // No-op on web
}

export function addNotificationListener(_callback: any): NotificationSubscription {
  return { remove: () => {} };
}

export function addNotificationResponseListener(_callback: any): NotificationSubscription {
  return { remove: () => {} };
}
