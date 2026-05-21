import React from "react";

// Assumes you already have Header and Footer components in your project
import Header from "../../components/Header";
import Footer from "../../components/Footer";

type TeamMember = {
  id: number;
  name: string;
  role: string;
  bio: string;
  email?: string;
};

const TEAM: TeamMember[] = [
  {
    id: 1,
    name: "Nguyễn Thiện Trí",
    role: "Founder & Data Scientist",
    bio: "Chuyên về phân tích dữ liệu bất động sản, xây dựng pipeline và mô hình dự đoán giá.",
    email: "tri@example.com",
  },
  {
    id: 2,
    name: "Lê Minh Anh",
    role: "Frontend Lead",
    bio: "Thiết kế UI/UX, tạo trải nghiệm tương tác cho biểu đồ và bản đồ.",
    email: "minhanh@example.com",
  },
  {
    id: 3,
    name: "Trần Thanh Hùng",
    role: "Backend & DevOps",
    bio: "Đảm bảo pipeline cập nhật dữ liệu, deploy và vận hành trên GCP.",
    email: "thung@example.com",
  },
];

const StatCard: React.FC<{ value: string; label: string }> = ({
  value,
  label,
}) => (
  <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-md flex flex-col items-start">
    <div className="text-2xl md:text-3xl font-semibold">{value}</div>
    <div className="text-sm text-slate-600 mt-1">{label}</div>
  </div>
);

