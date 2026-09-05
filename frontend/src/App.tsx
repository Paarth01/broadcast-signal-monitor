import { useEffect, useState } from "react";
import { fetchFaults, fetchStreamHistory, subscribeToStatus, type Fault, type StreamStatus } from "./api/client";
import ControlPanel from "./components/ControlPanel";
import FaultLog from "./components/FaultLog";
import StatusGrid from "./components/StatusGrid";
import StreamChart, { type HistoryPoint } from "./components/StreamChart";

const HISTORY_LENGTH = 40;

export default function App() {
  const [statuses, setStatuses] = useState<Record<string, StreamStatus>>({});
  const [history, setHistory] = useState<Record<string, HistoryPoint[]>>({});
  const [loadedHistoryFor, setLoadedHistoryFor] = useState<Set<string>>(new Set());
  const [selectedStream, setSelectedStream] = useState<string | null>(null);
  const [faults, setFaults] = useState<Fault[]>([]);
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const unsubscribe = subscribeToStatus((status) => {
      setStatuses((prev) => ({ ...prev, [status.name]: status }));
      setHistory((prev) => {
        const existing = prev[status.name] ?? [];
        const next = [...existing, { t: Date.now(), metrics: status.metrics }].slice(-HISTORY_LENGTH);
        return { ...prev, [status.name]: next };
      });
      setSelectedStream((prev) => prev ?? status.name);
    });
    return unsubscribe;
  }, []);

  // Seed each stream's chart from persisted history the first time it's
  // selected, so switching to a stream shows its recent trend immediately
  // instead of an empty chart that only fills in from this point forward.
  useEffect(() => {
    if (!selectedStream || loadedHistoryFor.has(selectedStream)) return;
    setLoadedHistoryFor((prev) => new Set(prev).add(selectedStream));
    fetchStreamHistory(selectedStream)
      .then((points) => {
        const seeded: HistoryPoint[] = points.map((p) => ({ t: new Date(p.timestamp).getTime(), metrics: p.metrics }));
        setHistory((prev) => {
          // Live SSE data may have already started arriving - persisted
          // history goes first, live points stay appended after it.
          const live = prev[selectedStream] ?? [];
          return { ...prev, [selectedStream]: [...seeded, ...live].slice(-HISTORY_LENGTH) };
        });
      })
      .catch(() => {});
  }, [selectedStream, loadedHistoryFor]);

  useEffect(() => {
    fetchFaults().then(setFaults).catch(() => {});
    const interval = setInterval(() => {
      fetchFaults().then(setFaults).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(tick);
  }, []);

  const statusList = Object.values(statuses);
  const selectedStatus = selectedStream ? statuses[selectedStream] : undefined;
  const selectedHistory = selectedStream ? history[selectedStream] ?? [] : [];

  return (
    <div className="shell">
      <div className="masthead">
        <h1>Signal health monitor</h1>
        <span className="clock">{now.toLocaleTimeString()}</span>
      </div>

      <div className="section-label">Media streams</div>
      <StatusGrid statuses={statusList} category="media" selectedStream={selectedStream} onSelect={setSelectedStream} />

      <div className="section-label">PTP synchronization</div>
      <StatusGrid statuses={statusList} category="ptp" selectedStream={selectedStream} onSelect={setSelectedStream} />

      <div className="section-label">
        Live trend{selectedStream ? ` — ${selectedStream}` : ""}
      </div>
      {selectedStatus ? (
        <StreamChart streamName={selectedStatus.name} category={selectedStatus.category} history={selectedHistory} />
      ) : (
        <p className="empty">Select a stream tile to see its trend.</p>
      )}

      <div className="section-label">Demo: inject a fault</div>
      <ControlPanel />

      <div className="section-label">Fault log</div>
      <FaultLog faults={faults} />
    </div>
  );
}
