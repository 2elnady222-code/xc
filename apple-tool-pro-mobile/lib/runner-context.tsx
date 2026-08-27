import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { normalizeRunnerUrl } from "@/lib/runner-utils";

export type RunnerSnapshot = {
  running: boolean;
  headless: true;
  total: number;
  active: number;
  success: number;
  failed: number;
  completed: number;
  progress: number;
  status: string;
  logs: string[];
};

type RunnerContextValue = {
  snapshot: RunnerSnapshot;
  runnerUrl: string;
  runnerToken: string;
  connectionMessage: string;
  setConnection: (url: string, token: string) => void;
  refresh: () => Promise<void>;
  start: (numbers: string[]) => Promise<void>;
  stop: () => Promise<void>;
  clearLogs: () => Promise<void>;
};

const emptySnapshot: RunnerSnapshot = {
  running: false,
  headless: true,
  total: 0,
  active: 0,
  success: 0,
  failed: 0,
  completed: 0,
  progress: 0,
  status: "Configure a Windows runner to begin.",
  logs: [],
};

const RunnerContext = createContext<RunnerContextValue | null>(null);

export function RunnerProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<RunnerSnapshot>(emptySnapshot);
  const [runnerUrl, setRunnerUrl] = useState("");
  const [runnerToken, setRunnerToken] = useState("");
  const [connectionMessage, setConnectionMessage] = useState("Not connected");

  const request = useCallback(async (path: string, options: RequestInit = {}) => {
    const baseUrl = normalizeRunnerUrl(runnerUrl);
    if (!baseUrl || !runnerToken.trim()) {
      throw new Error("Enter the runner address and pairing token in Settings.");
    }

    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Runner-Token": runnerToken.trim(),
        ...(options.headers ?? {}),
      },
    });
    const payload = (await response.json()) as RunnerSnapshot | { error: string };
    if (!response.ok || "error" in payload) {
      throw new Error("error" in payload ? payload.error : "Runner request failed.");
    }
    return payload as RunnerSnapshot;
  }, [runnerToken, runnerUrl]);

  const refresh = useCallback(async () => {
    try {
      const nextSnapshot = await request("/status");
      setSnapshot(nextSnapshot);
      setConnectionMessage(nextSnapshot.running ? "Headless run active" : "Connected");
    } catch (error) {
      setConnectionMessage(error instanceof Error ? error.message : "Runner unavailable");
    }
  }, [request]);

  const setConnection = useCallback((url: string, token: string) => {
    setRunnerUrl(normalizeRunnerUrl(url));
    setRunnerToken(token.trim());
    setConnectionMessage("Connection details updated");
  }, []);

  const start = useCallback(async (numbers: string[]) => {
    const nextSnapshot = await request("/start", {
      method: "POST",
      body: JSON.stringify({ numbers }),
    });
    setSnapshot(nextSnapshot);
    setConnectionMessage("Headless run active");
  }, [request]);

  const stop = useCallback(async () => {
    const nextSnapshot = await request("/stop", { method: "POST", body: "{}" });
    setSnapshot(nextSnapshot);
  }, [request]);

  const clearLogs = useCallback(async () => {
    const nextSnapshot = await request("/clear-logs", { method: "POST", body: "{}" });
    setSnapshot(nextSnapshot);
  }, [request]);

  useEffect(() => {
    if (!runnerUrl || !runnerToken) return;
    refresh();
    const interval = setInterval(refresh, 1000);
    return () => clearInterval(interval);
  }, [refresh, runnerToken, runnerUrl]);

  const value = useMemo(() => ({
    snapshot,
    runnerUrl,
    runnerToken,
    connectionMessage,
    setConnection,
    refresh,
    start,
    stop,
    clearLogs,
  }), [clearLogs, connectionMessage, refresh, runnerToken, runnerUrl, setConnection, snapshot, start, stop]);

  return <RunnerContext.Provider value={value}>{children}</RunnerContext.Provider>;
}

export function useRunner() {
  const context = useContext(RunnerContext);
  if (!context) throw new Error("useRunner must be used within RunnerProvider.");
  return context;
}
