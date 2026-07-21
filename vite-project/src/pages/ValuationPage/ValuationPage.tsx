import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  MapPin,
  DollarSign,
  Ruler,
  Search,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Home,
  Compass,
  Layers,
  Bed,
  Bath,
  DoorOpen,
  FileText,
  CornerDownRight,
  Map,
} from "lucide-react";
import Header from "../../components/Header";
import Footer from "../../components/Footer";
import { provinceDict } from "../../assets/geo";

// Types for form data
interface ValuationResult {
  estimatedPrice: number;
  confidence: string;
  priceRange: { min: number; max: number };
}

// Directions for house/balcony
const directions = [
  "Đông",
  "Tây",
  "Nam",
  "Bắc",
  "Đông Bắc",
  "Tây Bắc",
  "Đông Nam",
  "Tây Nam",
];

// Legal status options
const legalStatuses = [
  "Sổ đỏ",
  "Sổ hồng",
  "Sổ chung",
  "Hợp đồng mua bán",
  "Giấy tờ viết tay",
  "Chưa có sổ",
  "Đang chờ sổ",
];

// Interior options
const interiorOptions = [
  "Đầy đủ",
  "Cao cấp",
  "Cơ bản",
  "Hoàn thiện thô",
  "Chưa hoàn thiện",
  "Không nội thất",
];

