import React, { useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from "recharts";
import { db } from "../../../firebase";
import { collection, getDocs, query, where } from "firebase/firestore";
import { BDS_colorMap } from "../../../assets/colors";

// Type definitions
interface BarDataItem {
  LoaiBDS: string;
  value: number;
}

interface FirestoreDoc {
  bds_type: string;
  avg_price_million: number;
  [key: string]: any;
}

export default function BarChartsSection(): React.JSX.Element {
  const [hanoiData, setHanoiData] = useState<BarDataItem[]>([]);
  const [hcmData, setHcmData] = useState<BarDataItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const yearMonth = useMemo(() => {
    const now = new Date();
    const dateToUse = new Date(now);

    if (now.getDate() <= 15) {
      // go to previous month
      dateToUse.setMonth(dateToUse.getMonth() - 1);
    }

    const currentYear = dateToUse.getFullYear();
    const monthNumber = dateToUse.getMonth() + 1; // getMonth() is 0-indexed
    const currentMonth = monthNumber.toString().padStart(2, "0");
    return `${currentYear}-${currentMonth}`;
  }, []);

  const { currentMonth, currentYear } = useMemo(() => {
    const [year, month] = yearMonth.split("-");
    return { currentMonth: month, currentYear: year };
  }, [yearMonth]);

  // property types (used for legend and x-axis categories)
  const propertyTypes: BarDataItem[] = useMemo(
    () => [
      { LoaiBDS: "Căn hộ chung cư", value: 0 },
      { LoaiBDS: "Nhà biệt thự / Nhà liền kề", value: 0 },
      { LoaiBDS: "Nhà phố", value: 0 },
      { LoaiBDS: "Đất", value: 0 },
      { LoaiBDS: "Nhà ở", value: 0 },
    ],
    [],
  );

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const processData = (
          docs: FirestoreDoc[],
          propertyTypes: BarDataItem[],
        ): BarDataItem[] => {
          const priceData: { [key: string]: number[] } = {};
          docs.forEach((doc) => {
            if (!priceData[doc.bds_type]) {
              priceData[doc.bds_type] = [];
            }
            priceData[doc.bds_type].push(doc.avg_price_million);
          });

          const averagedData = propertyTypes.map((prop) => {
            const prices = priceData[prop.LoaiBDS];
            if (prices && prices.length > 0) {
              const sum = prices.reduce((a, b) => a + b, 0);
              return {
                ...prop,
                value: parseFloat((sum / prices.length).toFixed(2)),
              };
            }
            return { ...prop, value: 0 }; // Return 0 if no data
          });

          return averagedData;
        };

        const baseQuery = [
          where("year_month", "==", yearMonth),
          where("price_type", "==", "Bán"),
          where("district", "==", "All"),
          where(
            "bds_type",
            "in",
            propertyTypes.map((p) => p.LoaiBDS),
          ),
        ];

        const hanoiQuery = query(
          collection(db, "price_data"),
          ...baseQuery,
          where("province", "==", "Hà Nội"),
        );
        const hcmQuery = query(
          collection(db, "price_data"),
          ...baseQuery,
          where("province", "==", "Hồ Chí Minh"),
        );

        const [hanoiSnapshot, hcmSnapshot] = await Promise.all([
          getDocs(hanoiQuery),
          getDocs(hcmQuery),
        ]);

        const hanoiDocs = hanoiSnapshot.docs.map(
          (doc) => doc.data() as FirestoreDoc,
        );
        const hcmDocs = hcmSnapshot.docs.map(
          (doc) => doc.data() as FirestoreDoc,
        );

        setHanoiData(processData(hanoiDocs, propertyTypes));
        setHcmData(processData(hcmDocs, propertyTypes));
      } catch (err: unknown) {
        console.error("Error fetching Firestore data:", err);
        setError("Không thể tải dữ liệu. Vui lòng thử lại sau.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [yearMonth, propertyTypes]);

  // ---------- Dynamic height logic ----------
  const [viewportWidth, setViewportWidth] = useState<number>(
    typeof window !== "undefined" ? window.innerWidth : 1200,
  );

  useEffect(() => {
    function onResize(): void {
      setViewportWidth(window.innerWidth);
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // tuning constants — tweak to taste
  const minHeight: number = 220; // minimum chart height in px
  const maxHeight: number = 1000; // maximum chart height in px
  const desktopPerItem: number = 48; // px per bar on large screens
  const mobilePerItem: number = 42; // px per bar on small screens
  const topBottomPadding: number = 100; // px for label area, grid, etc.

  const perItem: number = viewportWidth < 768 ? mobilePerItem : desktopPerItem;

  const chartHeight: number = useMemo(() => {
    // use the number of property types to determine height so both charts look balanced
    const maxLen = propertyTypes.length;
    const h = maxLen * perItem + topBottomPadding;
    return Math.max(minHeight, Math.min(maxHeight, h));
  }, [propertyTypes.length, perItem]);

  const isHanoiDataAvailable = useMemo(
    () => hanoiData.some((d) => d.value > 0),
    [hanoiData],
  );
  const isHcmDataAvailable = useMemo(
    () => hcmData.some((d) => d.value > 0),
    [hcmData],
  );

  const yMax = useMemo(() => {
    const maxHanoi =
      hanoiData.length > 0 ? Math.max(...hanoiData.map((d) => d.value)) : 0;
    const maxHcm =
      hcmData.length > 0 ? Math.max(...hcmData.map((d) => d.value)) : 0;
    const overallMax = Math.max(maxHanoi, maxHcm);
    // add 15% padding, and have a default max of 100
    return overallMax > 0 ? Math.ceil(overallMax * 1.15) : 100;
  }, [hanoiData, hcmData]);

  if (loading) {
    return (
      <div className="w-full mt-12 lg:mt-6 flex justify-center items-center h-96">
        <div>Đang tải dữ liệu...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full mt-12 lg:mt-6 flex justify-center items-center h-96">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="w-full mt-12 lg:mt-6">
      <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl px-8 pt-8 border border-white/20">
        {/* Shared Legend (uses propertyTypes and BDS_colorMap) */}
        <div className="mb-4 flex justify-center">
          <div className="grid grid-cols-3 gap-x-6 gap-y-2 justify-items-start">
            {propertyTypes.map((d: BarDataItem, i: number) => (
              <div
                key={i}
                className="flex items-baseline space-x-2 text-md w-full"
              >
                <span
                  className="w-3 h-3 rounded-sm flex-shrink-0"
                  style={{
                    backgroundColor: d.LoaiBDS
                      ? BDS_colorMap[d.LoaiBDS] || "#3B82F6"
                      : "transparent",
                  }}
                />
                <span className="whitespace-normal break-words max-w-[9rem]">
                  {d.LoaiBDS}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Separate chart cards: each chart in its own card (stacked on mobile, side-by-side on lg) */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card for Hà Nội */}
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-6 border border-white/20">
            <div className="flex items-start justify-between mb-4">
              <h4 className="text-lg font-semibold">
                Trung bình giá bất động sản tại Hà Nội tháng {currentMonth}/
                {currentYear} (triệu VND/m2)
              </h4>
            </div>
            <div className="w-full">
              {isHanoiDataAvailable ? (
                <ResponsiveContainer width="100%" height={chartHeight}>
                  <BarChart
                    data={hanoiData}
                    margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="LoaiBDS"
                      axisLine={false}
                      tickLine={false}
                      tick={false}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      domain={[0, yMax]}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "white",
                        border: "none",
                        borderRadius: "12px",
                        boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
                      }}
                      animationDuration={0}
                    />
                    <Bar
                      dataKey="value"
                      radius={[6, 6, 0, 0]}
                      animationDuration={0}
                      barCategoryGap="20%"
                    >
                      {hanoiData.map((entry: BarDataItem, index: number) => (
                        <Cell
                          key={`hanoi-cell-${entry.LoaiBDS}-${index}`}
                          fill={BDS_colorMap[entry.LoaiBDS] || "#3B82F6"}
                        />
                      ))}
                      <LabelList
                        dataKey="value"
                        position="top"
                        style={{
                          fill: "#374151",
                          fontSize: 14,
                          fontWeight: "bold",
                        }}
                        formatter={(val: any) =>
                          Number(val).toLocaleString("de-DE", {
                            minimumFractionDigits: 1,
                            maximumFractionDigits: 1,
                          })
                        }
                      />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div
                  style={{ height: chartHeight }}
                  className="flex items-center justify-center text-gray-500 text-sm p-8 text-center"
                >
                  Không có dữ liệu hoặc dữ liệu của vùng quá ít
                </div>
              )}
            </div>
          </div>

          {/* Card for TP.HCM */}
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-6 border border-white/20">
            <div className="flex items-start justify-between mb-4">
              <h4 className="text-lg font-semibold">
                Trung bình giá bất động sản tại TP.HCM tháng {currentMonth}/
                {currentYear} (triệu VND/m2)
              </h4>
            </div>
            <div className="w-full">
              {isHcmDataAvailable ? (
                <ResponsiveContainer width="100%" height={chartHeight}>
                  <BarChart
                    data={hcmData}
                    margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="LoaiBDS"
                      axisLine={false}
                      tickLine={false}
                      tick={false}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      domain={[0, yMax]}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "white",
                        border: "none",
                        borderRadius: "12px",
                        boxShadow: "0 10px 40px rgba(0,0,0,0.1)",
                      }}
                      animationDuration={0}
                    />
                    <Bar
                      dataKey="value"
                      radius={[6, 6, 0, 0]}
                      animationDuration={0}
                      barCategoryGap="20%"
                    >
                      {hcmData.map((entry: BarDataItem, index: number) => (
                        <Cell
                          key={`hcm-cell-${entry.LoaiBDS}-${index}`}
                          fill={BDS_colorMap[entry.LoaiBDS] || "#60A5FA"}
                        />
                      ))}
                      <LabelList
                        dataKey="value"
                        position="top"
                        style={{
                          fill: "#374151",
                          fontSize: 14,
                          fontWeight: "bold",
                        }}
                        formatter={(val: any) =>
                          Number(val).toLocaleString("de-DE", {
                            minimumFractionDigits: 1,
                            maximumFractionDigits: 1,
                          })
                        }
                      />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div
                  style={{ height: chartHeight }}
                  className="flex items-center justify-center text-gray-500 text-sm p-8 text-center"
                >
                  Không có dữ liệu hoặc dữ liệu của vùng quá ít
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
