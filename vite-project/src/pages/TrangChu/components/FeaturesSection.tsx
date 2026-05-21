import React, { useEffect, useRef, useState } from "react";
import { TrendingUp, BarChart3, ChevronRight, Sparkles } from "lucide-react";

type Feature = {
  icon: React.JSX.Element;
  title: string;
  description: string;
  gradient: string;
  badge?: string;
  link?: string;
  onExplore?: () => void;
};

export default function FeaturesSection(): React.JSX.Element {
  const [visible, setVisible] = useState<boolean>(false);
  const sectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let observer: IntersectionObserver | null = null;

    observer = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true);
          }
        });
      },
      { threshold: 0.25 },
    );

    const el = sectionRef.current;
    if (el && observer) observer.observe(el);

    return () => {
      observer?.disconnect();
      observer = null;
    };
  }, []);

  const features: Feature[] = [
    {
      icon: <BarChart3 className="w-10 h-10" />,
      title: "Phân Tích Thị Trường",
      description:
        "Biểu đồ so sánh trực quan giá bất động sản giữa các khu vực (quận/huyện, tỉnh/thành phố), giúp bạn tiết kiệm thời gian tìm kiếm khu vực phù hợp với ngân sách của bản thân.",
      gradient: "from-blue-400 to-indigo-600",
      link: "/bieu-do-gia-ban",
    },
    {
      icon: <TrendingUp className="w-10 h-10" />,
      title: "Lịch Sử Giá",
      description:
        "Truy xuất và xem lại biến động giá trong quá khứ, giúp bạn tìm hiểu xu hướng giá cả và dự đoán xu hướng trong tương lai, hoặc đánh giá rủi ro đầu tư bất động sản.",
      gradient: "from-indigo-400 to-cyan-500",
      link: "/bieu-do-gia-ban",
    },
  ];

  function defaultExplore(feature: Feature) {
    if (feature.link) {
      window.location.href = feature.link;
      return;
    }
    const q = encodeURIComponent(feature.title);
    window.location.href = `/explore?feature=${q}`;
  }

  return (
    <section
      id="features-section"
      ref={sectionRef}
      className="py-10 relative overflow-hidden"
    >
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translate3d(0, 40px, 0);
          }
          to {
            opacity: 1;
            transform: translate3d(0, 0, 0);
          }
        }
        @keyframes blob {
          0% {
            transform: translate(0px, 0px) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.05);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.95);
          }
          100% {
            transform: translate(0px, 0px) scale(1);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .cards-enter {
          opacity: 0;
          transform: translateY(20px);
        }
        .cards-enter.cards-visible {
          animation: fadeInUp 0.8s ease-out forwards;
        }
      `}</style>

      <div className="absolute -top-8 -left-8 w-72 h-72 rounded-full mix-blend-soft-light opacity-10 bg-blue-300 animate-blob"></div>
      <div
        className="absolute top-16 right-10 w-56 h-56 rounded-full mix-blend-soft-light opacity-10 bg-purple-300 animate-blob"
        style={{ animationDelay: "1.2s" }}
      ></div>

      <div className="container mx-auto px-6 max-w-7xl relative z-10">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-2xl font-medium mb-6 border border-blue-100">
            <Sparkles className="w-8 h-8" />
            Tính năng nổi bật
          </div>
        </div>

        <div
          className={`grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch cards-enter ${
            visible ? "cards-visible" : ""
          }`}
        >
          {features.map((f: Feature, i: number) => (
            <article
              key={i}
              className={`group relative p-8 rounded-3xl bg-white/80 backdrop-blur-sm border border-gray-300/100 shadow-lg hover:bg-white/95 transition-all duration-500 hover:scale-105 hover:-translate-y-4 hover:shadow-2xl overflow-hidden h-full flex flex-col`}
              style={{
                animationDelay: `${i * 120}ms`,
                animation: visible
                  ? `fadeInUp 0.7s ease-out forwards`
                  : undefined,
              }}
            >
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-500 p-px pointer-events-none">
                <div
                  className={`h-full w-full rounded-3xl bg-gradient-to-r ${f.gradient} opacity-50`}
                ></div>
              </div>

              <div className="relative z-10 flex flex-col h-full">
                <div className="flex-1">
                  <div
                    className={`inline-flex p-4 rounded-2xl bg-gradient-to-r ${f.gradient} text-white mb-6 group-hover:scale-110 transition-transform duration-300 shadow-2xl ring-1 ring-white/10`}
                  >
                    {f.icon}
                  </div>

                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold text-gray-800">
                      {f.title}
                    </h3>
                    {f.badge && (
                      <div className="text-xs font-medium px-3 py-1 rounded-full bg-white/90 text-gray-800 border border-white/30">
                        {f.badge}
                      </div>
                    )}
                  </div>

                  <p className="text-gray-700 mb-6 text-justify">
                    {f.description}
                  </p>
                </div>

                <div className="flex items-center gap-3 mt-4">
                  <button
                    type="button"
                    aria-label={`Khám phá ${f.title}`}
                    onClick={() =>
                      f.onExplore ? f.onExplore() : defaultExplore(f)
                    }
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-full font-medium text-sm border border-transparent bg-gradient-to-r ${f.gradient} text-white shadow-md hover:shadow-lg transition transform hover:-translate-y-0.5 hover:cursor-pointer`}
                  >
                    Khám phá
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity duration-500 pointer-events-none">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(0,0,0,0.03),rgba(255,255,255,0))]"></div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
