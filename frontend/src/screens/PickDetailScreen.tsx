import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRoute } from '@react-navigation/native';
import { getPickDetail, placeBet } from '../services/api';
import { colors, spacing, radius } from '../utils/theme';

export const PickDetailScreen = () => {
  const route = useRoute<any>();
  const { id } = route.params;
  const [pick, setPick] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPickDetail(id)
      .then(setPick)
      .finally(() => setLoading(false));
  }, [id]);

  const handleLogBet = () => {
    Alert.prompt(
      'Log Bet',
      `Stake amount (${pick.decimal_odds}x odds)`,
      async (stakeStr) => {
        const stake = parseFloat(stakeStr);
        if (isNaN(stake) || stake <= 0) return;
        try {
          await placeBet({
            game_id: pick.game.id,
            prediction_id: pick.id,
            stake,
            decimal_odds: pick.decimal_odds,
            market: pick.market,
            selection: pick.selection,
          });
          Alert.alert('Bet logged ✓', `$${stake} on ${pick.selection}`);
        } catch {
          Alert.alert('Error', 'Could not log bet');
        }
      },
      'plain-text',
      '',
      'numeric'
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  if (!pick) return null;

  const features = pick.feature_summary ? JSON.parse(pick.feature_summary) : null;
  const evPct = (pick.expected_value * 100).toFixed(1);
  const modelPct = (pick.model_probability * 100).toFixed(0);
  const impliedPct = (pick.implied_probability * 100).toFixed(0);
  const edge = (pick.model_probability - pick.implied_probability) * 100;

  return (
    <ScrollView style={styles.container}>
      {/* Matchup header */}
      <Text style={styles.matchup}>
        {pick.game.away_team} @ {pick.game.home_team}
      </Text>
      <Text style={styles.selection}>
        {pick.market.toUpperCase()} · {pick.selection}
      </Text>

      {/* Key stats */}
      <View style={styles.statsGrid}>
        <StatBox label="Model probability" value={`${modelPct}%`} accent={colors.value} />
        <StatBox label="Book implied" value={`${impliedPct}%`} />
        <StatBox label="Decimal odds" value={pick.decimal_odds.toFixed(2)} />
        <StatBox label="Expected value" value={`+${evPct}%`} accent={colors.value} />
        <StatBox label="Edge" value={`+${edge.toFixed(1)}%`} accent={colors.accent} />
        <StatBox label="Confidence" value={pick.confidence_label.toUpperCase()} />
      </View>

      {/* Model reasoning */}
      {features ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Model reasoning</Text>
          {Object.entries(features).map(([key, val]) => (
            <View key={key} style={styles.featureRow}>
              <Text style={styles.featureKey}>{key.replace(/_/g, ' ')}</Text>
              <Text style={styles.featureVal}>{String(val)}</Text>
            </View>
          ))}
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={styles.premiumNote}>
            🔒 Upgrade to Premium to see full model reasoning and key stats.
          </Text>
        </View>
      )}

      {/* Disclaimer */}
      <Text style={styles.disclaimer}>
        This prediction is based on historical data and statistical modelling.
        It does not guarantee a winning outcome. Always bet within your means.
      </Text>

      {/* CTA */}
      <TouchableOpacity style={styles.btn} onPress={handleLogBet}>
        <Text style={styles.btnText}>Log this bet</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const StatBox = ({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) => (
  <View style={styles.statBox}>
    <Text style={styles.statLabel}>{label}</Text>
    <Text style={[styles.statValue, accent ? { color: accent } : {}]}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.md },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background },
  matchup: { fontSize: 22, fontWeight: '700', color: colors.textPrimary, marginBottom: 4 },
  selection: { fontSize: 13, color: colors.textSecondary, letterSpacing: 0.5, marginBottom: spacing.lg },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.lg },
  statBox: {
    width: '31%',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.sm,
    alignItems: 'center',
  },
  statLabel: { fontSize: 10, color: colors.textMuted, marginBottom: 4, textAlign: 'center' },
  statValue: { fontSize: 15, fontWeight: '700', color: colors.textPrimary },
  section: { backgroundColor: colors.surface, borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.md },
  sectionTitle: { fontSize: 13, fontWeight: '600', color: colors.textSecondary, marginBottom: spacing.sm, letterSpacing: 0.5 },
  featureRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: colors.border },
  featureKey: { fontSize: 13, color: colors.textSecondary, textTransform: 'capitalize', flex: 1 },
  featureVal: { fontSize: 13, fontWeight: '500', color: colors.textPrimary },
  premiumNote: { fontSize: 13, color: colors.neutral, lineHeight: 20 },
  disclaimer: { fontSize: 11, color: colors.textMuted, lineHeight: 16, marginBottom: spacing.lg },
  btn: { backgroundColor: colors.accent, borderRadius: radius.md, padding: spacing.md, alignItems: 'center', marginBottom: spacing.xl },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
