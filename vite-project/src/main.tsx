// File: src/main.tsx (or index.tsx depending on your setup)
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import TrangChu from "./pages/TrangChu/TrangChu";
import BieuDoGiaBanPage from "./pages/BieuDoGiaBanPage";
import AboutPage from "./pages/VeChungToi/AboutPage";

import FAQPage from "./pages/FaqPage/FAQPage";
import BieuDoGiaThuePage from "./pages/BieuDoGiaThuePage";
// import ValuationPage from "./pages/ValuationPage/ValuationPage";
import "./index.css";

const rootElement = document.getElementById("root");

if (rootElement) {
  ReactDOM.createRoot(rootElement as HTMLElement).render(
    <React.StrictMode>
      <HelmetProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<TrangChu />} />
            <Route path="/bieu-do-gia-ban" element={<BieuDoGiaBanPage />} />
            <Route
              path="/bieu-do-gia-cho-thue"
              element={<BieuDoGiaThuePage />}
            />
            {/* <Route path="/ve-chung-toi" element={<AboutPage />} /> */}

            <Route path="/cau-hoi-thuong-gap" element={<FAQPage />} />
            {/* <Route path="/dinh-gia-bat-dong-san" element={<ValuationPage />} /> */}
          </Routes>
        </BrowserRouter>
      </HelmetProvider>
    </React.StrictMode>,
  );
}
