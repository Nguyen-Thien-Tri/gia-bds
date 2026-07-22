import React, { useEffect, useRef, useState, useMemo } from "react";
import { Info } from "lucide-react";
import FilterHeaderFunnel from "../../../components/FilterHeaderFunnel";
import { provinceDict } from "../../../assets/geo";

// --- Types ---
export type MultiFilters = {
  city: string[];
  district: string[];
  realEstateType: string[];
  monthYear: string[];
};

interface FilterOption {
  value: string;
  label: string;
}

interface MultiSelectFilterProps {
  name: keyof MultiFilters;
  label: string;
  options: FilterOption[];
  selectedValues: string[];
  placeholder?: string;
  onChange: (filterName: keyof MultiFilters, values: string[]) => void;
  showSearch?: boolean;
  disabled?: boolean;
  maxSelection?: number;
  error?: string | boolean;
}

// --- Component: MultiSelectFilter ---
export function MultiSelectFilter({
  name,
  label,
  options,
  selectedValues,
  placeholder = "Select...",
  onChange,
  showSearch = true,
  disabled = false,
  maxSelection,
  error,
}: MultiSelectFilterProps): React.JSX.Element {
  const MAX_SELECTION =
    typeof maxSelection === "number" && !Number.isNaN(maxSelection)
      ? Math.max(0, Math.floor(maxSelection))
      : Infinity;

  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const [blockedOption, setBlockedOption] = useState<string | null>(null);
  const blockedTimeoutRef = useRef<number | null>(null);

  const showBlockedOnOption = (value: string) => {
    setBlockedOption(value);
    if (blockedTimeoutRef.current)
      window.clearTimeout(blockedTimeoutRef.current);
    blockedTimeoutRef.current = window.setTimeout(() => {
      setBlockedOption(null);
      blockedTimeoutRef.current = null;
    }, 2000);
  };

  const totalCount = options.length;
  const selectedCount = selectedValues.length;
  const allSelected = selectedCount === totalCount && totalCount > 0;

  const labelByValue = useMemo(() => {
    const m = new Map<string, string>();
    for (const o of options) m.set(o.value, o.label);
    return m;
  }, [options]);

  const selectedLabels = selectedValues.map((v) => labelByValue.get(v) ?? v);
  const showAllSelectedLabel =
    name === "city" && selectedCount > 0 && selectedCount === totalCount;

  const filteredOptions = useMemo(() => {
    if (!showSearch) return options;
    const q = searchTerm.trim().toLowerCase();
    if (!q) return options;
    return options.filter((o) => o.label.toLowerCase().includes(q));
  }, [options, searchTerm, showSearch]);

  const handleToggleOption = (value: string) => {
    if (disabled) return;
    const isSelected = selectedValues.includes(value);
    if (isSelected) {
      onChange(
        name,
        selectedValues.filter((v) => v !== value),
      );
      return;
    }
    if (selectedValues.length >= MAX_SELECTION) {
      showBlockedOnOption(value);
      return;
    }
    onChange(name, [...selectedValues, value]);
  };

  const handleRemoveValue = (e: React.MouseEvent, value: string) => {
    e.stopPropagation();
    if (disabled) return;
    onChange(
      name,
      selectedValues.filter((v) => v !== value),
    );
  };

  const handleClearAll = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (disabled) return;
    onChange(name, []);
  };

  const handleToggleSelectAll = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (disabled) return;
    if (allSelected) {
      onChange(name, []);
    } else {
      let allValues = options.map((o) => o.value);
      if (Number.isFinite(MAX_SELECTION))
        allValues = allValues.slice(0, MAX_SELECTION);
      onChange(name, allValues);
    }
  };

  const handleSelectVisible = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (disabled) return;
    const visibleValues = filteredOptions.map((o) => o.value);
    const combined = [...selectedValues];
    for (const v of visibleValues) {
      if (combined.includes(v)) continue;
      if (combined.length >= MAX_SELECTION) break;
      combined.push(v);
    }
    onChange(name, combined);
  };

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(e.target as Node)) setIsOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      if (blockedTimeoutRef.current)
        window.clearTimeout(blockedTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    if (!isOpen) setSearchTerm("");
  }, [isOpen]);

  const liveMessage = useMemo(() => {
    if (showAllSelectedLabel) return `${label ?? name}: Tất cả.`;
    if (selectedCount === 0) return `${label ?? name}: chưa chọn mục nào.`;
    if (selectedCount === 1) return `${label ?? name}: ${selectedLabels[0]}.`;
    return `${label ?? name}: ${selectedCount} mục đã chọn.`;
  }, [selectedCount, selectedLabels, label, name, showAllSelectedLabel]);

  return (
    <div className="relative" ref={containerRef}>
      <div
        onClick={() => !disabled && setIsOpen((s) => !s)}
        onKeyDown={(e) => {
          if (disabled) {
            if (e.key === "Escape") setIsOpen(false);
            return;
          }
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsOpen((s) => !s);
          } else if (e.key === "Escape") {
            setIsOpen(false);
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-disabled={disabled}
        aria-invalid={Boolean(error)}
        className={`w-full p-2 border rounded-lg bg-white shadow-sm focus:outline-none focus:border-blue-300 focus:ring-2 focus:ring-blue-300 flex justify-between items-center min-h-[44px] transition-shadow duration-150 ${
          disabled
            ? "opacity-60 cursor-not-allowed text-gray-400"
            : "cursor-pointer"
        } ${error ? "border-red-500" : "border-slate-300"}`}
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {selectedCount === 0 ? (
            <span className="text-gray-500">{placeholder}</span>
          ) : showAllSelectedLabel ? (
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="inline-flex items-center gap-2 text-xs px-2 py-1 rounded-full bg-blue-100 border border-blue-300 text-blue-700 select-none"
                onClick={(e) => e.stopPropagation()}
              >
                <span className="max-w-[10rem] truncate">Tất cả</span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearAll();
                  }}
                  className="ml-1 inline-flex items-center justify-center w-5 h-5 rounded-full bg-white text-gray-600 hover:text-gray-700 cursor-pointer overflow-hidden"
                >
                  <span className="leading-none pb-[2px]">×</span>
                </button>
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 min-w-0 flex-wrap">
              {selectedLabels.map((lbl, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-2 text-xs px-2 py-1 rounded-full bg-blue-100 border border-blue-300 text-blue-700 select-none"
                  onClick={(e) => e.stopPropagation()}
                >
                  <span className="max-w-[10rem] truncate">{lbl}</span>
                  <button
                    type="button"
                    onClick={(e) => handleRemoveValue(e, selectedValues[i])}
                    className="ml-1 inline-flex items-center justify-center w-5 h-5 rounded-full bg-white text-gray-600 hover:text-gray-700 cursor-pointer overflow-hidden"
                  >
                    <span className="leading-none pb-[2px]">×</span>
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
        <svg
          className={`w-4 h-4 transition-transform duration-150 ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>

      {isOpen && !disabled && (
        <div className="absolute z-20 w-full mt-2 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto ring-1 ring-black ring-opacity-5">
          <div className="p-2 border-b flex flex-col gap-2">
            <div className="flex justify-between items-center gap-2">
              <button
                onClick={handleToggleSelectAll}
                type="button"
                className="flex items-center gap-2 text-sm px-2 py-1 rounded hover:bg-gray-100"
              >
                <span
                  className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                    allSelected
                      ? "bg-blue-600 border-blue-600"
                      : "bg-white border-gray-500"
                  }`}
                >
                  {allSelected && <CheckIcon />}
                </span>
                <span className="text-gray-700">Chọn tất cả</span>
                <span className="text-xs text-gray-500 ml-1">
                  {" "}
                  {selectedCount} Đã chọn{" "}
                </span>
                {Number.isFinite(MAX_SELECTION) && (
                  <span className="text-xs text-gray-500 ml-2">
                    {" "}
                    · Tối đa {MAX_SELECTION}{" "}
                  </span>
                )}
              </button>
              {selectedCount > 0 && (
                <button
                  onClick={handleClearAll}
                  className="text-xs px-3 py-1 rounded-md text-gray-600 border border-gray-300 hover:bg-blue-50"
                >
                  Bỏ chọn
                </button>
              )}
            </div>
            {showSearch && (
              <div className="flex items-center gap-2">
                <input
                  ref={inputRef}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder={`Tìm ${label.toLowerCase()}`}
                  className="flex-1 text-sm p-2 border rounded focus:ring-1 focus:ring-blue-300"
                />
                {searchTerm.trim().length > 0 && (
                  <button
                    onClick={handleSelectVisible}
                    className="text-xs px-3 py-1 rounded-md border border-gray-300 hover:bg-blue-50"
                  >
                    Chọn trang
                  </button>
                )}
              </div>
            )}
          </div>
          <div>
            {filteredOptions.length === 0 ? (
              <div className="p-3 text-sm text-gray-500">Không có kết quả</div>
            ) : (
              filteredOptions.map((option) => {
                const checked = selectedValues.includes(option.value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleToggleOption(option.value)}
                    className="flex items-center p-2 hover:bg-gray-100 w-full text-left gap-3"
                  >
                    <span
                      className={`flex-shrink-0 w-5 h-5 rounded-full border flex items-center justify-center ${
                        checked
                          ? "bg-blue-600 border-blue-600"
                          : "bg-white border-gray-500"
                      }`}
                    >
                      {checked && <CheckIcon />}
                    </span>
                    <span className="flex-1">{option.label}</span>
                    {blockedOption === option.value && (
                      <span className="text-xs text-red-600">
                        Đã đạt giới hạn
                      </span>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
      <div className="sr-only" aria-live="polite">
        {liveMessage}
      </div>
      {error && (
        <p className="mt-1 text-xs text-red-600">
          {typeof error === "string" ? error : "Vui lòng chọn ít nhất 1 mục."}
        </p>
      )}
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

// --- Component: FiltersContainer ---
interface FiltersContainerProps {
  filters: MultiFilters;
  onChange?: (filterName: keyof MultiFilters, values: string[]) => void;
  onShowResults: (appliedFilters: MultiFilters) => void;
  realEstateTypes?: string[];
  monthYears?: string[];
}

export function FiltersContainer({
  filters,
  onChange,
  onShowResults,
  realEstateTypes = [],
  monthYears = [],
}: FiltersContainerProps): React.JSX.Element {
  // 1. Cooldown state (seconds)
  const [cooldown, setCooldown] = useState(0);

  // 2. Timer effect for countdown
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  const pickCurrentMonthOption = (opts?: string[]): string | null => {
    if (!opts || opts.length === 0) return null;
    const now = new Date();
    const displayDate = new Date(now);
    if (now.getDate() <= 15) {
      displayDate.setMonth(displayDate.getMonth() - 1);
    }
    const mm = String(displayDate.getMonth() + 1).padStart(2, "0");
    const yyyy = String(displayDate.getFullYear());
    return opts.find((o) => o.includes(mm) && o.includes(yyyy)) ?? null;
  };

  const citiesFromGeo = useMemo(() => {
    const priority = [
      "Hà Nội",
      "Hồ Chí Minh",
      "Bình Dương",
      "Đà Nẵng",
      "Khánh Hòa",
      "Đồng Nai",
      "Hải Phòng",
      "Bà Rịa Vũng Tàu",
    ];
    const allKeys = Object.keys(provinceDict as Record<string, string[]>);
    const otherProvinces = allKeys
      .filter((p) => !priority.includes(p))
      .sort((a, b) => a.localeCompare(b, "vi"));
    return [...priority, ...otherProvinces];
  }, []);
  const districtsByProvince = useMemo(() => {
    return provinceDict as Record<string, string[]>;
  }, []);

  const toOptions = (arr: string[]) => arr.map((v) => ({ value: v, label: v }));

  const initialDraft = useMemo<MultiFilters>(() => {
    const base: MultiFilters = {
      city: filters.city ?? [],
      district: filters.district ?? [],
      realEstateType: filters.realEstateType ?? [],
      monthYear: filters.monthYear ?? [],
    };
    if (!base.monthYear.length && monthYears.length) {
      const pick = pickCurrentMonthOption(monthYears);
      if (pick) base.monthYear = [pick];
    }
    return base;
  }, [monthYears]);

  const [draft, setDraft] = useState<MultiFilters>(initialDraft);
  const [errors, setErrors] = useState<
    Partial<Record<keyof MultiFilters, string>>
  >({});

  useEffect(() => {
    setDraft((prev) => ({
      city: filters.city ?? prev.city,
      district: filters.district ?? prev.district,
      realEstateType: filters.realEstateType ?? prev.realEstateType,
      monthYear: filters.monthYear ?? prev.monthYear,
    }));
  }, [filters]);

  // District is disabled only if NO city is selected
  const districtDisabled = draft.city.length === 0;

  // Get all available districts from ALL selected cities
  const availableDistricts = useMemo(() => {
    if (draft.city.length === 0) return [];
    const allDistricts = draft.city.flatMap(
      (city) => districtsByProvince[city] || [],
    );
    // Remove duplicates if any (though usually districts are unique per province,
    // but names might collide if we didn't track province.
    // For now we assume unique names or acceptable collision since UI is simple string match)
    return Array.from(new Set(allDistricts)).sort((a, b) =>
      a.localeCompare(b, "vi"),
    );
  }, [draft.city, districtsByProvince]);

  useEffect(() => {
    // If no city, clear districts
    if (draft.city.length === 0) {
      if (draft.district.length > 0) {
        setDraft((prev) => ({ ...prev, district: [] }));
      }
      return;
    }

    // If we have cities, ensure selected districts are valid for those cities
    const allowed = new Set(availableDistricts);
    const filtered = draft.district.filter((d) => allowed.has(d));

    if (filtered.length !== draft.district.length) {
      setDraft((prev) => ({ ...prev, district: filtered }));
    }
  }, [draft.city, availableDistricts]);

  const handleLocalChange = (
    filterName: keyof MultiFilters,
    values: string[],
  ) => {
    setDraft((prev) => ({ ...prev, [filterName]: values }));
    if (filterName === "city" && onChange) onChange(filterName, values);
    setErrors((prev) => {
      const next = { ...prev };
      if (values.length > 0) delete next[filterName];
      // We no longer require district to be selected if city is selected
      // But if we wanted to clear district error when it's valid, we can do:
      if (filterName === "district" && values.length > 0)
        delete next["district"];
      // Also clear district error if city changes (since options change)
      if (filterName === "city") delete next["district"];
      return next;
    });
  };

  const handleApply = () => {
    // 3. Block execution if cooldown is active
    if (cooldown > 0) return;

    const nextErrors: Partial<Record<keyof MultiFilters, string>> = {};
    if (!draft.city.length)
      nextErrors.city = "Vui lòng chọn ít nhất 1 tỉnh/thành phố.";
    // REMOVED requirement for district selection
    // if (!districtDisabled && !draft.district.length)
    //   nextErrors.district = "Vui lòng chọn ít nhất 1 quận/huyện.";
    if (!draft.realEstateType.length)
      nextErrors.realEstateType = "Vui lòng chọn ít nhất 1 loại BĐS.";
    if (!draft.monthYear.length)
      nextErrors.monthYear = "Vui lòng chọn ít nhất 1 tháng.";

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    // 4. Success logic and set 10s cooldown
    onShowResults(draft);
    setCooldown(5);
  };

  const activeCount =
    draft.city.length +
    draft.district.length +
    draft.realEstateType.length +
    draft.monthYear.length;

  return (
    <div className="mb-10 p-6 bg-white rounded-lg border border-blue-200 shadow-lg">
      <FilterHeaderFunnel
        title="Bộ lọc"
        activeCount={activeCount}
        onClick={() => {}}
      />

      <div className="grid grid-cols-1 gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tỉnh/Thành phố
          </label>
          <MultiSelectFilter
            name="city"
            label="Tỉnh/Thành phố"
            options={toOptions(citiesFromGeo)}
            selectedValues={draft.city}
            placeholder="Chọn tỉnh/thành phố"
            onChange={handleLocalChange}
            maxSelection={10}
            error={errors.city}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quận/Huyện
          </label>
          <MultiSelectFilter
            name="district"
            label="Quận/Huyện"
            options={toOptions(districtDisabled ? [] : availableDistricts)}
            selectedValues={draft.district}
            placeholder={
              districtDisabled
                ? "Chọn tỉnh/thành phố để chọn quận/huyện"
                : "Chọn quận/huyện, hoặc bỏ qua nếu bạn muốn xem theo tỉnh thành"
            }
            onChange={handleLocalChange}
            disabled={districtDisabled}
            maxSelection={10}
            error={errors.district}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Loại bất động sản
          </label>
          <MultiSelectFilter
            name="realEstateType"
            label="Loại BĐS"
            options={toOptions(realEstateTypes)}
            selectedValues={draft.realEstateType}
            placeholder="Chọn loại bất động sản"
            onChange={handleLocalChange}
            showSearch={false}
            maxSelection={3}
            error={errors.realEstateType}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Thời gian (tháng)
          </label>
          <MultiSelectFilter
            name="monthYear"
            label="Tháng/Năm"
            options={toOptions(monthYears)}
            selectedValues={draft.monthYear}
            placeholder="Chọn tháng/năm"
            onChange={handleLocalChange}
            showSearch={false}
            // maxSelection={6}
            error={errors.monthYear}
          />
        </div>

        <div className="flex items-center justify-center gap-2 w-full">
          <button
            onClick={handleApply}
            disabled={cooldown > 0}
            className={`cursor-pointer w-36 font-semibold py-2 px-4 rounded-lg transition-all duration-300 shadow 
              ${
                cooldown > 0
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-600 hover:to-cyan-600 hover:shadow-lg"
              }`}
          >
            {cooldown > 0 ? `Xem (${cooldown}s)` : "Xem"}
          </button>

          <div
            className="group relative flex items-center outline-none"
            tabIndex={0}
            role="button"
            aria-label="Thông tin bổ sung"
          >
            <Info className="w-5 h-5 text-gray-400 group-hover:text-gray-600 group-focus:text-gray-600 cursor-help transition-colors" />
            <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-48 p-2 bg-gray-800 text-white text-xs rounded-md shadow-lg opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-opacity duration-200 pointer-events-none z-50 text-center">
              Một số vùng có thể không hiển thị do không có dữ liệu
              <div className="absolute top-full left-1/2 -ml-1 border-4 border-transparent border-t-gray-800"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