const Avatar: React.FC<{ name: string; size?: number }> = ({
  name,
  size = 56,
}) => {
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("");
  const bgIdx =
    Math.abs(name.split("").reduce((acc, c) => acc + c.charCodeAt(0), 0)) % 6;
  const bgColors = [
    "bg-rose-400",
    "bg-amber-400",
    "bg-green-400",
    "bg-sky-400",
    "bg-violet-400",
    "bg-pink-400",
  ];
  return (
    <div
      className={`flex items-center justify-center rounded-full text-white font-semibold ${bgColors[bgIdx]}`}
      style={{ width: size, height: size }}
      aria-hidden
    >
      {initials}
    </div>
  );
};

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <Header />

      <main className="container mx-auto px-6 md:px-10 py-12 flex-1">
        {/* Hero */}
        <section className="rounded-3xl overflow-hidden bg-gradient-to-r from-indigo-600 to-cyan-500 text-white p-8 shadow-xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
            <div>
              <h1 className="text-3xl md:text-4xl font-extrabold leading-tight">
                Về chúng tôi
              </h1>
              <p className="mt-4 text-slate-100/90 max-w-xl">
                Chúng tôi xây dựng nền tảng giúp người dùng hiểu sâu về xu hướng
                giá bất động sản thông qua dữ liệu và trực quan hóa. Mục tiêu:
                giúp bạn đưa ra quyết định đầu tư &amp; lựa chọn khu vực dựa
                trên số liệu, không chỉ cảm giác.
              </p>

              <div className="mt-6 flex gap-3 flex-wrap">
                <a
                  href="#contact"
                  className="inline-flex items-center gap-2 bg-white/20 hover:bg-white/30 transition rounded-lg py-2 px-4 text-sm font-medium"
                >
                  Liên hệ chúng tôi
                </a>
                <a
                  href="#team"
                  className="inline-flex items-center gap-2 bg-white/10 hover:bg-white/20 transition rounded-lg py-2 px-4 text-sm font-medium"
                >
                  Xem đội ngũ
                </a>
              </div>
            </div>

            <div className="flex items-center justify-center">
              {/* Decorative card with quick stats */}
              <div className="grid grid-cols-2 gap-4 w-full max-w-md">
                <StatCard
                  value="10M+"
                  label="Bản ghi giao dịch được phân tích"
                />
                <StatCard value="250+" label="Khu vực được theo dõi" />
                <StatCard
                  value="95%"
                  label="Độ chính xác mô hình (thử nghiệm)"
                />
                <StatCard value="Daily" label="Cập nhật dữ liệu" />
              </div>
            </div>
          </div>
        </section>

        {/* Mission & Values */}
        <section className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="col-span-2 bg-white rounded-2xl p-6 shadow-sm">
            <h2 className="text-xl font-semibold">Sứ mệnh của chúng tôi</h2>
            <p className="mt-3 text-slate-700 leading-relaxed">
              Chúng tôi tin rằng dữ liệu minh bạch và trực quan tốt sẽ trao
              quyền cho người mua, nhà đầu tư và nhà nghiên cứu. Bằng cách kết
              hợp thu thập dữ liệu tự động, xử lý sạch và mô hình phân tích,
              chúng tôi cung cấp góc nhìn đáng tin cậy và có thể hành động được
              trên thị trường bất động sản.
            </p>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium">Minh bạch</h3>
                <p className="text-sm text-slate-600 mt-1">
                  Mọi kết quả đều kèm theo nguồn dữ liệu và phương pháp.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium">Khoa học</h3>
                <p className="text-sm text-slate-600 mt-1">
                  Đưa ra phân tích dựa trên thống kê và mô hình đã kiểm chứng.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium">Thực tiễn</h3>
                <p className="text-sm text-slate-600 mt-1">
                  Giao diện trực quan, dễ thao tác cho mọi loại người dùng.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-medium">Bảo mật</h3>
                <p className="text-sm text-slate-600 mt-1">
                  Tôn trọng và bảo vệ dữ liệu người dùng và nguồn dữ liệu.
                </p>
              </div>
            </div>
          </div>

          <aside className="bg-white rounded-2xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold">Cách chúng tôi vận hành</h3>
            <ol className="mt-4 space-y-3 text-sm text-slate-600">
              <li>
                <strong>Thu thập</strong>: Crawl &amp; ingest dữ liệu quảng cáo,
                giao dịch &amp; báo cáo chính thức.
              </li>
              <li>
                <strong>Tiền xử lý</strong>: Làm sạch, standardize và geocode
                địa chỉ.
              </li>
              <li>
                <strong>Phân tích</strong>: Thống kê, trực quan hóa và áp dụng
                mô hình dự đoán.
              </li>
              <li>
                <strong>Cập nhật</strong>: Hệ thống tự động cập nhật hàng ngày
                và giám sát chất lượng.
              </li>
            </ol>
          </aside>
        </section>

        {/* Team */}
        <section id="team" className="mt-10">
          <h2 className="text-2xl font-semibold">Đội ngũ</h2>
          <p className="mt-2 text-slate-600">
            Những người đứng sau nền tảng — kết hợp giữa phân tích dữ liệu,
            frontend và vận hành hệ thống.
          </p>

          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {TEAM.map((m) => (
              <article
                key={m.id}
                className="bg-white rounded-2xl p-5 shadow hover:shadow-lg transition"
              >
                <div className="flex items-center gap-4">
                  <Avatar name={m.name} size={64} />
                  <div>
                    <h3 className="font-semibold">{m.name}</h3>
                    <div className="text-sm text-slate-500">{m.role}</div>
                  </div>
                </div>

                <p className="mt-3 text-sm text-slate-600">{m.bio}</p>

                <div className="mt-4 flex items-center justify-between">
                  <a
                    href={`mailto:${m.email}`}
                    className="text-sm text-indigo-600 hover:underline"
                  >
                    {m.email}
                  </a>
                  <div className="text-xs text-slate-400">Member</div>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* Timeline / Roadmap */}
        <section className="mt-10">
          <h2 className="text-2xl font-semibold">Hành trình</h2>
          <div className="mt-6 space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-2.5 h-2.5 rounded-full bg-indigo-600 mt-2" />
              <div>
                <div className="text-sm font-semibold">2023 — Khởi động</div>
                <div className="text-sm text-slate-600">
                  Xây dựng bộ thu thập dữ liệu và dashboard đầu tiên.
                </div>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-2.5 h-2.5 rounded-full bg-indigo-600 mt-2" />
              <div>
                <div className="text-sm font-semibold">
                  2024 — Mở rộng vùng phủ
                </div>
                <div className="text-sm text-slate-600">
                  Mở rộng phân tích cho hơn 200 khu vực, tối ưu pipeline.
                </div>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-2.5 h-2.5 rounded-full bg-indigo-600 mt-2" />
              <div>
                <div className="text-sm font-semibold">
                  2025 — Tự động hóa &amp; ML
                </div>
                <div className="text-sm text-slate-600">
                  Ra mắt mô hình dự đoán, cảnh báo giá và APIs cho người dùng.
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section
          id="contact"
          className="mt-12 bg-gradient-to-r from-white to-slate-50 rounded-2xl p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm"
        >
          <div>
            <h3 className="text-lg font-semibold">
              Muốn hợp tác hoặc nhận dữ liệu?
            </h3>
            <p className="text-sm text-slate-600 mt-2">
              Gửi email cho chúng tôi hoặc đăng ký để trao đổi chi tiết hơn về
              nhu cầu của bạn.
            </p>
          </div>

          <div className="flex gap-3">
            <a
              href="mailto:hello@example.com"
              className="inline-flex items-center justify-center rounded-lg border py-2 px-4 text-sm font-medium hover:bg-slate-100"
            >
              hello@example.com
            </a>
            <a
              href="/signup"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 text-white py-2 px-4 text-sm font-medium hover:opacity-95"
            >
              Đăng ký dùng thử
            </a>
          </div>
        </section>

        {/* Footer spacer */}
        <div className="mt-12" />
      </main>

      <Footer />
    </div>
  );
}
