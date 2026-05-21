import React, { useState, useRef, useEffect, JSX } from "react";
import { Filter } from "lucide-react";
import { ProvinceDropdownProps } from "./types";

export default function ProvinceDropdown({
  value,
  onChange,
  options = [],
}: ProvinceDropdownProps): React.JSX.Element {
  const [open, setOpen] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent): void {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent): void {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div ref={containerRef} className="relative w-50">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="hover:cursor-pointer w-full text-left bg-white border border-slate-300 rounded-xl px-4 py-2 pr-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition flex items-center justify-between"
      >
        <div className="flex items-center min-w-0">
          <Filter className="w-4 h-4 mr-3 text-slate-500 flex-shrink-0" />
          <span className="truncate">{value}</span>
        </div>
        <span className="ml-3 text-slate-500 transform transition-transform duration-200">
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label="Tỉnh/thành phố"
          tabIndex={-1}
          className="absolute z-20 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-lg overflow-auto max-h-44 py-1"
        >
          {options.map((opt: string) => {
            const selected = opt === value;
            return (
              <li key={opt}>
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  onClick={() => {
                    onChange(opt);
                    setOpen(false);
                  }}
                  className={`hover:cursor-pointer w-full text-left px-4 py-2 text-sm hover:bg-slate-200 focus:bg-slate-50 transition flex items-center ${
                    selected ? "bg-blue-100 font-semibold" : "text-slate-700"
                  }`}
                >
                  <span className="truncate">{opt}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
