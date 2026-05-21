import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
  Brush,
  LabelList,
} from "recharts";

// Type definitions
interface DataPoint {
  [key: string]: string | number | null | undefined;
}

interface Colors {
  line: string;
  areaFrom: string;
  areaTo: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: DataPoint;
    value?: number | string | null;
  }>;
  label?: string;
  currencySymbol?: string;
  countKey?: string;
  yKey?: string;
}

interface RechartsPrebinnedChartProps {
  data?: DataPoint[];
  xKey?: string;
  yKey?: string;
  countKey?: string;
  height?: string | number;
  showArea?: boolean;
  colors?: Colors;
  yDomain?: [number | string, number | string]; // Allow passing domain for YAxis
  currencySymbol?: string;
}

/* Small formatter */
const numberWithCommas = (x: string | number | null | undefined): string => {
  if (x === null || x === undefined || Number.isNaN(x)) return "-";
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
};

/* Tooltip that supports optional countKey */
function CustomTooltip({
  active,
  payload,
  label,
  currencySymbol = " tỷ",
  countKey = "count",
  yKey = "price",
}: CustomTooltipProps): React.JSX.Element | null {
  if (!active || !payload || !payload.length) return null;

  const p = payload[0].payload;
  const priceValue =
    p && p[yKey] !== undefined && p[yKey] !== null
      ? numberWithCommas(p[yKey])
      : "-";
  const count = p && p[countKey] !== undefined ? p[countKey] : null;

  return (
    <div className="bg-white border rounded p-2 text-sm shadow-sm">
      <div className="font-medium">{label}</div>
      <div className="mt-1">
        Giá trung bình:{" "}
        <span className="font-semibold">
          {priceValue !== "-" ? `${priceValue}${currencySymbol}` : "-"}
        </span>
      </div>
      {count !== null && (
        <div className="text-xs text-slate-500 mt-1">Số tin: {count}</div>
      )}
    </div>
  );
}

/**
 * RechartsPrebinnedChart
 *
 * Props:
 *  - data: [{ range: "10-20", price: 123, count: 5 }, ...]
 *  - xKey: field for x axis (default "range")
 *  - yKey: field for y axis (default "Giá")
 *  - countKey: optional field for counts in tooltip (default "count")
 *  - height: "100%" or number px (default "100%")
 *  - showArea: boolean (default true)
 *  - colors: { line, areaFrom, areaTo }
 *  - currencySymbol: string to append in tooltip (default " tỷ", pass "" if you don't want a symbol)
 */
export default function RechartsPrebinnedChart({
  data = [],
  xKey = "range",
  yKey = "Giá",
  countKey = "count",
  height = "100%",
  showArea = true,
  colors = {
    line: "#667EEA",
    areaFrom: "rgba(102,126,234,0.28)",
    areaTo: "rgba(102,126,234,0)",
  },
  currencySymbol = " tỷ",
  yDomain,
}: RechartsPrebinnedChartProps): React.JSX.Element {
  const containerStyle: React.CSSProperties =
    typeof height === "number"
      ? { width: "100%", height: `${height}px` }
      : { width: "100%", height };

  return (
    <div className="w-full h-full overflow-hidden" style={containerStyle}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 6, right: 12, left: 0, bottom: 6 }}
        >
          <defs>
            <linearGradient
              id="areaGradientPrebinned"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop offset="0%" stopColor={colors.areaFrom} stopOpacity={1} />
              <stop offset="100%" stopColor={colors.areaTo} stopOpacity={0} />
            </linearGradient>
          </defs>

          {/* Show both vertical and horizontal dashed gray grid lines */}
          <CartesianGrid stroke="#E5E7EB" strokeDasharray="4 4" />

          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 12 }}
            tickLine={false}
            padding={{ left: 6, right: 6 }}
            interval={0}
            angle={-20}
            textAnchor="end"
            height={48}
          />

          <YAxis
            tick={{ fontSize: 15 }}
            tickFormatter={(val: any) =>
              val === null ? "-" : numberWithCommas(val)
            }
            width={40}
            domain={yDomain}
          />

          <Tooltip
            content={
              <CustomTooltip
                currencySymbol={currencySymbol}
                countKey={countKey}
                yKey={yKey}
              />
            }
          />

          {/* Main line */}
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={colors.line}
            strokeWidth={2}
            dot={{ r: 3, strokeWidth: 2, stroke: colors.line, fill: "#fff" }}
            activeDot={{ r: 6 }}
            isAnimationActive={true}
            animationDuration={900}
            connectNulls={false}
          >
            {/* Data labels at each point (formatted with commas) */}
            <LabelList
              dataKey={yKey}
              position="top"
              formatter={(val: any) =>
                val === null || val === undefined ? "" : numberWithCommas(val)
              }
              style={{ fontSize: 15, fill: "#374151" }}
              offset={8}
            />
          </Line>

          {showArea && (
            <Area
              type="monotone"
              dataKey={yKey}
              stroke="none"
              fill="url(#areaGradientPrebinned)"
              connectNulls={false}
            />
          )}

          <Brush
            dataKey={xKey}
            height={20}
            stroke={colors.line}
            travellerWidth={8}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
