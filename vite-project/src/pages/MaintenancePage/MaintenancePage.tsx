import React from "react";
import { motion } from "framer-motion";
import Header from "../../components/Header";
import Footer from "../../components/Footer";
import { Wrench } from "lucide-react";

interface MaintenancePageProps {
  /** Date or string to display (e.g. new Date() or "April 1, 2026") */
  date?: string | Date;
  /** If true, the component will occupy the full viewport height (useful when used alone). Default: false */
  fullScreen?: boolean;
  /** Optional small subtitle under the main message */
  subtitle?: string;
}

function formatDate(date?: string | Date) {
  if (!date) return "sớm";
  try {
    const d = typeof date === "string" ? new Date(date) : date;
    // Format in Vietnamese locale with day/month/year and time
    return d.toLocaleString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (e) {
    return String(date);
  }
}

export default function MaintenancePage({
  date,
  fullScreen = false,
  subtitle,
}: MaintenancePageProps) {
  const showDate = formatDate(date);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main
        className={`${
          fullScreen ? "min-h-screen" : "py-24"
        } mt-10 flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-6`}
      >
        <div className="w-full max-w-3xl rounded-2xl bg-white dark:bg-gray-800 shadow-lg p-8 sm:p-12 text-center">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 120, damping: 16 }}
          >
            {/* Icon */}
            <div className="mx-auto w-24 h-24 rounded-full bg-yellow-50 dark:bg-yellow-900/20 flex items-center justify-center mb-6">
              <Wrench className="w-12 h-12 text-yellow-500 dark:text-yellow-300" />
            </div>

            <h1 className="text-2xl sm:text-3xl font-semibold text-gray-900 dark:text-gray-100">
              Website hiện đang bảo trì để áp dụng cấu trúc tỉnh thành mới
            </h1>

            <p className="mt-4 text-sm sm:text-base text-gray-600 dark:text-gray-300">
              Vui lòng quay lại sau ngày 31-05{" "}
              {/* <strong className="text-gray-900 dark:text-gray-100">
                {showDate}
              </strong> */}
              .
            </p>

            {subtitle ? (
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                {subtitle}
              </p>
            ) : null}
          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

/*
Usage examples:

// 1) Embedded between your existing Header and Footer (recommended):
// <div className="min-h-screen flex flex-col">
//   <Header />
//   <MaintenancePage date={new Date('2026-01-10T15:00:00')} />
//   <Footer />
// </div>

// 2) Full viewport standalone (use fullScreen prop):
// <MaintenancePage fullScreen date="2026-01-10T15:00:00" />
*/
