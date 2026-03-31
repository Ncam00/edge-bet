import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, TouchableOpacity, RefreshControl } from 'react-native';
import { getSportCategories, getCategoryPicks, getSportPicks } from '../services/api';
import { colors, spacing, radius } from '../utils/theme';

interface SportCategory {
  category: string;
  emoji: string;
  sport_count: number;
  sports: string[];
}

interface SportPick {
  game_id: string;
  sport: string;
  sport_display: string;
  home_team: string;
  away_team: string;
  commence_time: string;
  best_bet: string;
  odds: number;
  ev_percent: number;
  confidence: string;
  edge: number;
}

const CATEGORY_EMOJIS: Record<string, string> = {
  basketball: '🏀',
  football: '🏈',
  baseball: '⚾',
  hockey: '🏒',
  soccer: '⚽',
  tennis: '🎾',
  mma: '🥊',
  boxing: '🥊',
  golf: '⛳',
  racing: '🏇',
  esports: '🎮',
  other: '🎯',
};

export const SportsScreen = () => {
  const [categories, setCategories] = useState<SportCategory[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [picks, setPicks] = useState<SportPick[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingPicks, setLoadingPicks] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadCategories = async () => {
    try {
      const data = await getSportCategories().catch(() => ({ categories: [] }));
      const cats = Array.isArray(data?.categories) ? data.categories : [];
      setCategories(cats);
      // Auto-select first category with sports
      const firstWithSports = cats.find((c: SportCategory) => c.sport_count > 0);
      if (firstWithSports) {
        setActiveCategory(firstWithSports.category);
        loadCategoryPicks(firstWithSports.category);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadCategoryPicks = async (category: string) => {
    setLoadingPicks(true);
    try {
      const data = await getCategoryPicks(category).catch(() => ({ picks: [] }));
      setPicks(Array.isArray(data?.picks) ? data.picks : []);
    } finally {
      setLoadingPicks(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadCategories();
  };

  const selectCategory = (category: string) => {
    setActiveCategory(category);
    loadCategoryPicks(category);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />
      }
    >
      <Text style={styles.title}>All Sports</Text>
      <Text style={styles.subtitle}>40+ sports • Real-time odds • AI-powered picks</Text>

      {/* Category Pills */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
        {categories.map((cat) => (
          <TouchableOpacity
            key={cat.category}
            style={[
              styles.categoryPill,
              activeCategory === cat.category && styles.categoryPillActive
            ]}
            onPress={() => selectCategory(cat.category)}
          >
            <Text style={styles.categoryEmoji}>{cat.emoji || CATEGORY_EMOJIS[cat.category.toLowerCase()] || '🎯'}</Text>
            <Text style={[
              styles.categoryText,
              activeCategory === cat.category && styles.categoryTextActive
            ]}>
              {cat.category}
            </Text>
            <Text style={styles.categoryCount}>{cat.sport_count}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Active Category Sports List */}
      {activeCategory && (
        <View style={styles.sportsGrid}>
          {categories
            .find(c => c.category === activeCategory)
            ?.sports?.map((sport: string) => (
              <TouchableOpacity 
                key={sport} 
                style={styles.sportChip}
                onPress={() => loadSportPicks(sport)}
              >
                <Text style={styles.sportChipText}>{sport.replace(/_/g, ' ')}</Text>
              </TouchableOpacity>
            ))
          }
        </View>
      )}

      {/* Picks Section */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>
          {activeCategory ? `${CATEGORY_EMOJIS[activeCategory.toLowerCase()] || '🎯'} ${activeCategory.toUpperCase()} PICKS` : '🎯 ALL PICKS'}
        </Text>
        <Text style={styles.pickCount}>{picks.length} value bets</Text>
      </View>

      {loadingPicks ? (
        <ActivityIndicator color={colors.accent} style={{ padding: 20 }} />
      ) : picks.length > 0 ? (
        picks.map((pick, index) => (
          <SportPickCard key={`${pick.game_id}-${index}`} pick={pick} />
        ))
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyEmoji}>🔍</Text>
          <Text style={styles.emptyText}>No value bets found in this category</Text>
          <Text style={styles.emptySubtext}>Check back when games are closer</Text>
        </View>
      )}
    </ScrollView>
  );

  async function loadSportPicks(sportKey: string) {
    setLoadingPicks(true);
    try {
      const data = await getSportPicks(sportKey);
      setPicks(data.picks || []);
    } finally {
      setLoadingPicks(false);
    }
  }
};

// Sport Pick Card Component
const SportPickCard = ({ pick }: { pick: SportPick }) => {
  const confidenceColors: Record<string, string> = {
    HIGH: colors.value,
    MEDIUM: colors.accent,
    LOW: colors.textMuted,
  };

  return (
    <View style={styles.pickCard}>
      <View style={styles.pickHeader}>
        <View style={styles.sportBadge}>
          <Text style={styles.sportBadgeText}>{pick.sport_display || pick.sport}</Text>
        </View>
        <View style={[styles.confidenceBadge, { backgroundColor: confidenceColors[pick.confidence] || colors.textMuted }]}>
          <Text style={styles.confidenceText}>{pick.confidence}</Text>
        </View>
      </View>
      
      <Text style={styles.matchup}>
        {pick.away_team} @ {pick.home_team}
      </Text>
      
      <View style={styles.pickDetails}>
        <View style={styles.betInfo}>
          <Text style={styles.betLabel}>Best Bet</Text>
          <Text style={styles.betValue}>{pick.best_bet}</Text>
        </View>
        <View style={styles.betInfo}>
          <Text style={styles.betLabel}>Odds</Text>
          <Text style={styles.betValue}>{pick.odds > 0 ? `+${pick.odds}` : pick.odds}</Text>
        </View>
        <View style={styles.betInfo}>
          <Text style={styles.betLabel}>EV</Text>
          <Text style={[styles.betValue, { color: colors.value }]}>+{pick.ev_percent?.toFixed(1)}%</Text>
        </View>
        <View style={styles.betInfo}>
          <Text style={styles.betLabel}>Edge</Text>
          <Text style={[styles.betValue, { color: colors.accent }]}>{(pick.edge * 100)?.toFixed(1)}%</Text>
        </View>
      </View>
      
      <Text style={styles.gameTime}>
        {new Date(pick.commence_time).toLocaleString()}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.md,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textMuted,
    marginBottom: spacing.lg,
  },
  categoryScroll: {
    marginBottom: spacing.lg,
  },
  categoryPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    marginRight: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  categoryPillActive: {
    backgroundColor: colors.accent,
    borderColor: colors.accent,
  },
  categoryEmoji: {
    fontSize: 16,
    marginRight: spacing.xs,
  },
  categoryText: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  categoryTextActive: {
    color: '#fff',
  },
  categoryCount: {
    fontSize: 12,
    color: colors.textMuted,
    marginLeft: spacing.xs,
    backgroundColor: colors.background,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  sportsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: spacing.lg,
  },
  sportChip: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radius.sm,
    marginRight: spacing.xs,
    marginBottom: spacing.xs,
  },
  sportChipText: {
    fontSize: 12,
    color: colors.textSecondary,
    textTransform: 'capitalize',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  pickCount: {
    fontSize: 13,
    color: colors.textMuted,
  },
  pickCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  pickHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  sportBadge: {
    backgroundColor: colors.background,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.sm,
  },
  sportBadgeText: {
    fontSize: 11,
    color: colors.accent,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  confidenceBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.sm,
  },
  confidenceText: {
    fontSize: 11,
    color: '#fff',
    fontWeight: '600',
  },
  matchup: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  pickDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  betInfo: {
    alignItems: 'center',
  },
  betLabel: {
    fontSize: 11,
    color: colors.textMuted,
    marginBottom: 2,
  },
  betValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  gameTime: {
    fontSize: 12,
    color: colors.textMuted,
  },
  emptyCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.xl,
    alignItems: 'center',
  },
  emptyEmoji: {
    fontSize: 40,
    marginBottom: spacing.sm,
  },
  emptyText: {
    fontSize: 16,
    color: colors.textPrimary,
    fontWeight: '500',
    marginBottom: spacing.xs,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.textMuted,
  },
});
