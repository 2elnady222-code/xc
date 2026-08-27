import { MaterialIcons } from "@expo/vector-icons";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { ScreenContainer } from "@/components/screen-container";
import { useRunner } from "@/lib/runner-context";

export default function SettingsScreen() {
  const { runnerUrl, runnerToken, connectionMessage, setConnection, snapshot } = useRunner();
  const [url, setUrl] = useState(runnerUrl);
  const [token, setToken] = useState(runnerToken);

  useEffect(() => setUrl(runnerUrl), [runnerUrl]);
  useEffect(() => setToken(runnerToken), [runnerToken]);

  const saveAndTest = () => {
    setConnection(url, token);
  };

  return (
    <ScreenContainer edges={["top", "left", "right"]} containerClassName="bg-[#071425]" className="bg-[#071425]">
      <View style={styles.container}>
        <Text style={styles.title}>Settings</Text>
        <Text style={styles.subtitle}>Connect this phone to the Windows runner on your private network.</Text>

        <View style={styles.card}>
          <Text style={styles.label}>RUNNER ADDRESS</Text>
          <TextInput
            value={url}
            onChangeText={setUrl}
            placeholder="http://192.168.1.10:8787"
            placeholderTextColor="#5C7290"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            style={styles.input}
          />
          <Text style={styles.label}>PAIRING TOKEN</Text>
          <TextInput
            value={token}
            onChangeText={setToken}
            placeholder="Private runner token"
            placeholderTextColor="#5C7290"
            autoCapitalize="none"
            autoCorrect={false}
            secureTextEntry
            style={styles.input}
          />
          <Pressable onPress={saveAndTest} style={({ pressed }) => [styles.connectButton, pressed && styles.pressed]}>
            <MaterialIcons name="lan" size={19} color="#071425" />
            <Text style={styles.connectText}>SAVE & TEST CONNECTION</Text>
          </Pressable>
          <Text style={styles.connection}>{connectionMessage}</Text>
        </View>

        <View style={styles.headlessCard}>
          <View style={styles.headlessIcon}><MaterialIcons name="visibility-off" size={21} color="#2693FF" /></View>
          <View style={styles.headlessCopy}>
            <Text style={styles.headlessTitle}>Android Headless Mode</Text>
            <Text style={styles.headlessText}>Always enabled. Phone-initiated runs use the Windows browser runner with no visible browser window.</Text>
          </View>
          <View style={styles.onPill}><Text style={styles.onText}>{snapshot.headless ? "ON" : "ON"}</Text></View>
        </View>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingHorizontal: 18, paddingTop: 16 },
  title: { color: "#F4F8FF", fontSize: 24, fontWeight: "800", letterSpacing: -0.5 },
  subtitle: { color: "#95A8C1", fontSize: 13, lineHeight: 19, marginTop: 6, marginBottom: 22 },
  card: { backgroundColor: "#0D2038", borderWidth: 1, borderColor: "#1D5F9F", borderRadius: 16, padding: 16 },
  label: { color: "#81BFFF", fontSize: 11, fontWeight: "700", letterSpacing: 0.9, marginBottom: 8 },
  input: { color: "#F4F8FF", backgroundColor: "#071425", borderWidth: 1, borderColor: "#245E9D", borderRadius: 11, minHeight: 48, paddingHorizontal: 13, fontSize: 14, marginBottom: 15 },
  connectButton: { height: 48, borderRadius: 11, alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 8, backgroundColor: "#2693FF", marginTop: 2 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.98 }] },
  connectText: { color: "#071425", fontWeight: "800", fontSize: 12, letterSpacing: 0.5 },
  connection: { color: "#95A8C1", fontSize: 12, marginTop: 12, textAlign: "center" },
  headlessCard: { marginTop: 16, flexDirection: "row", alignItems: "center", gap: 12, backgroundColor: "#0A1A2E", borderWidth: 1, borderColor: "#1D5F9F", borderRadius: 16, padding: 15 },
  headlessIcon: { width: 42, height: 42, alignItems: "center", justifyContent: "center", borderRadius: 12, backgroundColor: "#102C4D" },
  headlessCopy: { flex: 1 },
  headlessTitle: { color: "#F4F8FF", fontSize: 14, fontWeight: "700" },
  headlessText: { color: "#95A8C1", fontSize: 11, lineHeight: 16, marginTop: 3 },
  onPill: { backgroundColor: "#123B2A", paddingHorizontal: 9, paddingVertical: 5, borderRadius: 8 },
  onText: { color: "#37D67A", fontSize: 11, fontWeight: "800" },
});
