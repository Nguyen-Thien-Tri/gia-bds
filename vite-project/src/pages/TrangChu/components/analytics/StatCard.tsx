import { motion } from "framer-motion";
import { StatCardProps } from "./types";
import { cardVariants } from "./constants";

export default function StatCard({
  Icon,
  value,
  label,
  change,
  positive,
  loading,
}: StatCardProps) {
  const isPositiveTrend =
    positive ?? parseFloat(String(change).replace(",", ".")) >= 0;

  return (
    <motion.article
      variants={cardVariants}
      className="relative group bg-white rounded-2xl p-6 text-center shadow-lg border border-slate-200/50 overflow-hidden"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-cyan-50 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
      <div className="absolute top-0 left-1/2 -translate-x-1/2 h-1 w-0 group-hover:w-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-300 rounded-full" />
      <div className="relative z-10 flex flex-col items-center justify-between h-full group-hover:-translate-y-1 transition-transform duration-300">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white shadow-lg mb-4 group-hover:scale-110 transition-transform duration-300">
            <Icon className="w-8 h-8" />
          </div>
          <p
            className={`${value === "No data" ? "text-xl text-slate-400" : "text-3xl text-slate-800"} font-extrabold transition-colors duration-300`}
          >
            {loading ? "..." : value}
          </p>
          <p className="text-slate-500 font-medium mt-1.5">{label}</p>
        </div>
        <span
          className={`inline-block text-sm font-semibold px-3 py-1.5 rounded-full mt-3 transition-colors duration-300 ${
            value === "No data"
              ? "bg-slate-100 text-slate-400"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {loading ? (
            "..."
          ) : value === "No data" ? (
            "Không có dữ liệu"
          ) : (
            <>
              {!isPositiveTrend || change.startsWith("-") || change === "0,0%"
                ? change
                : "+" + change}{" "}
              so với tháng trước
            </>
          )}
        </span>
      </div>
    </motion.article>
  );
}
