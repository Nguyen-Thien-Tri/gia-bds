// import React from "react";
// import { Home, DollarSign, Users } from "lucide-react";
// import { motion } from "framer-motion";
import { NavLink } from "react-router-dom";
// Standalone TargetUsersSection component
// - Self-contained UserCard component
// - Accepts optional `users` prop to override default list
// - Export default for easy import into larger pages/components

const TargetUsersSection = ({ stats = null }) => {
  const statsList = stats || [
    // { label: "Lượt truy cập", value: "500K+" },
    { label: "Tỉnh thành", value: "60+" },
    // { label: "Đánh giá", value: "4.9" },
  ];

  return (
    <section className="relative py-8 md:py-12 bg-gradient-to-br from-slate-900 to-indigo-900 text-white">
      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        <div className="text-center mb-12">
          <h3 className="text-3xl md:text-4xl font-bold mb-2">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              Website{" "}
            </span>
            dành cho những ai?
          </h3>

          <p className="text-slate-300 max-w-3xl mx-auto">
            Từ người mua/thuê nhà lần đầu cho đến những chuyên gia tài chính và
            nhà đầu tư chuyên nghiệp.
          </p>
        </div>

        <div className="mt-12 bg-white/4 backdrop-blur-md border border-white/6 rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-center gap-6">
          <div className="flex-1 flex flex-col items-center md:items-start text-center md:text-left">
            <h4 className="text-xl font-semibold text-white">
              Bắt đầu sử dụng
            </h4>
            <p className="text-slate-200 mt-1">
              Tiết kiệm thời gian tìm kiếm và đưa ra quyết định mua/bán thông
              minh hơn.
            </p>
          </div>

          <div className="flex gap-4 flex-wrap justify-center md:justify-end w-full md:w-auto">
            <NavLink
              to="/bieu-do-gia-ban"
              className="hover:cursor-pointer px-6 py-3 rounded-lg bg-white text-indigo-700 font-semibold hover:scale-105 transition-transform focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              Khám phá
            </NavLink>
          </div>
        </div>

        <div
          className={`grid grid-cols-1 gap-6 mt-8 ${
            statsList.length === 1
              ? "sm:grid-cols-1 max-w-sm mx-auto"
              : statsList.length === 2
                ? "sm:grid-cols-2 max-w-2xl mx-auto"
                : "sm:grid-cols-3"
          } w-full`}
        >
          {statsList.map((s, i) => (
            <div
              key={i}
              className="text-center py-4 px-3 bg-white/4 rounded-lg"
            >
              <div className="text-2xl md:text-3xl font-bold">{s.value}</div>
              <div className="text-sm text-slate-200">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TargetUsersSection;
