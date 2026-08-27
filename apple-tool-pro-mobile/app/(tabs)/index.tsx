import * as DocumentPicker from "expo-document-picker";
import { File } from "expo-file-system";
import { MaterialIcons } from "@expo/vector-icons";
import { useMemo, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { ScreenContainer } from "@/components/screen-container";
import { useRunner } from "@/lib/runner-context";
import { parsePhoneNumbers } from "@/lib/runner-utils";

type StatCardProps = { label: string; value: number; color: string; icon: keyof typeof MaterialIcons.glyphMap };

export default function RunnerScreen() {
  const { snapshot, start, stop, connectionMessage } = useRunner();
  const [numbersText, setNumbersText] = useState("");
  const [busy, setBusy] = useState(false);
  const numberCount = useMemo(() => parsePhoneNumbers(numbersText).length, [numbersText]);

  const loadNumbers = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({ type: "text/plain", copyToCacheDirectory: true });
      if (result.canceled) return;
      const content = await new File(result.assets[0].uri).text();
      setNumbersText(content);
    } catch (error) {
      Alert.alert("Load failed", error instanceof Error ? error.message : "Unable to read the selected file.");
    }
  };

  const startAutomation = async () => {
    const numbers = parsePhoneNumbers(numbersText);
    if (!numbers.length) {
      Alert.alert("Phone numbers required", "Paste phone numbers or load a text file first.");
      return;
    }
    setBusy(true);
    try {
      await start(numbers);
    } catch (error) {
      Alert.alert("Unable to start", error instanceof Error ? error.message : "Check Settings and try again.");
    } finally {
      setBusy(false);
    }
  };

  const stopAutomation = async () => {
    setBusy(true);
    try {
      await stop();
    } catch (error) {
      Alert.alert("Unable to stop", error instanceof Error ? error.message : "Runner unavailable.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScreenContainer edges={["top", "left", "right"]} containerClassName="bg-[#071425]" className="bg-[#071425]">
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        <View style={styles.appHeader}>
          <View>
            <Text style={styles.appName}>Apple Tool Pro</Text>
            <Text style={styles.mode}>ANDROID CONTROLLER</Text>
          </View>
          <View style={styles.proBadge}><Text style={styles.proText}>PRO</Text></View>
        </View>

        <View style={styles.statsGrid}>
          <StatCard label="TOTAL" value={snapshot.total || numberCount} color="#2693FF" icon="format-list-numbered" />
          <StatCard label="ACTIVE" value={snapshot.active} color="#B9D8FF" icon="bolt" />
          <StatCard label="SUCCESS" value={snapshot.success} color="#37D67A" icon="check-circle-outline" />
          <StatCard label="FAILED" value={snapshot.failed} color="#FF5C6C" icon="error-outline" />
        </View>

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>Phone Numbers</Text>
            <Text style={styles.sectionSubtitle}>{numberCount} number{numberCount === 1 ? "" : "s"} ready</Text>
          </View>
          <View style={styles.smallActions}>
            <Pressable onPress={loadNumbers} style={({ pressed }) => [styles.smallButton, pressed && styles.pressed]}><Text style={styles.smallButtonText}>LOAD</Text></Pressable>
            <Pressable onPress={() => setNumbersText("")} style={({ pressed }) => [styles.smallButton, pressed && styles.pressed]}><Text style={styles.smallButtonText}>CLEAR</Text></Pressable>
          </View>
        </View>

        <TextInput
          value={numbersText}
          onChangeText={setNumbersText}
          multiline
          placeholder="Paste one phone number per line"
          placeholderTextColor="#5C7290"
          textAlignVertical="top"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="phone-pad"
          style={styles.numbersInput}
        />

        <View style={styles.statusCard}>
          <View style={styles.statusLine}>
            <View style={[styles.statusDot, { backgroundColor: snapshot.running ? "#37D67A" : "#2693FF" }]} />
            <Text style={styles.statusText} numberOfLines={2}>{snapshot.status}</Text>
          </View>
          <View style={styles.progressMeta}>
            <Text style={styles.progressLabel}>Status: {snapshot.completed}/{snapshot.total} ({snapshot.progress.toFixed(0)}%)</Text>
            <Text style={styles.progressLabel}>Success: {snapshot.success} · Failed: {snapshot.failed}</Text>
          </View>
          <View style={styles.progressTrack}><View style={[styles.progressFill, { width: `${snapshot.progress}%` }]} /></View>
          <Text style={styles.connectionText}>{connectionMessage}</Text>
        </View>

        {snapshot.running ? (
          <Pressable disabled={busy} onPress={stopAutomation} style={({ pressed }) => [styles.stopButton, (pressed || busy) && styles.pressed]}>
            {busy ? <ActivityIndicator color="#FFFFFF" /> : <><MaterialIcons name="stop" size={20} color="#FFFFFF" /><Text style={styles.stopText}>STOP</Text></>}
          </Pressable>
        ) : (
          <Pressable disabled={busy} onPress={startAutomation} style={({ pressed }) => [styles.startButton, (pressed || busy) && styles.pressed]}>
            {busy ? <ActivityIndicator color="#071425" /> : <><MaterialIcons name="play-arrow" size={22} color="#071425" /><Text style={styles.startText}>START AUTOMATION</Text></>}
          </Pressable>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

function StatCard({ label, value, color, icon }: StatCardProps) {
  return (
    <View style={styles.statCard}>
      <MaterialIcons name={icon} size={15} color={color} />
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 18, paddingTop: 14, paddingBottom: 26 },
  appHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 18 },
  appName: { color: "#F4F8FF", fontSize: 24, fontWeight: "800", letterSpacing: -0.6 },
  mode: { color: "#81BFFF", fontSize: 10, fontWeight: "800", letterSpacing: 1.5, marginTop: 3 },
  proBadge: { backgroundColor: "#102C4D", borderColor: "#2693FF", borderWidth: 1, borderRadius: 10, paddingHorizontal: 10, paddingVertical: 6 },
  proText: { color: "#81BFFF", fontSize: 11, fontWeight: "900", letterSpacing: 1 },
  statsGrid: { flexDirection: "row", gap: 7, marginBottom: 22 },
  statCard: { flex: 1, minHeight: 85, paddingHorizontal: 8, paddingVertical: 10, borderRadius: 14, backgroundColor: "#0D2038", borderWidth: 1, borderColor: "#1D5F9F" },
  statValue: { fontSize: 22, fontWeight: "800", marginTop: 5 },
  statLabel: { color: "#95A8C1", fontSize: 9, fontWeight: "700", marginTop: 2 },
  sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 10 },
  sectionTitle: { color: "#F4F8FF", fontSize: 17, fontWeight: "800" },
  sectionSubtitle: { color: "#95A8C1", fontSize: 11, marginTop: 2 },
  smallActions: { flexDirection: "row", gap: 7 },
  smallButton: { borderWidth: 1, borderColor: "#2693FF", backgroundColor: "#102C4D", paddingHorizontal: 11, paddingVertical: 7, borderRadius: 8 },
  smallButtonText: { color: "#B9D8FF", fontSize: 10, fontWeight: "800", letterSpacing: 0.6 },
  numbersInput: { minHeight: 178, maxHeight: 260, color: "#F4F8FF", fontSize: 14, lineHeight: 21, backgroundColor: "#0A1A2E", borderWidth: 1, borderColor: "#2693FF", borderRadius: 15, padding: 14 },
  statusCard: { marginTop: 16, padding: 14, borderRadius: 15, backgroundColor: "#0D2038", borderWidth: 1, borderColor: "#1D5F9F" },
  statusLine: { flexDirection: "row", alignItems: "center", gap: 8 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusText: { flex: 1, color: "#F4F8FF", fontSize: 13, fontWeight: "600", lineHeight: 18 },
  progressMeta: { flexDirection: "row", justifyContent: "space-between", gap: 8, marginTop: 13 },
  progressLabel: { flex: 1, color: "#95A8C1", fontSize: 10, lineHeight: 15 },
  progressTrack: { height: 7, borderRadius: 4, backgroundColor: "#071425", overflow: "hidden", marginTop: 9 },
  progressFill: { height: "100%", borderRadius: 4, backgroundColor: "#2693FF" },
  connectionText: { color: "#81BFFF", fontSize: 10, marginTop: 9 },
  startButton: { marginTop: 18, height: 54, borderRadius: 14, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 7, backgroundColor: "#37D67A" },
  startText: { color: "#071425", fontSize: 13, fontWeight: "900", letterSpacing: 0.8 },
  stopButton: { marginTop: 18, height: 54, borderRadius: 14, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 7, backgroundColor: "#E04958" },
  stopText: { color: "#FFFFFF", fontSize: 13, fontWeight: "900", letterSpacing: 0.8 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.98 }] },
});