export default function ValuationPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Rate limiting state
  const [timeLeft, setTimeLeft] = useState(0);

  // Dynamic district list based on selected city
  const [availableDistricts, setAvailableDistricts] = useState<string[]>([]);

  // Form State
  const [formData, setFormData] = useState({
    propertyType: "nhà riêng",
    transactionType: "sale", // sale | rent
    city: "",
    district: "",
    ward: "", // Địa chỉ 1 - Phường/Xã
    area: "",
    price: "", // Optional user input for current price check
    address: "",
    // New fields for ML model
    floors: "",
    bedrooms: "",
    bathrooms: "",
    frontage: "", // Mặt tiền
    alleyWidth: "", // Đường vào
    houseDirection: "",
    balconyDirection: "",
    legalStatus: "",
    interior: "",
    cornerUnit: "Không", // Căn góc
    latitude: "", // Tọa độ x
    longitude: "", // Tọa độ y
    description: "", // Mô tả
  });

  // Mock Data for Dropdowns
  const propertyTypes = [
    { value: "nhà riêng", label: "Nhà riêng" },
    { value: "căn hộ chung cư", label: "Căn hộ chung cư" },
    { value: "đất", label: "Đất nền" },
    { value: "nhà mặt phố", label: "Nhà mặt phố" },
    { value: "biệt thự", label: "Biệt thự" },
    { value: "văn phòng", label: "Văn phòng" },
  ];

  const cities = Object.keys(provinceDict).sort();

  // Update districts when city changes
  useEffect(() => {
    if (formData.city && provinceDict[formData.city]) {
      setAvailableDistricts(provinceDict[formData.city].sort());
    } else {
      setAvailableDistricts([]);
    }
  }, [formData.city]);

  // Check Rate Limit on Mount
  useEffect(() => {
    const checkRateLimit = () => {
      const lastValuationTime = localStorage.getItem("lastValuationTime");
      const valuationCount = parseInt(
        localStorage.getItem("valuationCount") || "0",
      );
      const now = Date.now();

      // Reset count if more than 1 minute has passed
      if (lastValuationTime && now - parseInt(lastValuationTime) > 60000) {
        localStorage.setItem("valuationCount", "0");
        setTimeLeft(0);
      } else if (valuationCount >= 3) {
        // If limit reached, calculate remaining time
        if (lastValuationTime) {
          const remaining = 60000 - (now - parseInt(lastValuationTime));
          if (remaining > 0) {
            setTimeLeft(Math.ceil(remaining / 1000));
          }
        }
      }
    };

    checkRateLimit();
    const interval = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(interval);
  }, [loading]); // Re-check when loading finishes (submission attempt)

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleValuation = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    // Rate Limit Check
    const valuationCount = parseInt(
      localStorage.getItem("valuationCount") || "0",
    );
    const lastValuationTime = localStorage.getItem("lastValuationTime");
    const now = Date.now();

    if (valuationCount >= 3) {
      if (lastValuationTime && now - parseInt(lastValuationTime) < 60000) {
        setTimeLeft(
          60 - Math.floor((now - parseInt(lastValuationTime)) / 1000),
        );
        setError(
          "Bạn đã vượt quá giới hạn định giá (3 lần/phút). Vui lòng thử lại sau.",
        );
        return;
      } else {
        // Reset if time passed
        localStorage.setItem("valuationCount", "0");
      }
    }

    setLoading(true);

    // Simulate API Call
    setTimeout(() => {
      // Mock Algorithm
      const basePrice = formData.transactionType === "sale" ? 50000000 : 200000; // 50tr/m2 or 200k/m2
      const area = parseFloat(formData.area) || 0;
      const estimated = basePrice * area * (Math.random() * 0.2 + 0.9); // +/- variance

      setResult({
        estimatedPrice: Math.round(estimated),
        confidence: "Cao",
        priceRange: {
          min: Math.round(estimated * 0.95),
          max: Math.round(estimated * 1.05),
        },
      });

      // Update Rate Limit
      localStorage.setItem("lastValuationTime", Date.now().toString());
      localStorage.setItem(
        "valuationCount",
        (
          parseInt(localStorage.getItem("valuationCount") || "0") + 1
        ).toString(),
      );

      setLoading(false);
    }, 2000);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(value);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow bg-gray-50/50 pt-24 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header Section */}
          <div className="text-center mb-10">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center justify-center p-3 mb-4 rounded-2xl bg-indigo-100 text-indigo-600"
            >
              <TrendingUp size={32} />
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl mb-3"
            >
              Định Giá Bất Động Sản
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-lg text-gray-500 max-w-2xl mx-auto"
            >
              Sử dụng công nghệ AI để phân tích dữ liệu thị trường và đưa ra
              định giá chính xác nhất cho bất động sản của bạn.
            </motion.p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Input Form */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="lg:col-span-2"
            >
              <div className="bg-white rounded-3xl shadow-xl shadow-indigo-100/50 overflow-hidden border border-gray-100">
                <div className="p-6 sm:p-8">
                  <form onSubmit={handleValuation} className="space-y-6">
                    {/* Transaction Type Toggle */}
                    <div className="flex bg-gray-100 p-1 rounded-xl w-fit mb-6">
                      <button
                        type="button"
                        onClick={() =>
                          setFormData({ ...formData, transactionType: "sale" })
                        }
                        className={`px-6 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                          formData.transactionType === "sale"
                            ? "bg-white text-indigo-600 shadow-sm"
                            : "text-gray-500 hover:text-gray-700"
                        }`}
                      >
                        Bán
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          setFormData({ ...formData, transactionType: "rent" })
                        }
                        className={`px-6 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                          formData.transactionType === "rent"
                            ? "bg-white text-indigo-600 shadow-sm"
                            : "text-gray-500 hover:text-gray-700"
                        }`}
                      >
                        Cho thuê
                      </button>
                    </div>

                    {/* ── Section: Thông tin cơ bản ── */}
                    <div>
                      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Home size={20} className="text-indigo-500" />
                        Thông tin cơ bản
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Property Type */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Building2 size={16} /> Loại bất động sản
                          </label>
                          <select
                            name="propertyType"
                            value={formData.propertyType}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                          >
                            {propertyTypes.map((type) => (
                              <option key={type.value} value={type.value}>
                                {type.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Area */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Ruler size={16} /> Diện tích (m²)
                          </label>
                          <input
                            type="number"
                            name="area"
                            value={formData.area}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 80"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                            required
                          />
                        </div>

                        {/* City */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <MapPin size={16} /> Tỉnh / Thành phố
                          </label>
                          <select
                            name="city"
                            value={formData.city}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                            required
                          >
                            <option value="">Chọn Tỉnh/Thành</option>
                            {cities.map((c) => (
                              <option key={c} value={c}>
                                {c}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* District */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <MapPin size={16} /> Quận / Huyện
                          </label>
                          <select
                            name="district"
                            value={formData.district}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                            required
                          >
                            <option value="">Chọn Quận/Huyện</option>
                            {availableDistricts.map((d) => (
                              <option key={d} value={d}>
                                {d}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Ward (Địa chỉ 1) */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Map size={16} /> Phường / Xã
                          </label>
                          <input
                            type="text"
                            name="ward"
                            value={formData.ward}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: Phường Láng Hạ"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>

                        {/* Detailed Address */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Home size={16} /> Địa chỉ chi tiết
                          </label>
                          <input
                            type="text"
                            name="address"
                            value={formData.address}
                            onChange={handleInputChange}
                            placeholder="Số nhà, tên đường..."
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>
                      </div>
                    </div>

                    {/* ── Section: Thông số kỹ thuật ── */}
                    <div className="border-t border-gray-100 pt-6">
                      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Layers size={20} className="text-indigo-500" />
                        Thông số kỹ thuật
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Floors */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Layers size={16} /> Số tầng
                          </label>
                          <input
                            type="number"
                            name="floors"
                            value={formData.floors}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 4"
                            min="1"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>

                        {/* Bedrooms */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Bed size={16} /> Số phòng ngủ
                          </label>
                          <input
                            type="number"
                            name="bedrooms"
                            value={formData.bedrooms}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 3"
                            min="1"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>

                        {/* Bathrooms */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Bath size={16} /> Số phòng tắm / WC
                          </label>
                          <input
                            type="number"
                            name="bathrooms"
                            value={formData.bathrooms}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 2"
                            min="1"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>

                        {/* Frontage (Mặt tiền) */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <DoorOpen size={16} /> Mặt tiền (m)
                          </label>
                          <input
                            type="number"
                            name="frontage"
                            value={formData.frontage}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 4.5"
                            step="0.1"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>

                        {/* Alley Width (Đường vào) */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <CornerDownRight size={16} /> Đường vào (m)
                          </label>
                          <input
                            type="number"
                            name="alleyWidth"
                            value={formData.alleyWidth}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 3.5"
                            step="0.1"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>

                        {/* Corner Unit (Căn góc) */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Building2 size={16} /> Căn góc
                          </label>
                          <select
                            name="cornerUnit"
                            value={formData.cornerUnit}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                          >
                            <option value="Không">Không</option>
                            <option value="Có">Có</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* ── Section: Hướng & Pháp lý ── */}
                    <div className="border-t border-gray-100 pt-6">
                      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Compass size={20} className="text-indigo-500" />
                        Hướng & Pháp lý
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* House Direction */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Compass size={16} /> Hướng nhà
                          </label>
                          <select
                            name="houseDirection"
                            value={formData.houseDirection}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                          >
                            <option value="">Chọn hướng</option>
                            {directions.map((d) => (
                              <option key={d} value={d}>
                                {d}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Balcony Direction */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Compass size={16} /> Hướng ban công
                          </label>
                          <select
                            name="balconyDirection"
                            value={formData.balconyDirection}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                          >
                            <option value="">Chọn hướng</option>
                            {directions.map((d) => (
                              <option key={d} value={d}>
                                {d}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Legal Status */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <FileText size={16} /> Pháp lý
                          </label>
                          <select
                            name="legalStatus"
                            value={formData.legalStatus}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                          >
                            <option value="">Chọn pháp lý</option>
                            {legalStatuses.map((s) => (
                              <option key={s} value={s}>
                                {s}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Interior */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <Home size={16} /> Nội thất
                          </label>
                          <select
                            name="interior"
                            value={formData.interior}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                          >
                            <option value="">Chọn nội thất</option>
                            {interiorOptions.map((opt) => (
                              <option key={opt} value={opt}>
                                {opt}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* ── Section: Tọa độ (nâng cao) ── */}
                    <div className="border-t border-gray-100 pt-6">
                      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Map size={20} className="text-indigo-500" />
                        Tọa độ{" "}
                        <span className="text-gray-400 font-normal text-sm">
                          (Nâng cao - hỗ trợ AI định giá chính xác hơn)
                        </span>
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Latitude */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <MapPin size={16} /> Vĩ độ (Latitude)
                          </label>
                          <input
                            type="number"
                            name="latitude"
                            value={formData.latitude}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 21.015"
                            step="0.0001"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>

                        {/* Longitude */}
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <MapPin size={16} /> Kinh độ (Longitude)
                          </label>
                          <input
                            type="number"
                            name="longitude"
                            value={formData.longitude}
                            onChange={handleInputChange}
                            placeholder="Ví dụ: 105.815"
                            step="0.0001"
                            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                          />
                        </div>
                      </div>
                    </div>

                    {/* ── Section: Mô tả ── */}
                    <div className="border-t border-gray-100 pt-6">
                      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <FileText size={20} className="text-indigo-500" />
                        Mô tả chi tiết{" "}
                        <span className="text-gray-400 font-normal text-sm">
                          (AI sẽ phân tích mô tả để định giá chính xác hơn)
                        </span>
                      </h3>
                      <div className="space-y-2">
                        <textarea
                          name="description"
                          value={formData.description}
                          onChange={handleInputChange}
                          placeholder="Mô tả chi tiết về bất động sản (ví dụ: Nhà đẹp phố Láng Hạ, ô tô vào nhà, kinh doanh tốt, nở hậu.)"
                          rows={4}
                          className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none resize-none"
                        />
                      </div>
                    </div>

                    {/* Optional Price */}
                    <div className="border-t border-gray-100 pt-6">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                          <DollarSign size={16} /> Giá mong muốn / Hiện tại
                          (VND){" "}
                          <span className="text-gray-400 font-normal">
                            (Tuỳ chọn)
                          </span>
                        </label>
                        <input
                          type="number"
                          name="price"
                          value={formData.price}
                          onChange={handleInputChange}
                          placeholder="Nhập giá để so sánh..."
                          className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-gray-50/50 outline-none"
                        />
                      </div>
                    </div>

                    {error && (
                      <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm flex items-center gap-2 animate-pulse">
                        <AlertCircle size={18} />
                        {error} {timeLeft > 0 && `(Thử lại sau ${timeLeft}s)`}
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={loading || timeLeft > 0}
                      className={`w-full py-4 rounded-xl font-bold text-lg text-white shadow-lg shadow-indigo-200 transition-all transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer ${
                        loading || timeLeft > 0
                          ? "bg-gray-400 cursor-not-allowed"
                          : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700"
                      }`}
                    >
                      {loading ? (
                        <span className="flex items-center justify-center gap-2">
                          <svg
                            className="animate-spin h-5 w-5 text-white"
                            xmlns="https://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            ></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                          </svg>
                          Đang phân tích...
                        </span>
                      ) : timeLeft > 0 ? (
                        `Vui lòng chờ ${timeLeft}s`
                      ) : (
                        "Định giá ngay"
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </motion.div>

            {/* Results Sidebar / Info */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="lg:col-span-1"
            >
              <AnimatePresence mode="wait">
                {result ? (
                  <motion.div
                    key="result"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-white rounded-3xl shadow-xl shadow-green-100 border border-green-100 overflow-hidden sticky top-24"
                  >
                    <div className="bg-gradient-to-br from-green-500 to-emerald-600 p-6 text-white text-center">
                      <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center mx-auto mb-4">
                        <CheckCircle2 size={32} className="text-white" />
                      </div>
                      <h3 className="text-xl font-bold opacity-90">
                        Kết quả định giá
                      </h3>
                      <div className="text-3xl font-extrabold mt-2">
                        {formatCurrency(result.estimatedPrice)}
                      </div>
                    </div>
                    <div className="p-6 space-y-6">
                      <div>
                        <div className="text-sm text-gray-500 mb-1">
                          Khoảng giá ước tính
                        </div>
                        <div className="font-semibold text-gray-800">
                          {formatCurrency(result.priceRange.min)} -{" "}
                          {formatCurrency(result.priceRange.max)}
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: "60%" }}
                          ></div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                        <span className="text-gray-600 text-sm">
                          Độ tin cậy
                        </span>
                        <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-lg uppercase">
                          {result.confidence}
                        </span>
                      </div>

                      <div className="text-xs text-gray-400 text-center leading-relaxed">
                        * Kết quả này chỉ mang tính chất tham khảo dựa trên dữ
                        liệu thị trường và thuật toán AI. Vui lòng liên hệ
                        chuyên gia để có định giá chính xác nhất.
                      </div>

                      <button
                        onClick={() => setResult(null)}
                        className="w-full py-3 border border-gray-200 text-gray-600 font-semibold rounded-xl hover:bg-gray-50 transition-colors cursor-pointer"
                      >
                        Định giá lại
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="info"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6 sticky top-24"
                  >
                    <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                      <AlertCircle className="text-indigo-500" size={20} />
                      Tại sao chọn chúng tôi?
                    </h3>
                    <ul className="space-y-4">
                      <li className="flex items-start gap-3">
                        <div className="bg-indigo-50 p-2 rounded-lg mt-0.5">
                          <TrendingUp size={16} className="text-indigo-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-800 text-sm">
                            Dữ liệu thực tế
                          </p>
                          <p className="text-xs text-gray-500">
                            Cập nhật liên tục từ hàng nghìn giao dịch.
                          </p>
                        </div>
                      </li>
                      <li className="flex items-start gap-3">
                        <div className="bg-indigo-50 p-2 rounded-lg mt-0.5">
                          <Search size={16} className="text-indigo-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-800 text-sm">
                            AI Phân tích
                          </p>
                          <p className="text-xs text-gray-500">
                            Thuật toán học sâu so sánh các yếu tố.
                          </p>
                        </div>
                      </li>
                      <li className="flex items-start gap-3">
                        <div className="bg-indigo-50 p-2 rounded-lg mt-0.5">
                          <CheckCircle2 size={16} className="text-indigo-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-800 text-sm">
                            Miễn phí 100%
                          </p>
                          <p className="text-xs text-gray-500">
                            Dành cho mọi khách hàng cá nhân.
                          </p>
                        </div>
                      </li>
                    </ul>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}