import React, { useEffect, useRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";

const Header: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const [isScrolled, setIsScrolled] = useState<boolean>(false);

  const menuRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setMobileOpen(false);
    }
    function onDown(e: MouseEvent) {
      if (!mobileOpen) return;
      const target = e.target as Node | null;
      if (
        target &&
        menuRef.current &&
        !menuRef.current.contains(target) &&
        buttonRef.current &&
        !buttonRef.current.contains(target)
      ) {
        setMobileOpen(false);
      }
    }
    function onResize() {
      if (window.innerWidth >= 768) setMobileOpen(false);
    }
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onDown);
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("resize", onResize);
    };
  }, [mobileOpen]);

  useEffect(() => {
    const onScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const toggleMobile = () => setMobileOpen((s) => !s);

  const logoWidth = 144;
  const logoHeight = 80;
  const scale = isScrolled ? 0.8 : 1;

  // helper class string used for all nav items to keep consistency (desktop uses underline pseudo)
  const underlineBase = `relative font-bold transition
    after:content-[''] after:block after:absolute after:left-0 after:bottom-0
    after:h-[2px] after:bg-sky-500 after:transition-all after:duration-200
    hover:after:w-full`;

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white shadow-sm">
      <div
        className={`max-w-9xl border-b border-gray-200 mx-auto px-6 flex items-center justify-between gap-4 transition-all duration-300 ${
          isScrolled ? "py-2" : "py-4"
        }`}
        style={{
          transition: "padding 200ms ease",
          willChange: "padding",
        }}
      >
        <div className="flex items-center gap-4 min-w-0">
          <Link to="/" className="flex items-center gap-3 group">
            <div
              className="rounded-lg shadow-md overflow-hidden flex-shrink-0"
              style={{
                width: logoWidth * scale,
                height: logoHeight * scale,
                transition:
                  "width 200ms ease, height 200ms ease, transform 200ms ease",
                transformOrigin: "left center",
              }}
            >
              <img
                className="w-full h-full object-contain"
                src="/Logo v6.png"
                alt="Logo"
                style={{
                  transform: `scale(${scale})`,
                  transformOrigin: "center",
                  display: "block",
                  width: "100%",
                  height: "100%",
                }}
              />
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {/* Desktop nav using NavLink (keeps underline behaviour) */}
          <nav className="hidden md:flex items-center gap-6 text-lg text-slate-600">
            <NavLink
              to="/"
              end
              className={({ isActive }: { isActive: boolean }) =>
                `${underlineBase} ${
                  isActive
                    ? "after:w-full text-slate-900"
                    : "after:w-0 text-slate-600"
                }`
              }
            >
              Trang chủ
            </NavLink>

            <NavLink
              to="/bieu-do-gia-ban"
              className={({ isActive }: { isActive: boolean }) =>
                `${underlineBase} ${
                  isActive
                    ? "after:w-full text-slate-900"
                    : "after:w-0 text-slate-600"
                }`
              }
            >
              Biểu đồ giá bán
            </NavLink>

            <NavLink
              to="/bieu-do-gia-cho-thue"
              className={({ isActive }: { isActive: boolean }) =>
                `${underlineBase} ${
                  isActive
                    ? "after:w-full text-slate-900"
                    : "after:w-0 text-slate-600"
                }`
              }
            >
              Biểu đồ giá cho thuê
            </NavLink>

            {/* <NavLink
              to="/dinh-gia-bat-dong-san"
              className={({ isActive }: { isActive: boolean }) =>
                `${underlineBase} ${
                  isActive
                    ? "after:w-full text-slate-900"
                    : "after:w-0 text-slate-600"
                }`
              }
            >
              Định giá
            </NavLink> */}

            <NavLink
              to="/cau-hoi-thuong-gap"
              className={({ isActive }: { isActive: boolean }) =>
                `${underlineBase} ${
                  isActive
                    ? "after:w-full text-slate-900"
                    : "after:w-0 text-slate-600"
                }`
              }
            >
              Câu hỏi thường gặp
            </NavLink>

            <a
              href="https://forms.gle/vWhcTxX256qP3jdU9"
              target="_blank"
              rel="noopener noreferrer"
              className={`${underlineBase} after:w-0 text-slate-600 hover:text-slate-900 hover:after:w-full`}
            >
              Hòm thư góp ý
            </a>
          </nav>

          <div className="h-8 w-px bg-gray-200 hidden md:block" />

          <div className="hidden! md:flex items-center gap-2 px-3 py-1.5 rounded-md border border-gray-200 hover:shadow-sm transition">
            <img
              src="/src/assets/profile-user-account-svgrepo-com.svg"
              alt="User profile"
              className="w-6 h-6 hover:cursor-pointer"
            />
            <a
              href="#"
              className="hidden md:inline-flex items-center px-4 py-1.5 rounded-md bg-cyan-500 text-white text-sm font-medium hover:bg-cyan-600 hover:scale-[1.02] transform transition shadow-md"
            >
              Đăng nhập
            </a>

            <a
              href="#"
              className="hidden md:inline-flex items-center px-4 py-1.5 rounded-md bg-cyan-500 text-white text-sm font-medium hover:bg-cyan-600 hover:scale-[1.02] transform transition shadow-md"
            >
              Đăng ký
            </a>
          </div>

          <button
            ref={buttonRef}
            onClick={toggleMobile}
            aria-expanded={mobileOpen}
            aria-controls="mobile-menu"
            className="md:hidden p-2 rounded-md hover:bg-gray-100 transition"
          >
            <svg
              className="w-6 h-6 text-slate-700"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="https://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div
          id="mobile-menu"
          ref={menuRef}
          className="md:hidden animate-fadeIn absolute left-0 right-0 top-full bg-white border-b border-gray-200 shadow-md z-40"
        >
          <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col gap-3">
            {/* Mobile: use italic for active item instead of underline */}
            <NavLink
              to="/"
              end
              onClick={() => setMobileOpen(false)}
              className={({ isActive }: { isActive: boolean }) =>
                `block w-full text-left font-semibold py-2 px-2 rounded hover:bg-gray-50 ${
                  isActive
                    ? "italic text-slate-900"
                    : "not-italic text-slate-700"
                }`
              }
            >
              Trang chủ
            </NavLink>

            <NavLink
              to="/bieu-do-gia-ban"
              onClick={() => setMobileOpen(false)}
              className={({ isActive }: { isActive: boolean }) =>
                `block w-full text-left font-semibold py-2 px-2 rounded hover:bg-gray-50 ${
                  isActive
                    ? "italic text-slate-900"
                    : "not-italic text-slate-700"
                }`
              }
            >
              Biểu đồ giá bán
            </NavLink>

            <NavLink
              to="/bieu-do-gia-cho-thue"
              onClick={() => setMobileOpen(false)}
              className={({ isActive }: { isActive: boolean }) =>
                `block w-full text-left font-semibold py-2 px-2 rounded hover:bg-gray-50 ${
                  isActive
                    ? "italic text-slate-900"
                    : "not-italic text-slate-700"
                }`
              }
            >
              Biểu đồ giá cho thuê
            </NavLink>

            <NavLink
              to="/cau-hoi-thuong-gap"
              onClick={() => setMobileOpen(false)}
              className={({ isActive }: { isActive: boolean }) =>
                `block w-full text-left font-semibold py-2 px-2 rounded hover:bg-gray-50 ${
                  isActive
                    ? "italic text-slate-900"
                    : "not-italic text-slate-700"
                }`
              }
            >
              Câu hỏi thường gặp
            </NavLink>

            <a
              href="https://forms.gle/vWhcTxX256qP3jdU9"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMobileOpen(false)}
              className="block w-full text-left font-semibold py-2 px-2 rounded hover:bg-gray-50 text-slate-700 hover:text-slate-900"
            >
              Hòm thư góp ý
            </a>

            <div className="border-t border-gray-100 pt-3 flex flex-col gap-2">
              <button
                onClick={() => setMobileOpen(false)}
                className="hidden! w-full inline-flex items-center justify-center py-2 px-2 rounded-md bg-cyan-500 text-white font-medium hover:bg-cyan-600"
              >
                Đăng nhập
              </button>

              <a
                href="#"
                onClick={() => setMobileOpen(false)}
                className="hidden! w-full inline-flex items-center justify-center py-2 px-2 rounded-md bg-cyan-500 text-white font-medium hover:bg-cyan-600"
              >
                Đăng ký
              </a>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(-6px) } to { opacity: 1; transform: translateY(0) } } .animate-fadeIn { animation: fadeIn 180ms ease-out both }`}</style>
    </header>
  );
};

export default Header;
