import React from "react";
import { Funnel } from "lucide-react";
import { motion } from "framer-motion";

interface FilterHeaderFunnelProps {
  title?: string;
  activeCount?: number;
  onClick?: () => void;
}

export default function FilterHeaderFunnel({
  title = "Bộ lọc",
  activeCount = 0,
  onClick,
}: FilterHeaderFunnelProps) {
  return (
    <div className="flex items-center gap-4 mb-4">
      {/* Icon button */}
      <motion.button
        onClick={onClick}
        aria-label="Open filters"
        // title="Mở bộ lọc"
        whileTap={{ scale: 0.96 }}
        whileHover={{ translateY: -2 }}
        className="relative flex items-center justify-center p-2 rounded-2xl bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
      >
        <span className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-600">
          <Funnel className="w-5 h-5 text-white" strokeWidth={1.8} />
        </span>

        {activeCount > 0 && (
          <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-0.5 text-xs font-semibold leading-none text-white rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 shadow">
            {activeCount}
          </span>
        )}
      </motion.button>

      {/* Title + subtitle */}
      <div className="flex flex-col">
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
      </div>

      {/* Spacer to push any other header controls to the right (optional) */}
      <div className="flex-1" />
    </div>
  );
}
