import React, { useEffect, useState } from "react";
import { Mail, Send, CheckCircle, XCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Status = "idle" | "loading" | "success" | "error";

const Footer: React.FC = () => {
  // Subscribe to Google Form state
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string>("");

  // Thay bằng URL Google Form của bạn
  const formUrl = "https://forms.gle/cSbA196TLVsd7z4n7";
  const openInNewTab = true;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setStatus("loading");

    try {
      if (openInNewTab) {
        window.open(formUrl, "_blank", "noopener,noreferrer");
      } else {
        window.location.href = formUrl;
      }

      // Nếu mở thành công, hiển thị trạng thái success
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setError("Không thể mở Google Form. Vui lòng thử lại sau.");
    }
  };

  return (
    <>
      <footer className="bg-gradient-to-br from-slate-800 via-slate-900 to-blue-900 text-white relative overflow-hidden">
        <div className="relative z-10 max-w-8xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-12 gap-5">
            {/* Logo and Company Info */}
            <div className="md:col-span-3 space-y-6">
              <div className="space-y-4">
                <h4 className="text-lg font-semibold text-blue-300 mb-3">
                  Thông tin liên hệ
                </h4>
                <div className="space-y-3">
                  <a
                    href="mailto:giabatdongsan@gmail.com"
                    className="flex items-center space-x-3 text-gray-300 hover:text-white hover:bg-white/10 p-2 rounded-lg transition-all duration-300 group"
                  >
                    <div className="p-2 bg-green-600 rounded-full group-hover:bg-green-500 transition-colors duration-300">
                      <Mail className="w-4 h-4" />
                    </div>
                    <span className="group-hover:translate-x-1 transition-transform duration-300">
                      hotro@giabatdongsan.info.vn
                    </span>
                  </a>
                </div>
              </div>
            </div>

            {/* Email Signup Section - now uses Google Form like SubscribeCTA */}
            <div className="md:col-span-6 space-y-4">
              <h4 className="text-lg font-semibold text-blue-300 border-b border-blue-600/30 pb-2">
                Nhận thông tin cập nhật
              </h4>

              <div className="w-full">
                <div
                  className="bg-white/10 backdrop-blur-sm rounded-2xl p-5 shadow-lg border border-white/20"
                  aria-live="polite"
                >
                  {/* Centered the icon + text block by adding justify-center and text-center */}
                  <div className="flex items-center gap-3 mb-4 justify-center">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white shadow-md">
                      <Mail className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0 text-center">
                      <div className="font-semibold text-white text-sm">
                        Đăng ký nhận thông tin về tính năng mới:
                        <br />
                        <span className="text-blue-300">
                          Định giá bất động sản,...
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {/* Form sẽ mở Google Form thay vì thu email trực tuyến */}
                    <form onSubmit={handleSubmit} className="space-y-3">
                      <motion.button
                        type="submit"
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.98 }}
                        className={`mx-auto w-full max-w-xs flex items-center gap-2 justify-center rounded-xl px-4 py-3 font-semibold text-white shadow-md transition-all duration-200 hover:cursor-pointer transform hover:scale-105
                          ${
                            status === "success"
                              ? "bg-green-500 hover:bg-green-600"
                              : "bg-blue-600 hover:bg-blue-700"
                          }`}
                        aria-label="Mở form đăng ký"
                      >
                        {status === "loading" ? (
                          <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                        ) : status === "success" ? (
                          <CheckCircle className="w-4 h-4" />
                        ) : (
                          <Send className="w-4 h-4" />
                        )}

                        <span className="text-sm">
                          {status === "success"
                            ? "Đã mở form đăng ký"
                            : "Đăng ký"}
                        </span>
                      </motion.button>
                    </form>
                  </div>

                  <AnimatePresence>
                    {status === "error" && (
                      <motion.div
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        className="mt-3 flex items-center gap-2 text-red-300 text-sm"
                      >
                        <XCircle className="w-4 h-4" />{" "}
                        <span>{error || "Đã có lỗi"}</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-700">
            <div className="flex flex-col justify-between items-center space-y-4 md:space-y-0">
              <div className="text-center">
                <p className="text-gray-400 text-sm">
                  © 2025 giabatdongsan.info.vn. All rights reserved.
                </p>
                <p className="text-gray-500 text-xs mt-1">
                  Nền tảng phân tích thị trường bất động sản hàng đầu Việt Nam
                </p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
};

export default Footer;
