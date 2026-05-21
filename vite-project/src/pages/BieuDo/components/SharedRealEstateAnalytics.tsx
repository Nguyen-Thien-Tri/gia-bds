import React, { useMemo, useState } from "react";
import { FiltersContainer, MultiFilters } from "./FilterSection";
import ChartsSection, { pageStyles } from "./ChartsSection";
import { BDS_colorMap } from "../../../assets/colors";

export type RealEstateRecord = {
  fullDate: Date;
  month: string;
  year: number;
  city: string;
  district: string;
  type: string;
  price: number;
};

type SharedRealEstateAnalyticsProps = {
  pageTitle: string;
  unitText?: string;
  priceUnit: string;
  realEstateTypes: string[];
  priceType: "Bán" | "Cho thuê";
};

export default function SharedRealEstateAnalytics({
  pageTitle,
  unitText,
  priceUnit,
  realEstateTypes,
  priceType,
}: SharedRealEstateAnalyticsProps): React.JSX.Element {
  const [realData, setRealData] = useState<RealEstateRecord[]>([]);
  const [initialDataLoaded, setInitialDataLoaded] = useState(false);

  const monthYears = useMemo(() => {
    const now = new Date();
    // Only show the current month if today is after the 15th
    const endMonth = now.getDate() > 15 ? now.getMonth() : now.getMonth() - 1;
    const end = new Date(now.getFullYear(), endMonth, 1);
    const start = new Date(2025, 11, 1); // From Dec 2025 (month 11 is December)

    const res: string[] = [];
    let curr = new Date(end);
    while (curr >= start) {
      res.push(
        `${String(curr.getMonth() + 1).padStart(2, "0")}/${curr.getFullYear()}`,
      );
      curr.setMonth(curr.getMonth() - 1);
    }
    return res;
  }, []);

  const defaultLast2Months = useMemo(() => {
    if (monthYears.length === 0) return [] as string[];
    const pickDesc = monthYears.slice(0, 2);
    const parseMonth = (m: string) => {
      const [mm, yyyy] = m.split("/").map(Number);
      return new Date(yyyy, mm - 1, 1);
    };
    return pickDesc.sort((a, b) => +parseMonth(a) - +parseMonth(b));
  }, [monthYears]);

  const [appliedFilters, setAppliedFilters] = useState<MultiFilters>(() => {
    // Helper to find available types from the requested defaults
    const defaultTypes = ["Căn hộ chung cư", "Nhà ở", "Đất"];
    const initialTypes = realEstateTypes.filter((t) =>
      defaultTypes.includes(t),
    );

    return {
      city: ["Hà Nội", "Hồ Chí Minh"],
      district: [],
      realEstateType: initialTypes,
      monthYear: defaultLast2Months,
    };
  });

  const [showCharts, setShowCharts] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const filteredData = useMemo(() => {
    const f = appliedFilters;
    return realData.filter((d) => {
      const cityOk = f.city.length === 0 || f.city.includes(d.city);
      const districtOk =
        f.district.length === 0 || f.district.includes(d.district);
      const typeOk =
        f.realEstateType.length === 0 || f.realEstateType.includes(d.type);
      const monthOk = f.monthYear.length === 0 || f.monthYear.includes(d.month);
      return cityOk && districtOk && typeOk && monthOk;
    });
  }, [realData, appliedFilters]);

  const toSingleFilters = (): {
    cities: string[];
    district: string;
    realEstateTypes: string[];
    monthYear: string;
    districts: string[];
  } => {
    return {
      cities: appliedFilters.city,
      district:
        appliedFilters.city.length > 1 || appliedFilters.district.length === 0
          ? "All"
          : appliedFilters.district[0],
      realEstateTypes: appliedFilters.realEstateType,
      monthYear:
        appliedFilters.monthYear.length === 0
          ? "All"
          : appliedFilters.monthYear[0],
      districts: appliedFilters.district,
    };
  };

  const fetchAndSetData = async (filters: MultiFilters) => {
    setIsLoading(true);
    setShowCharts(false);
    try {
      const { collection, query, where, getDocs } =
        await import("firebase/firestore");
      const { db } = await import("../../../firebase");

      const priceDataRef = collection(db, "price_data");

      // Format filters for Firestore
      const firestoreMonths = filters.monthYear.map((my) => {
        const [m, y] = my.split("/");
        return `${y}-${m}`;
      });

      const promises: Promise<any>[] = [];

      // Strategy: Iterate over EACH selected month.
      for (const month of firestoreMonths) {
        const baseConstraints = [
          where("price_type", "==", priceType),
          where("year_month", "==", month),
        ];

        // ---------------------------------------------------------
        // CASE A: Specific Districts Selected (Priority: District)
        // If districts are selected, we strictly fetch by District.
        // We IGNORE province constraints to avoid conflicts and optimize "in" usage.
        // ---------------------------------------------------------
        if (filters.district.length > 0) {
          const CHUNK_SIZE = 30;
          for (let i = 0; i < filters.district.length; i += CHUNK_SIZE) {
            const distChunk = filters.district.slice(i, i + CHUNK_SIZE);
            const isMultiDist = distChunk.length > 1;

            if (isMultiDist) {
              // Used 'in' for District -> Cannot use 'in' for Type
              const chunkBase = [
                ...baseConstraints,
                where("district", "in", distChunk),
              ];

              if (filters.realEstateType.length > 1) {
                // Must iterate types
                for (const type of filters.realEstateType) {
                  promises.push(
                    getDocs(
                      query(
                        priceDataRef,
                        ...chunkBase,
                        where("bds_type", "==", type),
                      ),
                    ),
                  );
                }
              } else {
                // Single type
                const typeC =
                  filters.realEstateType.length === 1
                    ? [where("bds_type", "==", filters.realEstateType[0])]
                    : [];
                promises.push(
                  getDocs(query(priceDataRef, ...chunkBase, ...typeC)),
                );
              }
            } else {
              // Single District (==) -> Can use 'in' for Type
              const chunkBase = [
                ...baseConstraints,
                where("district", "==", distChunk[0]),
              ];

              if (filters.realEstateType.length > 1) {
                const TYPE_SIZE = 30;
                for (
                  let t = 0;
                  t < filters.realEstateType.length;
                  t += TYPE_SIZE
                ) {
                  const typeChunk = filters.realEstateType.slice(
                    t,
                    t + TYPE_SIZE,
                  );
                  promises.push(
                    getDocs(
                      query(
                        priceDataRef,
                        ...chunkBase,
                        where("bds_type", "in", typeChunk),
                      ),
                    ),
                  );
                }
              } else {
                const typeC =
                  filters.realEstateType.length === 1
                    ? [where("bds_type", "==", filters.realEstateType[0])]
                    : [];
                promises.push(
                  getDocs(query(priceDataRef, ...chunkBase, ...typeC)),
                );
              }
            }
          }
        }
        // ---------------------------------------------------------
        // CASE B: No District Selected (Priority: Province)
        // Fetch "All" district records (summary) for the selected provinces.
        // ---------------------------------------------------------
        else {
          const isMultiCity = filters.city.length > 1;
          const isSingleCity = filters.city.length === 1;

          // Constraint: District must be 'All' when fetching province-level summary
          const provBase = [...baseConstraints, where("district", "==", "All")];

          if (isMultiCity) {
            // Used 'in' for Province -> Cannot use 'in' for Type
            const CHUNK_SIZE = 30;
            for (let i = 0; i < filters.city.length; i += CHUNK_SIZE) {
              const cityChunk = filters.city.slice(i, i + CHUNK_SIZE);
              const cityBase = [
                ...provBase,
                where("province", "in", cityChunk),
              ];

              if (filters.realEstateType.length > 1) {
                for (const type of filters.realEstateType) {
                  promises.push(
                    getDocs(
                      query(
                        priceDataRef,
                        ...cityBase,
                        where("bds_type", "==", type),
                      ),
                    ),
                  );
                }
              } else {
                const typeC =
                  filters.realEstateType.length === 1
                    ? [where("bds_type", "==", filters.realEstateType[0])]
                    : [];
                promises.push(
                  getDocs(query(priceDataRef, ...cityBase, ...typeC)),
                );
              }
            }
          } else if (isSingleCity) {
            // Single Province (==) -> Can use 'in' for Type
            const cityBase = [
              ...provBase,
              where("province", "==", filters.city[0]),
            ];

            if (filters.realEstateType.length > 1) {
              const TYPE_SIZE = 30;
              for (
                let t = 0;
                t < filters.realEstateType.length;
                t += TYPE_SIZE
              ) {
                const typeChunk = filters.realEstateType.slice(
                  t,
                  t + TYPE_SIZE,
                );
                promises.push(
                  getDocs(
                    query(
                      priceDataRef,
                      ...cityBase,
                      where("bds_type", "in", typeChunk),
                    ),
                  ),
                );
              }
            } else {
              const typeC =
                filters.realEstateType.length === 1
                  ? [where("bds_type", "==", filters.realEstateType[0])]
                  : [];
              promises.push(
                getDocs(query(priceDataRef, ...cityBase, ...typeC)),
              );
            }
          } else {
            // No city selected? With current UI validation this shouldn't happen usually.
            // But if it does, we just fetch global 'All' district records?
            // Or maybe strict return. For safety, adhere to logic B structure if simple.
            // (Leaving this fallback minimal or implicit if desired)
          }
        }
      }

      const snapshots = await Promise.all(promises);
      const allRaw = snapshots.flatMap((snap) =>
        snap.docs.map((doc: any) => doc.data()),
      );

      const parsed = allRaw.map((d) => {
        const [y, m] = d.year_month.split("-");
        return {
          fullDate: d.updated_at?.toDate() || new Date(),
          month: `${m}/${y}`,
          year: parseInt(y),
          city: d.province,
          district: d.district,
          type: d.bds_type,
          price: d.avg_price_million || 0,
        } as RealEstateRecord;
      });

      setRealData(parsed);
      setInitialDataLoaded(true);
    } catch (e) {
      console.error("Error fetching price data:", e);
    } finally {
      setIsLoading(false);
      setShowCharts(true);
    }
  };

  React.useEffect(() => {
    if (!initialDataLoaded) {
      fetchAndSetData(appliedFilters);
    }
  }, [initialDataLoaded]);

  const handleShowResults = (applied: MultiFilters) => {
    setAppliedFilters(applied);
    setIsLoading(true);
    setShowCharts(false);
    void fetchAndSetData(applied);
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <style>{pageStyles}</style>
      <style>{`
        .loader-glass { backdrop-filter: blur(6px); }
        .loader-pulse { animation: pulse 1.6s ease-in-out infinite; }
        @keyframes pulse { 0% { transform: scale(1); opacity: 1 } 50% { transform: scale(0.96); opacity: 0.75 } 100% { transform: scale(1); opacity: 1 } }
      `}</style>

      <div className="max-w-6xl mt-30 mx-auto">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold">{pageTitle}</h1>
          {unitText && (
            <p className="text-gray-500 text-sm mt-2 italic">{unitText}</p>
          )}
        </div>

        <FiltersContainer
          filters={appliedFilters}
          onShowResults={handleShowResults}
          realEstateTypes={realEstateTypes}
          monthYears={monthYears}
        />

        {isLoading && (
          <div
            className="flex items-center justify-center my-8"
            role="status"
            aria-live="polite"
          >
            <div className="flex items-center space-x-4 p-6 bg-white rounded-2xl shadow-lg loader-glass">
              <div className="w-14 h-14 rounded-full border-4 border-gray-100 flex items-center justify-center">
                <div className="w-9 h-9 rounded-full loader-pulse bg-gradient-to-r from-blue-500 to-teal-400 shadow-md" />
              </div>
              <div>
                <div className="text-lg font-medium">Loading</div>
              </div>
            </div>
          </div>
        )}

        <div className="transition-opacity duration-300">
          {showCharts ? (
            <ChartsSection
              filters={toSingleFilters()}
              data={filteredData}
              colorMap={BDS_colorMap as any}
              priceUnit={priceUnit}
            />
          ) : (
            <div className="h-6" aria-hidden />
          )}
        </div>
      </div>
    </div>
  );
}
