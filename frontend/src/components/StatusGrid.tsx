import type { StreamStatus } from "../api/client";

const PRIORITY_COLOR: Record<string, string> = {
  "1": "var(--red)",
  "2": "var(--amber)",
  "3": "var(--text-dim)",
  healthy: "var(--green)",
};

function colorFor(priority: number | null): string {
  if (priority === null) return PRIORITY_COLOR.healthy;
  return PRIORITY_COLOR[String(priority)] ?? PRIORITY_COLOR.healthy;
}

function formatMetric(key: string, value: number | boolean): string {
  if (typeof value === "boolean") return value ? "yes" : "no";
  const units: Record<string, string> = {
    bitrate_mbps: " Mbps",
    jitter_ms: " ms",
    packet_loss_pct: "%",
    seq_discontinuities: "",
    ptp_offset_us: " us",
    ptp_mean_path_delay_us: " us",
  };
  return `${value}${units[key] ?? ""}`;
}

const LABELS: Record<string, string> = {
  bitrate_mbps: "Bitrate",
  jitter_ms: "Jitter",
  packet_loss_pct: "Packet loss",
  seq_discontinuities: "Seq errors",
  ptp_offset_us: "Offset",
  ptp_mean_path_delay_us: "Path delay",
};

function StatusTile({
  status,
  isSelected,
  onSelect,
}: {
  status: StreamStatus;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const color = colorFor(status.priority);
  const metricEntries = Object.entries(status.metrics).filter(([key]) => key !== "rogue_master_detected");

  return (
    <div
      className="tile"
      onClick={onSelect}
      style={{ cursor: "pointer", borderColor: isSelected ? color : undefined }}
    >
      <div className="tile-head">
        <span className="tile-name">{status.name}</span>
        <span className="dot" style={{ background: color }} />
      </div>
      {metricEntries.map(([key, value]) => (
        <div className="tile-metric" key={key}>
          <span>{LABELS[key] ?? key}</span>
          <span>{formatMetric(key, value)}</span>
        </div>
      ))}
      {status.reason && (
        <div className="tile-reason" style={{ color }}>
          P{status.priority}: {status.reason}
        </div>
      )}
    </div>
  );
}

export default function StatusGrid({
  statuses,
  category,
  selectedStream,
  onSelect,
}: {
  statuses: StreamStatus[];
  category: "media" | "ptp";
  selectedStream?: string | null;
  onSelect?: (name: string) => void;
}) {
  const filtered = statuses.filter((s) => s.category === category);
  if (filtered.length === 0) {
    return <p className="empty">Waiting for telemetry...</p>;
  }
  return (
    <div className="grid">
      {filtered.map((s) => (
        <StatusTile
          status={s}
          key={s.name}
          isSelected={s.name === selectedStream}
          onSelect={() => onSelect?.(s.name)}
        />
      ))}
    </div>
  );
}
