import React, { useEffect, useState } from "react";
import {
  TrendingUp,
  School,
  Building,
  Building2Icon,
  DollarSign,
} from "lucide-react";
import { collection, query, where, getDocs } from "firebase/firestore";
import { db } from "../../../firebase";
import EmailSignupSection from "./SubscribeCTA";
import { ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

// Type definitions
interface PieDataItem {
  name: string;
  value: number;
  color: string;
}

interface Stat {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
}

const now = new Date();
const displayDate = new Date(now);
if (now.getDate() <= 15) {
  displayDate.setMonth(displayDate.getMonth() - 1);
}
const currentMonth = String(displayDate.getMonth() + 1).padStart(2, "0");
const currentYear = displayDate.getFullYear();

// Helper function to format numbers
const formatNumber = (num: number) =>
  new Intl.NumberFormat("de-DE").format(num);

export default function HeroSection(): React.JSX.Element {
  const [currentStat, setCurrentStat] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [stats, setStats] = useState<Stat[]>([
    { label: "Dự án", value: "...", icon: Building2Icon },
    { label: "Bất động sản đăng bán", value: "...", icon: School },
    {
      label: "Giá trị giao dịch (tỷ VND)",
      value: "...",
      icon: DollarSign,
    },
    {
      label: `Trung bình giá căn hộ chung cư`,
      value: "...",
      icon: Building,
    },
  ]);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const today = new Date();
        const dayOfMonth = today.getDate();
        const targetDate = new Date(today);

        if (dayOfMonth <= 15) {
          targetDate.setMonth(targetDate.getMonth() - 1);
        }

        const year = targetDate.getFullYear();
        const month = String(targetDate.getMonth() + 1).padStart(2, "0");
        const yearMonth = `${year}-${month}`;

        // 1. Fetch all metrics in one query
        const metricsRef = collection(db, "metrics");
        const metricsQuery = query(
          metricsRef,
          where("province", "==", "All"),
          where("year_month", "==", yearMonth),
          where("name", "in", [
            "project_count",
            "sales_bds_count",
            "total_sales_amt",
            "CHCC_price", // Added CHCC_price metric
          ]),
        );

        const metricsSnapshot = await getDocs(metricsQuery);
        const metricsData: { [key: string]: number } = {};
        metricsSnapshot.forEach((doc) => {
          const data = doc.data();
          metricsData[data.name] = data.value;
        });

        // 2. Update state
        setStats([
          {
            label: "Dự án",
            value: formatNumber(metricsData.project_count || 0),
            icon: Building2Icon,
          },
          {
            label: "Bất động sản đăng bán",
            value: formatNumber(metricsData.sales_bds_count || 0),
            icon: School,
          },
          {
            label: "Giá trị ước tính (tỷ VND)",
            value: formatNumber(Math.round(metricsData.total_sales_amt || 0)),
            icon: DollarSign,
          },
          {
            label: `Trung bình giá căn hộ chung cư`,
            value: `${((metricsData.CHCC_price || 0) / 1000).toLocaleString(
              "de-DE",
              {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              },
            )} tỷ VND`,
            icon: Building,
          },
        ]);
      } catch (error) {
        console.error("Error fetching hero stats:", error);
        // Keep placeholder or error state if fetch fails
        setStats([
          { label: "Dự án", value: "N/A", icon: Building2Icon },
          { label: "Bất động sản đăng bán", value: "N/A", icon: School },
          {
            label: "Giá trị ước tính (tỷ VND)",
            value: "N/A",
            icon: DollarSign,
          },
          {
            label: `Trung bình giá căn hộ chung cư`,
            value: "N/A",
            icon: Building,
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  useEffect(() => {
    if (loading) return;

    const timer = setInterval(() => {
      setCurrentStat((prev) => (prev + 1) % stats.length);
    }, 2000);

    return () => {
      clearInterval(timer);
    };
  }, [loading, stats.length]);

  const pieData: PieDataItem[] = [
    { name: "Căn hộ", value: 45, color: "#3B82F6" },
    { name: "Nhà riêng", value: 30, color: "#06B6D4" },
    { name: "Biệt thự", value: 15, color: "#8B5CF6" },
    { name: "Đất nền", value: 10, color: "#EC4899" },
  ];

  // ---------- JSX ----------
  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-20 -right-40 w-80 h-80 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-full opacity-80 " />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-full opacity-15 animate-pulse delay-1000" />
      </div>

      <div className="absolute max-xl:hidden lg:right-40 top-40 right-30 w-24 h-24 bg-white/80 backdrop-blur-sm rounded-full shadow-lg p-3 animate-pulse">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData.slice(0, 2)}
              dataKey="value"
              cx="50%"
              cy="50%"
              outerRadius={30}
            >
              {pieData.slice(0, 2).map((entry: PieDataItem, index: number) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="relative z-10 xl:container mx-auto px-6 py-30">
        {/* Use column layout so LeftHeroSection occupies full row for all viewports */}
        <div className="flex flex-col items-center justify-between min-h-[60vh]">
          {/* LeftHeroSection now occupies the full row and is centered */}
          <div className="w-full flex justify-center items-center">
            <div className="w-full max-w-4xl">
              {/* Main Title */}
              <div className="text-center space-y-4 mb-4">
                <div className="flex items-center justify-center space-x-2 text-blue-600 font-medium">
                  <TrendingUp className="w-5 h-5" />
                  <span>Phân tích thị trường bất động sản</span>
                </div>

                <h1 className="text-3xl lg:text-5xl font-bold text-gray-900 leading-tight">
                  <span className="block bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                    Thống kê thị trường giá bất động sản tại Việt Nam
                  </span>
                </h1>

                <p className="text-xl text-gray-600">
                  Nền tảng phân tích dữ liệu toàn diện về thị trường bất động
                  sản tại Việt Nam với thông tin chi tiết và biểu đồ trực quan
                  được cập nhật hằng tuần.
                </p>
              </div>

              {/* CTA Buttons */}
              <EmailSignupSection />

              {/* Date Card */}
              <div className="flex justify-center mt-8 mb-8">
                <div className="bg-white/80 backdrop-blur-sm rounded-xl px-8 py-3 shadow-lg border border-white/50 transition-all duration-500 text-center">
                  <div className="text-xl font-bold text-gray-900">
                    Tháng {currentMonth}/{currentYear}
                  </div>
                </div>
              </div>

              {/* Animated Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 justify-center">
                {stats.map((stat, index) => {
                  const Icon = stat.icon;
                  const isActive = currentStat === index;
                  return (
                    <div
                      key={index}
                      className={`bg-white/80 backdrop-blur-sm rounded-xl p-4 shadow-lg transition-all duration-500 text-center ${
                        isActive ? "scale-110 shadow-xl bg-blue-50" : ""
                      }`}
                    >
                      <div
                        className={`w-10 h-10 rounded-lg mb-3 flex items-center justify-center ${
                          isActive
                            ? "bg-blue-600 text-white"
                            : "bg-gray-100 text-gray-600"
                        } transition-all duration-300`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="text-2xl font-bold text-gray-900">
                        {loading ? "..." : stat.value}
                      </div>
                      <div className="text-sm text-gray-600">{stat.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Wave */}
      <div className="absolute bottom-0 w-full">
        <svg
          className="w-full h-24 text-white"
          fill="currentColor"
          viewBox="0 0 1200 120"
          preserveAspectRatio="none"
        >
          <path
            d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z"
            opacity=".25"
          />
          <path
            d="M0,0V15.81C13,36.92,27.64,56.86,47.69,72.05,99.41,111.27,165,111,224.58,91.58c31.15-10.15,60.09-26.07,89.67-39.8,40.92-19,84.73-46,130.83-49.67,36.26-2.85,70.9,9.42,98.6,31.56,31.77,25.39,62.32,62,103.63,73,40.44,10.79,81.35-6.69,119.13-24.28s75.16-39,116.92-43.05c59.73-5.85,113.28,22.88,168.9,38.84,30.2,8.66,59,6.17,87.09-7.5,22.43-10.89,48-26.93,60.65-49.24V0Z"
            opacity=".5"
          />
          <path d="M0,0V5.63C149.93,59,314.09,71.32,475.83,42.57c43-7.64,84.23-20.12,127.61-26.46,59-8.63,112.48,12.24,165.56,35.4C827.93,77.22,886,95.24,951.2,90c86.53-7,172.46-45.71,248.8-84.81V0Z" />
        </svg>
      </div>
    </div>
  );
}
