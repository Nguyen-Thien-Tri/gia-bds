import React, { useState, useRef, useEffect, useMemo, JSX } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  Building2Icon,
  School,
  DollarSign,
  Building,
} from "lucide-react";
import { provinceDict } from "../../../assets/geo";
import { BDS_colorMap } from "../../../assets/colors";
import RegionBar from "./RegionBarChart";
import { useMarketStats } from "../hooks/useMarketStats";
import { StatItem } from "./analytics/types";
import { containerVariants } from "./analytics/constants";
import { formatDate, getMostRecentMonday } from "./analytics/utils";
import StatCard from "./analytics/StatCard";
import ProvinceDropdown from "./analytics/ProvinceDropdown";
import { AreaChartCard, PieChartCard } from "./analytics/ChartCards";
import RechartsPrebinnedChart from "./LineChart2";

const defaultStats: StatItem[] = [
  {
    id: 1,
    Icon: Building2Icon,
    value: "...",
    label: "Dự án",
    change: "0",
    positive: true,
  },
  {
    id: 2,
    Icon: School,
    value: "...",
    label: "Bất động sản đăng bán",
    change: "0",
    positive: true,
  },
  {
    id: 3,
    Icon: DollarSign,
    value: "...",
    label: "Giá trị ước tính (tỷ VND)",
    change: "0",
    positive: true,
  },
  {
    id: 4,
    Icon: Building,
    value: "...",
    label: "Trung bình giá căn hộ chung cư (tỷ VND)",
    change: "0",
    positive: true,
  },
];

