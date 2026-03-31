import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, TouchableOpacity, RefreshControl, Modal, Platform } from 'react-native';
import { getTodaysRaces, getRacingTips, getRacingSummary, getRunnerAnalysis, getLiveVideoStreams, getYouTubeRacingStreams, getRaceVideo } from '../services/api';
import { colors, spacing, radius } from '../utils/theme';

interface Tip {
  race_id: string;
  track: string;
  race_number: number;
  race_name: string;
  post_time: string;
  race_type: string;
  country: string;
  going: string;
  distance: string;
  runner_number: number;
  runner_name: string;
  odds: number;
  morning_line: number;
  trainer: string;
  jockey: string | null;
  bet_type: string;
  confidence: string;
  confidence_score: number;
  expected_value: number;
  stake_percentage: number;
  form: string;
  form_rating: number;
  form_trend: string;
  reasoning: string[];
  edge_factors: string[];
  warnings: string[];
}

interface Race {
  id: string;
  race_type: string;
  track: string;
  country: string;
  race_number: number;
  race_name: string;
  distance: string;
  race_class?: string;
  going?: string;
  post_time: string;
  prize_money?: number;
  runners_count?: number;
  video?: {
    embed_url: string;
    backup_url: string;
    source: string;
    stream_type: string;
    is_live: boolean;
  };
}

interface VideoStream {
  id: string;
  name: string;
  url: string;
  embed_url: string;
  stream_type: string;
  region: string;
  is_live: boolean;
  thumbnail?: string;
}

interface RacingSummary {
  horses: { races: number; tracks: string[]; value_bets: number; high_confidence: number };
  greyhounds: { races: number; tracks: string[]; value_bets: number; high_confidence: number };
  total_value_bets: number;
}

interface RunnerAnalysis {
  runner: any;
  race: any;
  form_analysis: any;
  recommendation: any;
  verdict: string;
}

