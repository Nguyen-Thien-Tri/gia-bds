import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "../../components/Header";
import Footer from "../../components/Footer";
import { Helmet } from "react-helmet-async";

// FAQPage.tsx
// React + TypeScript single-file component using Tailwind CSS + Framer Motion.
// Drop this into your React project (e.g. pages/FAQPage.tsx or components/FAQPage.tsx)
// Requirements: tailwindcss, framer-motion (optional but recommended for smooth animations)

type FAQ = {
  id: string;
  question: string;
  answer: string;
  category: string;
  updatedAt?: string; // ISO date string
};

const SAMPLE_FAQS: FAQ[] = [
  {
    id: "faq-1",
    question: "Số liệu trên website được thống kê như thế nào?",
    answer:
      `Chúng tôi thống kê dựa trên các tin đăng bán/cho thuê từ các nền tảng đăng tin bất động sản uy tín như batdongsan.com, nhatot,... . ` +
      `Các tin đăng được kiểm tra và xử lý qua nhiều bước, bao gồm việc loại bỏ trùng lặp, loại bỏ các tin đăng với giá ảo, đồng thời điều chỉnh những tin bị sai lỗi nhập liệu, v.v, nhằm đưa ra kết quả thống kê khách quan và chính xác nhất cho người xem.`,
    category: "Số liệu",
    updatedAt: "2025-10-01",
  },
  // {
  //   id: "faq-2",
  //   question: "Làm sao để thay đổi mật khẩu?",
  //   answer:
  //     `Vào trang Hồ sơ → Bảo mật → Thay đổi mật khẩu. Bạn sẽ cần mật khẩu hiện tại để xác thực. ` +
  //     `Nếu quên mật khẩu, hãy dùng chức năng "Quên mật khẩu" để đặt lại.`,
  //   category: "Tài khoản",
  //   updatedAt: "2025-09-10",
  // },
  {
    id: "faq-3",
    question: "Số liệu trên website được cập nhật bao lâu một lần?",
    answer: `Số liệu trên website được cập nhật sau ngày 15 của tháng, với tần suất mỗi tuần 1 lần và 1 lần vào cuối tháng.`,
    category: "Số liệu",
    updatedAt: "2025-10-28",
  },
  // {
  //   id: "faq-4",
  //   question: "Làm thế nào để tải xuống báo cáo?",
  //   answer: `Trên bất kỳ trang báo cáo nào, nhấp nút "Xuất" và chọn "CSV". File CSV sẽ được tải xuống tự động.`,
  //   category: "Số liệu",
  //   updatedAt: "2025-08-05",
  // },
  {
    id: "faq-5",
    question: "Tôi có thể liên hệ hoặc gửi góp ý/feedback tới website qua đâu?",
    answer: `Bạn có thể gửi góp ý/feedback thông qua mục hòm thư góp ý của trang web.`,
    category: "Liên hệ",
    updatedAt: "2025-07-16",
  },
  // {
  //   id: "faq-6",
  //   question: "Giá bất động sản trên website được thống kê như thế nào?",
  //   answer: `Giá bất động sản trên website được thống kê từ các tin đăng bán/cho thuê trên Internet và những nguồn có uy tín.`,
  //   category: "Số liệu",
  //   updatedAt: "2025-10-28",
  // },
  // {
  //   id: "faq-7",
  //   question: "",
  //   answer: ``,
  //   category: "Số liệu",
  //   updatedAt: "2025-10-28",
  // },
];

function formatDate(iso?: string) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString();
  } catch {
    return iso;
  }
}

