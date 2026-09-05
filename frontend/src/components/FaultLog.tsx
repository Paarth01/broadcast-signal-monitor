import type { Fault } from "../api/client";

const PRIORITY_COLOR: Record<number, string> = {
  1: "var(--red)",
  2: "var(--amber)",
  3: "var(--text-dim)",
};

export default function FaultLog({ faults }: { faults: Fault[] }) {
  if (faults.length === 0) {
    return <p className="empty">No faults logged yet.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Stream</th>
          <th>Category</th>
          <th>Priority</th>
          <th>Reason</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {faults.map((f) => (
          <tr key={f.id}>
            <td>{new Date(f.timestamp + "Z").toLocaleTimeString()}</td>
            <td>{f.stream_name}</td>
            <td>{f.category}</td>
            <td>
              <span className="badge" style={{ color: PRIORITY_COLOR[f.priority], borderColor: PRIORITY_COLOR[f.priority], border: "1px solid" }}>
                P{f.priority}
              </span>
            </td>
            <td>{f.reason}</td>
            <td style={{ color: f.resolved ? "var(--green)" : "var(--text-dim)" }}>
              {f.resolved ? "Resolved" : "Active"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
