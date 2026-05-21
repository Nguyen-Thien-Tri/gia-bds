import React, { useState, ReactNode } from "react";
import { Mail, Send, CheckCircle, XCircle } from "lucide-react";
// eslint-disable-next-line no-unused-vars
import { motion, AnimatePresence } from "framer-motion";

interface EmailSignupSectionProps {
  children?: ReactNode;
  /** URL của Google Form (mặc định: thay bằng form của bạn) */
  formUrl?: string;
  /** Mở Google Form trong tab mới hay redirect cùng tab */
  openInNewTab?: boolean;
}

type Status = "idle" | "loading" | "success" | "error";

export default function EmailSignupSection({
  children,
  formUrl = "https://forms.gle/cSbA196TLVsd7z4n7",
  openInNewTab = true,
}: EmailSignupSectionProps) {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string>("");

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    setError("");
    setStatus("loading");

    try {
      // Mở Google Form (không prefill email vì đã loại bỏ input)
      if (openInNewTab) {
        window.open(formUrl, "_blank", "noopener,noreferrer");
      } else {
        window.location.href = formUrl;
      }

      setStatus("success");
    } catch (err) {
      setStatus("error");
      setError("Không thể mở Google Form. Vui lòng thử lại sau.");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className="w-full max-w-120 mx-auto "
    >
      <form
        onSubmit={handleSubmit}
        className="bg-white/90 backdrop-blur-sm rounded-2xl p-5 shadow-lg border border-gray-100"
        aria-live="polite"
      >
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center text-white shadow-md">
            <Mail className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-gray-900">
              Đăng ký nhận thông tin về tính năng mới:
              <br />
              Định giá bất động sản,...
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <motion.button
            type="submit"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            className={`flex items-center gap-2 justify-center rounded-xl px-4 py-3 font-semibold text-white shadow-md transition-all duration-200 hover:cursor-pointer
              w-full min-w-[140px] max-w-full
              ${
                status === "success"
                  ? "bg-green-500 hover:bg-green-600"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            aria-label="Đã mở Google Form"
          >
            {status === "loading" ? (
              <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
            ) : status === "success" ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span className="text-sm">
              {status === "success" ? "Đã mở form đăng ký" : "Đăng ký"}
            </span>
          </motion.button>
        </div>

        <AnimatePresence>
          {status === "error" && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              className="mt-3 flex items-center gap-2 text-red-600 text-sm"
            >
              <XCircle className="w-4 h-4" />{" "}
              <span>{error || "Đã có lỗi"}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {children && <div className="mt-3">{children}</div>}
      </form>
    </motion.div>
  );
}
