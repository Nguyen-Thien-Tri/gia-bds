import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Bar,
  Line,
  Cell,
  LabelList,
} from "recharts";

interface RawData {
  name?: string;
  acc?: number | string | null;
  diff?: number | string | null;
  // allow other fields
  [key: string]: any;
}

interface EnrichedData extends RawData {
  acc: number | null;
  diff: number | null;
  diffPct: number | null;
}

interface Props {
  data?: RawData[];
}

const formatNumber = (val: unknown): string => {
  if (val === null || val === undefined || Number.isNaN(Number(val)))
    return "-";
  return Number(val).toLocaleString("vi-VN");
};

const GrowthComposedChart: React.FC<Props> = ({ data = [] }) => {
  const enriched: EnrichedData[] = (data || []).map((d: RawData) => {
    const acc = Number(d.acc);
    const diff = Number(d.diff);
    const prev = acc - diff;
    const diffPct = prev && Number.isFinite(prev) ? (diff / prev) * 100 : null;

    return {
      ...d,
      acc: Number.isFinite(acc) ? acc : null,
      diff: Number.isFinite(diff) ? diff : null,
      diffPct: Number.isFinite(diffPct as number) ? (diffPct as number) : null,
    } as EnrichedData;
  });

  // --- Scrolling / sizing logic ---
  const POINT_WIDTH = 80; // px per datapoint
  const MIN_WIDTH = 700;
  const chartWidth = Math.max(enriched.length * POINT_WIDTH, MIN_WIDTH);

  const tooltipFormatter = (
    value: string | number,
    name?: string,
  ): [string, string] => {
    const seriesNames: Record<string, string> = {
      diffPct: "Thay đổi (%)",
      acc: "Giá trung bình",
    };
    const seriesKey = name && typeof name === "string" ? name : "";

    if (seriesKey === "diffPct") {
      const displayValue =
        value === null || value === undefined || Number.isNaN(Number(value))
          ? "-"
          : `${Number(value).toFixed(1)}%`;
      return [displayValue, `${seriesNames[seriesKey]} (so với kỳ trước)`];
    }

    const displayValue =
      typeof value === "number" ? formatNumber(value) : String(value);
    const seriesLabel = seriesNames[seriesKey]
      ? `${seriesNames[seriesKey]} (triệu VND/m2)`
      : seriesKey;
    return [displayValue, seriesLabel];
  };

  const tooltipLabelFormatter = (label: string) => `Khu vực: ${label}`;

  const containerStyle: React.CSSProperties = {
    width: "100%",
    overflowX: "auto",
  };
  const innerStyle: React.CSSProperties = { minWidth: chartWidth };

  return (
    <div style={containerStyle}>
      <div style={innerStyle}>
        <ResponsiveContainer width={chartWidth} height={420}>
          <ComposedChart
            data={enriched}
            margin={{ top: 6, right: 50, left: 8, bottom: 30 }}
          >
            <CartesianGrid strokeDasharray="3 3" />

            {/* Show all X labels */}
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
              interval={0}
              angle={0}
              textAnchor="middle"
              height={40}
            />

            <YAxis
              yAxisId="left"
              label={{
                value: "Giá",
                style: { fontWeight: "bold", textAnchor: "middle" },
                position: "insideLeft",
              }}
              tickFormatter={(val: any) =>
                val === null || val === undefined ? "-" : formatNumber(val)
              }
            />

            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[-50, 50]}
              ticks={[-50, -25, 0, 25, 50]}
              label={{
                value: "% thay đổi",
                angle: 90,
                position: "insideRight",
                style: { fontWeight: "bold", textAnchor: "middle" },
              }}
              tickFormatter={(val: any) =>
                val === null || val === undefined ? "-" : `${val}%`
              }
            />

            <Tooltip
              formatter={tooltipFormatter as any}
              labelFormatter={tooltipLabelFormatter}
            />

            <Bar
              dataKey="diffPct"
              name="Thay đổi (%)"
              yAxisId="right"
              barSize={12}
              radius={[6, 6, 0, 0]}
            >
              {enriched.map((entry, idx) => (
                <Cell
                  key={`g-${idx}`}
                  fill={
                    typeof entry.diffPct === "number" && entry.diffPct >= 0
                      ? "rgba(34,197,94,0.9)"
                      : "rgba(239,68,68,0.9)"
                  }
                />
              ))}
            </Bar>

            <Line
              type="monotone"
              dataKey="acc"
              name="Giá trung bình"
              stroke="#667eea"
              strokeWidth={2}
              dot={{ r: 3 }}
              yAxisId="left"
            >
              <LabelList
                dataKey="acc"
                position="top"
                formatter={(val: any) =>
                  val === null || val === undefined ? "-" : formatNumber(val)
                }
              />
            </Line>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default GrowthComposedChart;
