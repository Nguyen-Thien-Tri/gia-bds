import { LucideIcon } from "lucide-react";

export interface StatItem {
  id: number;
  Icon: LucideIcon;
  value: string;
  label: string;
  change: string;
  positive: boolean;
}

export interface StatCardProps {
  Icon: LucideIcon;
  value: string;
  label: string;
  change: string;
  positive?: boolean;
  loading?: boolean;
}

export interface ProvinceDropdownProps {
  value: string;
  onChange: (value: string) => void;
  options?: string[];
}

export type PrebinnedItem = {
  range: string;
  Giá: number | null;
};

export type PieItem = {
  label: string;
  value: number;
};

export type RegionItem = {
  name: string;
  value: number;
  province?: string;
};
