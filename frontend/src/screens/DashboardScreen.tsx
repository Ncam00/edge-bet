import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, TouchableOpacity, RefreshControl } from 'react-native';
import { getBankroll, getBets, getTodaysPicks, getTopProps, getSharpSignals } from '../services/api';
import { colors, spacing, radius } from '../utils/theme';

export const DashboardScreen = () => {
  const [stats, setStats] = useState<any>(null);
  const [bets, setBets] = useState<any[]>([]);
  const [picks, setPicks] = useState<any[]>([]);
  const [props, setProps] = useState<any[]>([]);
  const [sharpSignals, setSharpSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [bankroll, betsData, picksData, propsData, sharpsData] = await Promise.all([
        getBankroll().catch(() => null),
        getBets().catch(() => []),
        getTodaysPicks().catch(() => []),
        getTopProps().catch(() => ({ props: [] })),
        getSharpSignals().catch(() => ({ signals: [] })),
      ]);
      
      setStats(bankroll);
      setBets(Array.isArray(betsData) ? betsData : []);
      setPicks(Array.isArray(picksData) ? picksData : []);
      setProps(Array.isArray(propsData?.props) ? propsData.props : []);
      setSharpSignals(Array.isArray(sharpsData?.signals) ? sharpsData.signals : []);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

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

  // Filter HIGH confidence picks
  const highPicks = picks.filter((p: any) => p.confidence_label === 'high');
  const highProps = props.filter((p: any) => p.confidence === 'HIGH');

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />
      }
    >
      <Text style={styles.title}>EdgeBet Dashboard</Text>

      {/* HIGH Confidence Alert */}
      {(highPicks.length > 0 || highProps.length > 0) && (
        <View style={styles.alertCard}>
          <Text style={styles.alertTitle}>🔥 HIGH VALUE ALERTS</Text>
          <Text style={styles.alertCount}>
            {highPicks.length + highProps.length} top picks today
          </Text>
        </View>
      )}

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

      {/* Value Bets Section */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>🎯 TODAY'S VALUE BETS</Text>
        <Text style={styles.sectionCount}>{picks.length} picks</Text>
      </View>
      
      {picks.slice(0, 5).map((pick: any, index: number) => (
        <ValueBetCard key={index} pick={pick} />
      ))}

      {picks.length === 0 && (
        <Text style={styles.empty}>No value bets found. Check back soon!</Text>
      )}

      {/* Player Props Section */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>🏀 PLAYER PROPS</Text>
        <Text style={styles.sectionCount}>{props.length} props</Text>
      </View>
      
      {props.slice(0, 4).map((prop: any, index: number) => (
        <PropCard key={index} prop={prop} />
      ))}

      {props.length === 0 && (
        <Text style={styles.empty}>No player prop value bets found.</Text>
      )}

      {/* Sharp Money Section */}
      {sharpSignals.length > 0 && (
        <>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>🔍 SHARP MONEY SIGNALS</Text>
            <Text style={styles.sectionCount}>{sharpSignals.length} signals</Text>
          </View>
          
          {sharpSignals.slice(0, 3).map((signal: any, index: number) => (
            <SharpCard key={index} signal={signal} />
          ))}
        </>
      )}

      {/* Recent bets */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>📋 RECENT BETS</Text>
      </View>
      
      {bets.slice(0, 5).map((bet) => (
        <BetRow key={bet.id} bet={bet} />
      ))}

      {bets.length === 0 && (
        <Text style={styles.empty}>No bets logged yet. Start tracking from the Picks tab.</Text>
      )}
      
      <View style={{ height: 40 }} />
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

const ValueBetCard = ({ pick }: { pick: any }) => {
  const isHigh = pick.confidence_label === 'high';
  const accent = isHigh ? colors.value : colors.neutral;
  const evPct = (pick.expected_value * 100).toFixed(1);
  
  return (
    <View style={[styles.valueCard, { borderLeftColor: accent }]}>
      <View style={styles.valueHeader}>
        <Text style={[styles.confidenceBadge, { backgroundColor: isHigh ? colors.valueBg : colors.neutralBg, color: accent }]}>
          {isHigh ? '● HIGH' : '● VALUE'}
        </Text>
        <Text style={styles.valueOdds}>@{pick.decimal_odds?.toFixed(2)}</Text>
      </View>
      <Text style={styles.valueMatchup}>
        {pick.away_team || pick.game?.away_team} @ {pick.home_team || pick.game?.home_team}
      </Text>
      <Text style={styles.valueSelection}>{pick.market?.toUpperCase()} — {pick.selection}</Text>
      <View style={styles.valueStats}>
        <Text style={styles.valueStat}>Model: {(pick.model_probability * 100).toFixed(0)}%</Text>
        <Text style={styles.valueStat}>Book: {(pick.implied_probability * 100).toFixed(0)}%</Text>
        <Text style={[styles.valueEV, { color: accent }]}>+{evPct}% EV</Text>
      </View>
    </View>
  );
};

const PropCard = ({ prop }: { prop: any }) => {
  const isHigh = prop.confidence === 'HIGH';
  const accent = isHigh ? colors.value : colors.neutral;
  const valuePct = (prop.value * 100).toFixed(1);
  
  return (
    <View style={[styles.propCard, { borderLeftColor: accent }]}>
      <View style={styles.propHeader}>
        <Text style={styles.propPlayer}>{prop.player}</Text>
        <Text style={[styles.propBet, { color: accent }]}>{prop.best_bet}</Text>
      </View>
      <Text style={styles.propLine}>
        {prop.prop_type?.toUpperCase()} {prop.line} vs {prop.opponent}
      </Text>
      <View style={styles.propStats}>
        <Text style={styles.propStat}>Proj: {prop.projection}</Text>
        <Text style={styles.propStat}>Prob: {(prop.probability * 100).toFixed(0)}%</Text>
        <Text style={[styles.propValue, { color: accent }]}>+{valuePct}%</Text>
      </View>
    </View>
  );
};

const SharpCard = ({ signal }: { signal: any }) => {
  const isStrong = signal.confidence === 'HIGH';
  const accent = isStrong ? colors.value : colors.neutral;
  
  return (
    <View style={[styles.sharpCard, { borderLeftColor: accent }]}>
      <View style={styles.sharpHeader}>
        <Text style={styles.sharpType}>{signal.alert_type}</Text>
        <Text style={[styles.sharpStrength, { color: accent }]}>
          {(signal.signal_strength * 100).toFixed(0)}%
        </Text>
      </View>
      <Text style={styles.sharpGame}>{signal.game}</Text>
      <Text style={styles.sharpRec}>{signal.recommendation}</Text>
    </View>
  );
};

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
  
  // Alert card
  alertCard: {
    backgroundColor: colors.valueBg,
    borderRadius: radius.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.value + '40',
    alignItems: 'center',
  },
  alertTitle: { fontSize: 16, fontWeight: '700', color: colors.value, marginBottom: 4 },
  alertCount: { fontSize: 13, color: colors.value },
  
  // Bankroll
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
  
  // Stats grid
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.lg },
  statCard: {
    width: '47%',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  statLabel: { fontSize: 11, color: colors.textMuted, marginBottom: 4 },
  statValue: { fontSize: 22, fontWeight: '700', color: colors.textPrimary },
  
  // Section headers
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: spacing.md, marginBottom: spacing.sm },
  sectionTitle: { fontSize: 14, fontWeight: '600', color: colors.textSecondary, letterSpacing: 0.5 },
  sectionCount: { fontSize: 12, color: colors.textMuted },
  
  // Value bet cards
  valueCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderLeftWidth: 3,
  },
  valueHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  confidenceBadge: { fontSize: 10, fontWeight: '700', paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.pill, overflow: 'hidden' },
  valueOdds: { fontSize: 14, fontWeight: '600', color: colors.textSecondary },
  valueMatchup: { fontSize: 15, fontWeight: '600', color: colors.textPrimary, marginBottom: 2 },
  valueSelection: { fontSize: 12, color: colors.textMuted, marginBottom: 8 },
  valueStats: { flexDirection: 'row', justifyContent: 'space-between' },
  valueStat: { fontSize: 12, color: colors.textMuted },
  valueEV: { fontSize: 14, fontWeight: '700' },
  
  // Prop cards
  propCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
    borderLeftWidth: 3,
  },
  propHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  propPlayer: { fontSize: 14, fontWeight: '600', color: colors.textPrimary },
  propBet: { fontSize: 12, fontWeight: '700' },
  propLine: { fontSize: 12, color: colors.textMuted, marginVertical: 4 },
  propStats: { flexDirection: 'row', justifyContent: 'space-between' },
  propStat: { fontSize: 11, color: colors.textMuted },
  propValue: { fontSize: 13, fontWeight: '600' },
  
  // Sharp cards
  sharpCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
    borderLeftWidth: 3,
  },
  sharpHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  sharpType: { fontSize: 10, fontWeight: '700', color: colors.accent, letterSpacing: 0.5 },
  sharpStrength: { fontSize: 14, fontWeight: '700' },
  sharpGame: { fontSize: 13, fontWeight: '500', color: colors.textPrimary, marginVertical: 4 },
  sharpRec: { fontSize: 11, color: colors.textSecondary },
  
  // Bet rows
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
  empty: { color: colors.textMuted, fontSize: 13, textAlign: 'center', paddingTop: 20, paddingBottom: 20 },
});
