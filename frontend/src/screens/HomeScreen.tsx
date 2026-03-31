import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { PickCard } from '../components/PickCard';
import { getTodaysPicks } from '../services/api';
import { colors, spacing } from '../utils/theme';

export const HomeScreen = () => {
  const navigation = useNavigation<any>();
  const [picks, setPicks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPicks = async () => {
    try {
      const data = await getTodaysPicks();
      setPicks(Array.isArray(data) ? data : []);
      setError(null);
    } catch (e: any) {
      setError('Could not load picks. Please try again.');
      setPicks([]);
    }
  };

  useEffect(() => {
    loadPicks().finally(() => setLoading(false));
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPicks();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Today's Picks</Text>
        <Text style={styles.subtitle}>{picks.length} value bets found</Text>
      </View>

      <Text style={styles.disclaimer}>
        ⚠️ Data-driven insights only. Not guaranteed outcomes. Bet responsibly.
      </Text>

      {error && <Text style={styles.error}>{error}</Text>}

      <FlatList
        data={picks}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <PickCard
            {...item}
            onPress={() => navigation.navigate('PickDetail', { id: item.id })}
          />
        )}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.accent}
          />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No value bets found for today.</Text>
            <Text style={styles.emptySubtext}>
              Check back before tip-off — odds shift throughout the day.
            </Text>
          </View>
        }
        contentContainerStyle={{ paddingBottom: 80 }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  subtitle: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  disclaimer: {
    fontSize: 11,
    color: colors.textMuted,
    marginBottom: spacing.md,
    lineHeight: 16,
  },
  error: {
    color: colors.avoid,
    marginBottom: spacing.sm,
    fontSize: 13,
  },
  empty: {
    paddingTop: 60,
    alignItems: 'center',
  },
  emptyText: {
    color: colors.textSecondary,
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  emptySubtext: {
    color: colors.textMuted,
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
  },
});