export const RacingScreen = () => {
  const [tips, setTips] = useState<Tip[]>([]);
  const [races, setRaces] = useState<Race[]>([]);
  const [summary, setSummary] = useState<RacingSummary | null>(null);
  const [videoStreams, setVideoStreams] = useState<VideoStream[]>([]);
  const [activeTab, setActiveTab] = useState<'tips' | 'races' | 'live'>('tips');
  const [raceTypeFilter, setRaceTypeFilter] = useState<'all' | 'horse' | 'greyhound'>('all');
  const [regionFilter, setRegionFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTip, setSelectedTip] = useState<Tip | null>(null);
  const [runnerDetail, setRunnerDetail] = useState<RunnerAnalysis | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<VideoStream | null>(null);
  const [selectedRaceVideo, setSelectedRaceVideo] = useState<Race | null>(null);

  const loadData = async () => {
    try {
      const raceType = raceTypeFilter === 'all' ? undefined : raceTypeFilter;
      const region = regionFilter === 'all' ? undefined : regionFilter;
      const [tipsData, racesData, summaryData, videoData] = await Promise.all([
        getRacingTips(20, raceType).catch(() => ({ tips: [] })),
        getTodaysRaces(raceType).catch(() => ({ races: [] })),
        getRacingSummary().catch(() => null),
        getLiveVideoStreams(region).catch(() => ({ streams: [] })),
      ]);
      setTips(Array.isArray(tipsData?.tips) ? tipsData.tips : []);
      setRaces(Array.isArray(racesData?.races) ? racesData.races : []);
      setSummary(summaryData);
      setVideoStreams(Array.isArray(videoData?.streams) ? videoData.streams : []);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    loadData();
  }, [raceTypeFilter]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const loadRunnerDetail = async (tip: Tip) => {
    setSelectedTip(tip);
    setDetailLoading(true);
    try {
      const data = await getRunnerAnalysis(tip.race_id, tip.runner_number);
      setRunnerDetail(data);
    } catch {
      setRunnerDetail(null);
    } finally {
      setDetailLoading(false);
    }
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
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accent} />}
      >
        <Text style={styles.title}>Racing Tips</Text>
        <Text style={styles.subtitle}>AI-powered form analysis & betting recommendations</Text>

        {/* Summary Stats */}
        {summary && (
          <View style={styles.summaryCard}>
            <View style={styles.summaryRow}>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{tips.filter(t => t.confidence === 'HIGH').length}</Text>
                <Text style={styles.statLabel}>🔥 Hot Tips</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>🏇 {summary.horses?.races || 0}</Text>
                <Text style={styles.statLabel}>Horse Races</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>🐕 {summary.greyhounds?.races || 0}</Text>
                <Text style={styles.statLabel}>Greyhound</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={[styles.statValue, { color: colors.value }]}>{summary.total_value_bets || 0}</Text>
                <Text style={styles.statLabel}>Value Bets</Text>
              </View>
            </View>
          </View>
        )}

        {/* Filter Row */}
        <View style={styles.filterRow}>
          {(['all', 'horse', 'greyhound'] as const).map((type) => (
            <TouchableOpacity
              key={type}
              style={[styles.filterPill, raceTypeFilter === type && styles.filterPillActive]}
              onPress={() => setRaceTypeFilter(type)}
            >
              <Text style={[styles.filterText, raceTypeFilter === type && styles.filterTextActive]}>
                {type === 'all' ? '🎯 All' : type === 'horse' ? '🏇 Horses' : '🐕 Greys'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Tab Row */}
        <View style={styles.tabRow}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'tips' && styles.tabActive]}
            onPress={() => setActiveTab('tips')}
          >
            <Text style={[styles.tabText, activeTab === 'tips' && styles.tabTextActive]}>💎 Tips</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'races' && styles.tabActive]}
            onPress={() => setActiveTab('races')}
          >
            <Text style={[styles.tabText, activeTab === 'races' && styles.tabTextActive]}>📅 Races</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'live' && styles.tabActive]}
            onPress={() => setActiveTab('live')}
          >
            <Text style={[styles.tabText, activeTab === 'live' && styles.tabTextActive]}>📺 Live TV</Text>
          </TouchableOpacity>
        </View>

        {activeTab === 'tips' ? (
          <>
            {tips.length > 0 ? (
              tips.map((tip, index) => (
                <TipCard key={`${tip.race_id}-${tip.runner_number}-${index}`} tip={tip} onPress={() => loadRunnerDetail(tip)} />
              ))
            ) : (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyEmoji}>🔍</Text>
                <Text style={styles.emptyText}>No tips available</Text>
                <Text style={styles.emptySubtext}>Check back when racing starts</Text>
              </View>
            )}
          </>
        ) : activeTab === 'races' ? (
          <>
            {races.length > 0 ? (
              races.map((race) => (
                <RaceCard 
                  key={race.id} 
                  race={race} 
                  onWatchVideo={() => setSelectedRaceVideo(race)}
                />
              ))
            ) : (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyEmoji}>🏁</Text>
                <Text style={styles.emptyText}>No races available</Text>
                <Text style={styles.emptySubtext}>Check back when racing starts</Text>
              </View>
            )}
          </>
        ) : (
          <>
            {/* Live TV Tab */}
            <Text style={styles.sectionTitle}>📺 Live Racing Streams</Text>
            <Text style={styles.sectionSubtitle}>Free live video from racing channels worldwide</Text>
            
            {/* Region Filter */}
            <View style={styles.regionFilterRow}>
              {['all', 'AU', 'UK', 'US', 'HK'].map((region) => (
                <TouchableOpacity
                  key={region}
                  style={[styles.regionPill, regionFilter === region && styles.regionPillActive]}
                  onPress={() => setRegionFilter(region)}
                >
                  <Text style={[styles.regionText, regionFilter === region && styles.regionTextActive]}>
                    {region === 'all' ? '🌍 All' : region === 'AU' ? '🇦🇺 AUS' : region === 'UK' ? '🇬🇧 UK' : region === 'US' ? '🇺🇸 US' : '🇭🇰 HK'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            
            {videoStreams.length > 0 ? (
              videoStreams.map((stream, index) => (
                <VideoStreamCard 
                  key={`${stream.id}-${index}`} 
                  stream={stream}
                  onWatch={() => setSelectedVideo(stream)}
                />
              ))
            ) : (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyEmoji}>📺</Text>
                <Text style={styles.emptyText}>Loading streams...</Text>
                <Text style={styles.emptySubtext}>Free live racing video coming soon</Text>
              </View>
            )}
          </>
        )}
      </ScrollView>

      {/* Runner Detail Modal */}
      <Modal visible={!!selectedTip} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <TouchableOpacity style={styles.modalClose} onPress={() => { setSelectedTip(null); setRunnerDetail(null); }}>
              <Text style={styles.modalCloseText}>✕</Text>
            </TouchableOpacity>
            
            {detailLoading ? (
              <View style={styles.modalLoader}>
                <ActivityIndicator color={colors.accent} size="large" />
              </View>
            ) : selectedTip && (
              <ScrollView showsVerticalScrollIndicator={false}>
                <RunnerDetailView tip={selectedTip} detail={runnerDetail} />
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      {/* Video Stream Modal */}
      <Modal visible={!!selectedVideo} animationType="slide" transparent>
        <View style={styles.videoModalOverlay}>
          <View style={styles.videoModalContent}>
            <View style={styles.videoModalHeader}>
              <Text style={styles.videoModalTitle}>📺 {selectedVideo?.name}</Text>
              <TouchableOpacity onPress={() => setSelectedVideo(null)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>
            {selectedVideo && (
              <VideoPlayer 
                embedUrl={selectedVideo.embed_url} 
                streamType={selectedVideo.stream_type}
                name={selectedVideo.name}
              />
            )}
          </View>
        </View>
      </Modal>

      {/* Race Video Modal */}
      <Modal visible={!!selectedRaceVideo} animationType="slide" transparent>
        <View style={styles.videoModalOverlay}>
          <View style={styles.videoModalContent}>
            <View style={styles.videoModalHeader}>
              <Text style={styles.videoModalTitle}>
                📺 {selectedRaceVideo?.track} R{selectedRaceVideo?.race_number}
              </Text>
              <TouchableOpacity onPress={() => setSelectedRaceVideo(null)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>
            {selectedRaceVideo?.video && (
              <VideoPlayer 
                embedUrl={selectedRaceVideo.video.embed_url} 
                streamType={selectedRaceVideo.video.stream_type}
                name={`${selectedRaceVideo.track} Race ${selectedRaceVideo.race_number}`}
                backupUrl={selectedRaceVideo.video.backup_url}
              />
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
};

// Tip Card Component - Shows betting recommendation
const TipCard = ({ tip, onPress }: { tip: Tip; onPress: () => void }) => {
  const emoji = tip.race_type === 'horse' ? '🏇' : '🐕';
  const betTypeEmoji = tip.bet_type === 'win' ? '📈' : tip.bet_type === 'place' ? '🎯' : '💎';
  const confidenceColor = tip.confidence === 'HIGH' ? colors.value : tip.confidence === 'MEDIUM' ? colors.accent : colors.textMuted;
  const trendEmoji = tip.form_trend === 'improving' ? '📈' : tip.form_trend === 'declining' ? '📉' : '➡️';

  return (
    <TouchableOpacity style={styles.tipCard} onPress={onPress}>
      {/* Header */}
      <View style={styles.tipHeader}>
        <View style={styles.tipLeft}>
          <Text style={styles.tipEmoji}>{emoji}</Text>
          <View style={styles.tipNameBox}>
            <Text style={styles.tipRunner}>{tip.runner_name}</Text>
            <Text style={styles.tipTrack}>{tip.track} R{tip.race_number}</Text>
          </View>
        </View>
        <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor }]}>
          <Text style={styles.confidenceText}>{tip.confidence}</Text>
        </View>
      </View>

      {/* Bet Type & Key Numbers */}
      <View style={styles.tipBetRow}>
        <View style={styles.betTypeBox}>
          <Text style={styles.betTypeEmoji}>{betTypeEmoji}</Text>
          <Text style={styles.betTypeText}>{tip.bet_type.toUpperCase()}</Text>
        </View>
        <View style={styles.oddsBox}>
          <Text style={styles.boxLabel}>Odds</Text>
          <Text style={styles.oddsValue}>{tip.odds.toFixed(2)}</Text>
        </View>
        <View style={styles.evBox}>
          <Text style={styles.boxLabel}>Value</Text>
          <Text style={[styles.evValue, { color: colors.value }]}>+{(tip.expected_value * 100).toFixed(1)}%</Text>
        </View>
        <View style={styles.stakeBox}>
          <Text style={styles.boxLabel}>Stake</Text>
          <Text style={styles.stakeValue}>{tip.stake_percentage}%</Text>
        </View>
      </View>

      {/* Form Analysis Summary */}
      <View style={styles.formRow}>
        <View style={styles.formItem}>
          <Text style={styles.formLabel}>Form</Text>
          <Text style={styles.formValue}>{tip.form}</Text>
        </View>
        <View style={styles.formItem}>
          <Text style={styles.formLabel}>Rating</Text>
          <Text style={styles.formValue}>{tip.form_rating.toFixed(0)}/100</Text>
        </View>
        <View style={styles.formItem}>
          <Text style={styles.formLabel}>Trend</Text>
          <Text style={styles.formValue}>{trendEmoji} {tip.form_trend}</Text>
        </View>
      </View>

      {/* Key Reasons - Why to bet */}
      {tip.reasoning && tip.reasoning.length > 0 && (
        <View style={styles.reasonsBox}>
          {tip.reasoning.slice(0, 2).map((reason, i) => (
            <View key={i} style={styles.reasonRow}>
              <Text style={styles.reasonBullet}>✓</Text>
              <Text style={styles.reasonText}>{reason}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Risk Warnings */}
      {tip.warnings && tip.warnings.length > 0 && (
        <View style={styles.warningsBox}>
          {tip.warnings.slice(0, 1).map((warning, i) => (
            <View key={i} style={styles.warningRow}>
              <Text style={styles.warningBullet}>⚠️</Text>
              <Text style={styles.warningText}>{warning}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Meta - Trainer, Jockey, Time */}
      <View style={styles.metaRow}>
        <Text style={styles.metaText}>🎯 {tip.trainer}</Text>
        {tip.jockey && <Text style={styles.metaText}>🏇 {tip.jockey}</Text>}
        <Text style={styles.metaText}>
          ⏰ {new Date(tip.post_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      </View>

      <Text style={styles.tapHint}>Tap for full form analysis →</Text>
    </TouchableOpacity>
  );
};

// Full Runner Detail View - Shows in modal
const RunnerDetailView = ({ tip, detail }: { tip: Tip; detail: RunnerAnalysis | null }) => {
  const emoji = tip.race_type === 'horse' ? '🏇' : '🐕';
  
  return (
    <View>
      <Text style={styles.detailTitle}>{emoji} {tip.runner_name}</Text>
      <Text style={styles.detailSubtitle}>{tip.track} R{tip.race_number} • {tip.distance} • {tip.going}</Text>

      {/* Verdict Card - The bottom line */}
      {detail?.verdict && (
        <View style={styles.verdictCard}>
          <Text style={styles.verdictTitle}>🎯 THE VERDICT</Text>
          <Text style={styles.verdictText}>{detail.verdict}</Text>
        </View>
      )}

      {/* Recommendation Card */}
      {detail?.recommendation && (
        <View style={styles.recCard}>
          <Text style={styles.recTitle}>💰 BETTING RECOMMENDATION</Text>
          <View style={styles.recRow}>
            <View style={styles.recItem}>
              <Text style={styles.recLabel}>Bet Type</Text>
              <Text style={styles.recValue}>{detail.recommendation.bet_type?.toUpperCase() || 'N/A'}</Text>
            </View>
            <View style={styles.recItem}>
              <Text style={styles.recLabel}>Confidence</Text>
              <Text style={[styles.recValue, { color: detail.recommendation.confidence === 'HIGH' ? colors.value : colors.accent }]}>
                {detail.recommendation.confidence || 'N/A'}
              </Text>
            </View>
            <View style={styles.recItem}>
              <Text style={styles.recLabel}>Stake</Text>
              <Text style={styles.recValue}>{detail.recommendation.stake_percentage || 0}%</Text>
            </View>
          </View>

          {/* Why we like it */}
          {detail.recommendation.reasoning && detail.recommendation.reasoning.length > 0 && (
            <View style={styles.recReasons}>
              <Text style={styles.recReasonsTitle}>Why we like it:</Text>
              {detail.recommendation.reasoning.map((r: string, i: number) => (
                <View key={i} style={styles.recReasonRow}>
                  <Text style={styles.recReasonBullet}>✓</Text>
                  <Text style={styles.recReasonText}>{r}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Our Edge */}
          {detail.recommendation.edge_factors && detail.recommendation.edge_factors.length > 0 && (
            <View style={styles.edgeBox}>
              <Text style={styles.edgeTitle}>🔥 Our Edge:</Text>
              {detail.recommendation.edge_factors.map((e: string, i: number) => (
                <Text key={i} style={styles.edgeText}>• {e}</Text>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Form Analysis Card */}
      {detail?.form_analysis && (
        <View style={styles.formCard}>
          <Text style={styles.formCardTitle}>📊 FORM ANALYSIS</Text>
          
          {/* Form Grid */}
          <View style={styles.formGrid}>
            <View style={styles.formGridItem}>
              <Text style={styles.formGridValue}>{detail.form_analysis.recent_form}</Text>
              <Text style={styles.formGridLabel}>Recent Form</Text>
            </View>
            <View style={styles.formGridItem}>
              <Text style={styles.formGridValue}>{detail.form_analysis.form_rating}/100</Text>
              <Text style={styles.formGridLabel}>Form Rating</Text>
            </View>
            <View style={styles.formGridItem}>
              <Text style={styles.formGridValue}>{detail.form_analysis.wins_last_10}W / {detail.form_analysis.places_last_10}P</Text>
              <Text style={styles.formGridLabel}>Wins/Places</Text>
            </View>
            <View style={styles.formGridItem}>
              <Text style={styles.formGridValue}>{detail.form_analysis.trend}</Text>
              <Text style={styles.formGridLabel}>Trend</Text>
            </View>
          </View>

          {/* Detailed Stats */}
          <View style={styles.formStats}>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Win Strike Rate</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.winning_strike_rate}%</Text>
            </View>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Place Strike Rate</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.place_strike_rate}%</Text>
            </View>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Fitness Score</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.fitness_score}/100</Text>
            </View>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Going Suitability</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.going_suitability}/100</Text>
            </View>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Distance Suitability</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.distance_suitability}/100</Text>
            </View>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Days Since Run</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.days_since_last_run}</Text>
            </View>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Class</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.class_indicator?.replace(/_/g, ' ')}</Text>
            </View>
            <View style={styles.formStatRow}>
              <Text style={styles.formStatLabel}>Track Record</Text>
              <Text style={styles.formStatValue}>{detail.form_analysis.track_record?.replace(/_/g, ' ')}</Text>
            </View>
          </View>

          {/* Key Positives */}
          {detail.form_analysis.key_positives && detail.form_analysis.key_positives.length > 0 && (
            <View style={styles.positivesBox}>
              <Text style={styles.positivesTitle}>✅ Key Positives:</Text>
              {detail.form_analysis.key_positives.map((p: string, i: number) => (
                <Text key={i} style={styles.positiveText}>• {p}</Text>
              ))}
            </View>
          )}

          {/* Cautions */}
          {detail.form_analysis.key_negatives && detail.form_analysis.key_negatives.length > 0 && (
            <View style={styles.negativesBox}>
              <Text style={styles.negativesTitle}>⚠️ Cautions:</Text>
              {detail.form_analysis.key_negatives.map((n: string, i: number) => (
                <Text key={i} style={styles.negativeText}>• {n}</Text>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Runner Info Card */}
      {detail?.runner && (
        <View style={styles.runnerCard}>
          <Text style={styles.runnerCardTitle}>📋 RUNNER INFO</Text>
          <View style={styles.runnerInfoBox}>
            <Text style={styles.runnerInfoRow}>🎯 Trainer: {detail.runner.trainer}</Text>
            {detail.runner.jockey && <Text style={styles.runnerInfoRow}>🏇 Jockey: {detail.runner.jockey}</Text>}
            <Text style={styles.runnerInfoRow}>📊 Age: {detail.runner.age}</Text>
            {detail.runner.weight && <Text style={styles.runnerInfoRow}>⚖️ Weight: {detail.runner.weight} st</Text>}
            {detail.runner.box && <Text style={styles.runnerInfoRow}>📦 Box: {detail.runner.box}</Text>}
          </View>
        </View>
      )}
    </View>
  );
};

// Race Card Component
const RaceCard = ({ race, onWatchVideo }: { race: Race; onWatchVideo?: () => void }) => {
  const raceEmoji = race.race_type === 'horse' ? '🏇' : '🐕';

  return (
    <View style={styles.raceCard}>
      <View style={styles.raceHeader}>
        <View style={styles.raceInfo}>
          <Text style={styles.raceEmoji}>{raceEmoji}</Text>
          <View>
            <View style={styles.raceTitle}>
              <Text style={styles.trackName}>{race.track}</Text>
              <Text style={styles.raceNumber}>R{race.race_number}</Text>
            </View>
            <Text style={styles.raceMeta}>{race.distance} • {race.race_class || ''} • {race.country}</Text>
          </View>
        </View>
        <View style={styles.raceRight}>
          <Text style={styles.postTime}>
            {new Date(race.post_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
          {race.runners_count && race.runners_count > 0 && (
            <View style={styles.runnersBadge}>
              <Text style={styles.runnersBadgeText}>{race.runners_count} runners</Text>
            </View>
          )}
        </View>
      </View>
      {race.race_name && <Text style={styles.raceName}>{race.race_name}</Text>}
      {race.going && <Text style={styles.raceGoing}>Going: {race.going}</Text>}
      
      {/* Watch Video Button */}
      {race.video && onWatchVideo && (
        <TouchableOpacity style={styles.watchVideoBtn} onPress={onWatchVideo}>
          <Text style={styles.watchVideoBtnText}>📺 Watch Live</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

// Video Stream Card Component
const VideoStreamCard = ({ stream, onWatch }: { stream: VideoStream; onWatch: () => void }) => {
  const regionEmoji = stream.region === 'AU' ? '🇦🇺' : stream.region === 'UK' ? '🇬🇧' : stream.region === 'US' ? '🇺🇸' : stream.region === 'HK' ? '🇭🇰' : '🌍';
  const typeIcon = stream.stream_type === 'youtube' ? '▶️' : '📡';
  
  return (
    <TouchableOpacity style={styles.videoCard} onPress={onWatch}>
      <View style={styles.videoCardLeft}>
        <Text style={styles.videoTypeIcon}>{typeIcon}</Text>
        <View style={styles.videoCardInfo}>
          <Text style={styles.videoCardName}>{stream.name}</Text>
          <Text style={styles.videoCardMeta}>
            {regionEmoji} {stream.region} • {stream.stream_type === 'youtube' ? 'YouTube' : 'Live Stream'}
          </Text>
        </View>
      </View>
      <View style={styles.liveIndicator}>
        <View style={styles.liveDot} />
        <Text style={styles.liveText}>LIVE</Text>
      </View>
    </TouchableOpacity>
  );
};

// Video Player Component (Web-based iframe)
const VideoPlayer = ({ 
  embedUrl, 
  streamType, 
  name,
  backupUrl 
}: { 
  embedUrl: string; 
  streamType: string; 
  name: string;
  backupUrl?: string;
}) => {
  const [useBackup, setUseBackup] = useState(false);
  const currentUrl = useBackup && backupUrl ? backupUrl : embedUrl;
  
  // For web, use iframe
  if (Platform.OS === 'web') {
    return (
      <View style={styles.videoPlayerContainer}>
        <View style={styles.videoInfo}>
          <Text style={styles.videoInfoText}>🔴 Live: {name}</Text>
          {backupUrl && (
            <TouchableOpacity onPress={() => setUseBackup(!useBackup)}>
              <Text style={styles.switchStreamBtn}>
                {useBackup ? '📡 Switch to Primary' : '📺 Try Backup Stream'}
              </Text>
            </TouchableOpacity>
          )}
        </View>
        <iframe
          src={currentUrl}
          style={{
            width: '100%',
            height: 400,
            border: 'none',
            borderRadius: 12,
            backgroundColor: '#000',
          }}
          allow="autoplay; fullscreen; encrypted-media"
          allowFullScreen
          title={name}
        />
        <Text style={styles.videoHint}>
          Tip: If the stream doesn't load, try the backup stream or open directly in browser
        </Text>
        <TouchableOpacity 
          style={styles.openExternalBtn}
          onPress={() => window.open(currentUrl, '_blank')}
        >
          <Text style={styles.openExternalBtnText}>🔗 Open in New Tab</Text>
        </TouchableOpacity>
      </View>
    );
  }
  
  // For native, show instructions to open in browser
  return (
    <View style={styles.videoPlayerContainer}>
      <View style={styles.nativeVideoPlaceholder}>
        <Text style={styles.nativeVideoIcon}>📺</Text>
        <Text style={styles.nativeVideoText}>{name}</Text>
        <Text style={styles.nativeVideoSubtext}>
          Live video streaming is best viewed in your browser
        </Text>
        <View style={styles.nativeVideoInfo}>
          <Text style={styles.nativeVideoUrl}>{currentUrl}</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.md },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background },
  title: { fontSize: 28, fontWeight: 'bold', color: colors.textPrimary, marginBottom: spacing.xs },
  subtitle: { fontSize: 14, color: colors.textMuted, marginBottom: spacing.lg },

  // Summary
  summaryCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.lg },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between' },
  statBox: { alignItems: 'center' },
  statValue: { fontSize: 20, fontWeight: 'bold', color: colors.textPrimary },
  statLabel: { fontSize: 11, color: colors.textMuted, marginTop: 2 },

  // Filters
  filterRow: { flexDirection: 'row', marginBottom: spacing.md },
  filterPill: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm, backgroundColor: colors.surface, borderRadius: radius.md, marginRight: spacing.sm },
  filterPillActive: { backgroundColor: colors.accent },
  filterText: { fontSize: 13, color: colors.textMuted, fontWeight: '500' },
  filterTextActive: { color: '#fff' },

  // Tabs
  tabRow: { flexDirection: 'row', marginBottom: spacing.lg },
  tab: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', backgroundColor: colors.surface, borderRadius: radius.md, marginHorizontal: 4 },
  tabActive: { backgroundColor: colors.accent },
  tabText: { fontSize: 14, color: colors.textMuted, fontWeight: '500' },
  tabTextActive: { color: '#fff' },

  // Tip Card
  tipCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.md, borderLeftWidth: 4, borderLeftColor: colors.value },
  tipHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing.sm },
  tipLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  tipNameBox: { flex: 1 },
  tipEmoji: { fontSize: 28, marginRight: spacing.sm },
  tipRunner: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
  tipTrack: { fontSize: 13, color: colors.textMuted },
  confidenceBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: radius.sm },
  confidenceText: { fontSize: 11, fontWeight: '700', color: '#fff' },

  // Bet Row
  tipBetRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.sm, paddingVertical: spacing.sm, borderTopWidth: 1, borderBottomWidth: 1, borderColor: colors.border },
  betTypeBox: { flexDirection: 'row', alignItems: 'center' },
  betTypeEmoji: { fontSize: 16, marginRight: 4 },
  betTypeText: { fontSize: 13, fontWeight: '700', color: colors.accent },
  oddsBox: { alignItems: 'center' },
  boxLabel: { fontSize: 10, color: colors.textMuted },
  oddsValue: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  evBox: { alignItems: 'center' },
  evValue: { fontSize: 14, fontWeight: '700' },
  stakeBox: { alignItems: 'center' },
  stakeValue: { fontSize: 14, fontWeight: '600', color: colors.textPrimary },

  // Form Row
  formRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.sm },
  formItem: { alignItems: 'center' },
  formLabel: { fontSize: 10, color: colors.textMuted },
  formValue: { fontSize: 13, fontWeight: '600', color: colors.textPrimary },

  // Reasons
  reasonsBox: { backgroundColor: colors.background, borderRadius: radius.sm, padding: spacing.sm, marginBottom: spacing.sm },
  reasonRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 4 },
  reasonBullet: { color: colors.value, marginRight: 6, fontWeight: '700' },
  reasonText: { fontSize: 12, color: colors.textSecondary, flex: 1 },

  // Warnings
  warningsBox: { backgroundColor: '#ffcc0020', borderRadius: radius.sm, padding: spacing.sm, marginBottom: spacing.sm },
  warningRow: { flexDirection: 'row', alignItems: 'flex-start' },
  warningBullet: { marginRight: 6 },
  warningText: { fontSize: 12, color: '#cc9900', flex: 1 },

  // Meta
  metaRow: { flexDirection: 'row', flexWrap: 'wrap' },
  metaText: { fontSize: 11, color: colors.textMuted, marginRight: spacing.md },
  tapHint: { fontSize: 11, color: colors.accent, marginTop: spacing.xs, textAlign: 'right' },

  // Race Card
  raceCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.md },
  raceHeader: { flexDirection: 'row', justifyContent: 'space-between' },
  raceInfo: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  raceEmoji: { fontSize: 24, marginRight: spacing.sm },
  raceTitle: { flexDirection: 'row', alignItems: 'center' },
  trackName: { fontSize: 16, fontWeight: '600', color: colors.textPrimary },
  raceNumber: { fontSize: 14, color: colors.textMuted, marginLeft: spacing.sm },
  raceMeta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  raceRight: { alignItems: 'flex-end' },
  postTime: { fontSize: 14, fontWeight: '600', color: colors.accent },
  runnersBadge: { backgroundColor: colors.value + '20', paddingHorizontal: 6, paddingVertical: 2, borderRadius: radius.sm, marginTop: 4 },
  runnersBadgeText: { fontSize: 10, color: colors.value, fontWeight: '600' },
  raceName: { fontSize: 14, color: colors.textSecondary, fontStyle: 'italic', marginTop: spacing.xs },
  raceGoing: { fontSize: 12, color: colors.textMuted, marginTop: spacing.xs },

  // Empty
  emptyCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.xl, alignItems: 'center' },
  emptyEmoji: { fontSize: 40, marginBottom: spacing.sm },
  emptyText: { fontSize: 16, color: colors.textPrimary, fontWeight: '500', marginBottom: spacing.xs },
  emptySubtext: { fontSize: 14, color: colors.textMuted },

  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: colors.background, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: spacing.lg, maxHeight: '90%' },
  modalClose: { position: 'absolute', right: spacing.md, top: spacing.md, zIndex: 10 },
  modalCloseText: { fontSize: 24, color: colors.textMuted },
  modalLoader: { padding: spacing.xl, alignItems: 'center' },

  // Detail View
  detailTitle: { fontSize: 24, fontWeight: '700', color: colors.textPrimary, marginTop: spacing.md },
  detailSubtitle: { fontSize: 14, color: colors.textMuted, marginBottom: spacing.lg },

  // Verdict
  verdictCard: { backgroundColor: colors.value + '15', borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.lg, borderLeftWidth: 4, borderLeftColor: colors.value },
  verdictTitle: { fontSize: 14, fontWeight: '700', color: colors.value, marginBottom: spacing.sm },
  verdictText: { fontSize: 14, color: colors.textPrimary, lineHeight: 22 },

  // Recommendation
  recCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.lg },
  recTitle: { fontSize: 14, fontWeight: '700', color: colors.accent, marginBottom: spacing.md },
  recRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: spacing.md },
  recItem: { alignItems: 'center' },
  recLabel: { fontSize: 11, color: colors.textMuted },
  recValue: { fontSize: 18, fontWeight: '700', color: colors.textPrimary },
  recReasons: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.sm },
  recReasonsTitle: { fontSize: 12, fontWeight: '600', color: colors.textSecondary, marginBottom: spacing.xs },
  recReasonRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 4 },
  recReasonBullet: { color: colors.value, marginRight: 6, fontWeight: '700' },
  recReasonText: { fontSize: 12, color: colors.textPrimary, flex: 1 },
  edgeBox: { marginTop: spacing.sm, backgroundColor: colors.value + '15', borderRadius: radius.sm, padding: spacing.sm },
  edgeTitle: { fontSize: 12, fontWeight: '600', color: colors.value, marginBottom: 4 },
  edgeText: { fontSize: 12, color: colors.textPrimary },

  // Form Card
  formCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.lg },
  formCardTitle: { fontSize: 14, fontWeight: '700', color: colors.textSecondary, marginBottom: spacing.md },
  formGrid: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.sm },
  formGridItem: { width: '50%', alignItems: 'center', marginBottom: spacing.sm },
  formGridValue: { fontSize: 16, fontWeight: '700', color: colors.textPrimary },
  formGridLabel: { fontSize: 11, color: colors.textMuted },
  formStats: { borderTopWidth: 1, borderTopColor: colors.border, paddingTop: spacing.sm },
  formStatRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  formStatLabel: { fontSize: 13, color: colors.textMuted },
  formStatValue: { fontSize: 13, fontWeight: '600', color: colors.textPrimary },
  positivesBox: { marginTop: spacing.sm, backgroundColor: colors.value + '10', borderRadius: radius.sm, padding: spacing.sm },
  positivesTitle: { fontSize: 12, fontWeight: '600', color: colors.value, marginBottom: 4 },
  positiveText: { fontSize: 12, color: colors.textPrimary },
  negativesBox: { marginTop: spacing.sm, backgroundColor: '#ff990010', borderRadius: radius.sm, padding: spacing.sm },
  negativesTitle: { fontSize: 12, fontWeight: '600', color: '#ff9900', marginBottom: 4 },
  negativeText: { fontSize: 12, color: colors.textPrimary },

  // Runner Card
  runnerCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.lg },
  runnerCardTitle: { fontSize: 14, fontWeight: '700', color: colors.textSecondary, marginBottom: spacing.sm },
  runnerInfoBox: {},
  runnerInfoRow: { fontSize: 13, color: colors.textPrimary, marginBottom: 4 },

  // Video Components
  sectionTitle: { fontSize: 20, fontWeight: '700', color: colors.textPrimary, marginBottom: spacing.xs },
  sectionSubtitle: { fontSize: 13, color: colors.textMuted, marginBottom: spacing.md },
  
  regionFilterRow: { flexDirection: 'row', marginBottom: spacing.lg, flexWrap: 'wrap' },
  regionPill: { paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, backgroundColor: colors.surface, borderRadius: radius.sm, marginRight: spacing.xs, marginBottom: spacing.xs },
  regionPillActive: { backgroundColor: colors.accent },
  regionText: { fontSize: 12, color: colors.textMuted, fontWeight: '500' },
  regionTextActive: { color: '#fff' },
  
  videoCard: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.md, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderLeftWidth: 4, borderLeftColor: '#ff0000' },
  videoCardLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  videoTypeIcon: { fontSize: 28, marginRight: spacing.sm },
  videoCardInfo: { flex: 1 },
  videoCardName: { fontSize: 16, fontWeight: '600', color: colors.textPrimary },
  videoCardMeta: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
  liveIndicator: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#ff000020', paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: radius.sm },
  liveDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#ff0000', marginRight: 6 },
  liveText: { fontSize: 11, fontWeight: '700', color: '#ff0000' },
  
  videoModalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.9)', justifyContent: 'center' },
  videoModalContent: { backgroundColor: colors.background, margin: spacing.md, borderRadius: radius.lg, overflow: 'hidden' },
  videoModalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  videoModalTitle: { fontSize: 18, fontWeight: '600', color: colors.textPrimary },
  
  videoPlayerContainer: { backgroundColor: '#000', minHeight: 300 },
  videoInfo: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: spacing.sm, backgroundColor: colors.surface },
  videoInfoText: { fontSize: 14, fontWeight: '600', color: colors.textPrimary },
  switchStreamBtn: { fontSize: 12, color: colors.accent, fontWeight: '500' },
  videoHint: { fontSize: 11, color: colors.textMuted, padding: spacing.sm, backgroundColor: colors.surface },
  openExternalBtn: { backgroundColor: colors.accent, padding: spacing.md, alignItems: 'center' },
  openExternalBtnText: { fontSize: 14, fontWeight: '600', color: '#fff' },
  
  nativeVideoPlaceholder: { backgroundColor: colors.surface, padding: spacing.xl, alignItems: 'center' },
  nativeVideoIcon: { fontSize: 60, marginBottom: spacing.md },
  nativeVideoText: { fontSize: 18, fontWeight: '600', color: colors.textPrimary, marginBottom: spacing.xs },
  nativeVideoSubtext: { fontSize: 14, color: colors.textMuted, textAlign: 'center', marginBottom: spacing.md },
  nativeVideoInfo: { backgroundColor: colors.background, padding: spacing.sm, borderRadius: radius.sm, width: '100%' },
  nativeVideoUrl: { fontSize: 11, color: colors.accent, textAlign: 'center' },
  
  watchVideoBtn: { backgroundColor: '#ff000020', paddingVertical: spacing.sm, paddingHorizontal: spacing.md, borderRadius: radius.md, marginTop: spacing.sm, alignSelf: 'flex-start' },
  watchVideoBtnText: { fontSize: 13, fontWeight: '600', color: '#ff0000' },
});
