import { useState, useEffect } from "react";
import { collection, query, where, getDocs } from "firebase/firestore";
import { db } from "../../../firebase";
import { Building2Icon, School, DollarSign, Building } from "lucide-react";
import {
  StatItem,
  PrebinnedItem,
  PieItem,
  RegionItem,
} from "../components/analytics/types";
import {
  APARTMENT_AREA_LABELS,
  HOUSE_AREA_LABELS,
  LAND_AREA_LABELS,
  PRICE_RANGES,
} from "../components/analytics/constants";
import { formatNumber } from "../components/analytics/utils";
import { provinceDict } from "../../../assets/geo";

export function useMarketStats(
  selectedProvince: string,
  initialStats: StatItem[],
) {
  const [displayStats, setDisplayStats] = useState<StatItem[]>(initialStats);
  const [apartmentPriceByArea, setApartmentPriceByArea] = useState<
    PrebinnedItem[]
  >([]);
  const [housePriceByArea, setHousePriceByArea] = useState<PrebinnedItem[]>([]);
  const [landPriceByArea, setLandPriceByArea] = useState<PrebinnedItem[]>([]);
  const [priceDistribution, setPriceDistribution] = useState<PieItem[]>([]);
  const [housePriceDistribution, setHousePriceDistribution] = useState<
    PieItem[]
  >([]);
  const [apartmentDistricts, setApartmentDistricts] = useState<RegionItem[]>(
    [],
  );
  const [townhouseDistricts, setTownhouseDistricts] = useState<RegionItem[]>(
    [],
  );
  const [individualHouseDistricts, setIndividualHouseDistricts] = useState<
    RegionItem[]
  >([]);
  const [landDistricts, setLandDistricts] = useState<RegionItem[]>([]);
  const [totalBDS, setTotalBDS] = useState<number>(0);
  const [totalHouseBDS, setTotalHouseBDS] = useState<number>(0);
  const [remoteLastUpdated, setRemoteLastUpdated] = useState<Date | undefined>(
    undefined,
  );
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const today = new Date();
        const dayOfMonth = today.getDate();
        const targetDate = new Date(today);

        if (dayOfMonth <= 15) {
          targetDate.setMonth(targetDate.getMonth() - 1);
        }

        const year = targetDate.getFullYear();
        const month = String(targetDate.getMonth() + 1).padStart(2, "0");
        const currentYearMonth = `${year}-${month}`;

        const provinceValue =
          selectedProvince === "Toàn quốc" ? "All" : selectedProvince;

        const metricsRef = collection(db, "metrics");
        const q = query(
          metricsRef,
          where("province", "==", provinceValue),
          where("year_month", "==", currentYearMonth),
          where("name", "in", [
            "project_count",
            "sales_bds_count",
            "total_sales_amt",
            "CHCC_price",
            "CHCC_price_by_m2",
            "nha_o_price_by_m2",
            "land_price_by_m2",
            "CHCC_count_by_price",
            "nha_o_count_by_price",
            "top 5 quan by CHCC price",
            "top 5 quan by nha pho price",
            "top 5 quan by nha rieng price",
            "top 5 quan by land price",
          ]),
        );

        const snapshot = await getDocs(q);
        const currentData: Record<string, any> = {};

        if (!snapshot.empty) {
          // Since we query by specific year_month, all docs are relevant.
          // Pick the first one to get updated_at, or find one that has it.
          const firstDocData = snapshot.docs[0].data();
          if (firstDocData.updated_at) {
            const updatedAt = (firstDocData.updated_at as any).toDate
              ? (firstDocData.updated_at as any).toDate()
              : new Date(firstDocData.updated_at);
            if (!Number.isNaN(updatedAt.getTime())) {
              setRemoteLastUpdated(updatedAt);
            }
          }
        }

        snapshot.forEach((doc) => {
          const d = doc.data();
          // Store entire doc data so we can access vs_LM
          currentData[d.name] = d;
        });

        // Helper to format vs_LM percentage
        const formatChange = (val: any) => {
          if (val === undefined || val === null) return "0,0%";
          // Assuming vs_LM is a number (percentage or ratio).
          // If vs_LM is already a percentage number (e.g. 5.2 for 5.2%), just format it.
          // If it's a ratio (e.g. 0.052), multiply by 100.
          // Let's assume it's a number. Checking type safety is good.
          const num = typeof val === "string" ? parseFloat(val) : val;
          if (isNaN(num)) return "0,0%";

          return (
            num.toLocaleString("de-DE", {
              minimumFractionDigits: 1,
              maximumFractionDigits: 1,
            }) + "%"
          );
        };

        const newStats: StatItem[] = [
          {
            id: 1,
            Icon: Building2Icon,
            value: currentData.project_count?.value
              ? formatNumber(currentData.project_count.value)
              : "No data",
            label: "Dự án",
            change: formatChange(currentData.project_count?.vs_LM),
            positive: (currentData.project_count?.vs_LM || 0) >= 0,
          },
          {
            id: 2,
            Icon: School,
            value: currentData.sales_bds_count?.value
              ? formatNumber(currentData.sales_bds_count.value)
              : "No data",
            label: "Bất động sản đăng bán",
            change: formatChange(currentData.sales_bds_count?.vs_LM),
            positive: (currentData.sales_bds_count?.vs_LM || 0) >= 0,
          },
          {
            id: 3,
            Icon: DollarSign,
            value: currentData.total_sales_amt?.value
              ? formatNumber(Math.round(currentData.total_sales_amt.value))
              : "No data",
            label: "Giá trị ước tính (tỷ VND)",
            change: formatChange(currentData.total_sales_amt?.vs_LM),
            positive: (currentData.total_sales_amt?.vs_LM || 0) >= 0,
          },
          {
            id: 4,
            Icon: Building,
            value:
              currentData.CHCC_price?.value && currentData.CHCC_price.value > 0
                ? (currentData.CHCC_price.value / 1000).toLocaleString(
                    "de-DE",
                    {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    },
                  )
                : "No data",
            label: "Trung bình giá căn hộ chung cư (tỷ VND)",
            change: formatChange(currentData.CHCC_price?.vs_LM),
            positive: (currentData.CHCC_price?.vs_LM || 0) >= 0,
          },
        ];

        setDisplayStats(newStats);

        const mapAreaPrice = (priceArray: number[], labels: string[]) => {
          if (!Array.isArray(priceArray)) return [];
          return priceArray.map((val: number, idx: number) => ({
            range: labels[idx] || `Range ${idx + 1}`,
            Giá: val === -1 ? null : val,
          }));
        };

        setApartmentPriceByArea(
          mapAreaPrice(
            currentData.CHCC_price_by_m2?.value,
            APARTMENT_AREA_LABELS,
          ),
        );
        setHousePriceByArea(
          mapAreaPrice(currentData.nha_o_price_by_m2?.value, HOUSE_AREA_LABELS),
        );
        setLandPriceByArea(
          mapAreaPrice(currentData.land_price_by_m2?.value, LAND_AREA_LABELS),
        );

        const mapPriceDistribution = (counts: number[]) => {
          if (!Array.isArray(counts)) return [];
          const totalCount = counts.reduce((a, b) => a + b, 0);
          return counts.map((count, idx) => ({
            label: PRICE_RANGES[idx] || `Range ${idx + 1}`,
            value:
              totalCount > 0
                ? parseFloat(((count / totalCount) * 100).toFixed(1))
                : 0,
          }));
        };

        setPriceDistribution(
          mapPriceDistribution(currentData.CHCC_count_by_price?.value),
        );
        setHousePriceDistribution(
          mapPriceDistribution(currentData.nha_o_count_by_price?.value),
        );

        const mapRegionStats = (items: any[]): RegionItem[] => {
          if (!Array.isArray(items)) return [];
          const result: RegionItem[] = [];
          for (const item of items) {
            if (!item || !item.district) continue;
            const trimmedDistrict = item.district.trim();
            let province = item.province;
            let isValid = false;

            if (selectedProvince === "Toàn quốc") {
              // For "Toàn quốc", look up in geo.ts to find matching province
              for (const [p, districts] of Object.entries(provinceDict)) {
                if (districts.includes(trimmedDistrict)) {
                  province = p;
                  isValid = true;
                  break;
                }
              }
            } else {
              // For a specific province, district must exist in that province's list
              const districtsOfProvince = provinceDict[selectedProvince];
              if (districtsOfProvince && districtsOfProvince.includes(trimmedDistrict)) {
                isValid = true;
              }
            }

            if (isValid) {
              result.push({
                name: trimmedDistrict,
                value: item.price || 0,
                province: selectedProvince === "Toàn quốc" ? province : undefined,
              });
            }
          }
          return result;
        };

        setApartmentDistricts(
          mapRegionStats(currentData["top 5 quan by CHCC price"]?.value),
        );
        setTownhouseDistricts(
          mapRegionStats(currentData["top 5 quan by nha pho price"]?.value),
        );
        setIndividualHouseDistricts(
          mapRegionStats(currentData["top 5 quan by nha rieng price"]?.value),
        );
        setLandDistricts(
          mapRegionStats(currentData["top 5 quan by land price"]?.value),
        );

        const sumArray = (arr: number[]) =>
          Array.isArray(arr) ? arr.reduce((a, b) => a + b, 0) : 0;
        setTotalBDS(sumArray(currentData.CHCC_count_by_price?.value));
        setTotalHouseBDS(sumArray(currentData.nha_o_count_by_price?.value));
      } catch (error) {
        console.error("Error fetching market stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [selectedProvince]);

  return {
    displayStats,
    apartmentPriceByArea,
    housePriceByArea,
    landPriceByArea,
    priceDistribution,
    housePriceDistribution,
    apartmentDistricts,
    townhouseDistricts,
    individualHouseDistricts,
    landDistricts,
    totalBDS,
    totalHouseBDS,
    remoteLastUpdated,
    loading,
  };
}
