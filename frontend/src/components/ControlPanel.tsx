import { useState } from "react";
import { injectFault } from "../api/client";

const DEMO_ACTIONS: { label: string; stream: string; fault: string }[] = [
  { label: "Packet loss: OB van", stream: "ob-van-uplink", fault: "packet_loss" },
  { label: "Jitter spike: camera 1", stream: "camera-1-studio-a", fault: "jitter" },
  { label: "Dropout: satellite feed", stream: "satellite-feed", fault: "dropout" },
  { label: "Soft drift (ML-only): camera 2", stream: "camera-2-studio-a", fault: "soft_drift" },
  { label: "PTP drift: studio A slave", stream: "ptp-slave-studio-a", fault: "ptp_drift" },
  { label: "Rogue PTP master: OB van", stream: "ptp-slave-ob-van", fault: "ptp_rogue_master" },
];

export default function ControlPanel() {
  const [pending, setPending] = useState<string | null>(null);

  async function handleClick(stream: string, fault: string, label: string) {
    setPending(label);
    try {
      await injectFault(stream, fault, 15);
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="controls">
      {DEMO_ACTIONS.map((action) => (
        <button
          key={action.label}
          onClick={() => handleClick(action.stream, action.fault, action.label)}
          disabled={pending === action.label}
        >
          {pending === action.label ? "Injecting..." : action.label}
        </button>
      ))}
    </div>
  );
}
