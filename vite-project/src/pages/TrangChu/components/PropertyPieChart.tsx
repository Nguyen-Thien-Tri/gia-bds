import { useState } from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { priceColorMap } from "../../../assets/colors"; // <- adjust path if needed

interface DataEntry {
  label: string;
  value: number;
}

interface PropertyPieChartProps {
  data?: DataEntry[];
  total?: number;
  loading?: boolean;
  centerLabel?: string;
}

export default function PropertyPieChart({
  data = [],
  total = 0,
  loading = false,
  centerLabel = "Căn hộ chung cư",
}: PropertyPieChartProps) {
  // local hidden slices state to mimic the original behaviour
  const [hiddenSlices, setHiddenSlices] = useState<Set<number>>(new Set());

  const toggleSlice = (idx: number) => {
    setHiddenSlices((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const getColor = (label: string): string => 
    (priceColorMap as any)[label] ?? "#64748b"; // fallback color

  return (
    <div className="h-full relative">
      {loading && (
        <div className="absolute inset-0 bg-gradient-to-r from-white to-slate-50 animate-pulse rounded-xl z-10" />
      )}

      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip
            formatter={(value: any, name: string) => [`${value}%`, name]}
            wrapperStyle={{ zIndex: 9999 }}
          />
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            innerRadius={64}
            outerRadius={96}
            paddingAngle={4}
            isAnimationActive={false}
          >
            {data.map((entry, idx) => (
              <Cell
                key={`cell-${idx}`}
                fill={getColor(entry.label)}
                fillOpacity={hiddenSlices.has(idx) ? 0.12 : 1}
              />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>

      {/* center text */}
      <div className="absolute left-0 right-0 top-0 bottom-0 flex items-center justify-center pointer-events-none">
        <div className="text-center">
          <div className="font-bold text-lg text-slate-900">
            {total.toLocaleString()}
          </div>
          <div className="text-xs text-slate-600">{centerLabel}</div>
        </div>
      </div>

      {/* accessible legend */}
      <div className="grid grid-cols-2 gap-2 mt-4 text-sm text-slate-700">
        {data.map((p, idx) => {
          const color = getColor(p.label);
          return (
            <button
              key={`${p.label}-${idx}`}
              type="button"
              onClick={() => toggleSlice(idx)}
              // Thay đổi ở đây:
              // 1. justify-start: Căn chỉnh nội dung (dot + text) về bên trái của button.
              // 2. w-40 (hoặc một giá trị width phù hợp): Đặt chiều rộng cố định cho button.
              // 3. mx-auto: Canh giữa button này trong ô lưới của nó.
              className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-slate-50 w-40 mx-auto"
            >
              <span
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 9999,
                  background: color,
                  display: "inline-block",
                  // Thêm flex-shrink: 0 để dot không bị co lại
                  flexShrink: 0,
                  opacity: hiddenSlices.has(idx) ? 0.3 : 1,
                }}
              />
              <span className="truncate">
                {p.label} ({p.value}%)
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
