import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors, spacing, radius } from '../utils/theme';

interface PickCardProps {
  game: {
    home_team: string;
    away_team: string;
    commence_time: string;
  };
  market: string;
  selection: string;
  model_probability: number;
  implied_probability: number;
  decimal_odds: number;
  expected_value: number;
  confidence_label: 'high' | 'medium' | 'low';
  onPress?: () => void;
}

const EV_COLOR = {
  high: colors.value,
  medium: colors.neutral,
  low: colors.textMuted,
};

const EV_BG = {
  high: colors.valueBg,
  medium: colors.neutralBg,
  low: colors.surfaceAlt,
};

const EV_LABEL = {
  high: '● HIGH VALUE',
  medium: '● VALUE',
  low: '● WATCH',
};

export const PickCard: React.FC<PickCardProps> = ({
  game,
  market,
  selection,
  model_probability,
  implied_probability,
  decimal_odds,
  expected_value,
  confidence_label,
  onPress,
}) => {
  const accent = EV_COLOR[confidence_label];
  const bg = EV_BG[confidence_label];
  const kickoff = new Date(game.commence_time).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
  const evPct = (expected_value * 100).toFixed(1);
  const modelPct = (model_probability * 100).toFixed(0);
  const impliedPct = (implied_probability * 100).toFixed(0);

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.8}>
      <View style={[styles.card, { borderLeftColor: accent }]}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.badge, { color: accent, backgroundColor: bg }]}>
            {EV_LABEL[confidence_label]}
          </Text>
          <Text style={styles.time}>{kickoff}</Text>
        </View>

        {/* Matchup */}
        <Text style={styles.matchup}>
          {game.away_team} @ {game.home_team}
        </Text>
        <Text style={styles.selection}>
          {market.toUpperCase()} — {selection}
        </Text>

        {/* Stats row */}
        <View style={styles.statsRow}>
          <Stat label="Model prob" value={`${modelPct}%`} accent={accent} />
          <Stat label="Book implied" value={`${impliedPct}%`} />
          <Stat label="Odds" value={decimal_odds.toFixed(2)} />
          <Stat label="EV" value={`+${evPct}%`} accent={accent} large />
        </View>
      </View>
    </TouchableOpacity>
  );
};

const Stat = ({
  label,
  value,
  accent,
  large,
}: {
  label: string;
  value: string;
  accent?: string;
  large?: boolean;
}) => (
  <View style={styles.stat}>
    <Text style={styles.statLabel}>{label}</Text>
    <Text
      style={[
        styles.statValue,
        accent ? { color: accent } : {},
        large ? { fontSize: 18 } : {},
      ]}
    >
      {value}
    </Text>
  </View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderLeftWidth: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  badge: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.pill,
    overflow: 'hidden',
  },
  time: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  matchup: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  selection: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.md,
    letterSpacing: 0.5,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  stat: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 10,
    color: colors.textMuted,
    marginBottom: 2,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
});
