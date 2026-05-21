import React, { useEffect, useRef } from "react";
import Chart from "chart.js/auto";

// PriceLineChart
// - Extracted single-file component for the line chart
// - Legend is removed (display: false)
// - Keeps value labels above each point and dashed guideline to x-axis
// - Accepts `labels` and `data` props (arrays), plus optional `className`

interface PriceLineChartProps {
  labels?: string[];
  data?: number[];
  className?: string;
}

interface ColorStop {
  stop: number;
  color: string;
}

export default function PriceLineChart({
  labels = [
    "Tháng 1",
    "Tháng 2",
    "Tháng 3",
    "Tháng 4",
    "Tháng 5",
    "Tháng 6",
    "Tháng 7",
    "Tháng 8",
    "Tháng 9",
    "Tháng 10",
    "Tháng 11",
    "Tháng 12",
  ],
  data = [
    38.2, 39.1, 41.3, 43.5, 42.8, 44.2, 46.1, 45.3, 47.2, 48.6, 46.8, 45.2,
  ],
  className = "w-full h-full",
}: PriceLineChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  // small util to create vertical gradient
  const createGradient = (
    ctx: CanvasRenderingContext2D,
    height: number,
    colorStops: ColorStop[] = [],
  ): CanvasGradient => {
    const g = ctx.createLinearGradient(0, 0, 0, height);
    colorStops.forEach(({ stop, color }) => g.addColorStop(stop, color));
    return g;
  };

  // plugin: draw value label above points and dashed guideline to x-axis
  const valueDotAndGuidelinePlugin = {
    id: "valueDotAndGuidelinePlugin",
    afterDatasetsDraw(chart: Chart) {
      const {
        ctx,
        chartArea: { bottom },
      } = chart;
      ctx.save();
      chart.data.datasets.forEach((dataset, datasetIndex) => {
        if (!chart.isDatasetVisible(datasetIndex)) return;
        const meta = chart.getDatasetMeta(datasetIndex);
        if (!meta || meta.type !== "line") return;

        meta.data.forEach((element, index) => {
          const point = element;
          const x = point.x;
          const y = point.y;
          const value = dataset.data[index];
          if (value == null || isNaN(Number(value))) return;

          // guideline
          ctx.save();
          ctx.setLineDash([6, 6]);
          ctx.lineWidth = 1;
          try {
            ctx.strokeStyle = (function (c: string | undefined) {
              if (typeof c === "string" && c.startsWith("rgba")) return c;
              return (c || "#94a3b8") + "33"; // add subtle alpha
            })(dataset.borderColor as string);
          } catch (e) {
            ctx.strokeStyle = "rgba(148,163,184,0.18)";
          }
          ctx.beginPath();
          ctx.moveTo(x, bottom);
          ctx.lineTo(x, y + 2);
          ctx.stroke();
          ctx.restore();

          // value text
          ctx.save();
          ctx.textAlign = "center";
          ctx.textBaseline = "bottom";
          ctx.font = "600 12px Inter, system-ui, Arial";
          ctx.fillStyle = "#0f172a";
          const text = `${Number(value).toFixed(1)}`;
          ctx.fillText(text, x, y - 8);
          ctx.restore();
        });
      });
      ctx.restore();
    },
  };

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // determine a reasonable gradient height (300 falls back)
    const rect = canvas.getBoundingClientRect();
    const g = createGradient(ctx, rect.height || 300, [
      { stop: 0, color: "rgba(102,126,234,0.28)" },
      { stop: 0.6, color: "rgba(102,126,234,0.08)" },
      { stop: 1, color: "rgba(102,126,234,0)" },
    ]);

    // destroy existing
    if (chartRef.current) {
      try {
        chartRef.current.destroy();
      } catch (e) {
        /* ignore */
      }
      chartRef.current = null;
    }

    chartRef.current = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Giá trung bình",
            data,
            borderColor: "#667eea",
            backgroundColor: g,
            borderWidth: 3,
            fill: true,
            tension: 0.36,
            pointRadius: 5,
            pointHoverRadius: 7,
            pointBackgroundColor: "#fff",
            pointBorderColor: "#667eea",
            pointBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          // legend intentionally hidden
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(15,23,42,0.95)",
            titleColor: "#f8fafc",
            bodyColor: "#cbd5e1",
            borderColor: "rgba(148,163,184,0.12)",
            borderWidth: 1,
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label(ctx) {
                if (ctx.parsed.y == null) return ctx.dataset.label + ": -";
                return `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(
                  1,
                )} triệu VND/m²`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: false,
            min: 34,
            max: 52,
            grid: { color: "rgba(148,163,184,0.06)", drawBorder: false },
            ticks: { color: "#64748b" },
            title: { display: false },
          },
          x: { grid: { display: false }, ticks: { color: "#64748b" } },
        },
      },
      plugins: [valueDotAndGuidelinePlugin],
    });

    // cleanup
    return () => {
      if (chartRef.current) {
        try {
          chartRef.current.destroy();
        } catch (e) {
          // ignore
        }
        chartRef.current = null;
      }
    };
    // we only re-create when labels or data change
  }, [labels, data]);

  return (
    <canvas
      ref={canvasRef}
      aria-label="Biểu đồ giá trung bình"
      className={className}
    />
  );
}