export default function FAQPage({ faqs = SAMPLE_FAQS }: { faqs?: FAQ[] }) {
  const [query, setQuery] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("Tất cả");
  const searchRef = useRef<HTMLInputElement | null>(null);

  // Build categories with counts
  const categories = useMemo(() => {
    const map = new Map<string, number>();
    faqs.forEach((f) => map.set(f.category, (map.get(f.category) || 0) + 1));
    const arr = ["Tất cả", ...Array.from(map.keys())];
    return { map, arr } as const;
  }, [faqs]);

  // Filtered list
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return faqs.filter((f) => {
      if (selectedCategory !== "Tất cả" && f.category !== selectedCategory)
        return false;
      if (!q) return true;
      return (
        f.question.toLowerCase().includes(q) ||
        f.answer.toLowerCase().includes(q) ||
        f.category.toLowerCase().includes(q)
      );
    });
  }, [faqs, query, selectedCategory]);

  useEffect(() => {
    // If URL has hash to a question id, open it
    if (typeof window !== "undefined") {
      const hash = window.location.hash.replace("#", "");
      if (hash) setActiveId(hash);
    }
  }, []);

  useEffect(() => {
    // When active changes, update hash without scrolling if possible
    if (typeof window !== "undefined") {
      if (activeId) {
        history.replaceState(null, "", `#${activeId}`);
      } else {
        history.replaceState(
          null,
          "",
          window.location.pathname + window.location.search,
        );
      }
    }
  }, [activeId]);

  function toggle(id: string) {
    setActiveId((cur) => (cur === id ? null : id));
  }

  async function copyLink(id: string) {
    const url =
      typeof window !== "undefined"
        ? `${window.location.origin}${window.location.pathname}#${id}`
        : `#${id}`;
    try {
      await navigator.clipboard.writeText(url);
      toast("Đã sao chép liên kết");
    } catch {
      // Fallback
      const tmp = document.createElement("input");
      document.body.appendChild(tmp);
      tmp.value = url;
      tmp.select();
      document.execCommand("copy");
      document.body.removeChild(tmp);
      toast("Đã sao chép liên kết");
    }
  }

  function toast(msg: string) {
    // Minimal toast: you can replace with your notification system
    const el = document.createElement("div");
    el.textContent = msg;
    el.className =
      "fixed bottom-6 right-6 bg-black/80 text-white px-4 py-2 rounded-lg text-sm shadow-lg z-50";
    document.body.appendChild(el);
    setTimeout(() => el.classList.add("opacity-0"), 1600);
    setTimeout(() => el.remove(), 2200);
  }

  // Build JSON-LD FAQ schema for SEO
  const jsonLd = useMemo(() => {
    const mainEntity = filtered.slice(0, 10).map((f) => ({
      "@type": "Question",
      name: f.question,
      acceptedAnswer: { "@type": "Answer", text: f.answer },
    }));
    return {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity,
    };
  }, [filtered]);

  const latestUpdated = useMemo(() => {
    if (!faqs || faqs.length === 0) return "";
    const latest = faqs.reduce((latestSoFar, f) => {
      if (!latestSoFar.updatedAt) return f;
      if (!f.updatedAt) return latestSoFar;
      return latestSoFar.updatedAt > f.updatedAt ? latestSoFar : f;
    }, faqs[0]);
    return latest.updatedAt || "";
  }, [faqs]);

  return (
    <>
      <Helmet>
        <title>Câu hỏi thường gặp (FAQ) | giabatdongsan.info.vn</title>
        <meta
          name="description"
          content="Giải đáp các thắc mắc về dữ liệu, cách cập nhật và cách liên hệ với giabatdongsan.info.vn."
        />
        <link
          rel="canonical"
          href="https://giabatdongsan.info.vn/cau-hoi-thuong-gap"
        />
      </Helmet>
      <Header />
      <div className="min-h-screen bg-gray-50 mt-40 py-12 px-4 sm:px-6 lg:px-8">
        {/* JSON-LD for SEO */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />

        <div className="max-w-5xl mx-auto">
          <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold text-gray-900">
                Câu hỏi thường gặp (FAQ)
              </h1>
              <p className="mt-1 text-gray-600">
                Tìm câu trả lời nhanh cho các thắc mắc thường gặp về website.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative w-72">
                <input
                  ref={searchRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Tìm kiếm câu hỏi"
                  className="w-full rounded-full border border-gray-200 px-4 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  aria-label="Tìm kiếm trong FAQ"
                />
                {query && (
                  <button
                    onClick={() => setQuery("")}
                    className="absolute right-2 top-1/2 -translate-y-1/2 bg-gray-100 hover:bg-gray-200 p-1 rounded-full text-sm"
                    aria-label="Xóa tìm kiếm"
                  >
                    ✕
                  </button>
                )}
              </div>
              <button
                onClick={() => searchRef.current?.focus()}
                className="hidden sm:inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-white text-sm font-medium shadow hover:bg-indigo-700 hover:cursor-pointer"
              >
                Tìm kiếm
              </button>
            </div>
          </header>

          <main className="mt-8 grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Left: categories */}
            <aside className="lg:col-span-1">
              <div className="sticky top-6 space-y-4">
                <div className="rounded-xl bg-white p-4 shadow-sm">
                  <h3 className="text-sm font-semibold text-gray-700">
                    Chuyên mục
                  </h3>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {categories.arr.map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat)}
                        className={`text-sm px-3 py-1 rounded-full border ${
                          selectedCategory === cat
                            ? "bg-indigo-600 text-white border-indigo-600"
                            : "bg-white text-gray-700 border-gray-200"
                        } hover:cursor-pointer`}
                        aria-pressed={selectedCategory === cat}
                      >
                        {cat}
                        {cat !== "Tất cả" && (
                          <span className="ml-2 text-xs text-gray-400">
                            ({categories.map.get(cat) || 0})
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* <div className="rounded-xl bg-white p-4 shadow-sm">
                  <h4 className="text-sm font-medium text-gray-700">
                    Tùy chọn
                  </h4>
                  <div className="mt-3 flex flex-col gap-2">
                    <button
                      onClick={() => {
                        setQuery("");
                        setSelectedCategory("Tất cả");
                      }}
                      className="w-full text-left text-sm px-3 py-2 rounded-md border border-gray-200 hover:bg-gray-50"
                    >
                      Hiển thị tất cả
                    </button>
                    <a
                      href="#contact"
                      className="w-full text-left text-sm px-3 py-2 rounded-md border border-gray-200 hover:bg-gray-50"
                    >
                      Báo lỗi / Góp ý
                    </a>
                  </div>
                </div> */}

                {/* <div className="rounded-xl bg-white p-4 shadow-sm text-sm text-gray-600">
                  <div className="font-medium text-gray-700">Mẹo tìm kiếm</div>
                  <ul className="mt-2 list-disc list-inside space-y-1">
                    <li>Dùng từ khóa cụ thể (ví dụ: "đăng ký", "CSV").</li>
                    <li>Thử chọn chuyên mục để thu hẹp kết quả tìm kiếm.</li>
                  </ul>
                </div> */}
              </div>
            </aside>

            {/* Right: FAQ list */}
            <section className="lg:col-span-3">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    Hiển thị{" "}
                    <span className="font-medium text-gray-900">
                      {filtered.length}
                    </span>{" "}
                    kết quả
                  </div>
                  <div className="text-sm text-gray-500">
                    Cập nhật: {formatDate(latestUpdated) || "—"}
                  </div>
                </div>

                {filtered.length === 0 ? (
                  <div className="rounded-xl bg-white p-8 shadow-sm text-center">
                    <h3 className="text-lg font-semibold text-gray-800">
                      Không tìm thấy kết quả
                    </h3>
                    <p className="mt-2 text-gray-600">
                      Hãy thử các từ khóa khác hoặc bỏ chọn chuyên mục.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filtered.map((f) => (
                      <article
                        key={f.id}
                        id={f.id}
                        className="rounded-xl bg-white p-4 shadow-sm cursor-pointer"
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-1">
                            <button
                              aria-expanded={activeId === f.id}
                              aria-controls={`panel-${f.id}`}
                              onClick={() => toggle(f.id)}
                              className="w-full text-left flex items-center gap-3 cursor-pointer"
                            >
                              <span className="flex-none inline-flex w-9 h-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 font-semibold">
                                Q
                              </span>
                              <div className="flex-1">
                                <div className="flex items-center justify-between">
                                  <h3 className="text-md font-medium text-gray-900">
                                    {f.question}
                                  </h3>
                                  <div className="ml-4 flex items-center gap-2 text-sm text-gray-400">
                                    <span className="hidden sm:inline">
                                      {formatDate(f.updatedAt)}
                                    </span>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        copyLink(f.id);
                                      }}
                                      className="px-2 py-1 rounded hover:bg-gray-100"
                                      aria-label="Sao chép liên kết tới câu hỏi"
                                    >
                                      🔗
                                    </button>
                                  </div>
                                </div>
                                <div className="mt-1 text-sm text-gray-600 hidden sm:block">
                                  Chuyên mục:{" "}
                                  <span className="font-medium text-gray-700">
                                    {f.category}
                                  </span>
                                </div>
                              </div>
                            </button>

                            <AnimatePresence initial={false}>
                              {activeId === f.id && (
                                <motion.section
                                  id={`panel-${f.id}`}
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: "auto" }}
                                  exit={{ opacity: 0, height: 0 }}
                                  transition={{ duration: 0.22 }}
                                  className="mt-4 overflow-hidden text-gray-700"
                                >
                                  <div className="prose max-w-none">
                                    {/* The answer may contain HTML — sanitize if coming from external source */}
                                    <div>{f.answer}</div>
                                  </div>
                                </motion.section>
                              )}
                            </AnimatePresence>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                )}

                {/* <div className="mt-6 text-sm text-gray-500">
                  Vẫn cần hỗ trợ? Liên hệ với chúng tôi: giabatdongsan@gmail.com
                  <a
                    href="#contact"
                    className="text-indigo-600 hover:underline"
                  >
                    Liên hệ với chúng tôi
                  </a>
                </div> */}
              </div>
            </section>
          </main>
        </div>
      </div>

      <Footer />
    </>
  );
}
