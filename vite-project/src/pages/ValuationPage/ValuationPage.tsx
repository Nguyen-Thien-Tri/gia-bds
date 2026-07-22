import React, { useState, useEffect, useRef, useMemo } from "react";
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
  Bed,
  Bath,
  Layers,
  Scale,
  ChevronLeft,
  ChevronRight,
  FileDown,
  HelpCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import Header from "../../components/Header";
import Footer from "../../components/Footer";
import { provinceDict } from "../../assets/geo";
import { db } from "../../firebase";
import {
  collection,
  query,
  where,
  orderBy,
  limit,
  getDocs,
} from "firebase/firestore";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

// Fix Leaflet default icon
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";
const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

// ─── Types ───────────────────────────────────────────────────────────────────

interface ValuationResult {
  estimatedPrice: number;
  confidence: string;
  confidenceScore: number; // 0-1
  priceRange: { min: number; max: number };
  breakdown: PriceBreakdownItem[];
}

interface PriceBreakdownItem {
  label: string;
  impact: number; // 0-100 (percentage)
  description: string;
  icon: React.ReactNode;
  color: string;
}

interface MarketComparison {
  avgPrice: number | null;
  maxPrice: number | null;
  minPrice: number | null;
  recordCount: number;
  yearMonth: string | null;
}

interface ValidationErrors {
  area?: string;
  price?: string;
  bedrooms?: string;
  bathrooms?: string;
  floors?: string;
}

type StepNumber = 1 | 2 | 3;

// ─── Constants ───────────────────────────────────────────────────────────────

const propertyTypes = [
  { value: "apartment", label: "Căn hộ chung cư" },
  { value: "house", label: "Nhà riêng" },
  { value: "villa", label: "Biệt thự" },
  { value: "land", label: "Đất nền" },
  { value: "office", label: "Văn phòng" },
];

// Map propertyType value → BDS type name in Firestore
const propertyTypeToBDS: Record<string, string> = {
  apartment: "Căn hộ chung cư",
  house: "Nhà ở",
  villa: "Nhà biệt thự / Nhà liền kề",
  land: "Đất",
  office: "Văn phòng",
};

const legalStatuses = [
  { value: "pink_book", label: "Sổ hồng" },
  { value: "red_book", label: "Sổ đỏ" },
  { value: "contract", label: "Hợp đồng mua bán" },
  { value: "certificate", label: "Giấy tay" },
  { value: "other", label: "Khác" },
];

const cities = Object.keys(provinceDict).sort();

// Mock coordinates per district for map pins
const mockCoordinates: Record<string, [number, number]> = {
  "Quận 1": [10.7769, 106.7009],
  "Quận 3": [10.7802, 106.6867],
  "Quận 7": [10.7411, 106.7241],
  "Bình Thạnh": [10.8038, 106.7122],
  "Cầu Giấy": [21.0333, 105.8],
  "Ba Đình": [21.0343, 105.8136],
  "Hoàn Kiếm": [21.0289, 105.8524],
  "Hai Bà Trưng": [21.0136, 105.8545],
  "Đống Đa": [21.0164, 105.8267],
  "Thủ Đức": [10.8461, 106.7648],
  "Hải Châu": [16.0611, 108.2234],
  "Sơn Trà": [16.1054, 108.2525],
  "Thuận An": [10.9333, 106.7],
  "Dĩ An": [10.9167, 106.7667],
};

const stepTitles: Record<StepNumber, string> = {
  1: "Thông tin cơ bản",
  2: "Chi tiết bất động sản",
  3: "Kết quả định giá",
};

// ─── Helper ──────────────────────────────────────────────────────────────────

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(value);
};

const formatCompactCurrency = (value: number) => {
  if (value >= 1_000_000_000) {
    return (value / 1_000_000_000).toFixed(1) + " tỷ";
  }
  if (value >= 1_000_000) {
    return (value / 1_000_000).toFixed(0) + " triệu";
  }
  return formatCurrency(value);
};

const getCurrentYearMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function ValuationPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<StepNumber>(1);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>(
    {},
  );
  const [marketData, setMarketData] = useState<MarketComparison | null>(null);
  const [marketLoading, setMarketLoading] = useState(false);
  const [showBreakdownInfo, setShowBreakdownInfo] = useState(false);

  // Rate limiting state
  const timeLeftRef = useRef(0);
  const [, forceRender] = useState(0);

  // Refs for PDF
  const resultRef = useRef<HTMLDivElement>(null);

  // Form State
  const [formData, setFormData] = useState({
    propertyType: "apartment",
    transactionType: "sale" as const,
    city: "",
    district: "",
    area: "",
    price: "",
    address: "",
    bedrooms: "",
    bathrooms: "",
    floors: "",
    legalStatus: "pink_book",
  });

  // Districts filtered by selected city
  const availableDistricts = useMemo(() => {
    if (!formData.city) return [];
    return provinceDict[formData.city] || [];
  }, [formData.city]);

  // Reset district when city changes
  useEffect(() => {
    if (formData.city) {
      const dists = provinceDict[formData.city] || [];
      if (!dists.includes(formData.district)) {
        setFormData((prev) => ({ ...prev, district: "" }));
      }
    }
  }, [formData.city]);

  // ─── Rate Limiting ─────────────────────────────────────────────────────────

  useEffect(() => {
    const checkRateLimit = () => {
      const firstTime = localStorage.getItem("valuationFirstTime");
      const count = parseInt(localStorage.getItem("valuationCount") || "0");
      const now = Date.now();

      if (!firstTime) {
        localStorage.setItem("valuationFirstTime", now.toString());
        return;
      }

      const elapsed = now - parseInt(firstTime);

      if (elapsed >= 60000) {
        // Reset after 1 minute
        localStorage.setItem("valuationFirstTime", now.toString());
        localStorage.setItem("valuationCount", "0");
        timeLeftRef.current = 0;
        forceRender((v) => v + 1);
      } else if (count >= 3) {
        // Blocked
        timeLeftRef.current = Math.ceil((60000 - elapsed) / 1000);
        forceRender((v) => v + 1);
      }
    };

    checkRateLimit();

    const interval = setInterval(() => {
      if (timeLeftRef.current > 0) {
        timeLeftRef.current -= 1;
        forceRender((v) => v + 1);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // ─── Validation ────────────────────────────────────────────────────────────

  const validateStep1 = (): boolean => {
    const errors: ValidationErrors = {};
    if (!formData.city) {
      setError("Vui lòng chọn Tỉnh / Thành phố");
      return false;
    }
    if (!formData.district) {
      setError("Vui lòng chọn Quận / Huyện");
      return false;
    }
    setError(null);
    return true;
  };

  const validateStep2 = (): boolean => {
    const errors: ValidationErrors = {};
    const area = parseFloat(formData.area);

    if (!formData.area || isNaN(area) || area <= 0) {
      errors.area = "Diện tích phải lớn hơn 0";
    } else if (area > 10000) {
      errors.area = "Diện tích không hợp lệ (> 10.000m²)";
    }

    if (formData.price) {
      const price = parseFloat(formData.price);
      if (isNaN(price) || price < 0) {
        errors.price = "Giá không hợp lệ";
      }
    }

    if (formData.bedrooms) {
      const bd = parseInt(formData.bedrooms);
      if (isNaN(bd) || bd < 0 || bd > 50) {
        errors.bedrooms = "Số phòng ngủ từ 0-50";
      }
    }

    if (formData.bathrooms) {
      const bt = parseInt(formData.bathrooms);
      if (isNaN(bt) || bt < 0 || bt > 50) {
        errors.bathrooms = "Số phòng tắm từ 0-50";
      }
    }

    if (formData.floors) {
      const fl = parseInt(formData.floors);
      if (isNaN(fl) || fl < 0 || fl > 100) {
        errors.floors = "Số tầng từ 0-100";
      }
    }

    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) {
      setError("Vui lòng kiểm tra lại thông tin nhập");
      return false;
    }
    setError(null);
    return true;
  };

  // ─── Handlers ──────────────────────────────────────────────────────────────

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear validation error on change
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const nextStep = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    } else if (step === 2 && validateStep2()) {
      handleValuation();
    }
  };

  const prevStep = () => {
    if (step === 2) setStep(1);
    if (step === 3) setStep(2);
  };

  const fetchMarketComparison = async () => {
    setMarketLoading(true);
    try {
      const priceDataRef = collection(db, "price_data");
      const bdsType =
        propertyTypeToBDS[formData.propertyType] || formData.propertyType;
      const priceType = "Bán";

      const q = query(
        priceDataRef,
        where("province", "==", formData.city),
        where("district", "==", formData.district),
        where("bds_type", "==", bdsType),
        where("price_type", "==", priceType),
        orderBy("year_month", "desc"),
        limit(1),
      );

      const snapshot = await getDocs(q);

      if (!snapshot.empty) {
        const doc = snapshot.docs[0].data();
        setMarketData({
          avgPrice: doc.avg_price_million
            ? doc.avg_price_million * 1_000_000
            : null,
          maxPrice: doc.max_price_million
            ? doc.max_price_million * 1_000_000
            : null,
          minPrice: doc.min_price_million
            ? doc.min_price_million * 1_000_000
            : null,
          recordCount: doc.record_count || 0,
          yearMonth: doc.year_month || null,
        });
      } else {
        setMarketData(null);
      }
    } catch (e) {
      console.error("Error fetching market data:", e);
      setMarketData(null);
    } finally {
      setMarketLoading(false);
    }
  };

  const handleValuation = async () => {
    setError(null);
    setResult(null);
    setMarketData(null);

    // Rate limit check
    const firstTime = localStorage.getItem("valuationFirstTime");
    const count = parseInt(localStorage.getItem("valuationCount") || "0");
    const now = Date.now();

    if (firstTime && count >= 3) {
      const elapsed = now - parseInt(firstTime);
      if (elapsed < 60000) {
        timeLeftRef.current = Math.ceil((60000 - elapsed) / 1000);
        setError(
          "Bạn đã vượt quá giới hạn định giá (3 lần/phút). Vui lòng thử lại sau.",
        );
        forceRender((v) => v + 1);
        return;
      } else {
        localStorage.setItem("valuationFirstTime", now.toString());
        localStorage.setItem("valuationCount", "0");
        timeLeftRef.current = 0;
      }
    }

    setLoading(true);

    // Simulate API Call (replace with real API later)
    setTimeout(async () => {
      const area = parseFloat(formData.area) || 0;
      const bedrooms = parseInt(formData.bedrooms) || 0;
      const bathrooms = parseInt(formData.bathrooms) || 0;
      const floors = parseInt(formData.floors) || 0;

      // Mock algorithm
      const basePricePerM2 = 50_000_000;
      const locationFactor =
        formData.city === "Hồ Chí Minh" || formData.city === "Hà Nội"
          ? 1.3
          : 1.0;
      const districtBonus =
        availableDistricts.indexOf(formData.district) >= 0 ? 1.05 : 1.0;
      const sizeFactor = area > 100 ? 0.95 : area < 30 ? 1.1 : 1.0;
      const roomBonus = 1 + bedrooms * 0.02 + bathrooms * 0.015;
      const floorBonus =
        formData.propertyType === "house" || formData.propertyType === "villa"
          ? 1 + floors * 0.03
          : 1.0;

      const variance = Math.random() * 0.1 + 0.95;
      const estimated =
        basePricePerM2 *
        area *
        locationFactor *
        districtBonus *
        sizeFactor *
        roomBonus *
        floorBonus *
        variance;
      const rounded = Math.round(estimated / 100000) * 100000;

      const breakdownItems: PriceBreakdownItem[] = [
        {
          label: "Vị trí & khu vực",
          impact: Math.round(35 + Math.random() * 10),
          description:
            formData.city === "Hồ Chí Minh" || formData.city === "Hà Nội"
              ? `${formData.city} là thành phố lớn, mật độ dân cư cao, giá BĐS cao hơn 30% so với mặt bằng chung. Khu vực ${formData.district} có hạ tầng phát triển tốt.`
              : `${formData.city} có tốc độ đô thị hóa ổn định. Khu vực ${formData.district} có tiềm năng tăng giá.`,
          icon: <MapPin size={18} />,
          color: "bg-blue-500",
        },
        {
          label: "Diện tích",
          impact: Math.round(20 + Math.random() * 10),
          description:
            area > 100
              ? `Diện tích ${area}m² khá lớn, thường có đơn giá/m² thấp hơn khoảng 5%.`
              : area < 30
                ? `Diện tích ${area}m² nhỏ, phù hợp nhu cầu căn hộ vừa phải, đơn giá/m² cao hơn.`
                : `Diện tích ${area}m² là kích thước phổ biến, giá trị ổn định.`,
          icon: <Ruler size={18} />,
          color: "bg-teal-500",
        },
        {
          label: "Loại hình & tiện ích",
          impact: Math.round(15 + Math.random() * 8),
          description:
            propertyTypes.find((p) => p.value === formData.propertyType)
              ?.label || formData.propertyType,
          icon: <Building2 size={18} />,
          color: "bg-purple-500",
        },
        {
          label: "Phòng ốc & nội thất",
          impact: Math.round(10 + Math.random() * 8),
          description: `${bedrooms} phòng ngủ, ${bathrooms} phòng tắm${floors > 0 ? `, ${floors} tầng` : ""}. Số lượng phòng phù hợp với nhu cầu gia đình.`,
          icon: <Bed size={18} />,
          color: "bg-amber-500",
        },
        {
          label: "Xu hướng thị trường",
          impact: Math.round(8 + Math.random() * 7),
          description:
            "Thị trường mua bán đang ổn định, nhu cầu nhà ở vẫn duy trì ở mức cao.",
          icon: <TrendingUp size={18} />,
          color: "bg-rose-500",
        },
      ];

      // Normalize to 100%
      const totalImpact = breakdownItems.reduce(
        (sum, item) => sum + item.impact,
        0,
      );
      breakdownItems.forEach((item) => {
        item.impact = Math.round((item.impact / totalImpact) * 100);
      });

      setResult({
        estimatedPrice: rounded,
        confidence: rounded > 0 ? "Cao" : "Thấp",
        confidenceScore: 0.85 + Math.random() * 0.1,
        priceRange: {
          min: Math.round(rounded * 0.92),
          max: Math.round(rounded * 1.08),
        },
        breakdown: breakdownItems,
      });

      // Update rate limit
      if (!firstTime) {
        localStorage.setItem("valuationFirstTime", now.toString());
      }
      localStorage.setItem("valuationCount", ((count || 0) + 1).toString());
      timeLeftRef.current = 0;

      setLoading(false);
      setStep(3);

      // Fetch market comparison
      fetchMarketComparison();
    }, 2000);
  };

  const resetForm = () => {
    setResult(null);
    setMarketData(null);
    setStep(1);
    setError(null);
    setValidationErrors({});
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const exportPDF = async () => {
    if (!resultRef.current) return;
    try {
      const canvas = await html2canvas(resultRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save("ket-qua-dinh-gia-bat-dong-san.pdf");
    } catch (e) {
      console.error("PDF export error:", e);
      setError("Có lỗi khi xuất PDF. Vui lòng thử lại.");
    }
  };

  // Get coordinates for map
  const mapCenter = useMemo<[number, number]>(() => {
    if (formData.district && mockCoordinates[formData.district]) {
      return mockCoordinates[formData.district];
    }
    if (formData.city === "Hồ Chí Minh") return [10.8231, 106.6297];
    if (formData.city === "Hà Nội") return [21.0285, 105.8542];
    if (formData.city === "Đà Nẵng") return [16.0544, 108.2022];
    return [10.8231, 106.6297];
  }, [formData.city, formData.district]);

  // ─── Render Helpers ─────────────────────────────────────────────────────────

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8 gap-2 sm:gap-4">
      {([1, 2, 3] as StepNumber[]).map((s) => (
        <React.Fragment key={s}>
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                step === s
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-200 scale-110"
                  : step > s
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-400"
              }`}
            >
              {step > s ? <CheckCircle2 size={18} /> : s}
            </div>
            <span
              className={`text-xs sm:text-sm font-medium hidden sm:block ${
                step === s
                  ? "text-blue-600"
                  : step > s
                    ? "text-blue-600"
                    : "text-gray-400"
              }`}
            >
              {stepTitles[s]}
            </span>
          </div>
          {s < 3 && (
            <div
              className={`w-8 sm:w-12 h-0.5 rounded ${
                step > s ? "bg-blue-400" : "bg-gray-200"
              }`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  const renderFieldError = (field: keyof ValidationErrors) => {
    if (!validationErrors[field]) return null;
    return (
      <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
        <AlertCircle size={12} />
        {validationErrors[field]}
      </p>
    );
  };

  const renderComparisonBar = (
    label: string,
    value: number | null,
    color: string,
  ) => {
    if (!result || !value) return null;
    const maxVal = Math.max(result.estimatedPrice, marketData?.maxPrice || 0);
    const pct = maxVal > 0 ? (value / maxVal) * 100 : 0;
    return (
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">{label}</span>
          <span className="font-semibold">{formatCompactCurrency(value)}</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all duration-700 ${color}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    );
  };

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow bg-gray-50/50 pt-32 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header Section */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center justify-center p-3 mb-4 rounded-2xl bg-blue-50 text-blue-600"
            >
              <TrendingUp size={32} />
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl mb-3"
            >
              Định giá tham khảo cho Bất Động Sản
            </motion.h1>
          </div>

          {/* Step Indicator */}
          {renderStepIndicator()}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Form */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="lg:col-span-2"
            >
              <div className="bg-white rounded-3xl shadow-xl shadow-blue-100/50 overflow-hidden border border-gray-100">
                <div className="p-6 sm:p-8">
                  {/* ── Step 1: Basic Info ── */}
                  {step <= 2 && (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        nextStep();
                      }}
                      className="space-y-6"
                    >
                      {/* Transaction Type - Chỉ Bán */}
                      <div className="inline-flex items-center gap-2 px-4 py-2 mb-6 bg-blue-50 text-blue-700 rounded-xl text-sm font-medium">
                        <Building2 size={16} />
                        Giao dịch mua bán
                      </div>

                      {step === 1 && (
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
                              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                            >
                              {propertyTypes.map((type) => (
                                <option key={type.value} value={type.value}>
                                  {type.label}
                                </option>
                              ))}
                            </select>
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
                              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
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

                          {/* District - now dependent on city */}
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                              <MapPin size={16} /> Quận / Huyện
                            </label>
                            <select
                              name="district"
                              value={formData.district}
                              onChange={handleInputChange}
                              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                              required
                              disabled={!formData.city}
                            >
                              <option value="">
                                {formData.city
                                  ? "Chọn Quận/Huyện"
                                  : "Chọn Tỉnh/Thành trước"}
                              </option>
                              {availableDistricts.map((d) => (
                                <option key={d} value={d}>
                                  {d}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                      )}

                      {step === 2 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                              className={`w-full px-4 py-3 rounded-xl border transition-all bg-gray-50/50 outline-none ${
                                validationErrors.area
                                  ? "border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200"
                                  : "border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                              }`}
                              required
                            />
                            {renderFieldError("area")}
                          </div>

                          {/* Price */}
                          <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                              <DollarSign size={16} /> Giá mong muốn (VND)
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
                              className={`w-full px-4 py-3 rounded-xl border transition-all bg-gray-50/50 outline-none ${
                                validationErrors.price
                                  ? "border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200"
                                  : "border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                              }`}
                            />
                            {renderFieldError("price")}
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
                              placeholder="Ví dụ: 2"
                              min="0"
                              className={`w-full px-4 py-3 rounded-xl border transition-all bg-gray-50/50 outline-none ${
                                validationErrors.bedrooms
                                  ? "border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200"
                                  : "border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                              }`}
                            />
                            {renderFieldError("bedrooms")}
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
                              placeholder="Ví dụ: 1"
                              min="0"
                              className={`w-full px-4 py-3 rounded-xl border transition-all bg-gray-50/50 outline-none ${
                                validationErrors.bathrooms
                                  ? "border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200"
                                  : "border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                              }`}
                            />
                            {renderFieldError("bathrooms")}
                          </div>

                          {/* Floors - show for house/villa */}
                          {(formData.propertyType === "house" ||
                            formData.propertyType === "villa") && (
                            <div className="space-y-2">
                              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <Layers size={16} /> Số tầng
                              </label>
                              <input
                                type="number"
                                name="floors"
                                value={formData.floors}
                                onChange={handleInputChange}
                                placeholder="Ví dụ: 2"
                                min="0"
                                className={`w-full px-4 py-3 rounded-xl border transition-all bg-gray-50/50 outline-none ${
                                  validationErrors.floors
                                    ? "border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-200"
                                    : "border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
                                }`}
                              />
                              {renderFieldError("floors")}
                            </div>
                          )}

                          {/* Legal Status */}
                          <div
                            className={`space-y-2 ${
                              formData.propertyType === "house" ||
                              formData.propertyType === "villa"
                                ? ""
                                : "md:col-span-2"
                            }`}
                          >
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                              <Scale size={16} /> Tình trạng pháp lý
                            </label>
                            <select
                              name="legalStatus"
                              value={formData.legalStatus}
                              onChange={handleInputChange}
                              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all bg-gray-50/50 outline-none cursor-pointer"
                            >
                              {legalStatuses.map((s) => (
                                <option key={s.value} value={s.value}>
                                  {s.label}
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Detailed Address */}
                          <div className="md:col-span-2 space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                              <Home size={16} /> Địa chỉ chi tiết
                            </label>
                            <input
                              type="text"
                              name="address"
                              value={formData.address}
                              onChange={handleInputChange}
                              placeholder="Số nhà, tên đường..."
                              list="address-suggestions"
                              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all bg-gray-50/50 outline-none"
                            />
                            <datalist id="address-suggestions">
                              <option
                                value={`${formData.district}, ${formData.city}`}
                              />
                              <option
                                value={`Khu đô thị mới, ${formData.district}, ${formData.city}`}
                              />
                            </datalist>
                          </div>
                        </div>
                      )}

                      {error && (
                        <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm flex items-center gap-2">
                          <AlertCircle size={18} />
                          {error}
                          {timeLeftRef.current > 0 &&
                            ` (Thử lại sau ${timeLeftRef.current}s)`}
                        </div>
                      )}

                      {/* Navigation Buttons */}
                      <div className="flex gap-3">
                        {step === 2 && (
                          <button
                            type="button"
                            onClick={prevStep}
                            className="flex items-center gap-2 px-6 py-3 border border-gray-200 text-gray-600 font-semibold rounded-xl hover:bg-gray-50 transition-colors cursor-pointer"
                          >
                            <ChevronLeft size={18} />
                            Quay lại
                          </button>
                        )}
                        <button
                          type="submit"
                          disabled={loading || timeLeftRef.current > 0}
                          className={`flex-1 py-4 rounded-xl font-bold text-lg text-white shadow-lg shadow-blue-200 transition-all transform hover:scale-[1.02] active:scale-[0.98] cursor-pointer ${
                            loading || timeLeftRef.current > 0
                              ? "bg-gray-400 cursor-not-allowed"
                              : "bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                          }`}
                        >
                          {loading ? (
                            <span className="flex items-center justify-center gap-2">
                              <svg
                                className="animate-spin h-5 w-5 text-white"
                                xmlns="http://www.w3.org/2000/svg"
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
                                />
                                <path
                                  className="opacity-75"
                                  fill="currentColor"
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                />
                              </svg>
                              Đang phân tích...
                            </span>
                          ) : timeLeftRef.current > 0 ? (
                            `Vui lòng chờ ${timeLeftRef.current}s`
                          ) : step === 1 ? (
                            <span className="flex items-center justify-center gap-2">
                              Tiếp theo
                              <ChevronRight size={18} />
                            </span>
                          ) : (
                            "Định giá ngay"
                          )}
                        </button>
                      </div>
                    </form>
                  )}

                  {/* ── Step 3: Results ── */}
                  {step === 3 && result && (
                    <div ref={resultRef} className="space-y-6">
                      {/* Result Header */}
                      <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-6 sm:p-8 rounded-2xl text-white text-center">
                        <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center mx-auto mb-4">
                          <CheckCircle2 size={32} className="text-white" />
                        </div>
                        <h3 className="text-xl font-bold opacity-90">
                          Kết quả định giá
                        </h3>
                        <div className="text-3xl sm:text-4xl font-extrabold mt-2">
                          {formatCurrency(result.estimatedPrice)}
                        </div>
                        <div className="flex items-center justify-center gap-4 mt-4">
                          <span className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-lg text-sm">
                            Độ tin cậy: {result.confidence}
                          </span>
                          <span className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-lg text-sm">
                            {result.priceRange.min && result.priceRange.max
                              ? `${formatCompactCurrency(result.priceRange.min)} - ${formatCompactCurrency(result.priceRange.max)}`
                              : ""}
                          </span>
                        </div>
                      </div>

                      {/* Confidence bar */}
                      <div className="px-2">
                        <div className="flex justify-between text-sm text-gray-500 mb-1">
                          <span>Độ chính xác</span>
                          <span>
                            {Math.round(result.confidenceScore * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                          <div
                            className="h-2.5 rounded-full bg-gradient-to-r from-blue-400 via-cyan-400 to-cyan-600 transition-all duration-1000"
                            style={{
                              width: `${result.confidenceScore * 100}%`,
                            }}
                          />
                        </div>
                      </div>

                      {/* Breakdown */}
                      <div className="bg-gray-50 rounded-2xl p-5 space-y-4">
                        <div className="flex items-center justify-between">
                          <h4 className="font-bold text-gray-800 flex items-center gap-2">
                            <TrendingUp size={18} className="text-blue-500" />
                            Cách tính giá
                          </h4>
                          <button
                            type="button"
                            onClick={() =>
                              setShowBreakdownInfo(!showBreakdownInfo)
                            }
                            className="text-blue-500 hover:text-blue-700 text-xs flex items-center gap-1 cursor-pointer"
                          >
                            <HelpCircle size={14} />
                            {showBreakdownInfo
                              ? "Ẩn giải thích"
                              : "Xem giải thích"}
                          </button>
                        </div>

                        {result.breakdown.map((item, idx) => (
                          <div key={idx} className="space-y-1">
                            <div className="flex justify-between items-center text-sm">
                              <span className="flex items-center gap-1.5 text-gray-700">
                                <span
                                  className={
                                    item.color + " p-1 rounded-lg text-white"
                                  }
                                >
                                  {item.icon}
                                </span>
                                {item.label}
                              </span>
                              <span className="font-semibold text-gray-900">
                                {item.impact}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-2 rounded-full transition-all duration-700 ${item.color}`}
                                style={{ width: `${item.impact}%` }}
                              />
                            </div>
                            {showBreakdownInfo && (
                              <motion.p
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                className="text-xs text-gray-500 mt-1 pl-7"
                              >
                                {item.description}
                              </motion.p>
                            )}
                          </div>
                        ))}

                        <p className="text-[10px] text-gray-400 italic mt-2">
                          * Tỉ lệ % thể hiện mức độ ảnh hưởng của từng yếu tố
                          đến giá trị BĐS. Khi có dữ liệu từ model AI thực tế,
                          thông tin sẽ được cập nhật chính xác hơn.
                        </p>
                      </div>

                      {/* Market Comparison */}
                      <div className="bg-gray-50 rounded-2xl p-5">
                        <h4 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                          <Search size={18} className="text-blue-500" />
                          So sánh với thị trường
                        </h4>
                        {marketLoading ? (
                          <div className="flex items-center justify-center py-6">
                            <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full" />
                            <span className="ml-3 text-gray-500 text-sm">
                              Đang tải dữ liệu thị trường...
                            </span>
                          </div>
                        ) : marketData && marketData.avgPrice ? (
                          <div className="space-y-3">
                            {renderComparisonBar(
                              "🏠 Giá định giá của bạn",
                              result.estimatedPrice,
                              "bg-blue-500",
                            )}
                            {renderComparisonBar(
                              "📊 Giá trung bình khu vực",
                              marketData.avgPrice,
                              "bg-teal-400",
                            )}
                            {marketData.maxPrice &&
                              renderComparisonBar(
                                "🔺 Giá cao nhất KV",
                                marketData.maxPrice,
                                "bg-rose-400",
                              )}
                            {marketData.minPrice &&
                              renderComparisonBar(
                                "🔻 Giá thấp nhất KV",
                                marketData.minPrice,
                                "bg-blue-400",
                              )}

                            <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-400">
                              Dữ liệu từ {marketData.recordCount} giao dịch
                              {marketData.yearMonth &&
                                ` trong tháng ${marketData.yearMonth}`}
                            </div>
                          </div>
                        ) : (
                          <div className="text-center py-6 text-gray-400 text-sm">
                            <Search
                              size={24}
                              className="mx-auto mb-2 opacity-50"
                            />
                            Chưa có dữ liệu thị trường cho khu vực này.
                            <br />
                            <span className="text-xs">
                              (Cần có dữ liệu trong collection "price_data" với
                              province="{formData.city}", district="
                              {formData.district}")
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Map */}
                      <div className="bg-gray-50 rounded-2xl p-5">
                        <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                          <MapPin size={18} className="text-red-500" />
                          Vị trí bất động sản
                        </h4>
                        <div className="rounded-xl overflow-hidden h-[200px] sm:h-[250px] border border-gray-200">
                          <MapContainer
                            center={mapCenter}
                            zoom={13}
                            scrollWheelZoom={false}
                            style={{ height: "100%", width: "100%" }}
                          >
                            <TileLayer
                              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />
                            <Marker position={mapCenter}>
                              <Popup>
                                <div className="text-sm">
                                  <strong>
                                    {formData.district}, {formData.city}
                                  </strong>
                                  <br />
                                  Giá ước tính:{" "}
                                  {formatCompactCurrency(result.estimatedPrice)}
                                </div>
                              </Popup>
                            </Marker>
                          </MapContainer>
                        </div>
                        <p className="text-xs text-gray-400 mt-2 italic">
                          * Vị trí hiển thị gần đúng dựa trên quận/huyện đã
                          chọn.
                        </p>
                      </div>

                      {/* Disclaimer */}
                      <div className="text-xs text-gray-400 text-center leading-relaxed bg-gray-50 rounded-xl p-4">
                        * Kết quả này chỉ mang tính chất tham khảo dựa trên dữ
                        liệu thị trường và thuật toán AI. Vui lòng liên hệ
                        chuyên gia để có định giá chính xác nhất.
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-3">
                        <button
                          onClick={resetForm}
                          className="flex-1 py-3 border border-gray-200 text-gray-600 font-semibold rounded-xl hover:bg-gray-50 transition-colors cursor-pointer"
                        >
                          Định giá lại
                        </button>
                        <button
                          onClick={exportPDF}
                          className="flex items-center justify-center gap-2 py-3 px-6 bg-blue-50 text-blue-600 font-semibold rounded-xl hover:bg-blue-100 transition-colors cursor-pointer"
                        >
                          <FileDown size={18} />
                          <span className="hidden sm:inline">Xuất PDF</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>

            {/* Right Column - Info Sidebar */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
              className="lg:col-span-1"
            >
              <AnimatePresence mode="wait">
                {step < 3 ? (
                  <motion.div
                    key="info"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6 sticky top-24"
                  >
                    <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                      <AlertCircle className="text-blue-500" size={20} />
                      Tại sao chọn chúng tôi?
                    </h3>
                    <ul className="space-y-4">
                      <li className="flex items-start gap-3">
                        <div className="bg-blue-50 p-2 rounded-lg mt-0.5">
                          <TrendingUp size={16} className="text-blue-600" />
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
                        <div className="bg-blue-50 p-2 rounded-lg mt-0.5">
                          <Search size={16} className="text-blue-600" />
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
                        <div className="bg-blue-50 p-2 rounded-lg mt-0.5">
                          <CheckCircle2 size={16} className="text-blue-600" />
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
                    {step === 1 && (
                      <div className="mt-6 pt-4 border-t border-gray-100">
                        <p className="text-xs text-gray-400">
                          <strong>Bước {step}/2:</strong> {stepTitles[step]}
                        </p>
                      </div>
                    )}
                    {step === 2 && (
                      <div className="mt-6 pt-4 border-t border-gray-100 space-y-2">
                        <p className="text-xs text-gray-400">
                          <strong>Thông tin đã chọn:</strong>
                        </p>
                        <div className="text-xs text-gray-600 space-y-1">
                          <p>
                            •{" "}
                            {
                              propertyTypes.find(
                                (p) => p.value === formData.propertyType,
                              )?.label
                            }
                          </p>
                          <p>
                            • {formData.city} - {formData.district}
                          </p>
                          {formData.area && (
                            <p>• Diện tích: {formData.area}m²</p>
                          )}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ) : result ? (
                  <motion.div
                    key="summary"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-3xl shadow-lg border border-gray-100 p-6 sticky top-24 space-y-4"
                  >
                    <h3 className="font-bold text-gray-900 flex items-center gap-2">
                      <CheckCircle2 className="text-blue-500" size={20} />
                      Thông tin định giá
                    </h3>
                    <div className="space-y-2 text-sm text-gray-600">
                      <p>
                        <strong>Loại:</strong>{" "}
                        {
                          propertyTypes.find(
                            (p) => p.value === formData.propertyType,
                          )?.label
                        }
                      </p>
                      <p>
                        <strong>Giao dịch:</strong> Mua bán
                      </p>
                      <p>
                        <strong>Vị trí:</strong> {formData.district},{" "}
                        {formData.city}
                      </p>
                      <p>
                        <strong>Diện tích:</strong> {formData.area}m²
                      </p>
                      {formData.bedrooms && (
                        <p>
                          <strong>Phòng ngủ:</strong> {formData.bedrooms}
                        </p>
                      )}
                      {formData.bathrooms && (
                        <p>
                          <strong>Phòng tắm:</strong> {formData.bathrooms}
                        </p>
                      )}
                    </div>
                    <div className="pt-3 border-t border-gray-100">
                      <button
                        onClick={prevStep}
                        className="w-full py-2 text-blue-600 text-sm font-semibold hover:text-blue-800 transition-colors cursor-pointer"
                      >
                        ← Chỉnh sửa thông tin
                      </button>
                    </div>
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </motion.div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
