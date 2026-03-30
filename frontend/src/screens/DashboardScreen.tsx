import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import { getBankroll, getBets } from '../services/api';
import { colors, spacing, radius } from '../utils/theme';

export const DashboardScreen = () => {
  const [stats, setStats] = useState<any>(null);
  const [bets, setBets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getBankroll(), getBets()])
      .then(([s, b]) => {
        setStats(s);
        setBets(b);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  const roi = stats?.roi !== null ? `${(stats.roi * 100).toFixed(1)}%` : '—';
  const winRate = stats?.win_rate !== null ? `${(stats.win_rate * 100).toFixed(0)}%` : '—';
  const pl = stats?.total_profit_loss ?? 0;
  const plColor = pl >= 0 ? colors.value : colors.avoid;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Dashboard</Text>

      {/* Bankroll */}
      <View style={styles.bankrollCard}>
        <Text style={styles.bankrollLabel}>Current bankroll</Text>
        <Text style={styles.bankrollAmount}>
          ${stats?.bankroll?.toFixed(2) ?? '0.00'}
        </Text>
        <Text style={[styles.bankrollPL, { color: plColor }]}>
          {pl >= 0 ? '+' : ''}${pl.toFixed(2)} all time
        </Text>
      </View>

      {/* Stats grid */}
      <View style={styles.grid}>
        <StatCard label="Total bets" value={String(stats?.total_bets ?? 0)} />
        <StatCard label="Win rate" value={winRate} accent={colors.value} />
        <StatCard label="ROI" value={roi} accent={pl >= 0 ? colors.value : colors.avoid} />
        <StatCard label="Total staked" value={`$${stats?.total_staked?.toFixed(0) ?? 0}`} />
      </View>

      {/* Recent bets */}
      <Text style={styles.sectionTitle}>Recent bets</Text>
      {bets.slice(0, 10).map((bet) => (
        <BetRow key={bet.id} bet={bet} />
      ))}

      {bets.length === 0 && (
        <Text style={styles.empty}>No bets logged yet. Start tracking from the Picks tab.</Text>
      )}
    </ScrollView>
  );
};

const StatCard = ({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) => (
  <View style={styles.statCard}>
    <Text style={styles.statLabel}>{label}</Text>
    <Text style={[styles.statValue, accent ? { color: accent } : {}]}>{value}</Text>
  </View>
);

const BetRow = ({ bet }: { bet: any }) => {
  const OUTCOME_COLOR: Record<string, string> = {
    win: colors.value,
    loss: colors.avoid,
    pending: colors.neutral,
    push: colors.textSecondary,
  };
  const color = OUTCOME_COLOR[bet.outcome] ?? colors.textSecondary;
  const pl = bet.profit_loss;

  return (
    <View style={styles.betRow}>
      <View style={{ flex: 1 }}>
        <Text style={styles.betMatchup} numberOfLines={1}>
          {bet.game?.away_team} @ {bet.game?.home_team}
        </Text>
        <Text style={styles.betMeta}>
          {bet.market} · {bet.selection} · ${bet.stake} @ {bet.decimal_odds}
        </Text>
      </View>
      <View style={{ alignItems: 'flex-end' }}>
        <Text style={[styles.betOutcome, { color }]}>{bet.outcome.toUpperCase()}</Text>
        {pl !== null && (
          <Text style={[styles.betPL, { color: pl >= 0 ? colors.value : colors.avoid }]}>
            {pl >= 0 ? '+' : ''}${pl.toFixed(2)}
          </Text>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.md },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background },
  title: { fontSize: 24, fontWeight: '700', color: colors.textPrimary, marginBottom: spacing.md },
  bankrollCard: {
    backgroundColor: colors.accentBg,
    borderRadius: radius.lg,
    padding: spacing.lg,
    alignItems: 'center',
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.accent + '40',
  },
  bankrollLabel: { fontSize: 12, color: colors.textSecondary, letterSpacing: 0.5, marginBottom: 4 },
  bankrollAmount: { fontSize: 40, fontWeight: '700', color: colors.textPrimary },
  bankrollPL: { fontSize: 14, marginTop: 4 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.lg },
  statCard: {
    width: '47%',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  statLabel: { fontSize: 11, color: colors.textMuted, marginBottom: 4 },
  statValue: { fontSize: 22, fontWeight: '700', color: colors.textPrimary },
  sectionTitle: { fontSize: 14, fontWeight: '600', color: colors.textSecondary, marginBottom: spacing.sm, letterSpacing: 0.5 },
  betRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginBottom: 6,
  },
  betMatchup: { fontSize: 13, fontWeight: '500', color: colors.textPrimary, marginBottom: 2 },
  betMeta: { fontSize: 11, color: colors.textMuted },
  betOutcome: { fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
  betPL: { fontSize: 13, fontWeight: '600', marginTop: 2 },
  empty: { color: colors.textMuted, fontSize: 13, textAlign: 'center', paddingTop: 40 },
});
