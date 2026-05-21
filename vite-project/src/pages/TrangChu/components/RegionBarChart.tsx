import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
} from "recharts";
import { RegionItem } from "./analytics/types";

// Type definitions
interface RegionBarProps {
  data?: RegionItem[];
  color?: string;
  yDomain?: [number | string, number | string];
}

const MIN_BAR_WIDTH = 100; // Increased to give more space for district names

const CustomTick = (props: any) => {
  const { x, y, payload, data } = props;
  const item = data[payload.index];

  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0}
        y={0}
        textAnchor="middle"
        fill="#374151"
        style={{ fontSize: 14, fontWeight: 500 }}
      >
        <tspan x="0" dy="1.2em">
          {payload.value}
        </tspan>
        {item?.province && (
          <tspan x="0" dy="1.2em" style={{ fontSize: 14, fill: "#64748b" }}>
            ({item.province})
          </tspan>
        )}
      </text>
    </g>
  );
};

/**
 * RegionBarChart
 * Props:
 *  - data: array of { name, value, province }
 *  - color: string; a CSS color ("#fb923c") or any valid css color string.
 */
export default function RegionBar({
  data = [],
  color = "#3B82F6", // Default to a blue color
  yDomain,
}: RegionBarProps) {
  const chartWidth = data.length * MIN_BAR_WIDTH;

  return (
    <div
      className="w-full h-full"
      style={{ overflowX: "auto", overflowY: "hidden" }}
    >
      <div
        style={{ minWidth: `${chartWidth}px`, width: "100%", height: "100%" }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 0, bottom: 60 }}
            barCategoryGap="20%"
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />

            <XAxis
              dataKey="name"
              interval={0}
              tick={(props) => <CustomTick {...props} data={data} />}
              axisLine={{ stroke: "#e2e8f0" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 13, fill: "#64748b" }}
              axisLine={false}
              tickLine={false}
              domain={yDomain}
            />

            <Tooltip
              cursor={{ fill: "rgba(0, 0, 0, 0.05)" }}
              contentStyle={{
                background: "#fff",
                border: "none",
                borderRadius: "12px",
                boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
              }}
            />

            <Bar
              dataKey="value"
              name="Giá trung bình"
              fill={color}
              radius={[4, 4, 0, 0]}
              barSize={40}
            >
              <LabelList
                dataKey="value"
                position="top"
                formatter={(val: any) =>
                  val === null || val === undefined
                    ? ""
                    : Number(val).toLocaleString("de-DE")
                }
                style={{ fill: "#374151", fontSize: 14, fontWeight: 700 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
