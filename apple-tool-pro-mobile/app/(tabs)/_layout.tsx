import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { MaterialIcons } from "@expo/vector-icons";

import { HapticTab } from "@/components/haptic-tab";
import { Platform } from "react-native";
import { useColors } from "@/hooks/use-colors";
import { RunnerProvider } from "@/lib/runner-context";

export default function TabLayout() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const bottomPadding = Platform.OS === "web" ? 12 : Math.max(insets.bottom, 8);
  const tabBarHeight = 56 + bottomPadding;

  return (
    <RunnerProvider>
      <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.tint,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarStyle: {
          paddingTop: 8,
          paddingBottom: bottomPadding,
          height: tabBarHeight,
          backgroundColor: colors.background,
          borderTopColor: colors.border,
          borderTopWidth: 0.5,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Runner",
          tabBarIcon: ({ color }) => <MaterialIcons size={24} name="play-circle-outline" color={color} />,
        }}
      />
      <Tabs.Screen
        name="logs"
        options={{
          title: "Logs",
          tabBarIcon: ({ color }) => <MaterialIcons size={23} name="article" color={color} />,
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: "Settings",
          tabBarIcon: ({ color }) => <MaterialIcons size={23} name="settings" color={color} />,
        }}
      />
      </Tabs>
    </RunnerProvider>
  );
}
