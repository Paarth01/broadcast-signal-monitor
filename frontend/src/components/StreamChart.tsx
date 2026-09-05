import { useEffect, useRef } from "react";
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from "chart.js";
import type { StreamStatus } from "../api/client";

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend);

export type HistoryPoint = { t: number; metrics: Record<string, number | boolean> };

const MEDIA_METRICS = [
  { key: "packet_loss_pct", label: "Packet loss (%)", color: "#e0483e", axis: "y" as const },
  { key: "jitter_ms", label: "Jitter (ms)", color: "#e8a33d", axis: "y1" as const },
];

const PTP_METRICS = [
  { key: "ptp_offset_us", label: "Offset (us)", color: "#e0483e", axis: "y" as const },
  { key: "ptp_mean_path_delay_us", label: "Path delay (us)", color: "#e8a33d", axis: "y1" as const },
];

export default function StreamChart({
  streamName,
  category,
  history,
}: {
  streamName: string;
  category: "media" | "ptp";
  history: HistoryPoint[];
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartRef = useRef<Chart | null>(null);

  const metricConfig = category === "media" ? MEDIA_METRICS : PTP_METRICS;

  useEffect(() => {
    if (!canvasRef.current) return;

    chartRef.current = new Chart(canvasRef.current, {
      type: "line",
      data: {
        labels: [],
        datasets: metricConfig.map((m) => ({
          label: m.label,
          data: [] as number[],
          borderColor: m.color,
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          yAxisID: m.axis,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { labels: { color: "#8a9096", font: { size: 11 } } },
        },
        scales: {
          x: { ticks: { display: false }, grid: { display: false } },
          y: {
            position: "left",
            ticks: { color: "#8a9096", font: { size: 10 } },
            grid: { color: "#262b2f" },
          },
          y1: {
            position: "right",
            ticks: { color: "#8a9096", font: { size: 10 } },
            grid: { display: false },
          },
        },
      },
    });

    return () => chartRef.current?.destroy();
    // Recreate the chart when switching streams/categories rather than
    // trying to reconfigure axes on an existing instance.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamName, category]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    chart.data.labels = history.map((_, i) => String(i));
    metricConfig.forEach((m, idx) => {
      chart.data.datasets[idx].data = history.map((h) => Number(h.metrics[m.key] ?? 0));
    });
    chart.update("none");
  }, [history, metricConfig]);

  return (
    <div style={{ position: "relative", height: 220 }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