export default function AnalyticsSection({
  stats = defaultStats,
  className = "",
}): React.JSX.Element {
  const [selectedProvince, setSelectedProvince] = useState<string>("Toàn quốc");
  const [visible, setVisible] = useState<boolean>(false);
  const containerRef = useRef<HTMLElement | null>(null);

  const provinces = useMemo(() => {
    const priority = [
      "Hà Nội",
      "Hồ Chí Minh",
      "Bình Dương",
      "Đà Nẵng",
      "Khánh Hòa",
      "Đồng Nai",
      "Hải Phòng",
      "Bà Rịa Vũng Tàu",
    ];
    const allKeys = Object.keys(provinceDict as Record<string, string[]>);
    const otherProvinces = allKeys
      .filter((p) => !priority.includes(p))
      .sort((a, b) => a.localeCompare(b));
    return ["Toàn quốc", ...priority, ...otherProvinces];
  }, []);

  const {
    displayStats,
    apartmentPriceByArea,
    housePriceByArea,
    landPriceByArea,
    priceDistribution,
    housePriceDistribution,
    apartmentDistricts,
    townhouseDistricts,
    individualHouseDistricts,
    landDistricts,
    totalBDS,
    totalHouseBDS,
    remoteLastUpdated,
    loading: dataLoading,
  } = useMarketStats(selectedProvince, stats);

  // Still handle a small UI delay/lazy load for smooth entry
  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setVisible(true);
            obs.disconnect();
          }
        });
      },
      { threshold: 0.12 },
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, []);

  const [uiLoading, setUiLoading] = useState(true);
  useEffect(() => {
    if (visible) {
      const t = setTimeout(() => setUiLoading(false), 220);
      return () => clearTimeout(t);
    }
  }, [visible]);

  const loading = dataLoading || uiLoading;
  const displayDate = remoteLastUpdated ?? getMostRecentMonday();

  return (
    <section
      ref={containerRef}
      className={`xl:container mx-auto relative ${className}`}
      aria-labelledby="stats-heading"
    >
      <div className="py-10 sm:py-12 bg-slate-50">
        <div className="absolute top-0 right-0 flex-shrink-0 mt-1 mr-1">
          <div className="inline-flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-sm text-sm text-slate-700">
            <Clock className="w-4 h-4 text-slate-500" />
            <span className="whitespace-nowrap">
              Cập nhật lần cuối: {formatDate(displayDate)}
            </span>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <header className="flex justify-center mb-3 gap-3">
            <h2
              id="stats-heading"
              className="text-3xl sm:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500 pb-2 text-center"
            >
              Thống kê thị trường bất động sản Việt Nam{" "}
              {` tháng ${String(displayDate.getMonth() + 1).padStart(2, "0")}/${displayDate.getFullYear()}`}
            </h2>
          </header>

          <div className="flex justify-center items-center gap-3 mb-10">
            <span className="text-slate-700 font-medium">Tỉnh/thành phố :</span>
            <ProvinceDropdown
              value={selectedProvince}
              onChange={(v: string) => setSelectedProvince(v)}
              options={provinces}
            />
          </div>

          <motion.div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {displayStats.map((s) => (
              <StatCard key={s.id} {...s} loading={loading} />
            ))}
          </motion.div>
        </div>
      </div>

      <div className="p-8 bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.08 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            <AreaChartCard
              title="Biểu đồ giá căn hộ chung cư theo diện tích"
              data={apartmentPriceByArea}
              loading={loading}
            />
            <PieChartCard
              title="Phân bố theo mức giá"
              data={priceDistribution}
              total={totalBDS}
              loading={loading}
              centerLabel="Căn hộ chung cư"
            />
            <AreaChartCard
              title="Biểu đồ giá nhà ở theo diện tích"
              data={housePriceByArea}
              loading={loading}
            />
            <PieChartCard
              title="Phân bố giá nhà ở theo mức giá"
              data={housePriceDistribution}
              total={totalHouseBDS}
              loading={loading}
              centerLabel="Nhà ở"
            />
          </motion.div>

          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="lg:col-span-2 bg-white rounded-2xl p-5 shadow-lg border border-white/40">
              <h4 className="text-lg text-center font-semibold text-slate-700 mb-3">
                Biểu đồ giá đất theo diện tích
              </h4>
              <div className="text-xs text-center text-slate-800 mb-3">
                Đơn vị: triệu VND/m²
              </div>
              <div className="relative h-96">
                {loading && (
                  <div className="absolute inset-0 bg-gradient-to-r from-white to-slate-50 animate-pulse rounded-xl z-20" />
                )}
                {!loading &&
                  (!landPriceByArea ||
                    landPriceByArea.length === 0 ||
                    !landPriceByArea.some((d) => d.Giá > 0)) && (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm p-8 text-center bg-slate-50/50 rounded-xl">
                      Không có dữ liệu hoặc dữ liệu của vùng quá ít
                    </div>
                  )}
                <div
                  className={`w-full h-full overflow-x-auto ${!loading && (!landPriceByArea?.length || !landPriceByArea.some((d) => d.Giá > 0)) ? "opacity-0" : "opacity-100"}`}
                >
                  <div
                    className="h-full"
                    style={{
                      minWidth: `${Math.max(landPriceByArea.length * 60, 520)}px`,
                    }}
                  >
                    <RechartsPrebinnedChart
                      data={landPriceByArea}
                      xKey="range"
                      yKey="Giá"
                      currencySymbol=" triệu"
                      yDomain={[
                        0,
                        Math.ceil(
                          (Math.max(
                            ...(landPriceByArea || []).map((d) =>
                              typeof d.Giá === "number" ? d.Giá : 0,
                            ),
                          ) || 0) * 1.2,
                        ),
                      ]}
                    />
                  </div>
                </div>
              </div>
            </div>

            {[
              {
                title: "Top các quận huyện theo giá căn hộ chung cư",
                data: apartmentDistricts,
                color: BDS_colorMap["Căn hộ chung cư"],
              },
              {
                title: "Top các quận huyện theo giá nhà phố",
                data: townhouseDistricts,
                color: BDS_colorMap["Nhà phố"],
              },
              {
                title: "Top các quận huyện theo giá nhà ở",
                data: individualHouseDistricts,
                color: BDS_colorMap["Nhà ở"],
              },
              {
                title: "Top các quận huyện theo giá đất",
                data: landDistricts,
                color: BDS_colorMap["Đất"],
              },
            ].map((chart, idx) => {
              const maxValue =
                chart.data && chart.data.length > 0
                  ? Math.max(...chart.data.map((d) => d.value ?? 0))
                  : 0;
              const yMax = maxValue > 0 ? Math.ceil(maxValue * 1.1) : 100;

              return (
                <div
                  key={idx}
                  className="bg-white rounded-2xl shadow-lg border border-white/40"
                >
                  <h4 className="mb-1 text-lg text-center font-semibold text-slate-700">
                    {chart.title}
                  </h4>
                  <div className="text-xs text-center text-slate-800 mb-3">
                    Đơn vị: triệu VND/m²
                  </div>
                  <div className="h-[400px] relative">
                    {loading && (
                      <div className="absolute inset-0 bg-gradient-to-r from-white to-slate-50 animate-pulse rounded-xl z-20" />
                    )}
                    {!loading &&
                      (!chart.data?.length ||
                        !chart.data.some((d) => (d.value ?? 0) > 0)) && (
                        <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm p-8 text-center bg-slate-50/50 rounded-xl">
                          Không có dữ liệu hoặc dữ liệu của vùng quá ít
                        </div>
                      )}
                    <div
                      className={`h-full ${!loading && (!chart.data?.length || !chart.data.some((d) => (d.value ?? 0) > 0)) ? "opacity-0" : "opacity-100"}`}
                    >
                      <RegionBar
                        data={chart.data}
                        color={chart.color}
                        yDomain={[0, yMax]}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
