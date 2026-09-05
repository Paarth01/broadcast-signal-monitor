export type StreamStatus = {
  name: string;
  category: "media" | "ptp";
  priority: 1 | 2 | 3 | null;
  reason: string | null;
  metrics: Record<string, number | boolean>;
  timestamp: string;
};

export type Fault = {
  id: number;
  stream_name: string;
  timestamp: string;
  priority: number;
  category: string;
  reason: string;
  resolved: boolean;
};

const BASE = "/api";

export async function fetchFaults(): Promise<Fault[]> {
  const res = await fetch(`${BASE}/faults`);
  if (!res.ok) throw new Error("Failed to load faults");
  return res.json();
}

export type MetricPoint = { timestamp: string; metrics: Record<string, number> };

export async function fetchStreamHistory(name: string): Promise<MetricPoint[]> {
  const res = await fetch(`${BASE}/streams/${encodeURIComponent(name)}/history`);
  if (!res.ok) throw new Error("Failed to load stream history");
  return res.json();
}

export async function injectFault(streamName: string, faultType: string, durationSeconds = 15) {
  const res = await fetch(`${BASE}/simulate/fault`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      stream_name: streamName,
      fault_type: faultType,
      duration_seconds: durationSeconds,
    }),
  });
  if (!res.ok) throw new Error("Failed to inject fault");
  return res.json();
}

// Subscribes to the SSE stream and calls onUpdate for every status event.
// Returns a cleanup function to close the connection.
export function subscribeToStatus(onUpdate: (status: StreamStatus) => void): () => void {
  const source = new EventSource(`${BASE}/stream/events`);
  source.addEventListener("status", (event) => {
    const payload = JSON.parse((event as MessageEvent).data) as StreamStatus;
    onUpdate(payload);
  });
  return () => source.close();
}
