import React, { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";

// Import color map provided by the project
// Adjust the import path if your color.ts is placed elsewhere (e.g. "../color" or "../../lib/color").
import { BDS_colorMap } from "../../../assets/colors";

/**
 * ChartsSection (TSX)
 *
 * Props:
 *  - filters: { realEstateType: string, cities?: string[] }
 *  - data: array of items { type: string, price: number, count?: number, month?: string, district?: string, city?: string, ... }
 *  - colorMap: Record<string, string>
 *  - priceUnit: string
 */

type Filters = {
  realEstateTypes?: string[];
  cities?: string[];
  district?: string;
  monthYear?: string;
  districts?: string[];
};

type DataItem = {
  type: string;
  price: number;
  month?: string;
  district?: string;
  city?: string;
  [key: string]: any;
};

type ChartsSectionProps = {
  filters?: Filters;
  data?: DataItem[];
  colorMap?: Record<string, string>;
  priceUnit?: string;
};

// Use keys from BDS_colorMap as the default list of types to display
const defaultTypes: string[] = Object.keys(BDS_colorMap);

type CustomTooltipProps = {
  active?: boolean;
  payload?: any[] | readonly any[];
  label?: string | number | undefined;
  priceUnit?: string;
};

const CustomTooltip: React.FC<CustomTooltipProps> = ({
  active,
  payload,
  label,
  priceUnit = "triệu/m2",
}) => {
  if (active && payload && payload.length) {
    const p = payload[0] as any;
    const value = typeof p?.value === "number" ? (p.value as number) : NaN;
    const color = p?.color ?? "#000";
    return (
      <div className="bg-white/80 backdrop-blur-sm p-3 rounded-lg shadow-lg border border-gray-200">
        <p style={{ color }}>{`${label}: ${
          Number.isFinite(value) ? value.toFixed(2) : "-"
        } ${priceUnit}`}</p>
      </div>
    );
  }
  return null;
};

type DataLabelProps = {
  x?: number;
  y?: number;
  width?: number;
  value?: number;
};

const DataLabel: React.FC<DataLabelProps> = ({
  x = 0,
  y = 0,
  width = 0,
  value = 0,
}) => {
  return (
    <text
      x={x + width / 2}
      y={y - 5}
      fill="#666"
      textAnchor="middle"
      dy={0}
      fontSize={15}
    >
      {Number.isFinite(value) ? value.toFixed(2) : "-"}
    </text>
  );
};

export default function ChartsSection({
  filters = { realEstateTypes: [], cities: [] },
  data = [],
  colorMap = {},
  priceUnit,
}: ChartsSectionProps): React.JSX.Element {
  // Merge project color map with any colorMap prop passed in (prop takes precedence)
  const mergedColorMap = useMemo(
    () => ({
      ...(BDS_colorMap as Record<string, string>),
      ...(colorMap || {}),
    }),
    [colorMap],
  );

  const chartTypesToDisplay =
    !filters.realEstateTypes || filters.realEstateTypes.length === 0
      ? Object.keys(mergedColorMap).length
        ? Object.keys(mergedColorMap)
        : defaultTypes
      : filters.realEstateTypes;

  type AnalyticsChartProps = {
    title: string;
    type: string;
    color: string;
  };

  const AnalyticsChart: React.FC<AnalyticsChartProps> = ({
    title,
    type,
    color,
  }) => {
    // Requirement: if districts are selected -> x-axis = district
    // otherwise -> x-axis = city (Province)
    const detectDefaultXAxis = (): "month" | "district" | "city" => {
      const dists = filters?.districts ?? [];
      if (dists.length > 0) return "district";
      return "city";
    };

    // filteredForType still used for aggregations, but x-axis decision uses filters
    const filteredForType = useMemo(
      () => data.filter((d) => d.type === type),
      [data, type],
    );

    const [xAxisKey, setXAxisKey] = useState<"month" | "district" | "city">(
      detectDefaultXAxis,
    );

    // new: keep previous non-month key to allow toggling back
    const [prevXAxisKey, setPrevXAxisKey] = useState<
      "month" | "district" | "city" | null
    >(() => {
      const detected = detectDefaultXAxis();
      return detected === "month" ? null : detected;
    });

    // Warning / helper message to user
    const [warning, setWarning] = useState<string | null>(null);

    // Recompute default when filters change (instead of inferring from data)
    React.useEffect(() => {
      const detected = detectDefaultXAxis();

      // If we're currently showing a non-month view and the detected default changed,
      // update the current view to the new detected default.
      if (xAxisKey !== detected && xAxisKey !== "month") {
        setXAxisKey(detected);
      }

      // If we're currently on month, update prevXAxisKey so toggle-back returns the fresh detected default.
      if (xAxisKey === "month") {
        setPrevXAxisKey(detected === "month" ? null : detected);
      } else {
        // Ensure prevXAxisKey doesn't accidentally equal the current key
        if (prevXAxisKey === xAxisKey) {
          setPrevXAxisKey(null);
        }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters?.cities, xAxisKey, data, type]);

    // fixed pixel width per bar (change this value to control bar width)
    const BAR_WIDTH = 48; // px
    const MIN_CHART_WIDTH = 600; // px
    const effectiveGap = 50;

    const monthsSet = useMemo(() => {
      return new Set(
        filteredForType
          .map((d) => (d.month ?? "").toString().trim())
          .filter((m) => m !== ""),
      );
    }, [filteredForType]);

    // Reusable grouped chart data (depends on xAxisKey)
    const chartData = useMemo(() => {
      const filteredData = filteredForType;
      const groupedData = filteredData.reduce<
        Record<string, { name: string; total: number; count: number }>
      >((acc, item) => {
        const key = String(item[xAxisKey] ?? "Unknown");
        const itemPrice = Number(item.price) || 0;
        if (!acc[key]) acc[key] = { name: key, total: 0, count: 0 };
        acc[key].total += itemPrice;
        acc[key].count += 1;
        return acc;
      }, {});

      const result = Object.entries(groupedData).map(([key, value]) => ({
        name: key,
        // compute simple average price per group
        [type]: value.count > 0 ? value.total / value.count : 0,
      })) as Array<Record<string, any>>;

      // sort months chronologically if using month
      if (xAxisKey === "month") {
        return result.sort((a, b) => {
          const [m1 = "1", y1 = "1970"] = String(a.name).split("/");
          const [m2 = "1", y2 = "1970"] = String(b.name).split("/");
          return (
            new Date(Number(y1), Number(m1) - 1).getTime() -
            new Date(Number(y2), Number(m2) - 1).getTime()
          );
        });
      }
      return result;
    }, [filteredForType, type, xAxisKey]);

    const chartWidth = Math.max(
      MIN_CHART_WIDTH,
      chartData.length * BAR_WIDTH +
        Math.max(0, chartData.length - 1) * effectiveGap +
        40,
    );

    // Whether we have any data to show (used to hide the toggle button when there's "Không có dữ liệu")
    const hasData = Boolean(chartData && chartData.length > 0);

    // Toggle handler: if not month -> save current and switch to month.
    // if already month -> restore previous (or detected default if none).
    const handleToggleMonth = () => {
      const monthsCount = monthsSet.size;

      if (xAxisKey !== "month") {
        // User requested month view
        if (monthsCount <= 1) {
          // show gentle reminder but still switch to month (per requirement)
          setWarning("Vui lòng chọn nhiều hơn 1 tháng để xem biến động giá");
          // auto-clear the warning after a few seconds
          window.setTimeout(() => setWarning(null), 4000);
        } else {
          setWarning(null);
        }

        setPrevXAxisKey(xAxisKey);
        setXAxisKey("month");
      } else {
        const to = prevXAxisKey ?? detectDefaultXAxis();
        setXAxisKey(to);
        setPrevXAxisKey(null);
        setWarning(null);
      }
    };

    const renderChart = () => {
      const gradientId = `colorGradient-${String(type).replace(/\s/g, "")}`;
      const rotateTicks = 0;

      // If there's no data to show for the current grouping
      if (!chartData || chartData.length === 0) {
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500">Không có dữ liệu</div>
          </div>
        );
      }

      // Special requirement: use BarChart if month view contains only 1 month
      const usingSingleMonthBar = xAxisKey === "month" && chartData.length <= 1;

      if (xAxisKey === "month" && !usingSingleMonthBar) {
        // Calculate max value for Y axis domain
        const maxValue = Math.max(
          ...chartData.map((d) => Number(d[type]) || 0),
          0,
        );
        const yAxisMax = Math.ceil(maxValue * 1.15);

        return (
          <div style={{ width: "100%", height: "100%", overflowX: "auto" }}>
            <div style={{ minWidth: chartWidth, height: "100%" }}>
              <ResponsiveContainer width={chartWidth} height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 20, right: 30, left: 30, bottom: 5 }} // <-- tăng left ở đây
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#e0e0e0"
                  />
                  <XAxis
                    dataKey="name"
                    // nếu muốn đẩy tick labels nữa, có thể thêm padding
                    padding={{ left: 20, right: 0 }}
                    tick={{
                      fontSize: 12,
                      angle: rotateTicks,
                      textAnchor: rotateTicks ? "end" : "middle",
                    }}
                  />
                  <YAxis tick={{ fontSize: 12 }} domain={[0, yAxisMax]} />
                  <Tooltip content={<CustomTooltip priceUnit={priceUnit} />} />
                  <Line
                    type="monotone"
                    dataKey={type}
                    stroke={color}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 8 }}
                  >
                    <LabelList dataKey={type} content={<DataLabel />} />
                  </Line>
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      }

      // Default to BarChart (used for non-month xAxis or for single-month month view)
      return (
        <div style={{ width: "100%", height: "100%", overflowX: "auto" }}>
          <div style={{ minWidth: chartWidth, height: "100%" }}>
            <ResponsiveContainer width={chartWidth} height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
                barSize={BAR_WIDTH}
                barCategoryGap={effectiveGap}
              >
                <defs>
                  <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={color} stopOpacity={0.95} />
                    <stop offset="95%" stopColor={color} stopOpacity={0.65} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#e0e0e0"
                />
                <XAxis
                  dataKey="name"
                  tick={{
                    fontSize: 12,
                    angle: rotateTicks,
                    textAnchor: rotateTicks ? "end" : "middle",
                  }}
                />
                <YAxis tick={{ fontSize: 18 }} />
                <Tooltip content={<CustomTooltip priceUnit={priceUnit} />} />
                <Bar
                  dataKey={type}
                  fill={`url(#${gradientId})`}
                  radius={[4, 4, 0, 0]}
                  barSize={BAR_WIDTH}
                >
                  <LabelList dataKey={type} content={<DataLabel />} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    };

    const xAxisLabel =
      xAxisKey === "district"
        ? "Quận/Huyện"
        : xAxisKey === "city"
          ? "Tỉnh/Thành phố"
          : "Tháng";

    return (
      <div className="bg-white p-6 rounded-2xl shadow-md hover:shadow-xl transition-shadow duration-300 w-full animate-fade-in">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
          <h3 className="text-lg font-bold text-gray-800 mb-2 sm:mb-0">
            Trung bình giá <span style={{ color }}>{title}</span>
          </h3>
          <div className="flex items-center space-x-2">
            {/* Toggle button: click 2 chiều */}
            {hasData && (
              <button
                type="button"
                aria-pressed={xAxisKey === "month"}
                aria-label="Xem biến động giá theo tháng"
                onClick={handleToggleMonth}
                className={`cursor-pointer inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200   ${
                  xAxisKey === "month"
                    ? "bg-blue-500 text-white shadow-md transform hover:scale-[1.02] active:scale-95"
                    : "bg-white text-gray-700 border border-gray-400 hover:scale-[1.02] hover:shadow-sm hover:bg-gray-200"
                }`}
              >
                <svg
                  xmlns="https://www.w3.org/2000/svg"
                  className="h-4 w-4 flex-shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d="M3 3v18h18" />
                  <path d="M19 9l-5 5-4-4-6 6" />
                </svg>

                <span>Biến động giá theo tháng</span>
              </button>
            )}
          </div>
        </div>

        {/* Helper / warning message shown when user clicks month but only 1 month present */}
        {warning && (
          <div className="mb-3 p-3 rounded-md bg-yellow-50 border border-yellow-200 text-yellow-800">
            {warning}
          </div>
        )}

        <div style={{ height: "500px" }}>{renderChart()}</div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 gap-8">
      {chartTypesToDisplay.map((type) => (
        <AnalyticsChart
          key={type}
          title={type}
          type={type}
          color={mergedColorMap[type] || "#3b82f6"}
        />
      ))}
    </div>
  );
}

// Export small helper CSS string to paste into your page (optional)
export const pageStyles = `@keyframes fade-in { from { opacity: 0; transform: translateY(10px);} to { opacity: 1; transform: translateY(0);} } .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }`;
