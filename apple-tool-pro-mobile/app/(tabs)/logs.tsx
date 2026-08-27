import * as Clipboard from "expo-clipboard";
import { MaterialIcons } from "@expo/vector-icons";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";

import { ScreenContainer } from "@/components/screen-container";
import { useRunner } from "@/lib/runner-context";

export default function LogsScreen() {
  const { snapshot, clearLogs } = useRunner();

  const copyLogs = async () => {
    await Clipboard.setStringAsync(snapshot.logs.join("\n"));
  };

  return (
    <ScreenContainer edges={["top", "left", "right"]} containerClassName="bg-[#071425]" className="bg-[#071425]">
      <View style={styles.container}>
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Live Execution Logs</Text>
            <Text style={styles.subtitle}>{snapshot.running ? "Streaming from headless runner" : "Latest runner messages"}</Text>
          </View>
          <View style={styles.actions}>
            <Pressable accessibilityLabel="Copy logs" onPress={copyLogs} style={styles.iconButton}>
              <MaterialIcons name="content-copy" size={19} color="#B9D8FF" />
            </Pressable>
            <Pressable accessibilityLabel="Clear logs" onPress={clearLogs} style={styles.iconButton}>
              <MaterialIcons name="delete-outline" size={20} color="#FF8290" />
            </Pressable>
          </View>
        </View>

        <FlatList
          data={snapshot.logs}
          keyExtractor={(item, index) => `${index}-${item}`}
          contentContainerStyle={snapshot.logs.length ? styles.logList : styles.emptyList}
          renderItem={({ item }) => <Text style={[styles.logLine, getLogStyle(item)]}>{item}</Text>}
          ListEmptyComponent={<Text style={styles.emptyText}>No execution logs yet.</Text>}
          showsVerticalScrollIndicator={false}
        />
      </View>
    </ScreenContainer>
  );
}

function getLogStyle(item: string) {
  if (item.includes("SUCCESS")) return { color: "#37D67A" };
  if (item.includes("FAILED") || item.includes("Error")) return { color: "#FF7180" };
  if (item.includes("Retry") || item.includes("paused")) return { color: "#FFC45D" };
  return { color: "#C9D9ED" };
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingHorizontal: 18, paddingTop: 16 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 18 },
  title: { color: "#F4F8FF", fontSize: 22, fontWeight: "800", letterSpacing: -0.4 },
  subtitle: { color: "#95A8C1", fontSize: 12, marginTop: 4 },
  actions: { flexDirection: "row", gap: 8 },
  iconButton: { width: 38, height: 38, alignItems: "center", justifyContent: "center", borderRadius: 12, backgroundColor: "#0D2038", borderWidth: 1, borderColor: "#1F5E9E" },
  logList: { padding: 14, borderRadius: 16, backgroundColor: "#0A1A2E", borderWidth: 1, borderColor: "#1D5F9F", gap: 11 },
  emptyList: { flexGrow: 1, alignItems: "center", justifyContent: "center" },
  logLine: { fontFamily: "monospace", fontSize: 12, lineHeight: 18 },
  emptyText: { color: "#95A8C1", fontSize: 14 },
});
