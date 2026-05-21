import React from "react";
import RechartsPrebinnedChart from "../LineChart2";
import PropertyPieChart from "../PropertyPieChart";
import { PrebinnedItem, PieItem } from "./types";

export function AreaChartCard({
  title,
  data,
  loading,
  minWidth = 520,
}: {
  title: string;
  data: PrebinnedItem[];
  loading: boolean;
  minWidth?: number;
}) {
  /* 
    Calculate the maximum value in the dataset to set the Y-axis domain.
    The requirement is to set max Y = 1.1 * max data value.
  */
  const maxValue = React.useMemo(() => {
    if (!data || data.length === 0) return 0;
    return Math.max(
      ...data.map((d) => (typeof d.Giá === "number" ? d.Giá : 0)),
    );
  }, [data]);

  const hasData = data && data.length > 0 && data.some((d) => d.Giá > 0);
  const yDomain: [number, number] = [0, Math.ceil(maxValue * 1.2)];

  return (
    <div className="md:col-span-2 bg-white rounded-2xl p-5 shadow-lg border border-white/40">
      <div className="flex items-center justify-center mb-3">
        <h3 className="text-lg text-center font-semibold text-slate-700">
          {title}
        </h3>
      </div>
      <div className="text-xs text-slate-800">(triệu VND/m²)</div>

      <div className="relative h-80">
        {loading && (
          <div className="absolute inset-0 bg-gradient-to-r from-white to-slate-50 animate-pulse rounded-xl z-20" />
        )}

        {!loading && !hasData && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm p-8 text-center bg-slate-50/50 rounded-xl">
            Không có dữ liệu hoặc dữ liệu của vùng quá ít
          </div>
        )}

        <div
          className={`w-full h-full overflow-x-auto ${!hasData && !loading ? "opacity-0" : "opacity-100"}`}
        >
          <div
            className="h-full"
            style={{
              minWidth: `${Math.max(data.length * 60, minWidth)}px`,
            }}
          >
            <RechartsPrebinnedChart
              data={data}
              xKey="range"
              yKey="Giá"
              currencySymbol=" triệu"
              yDomain={yDomain}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export function PieChartCard({
  title,
  data,
  total,
  loading,
  centerLabel,
}: {
  title: string;
  data: PieItem[];
  total: number;
  loading: boolean;
  centerLabel?: string;
}) {
  const hasData = data && data.length > 0 && data.some((d) => d.value > 0);

  return (
    <div className="h-105 bg-white rounded-2xl p-5 shadow-lg border border-white/40">
      <h3 className="text-lg text-center font-semibold text-slate-700 mb-3">
        {title}
      </h3>
      <div className="h-48 relative">
        {loading && (
          <div className="absolute inset-0 bg-gradient-to-r from-white to-slate-50 animate-pulse rounded-xl z-20" />
        )}
        {!loading && !hasData && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm p-8 text-center bg-slate-50/50 rounded-xl">
            Không có dữ liệu hoặc dữ liệu của vùng quá ít
          </div>
        )}
        <div
          className={`h-full ${!hasData && !loading ? "opacity-0" : "opacity-100"}`}
        >
          <PropertyPieChart
            data={data}
            total={total}
            loading={loading}
            centerLabel={centerLabel}
          />
        </div>
      </div>
    </div>
  );
}
