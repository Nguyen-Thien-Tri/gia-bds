export const range = (start: number, stop: number, step: number) => {
  const arr = [];
  for (let i = start; i < stop; i += step) {
    arr.push(i);
  }
  return arr;
};

export const CHCC_BINS = [
  0, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240,
];
export const LAND_BINS = [
  0,
  ...range(40, 501, 20),
  ...range(600, 3001, 100),
  ...range(3500, 8001, 500),
];
export const NHA_O_BINS = [0, 30, ...range(60, 401, 20)];

export function generateAreaLabels(bins: number[]) {
  const labels = [];
  for (let i = 0; i < bins.length - 1; i++) {
    if (i === 0 && bins[i] === 0) {
      labels.push(`< ${bins[i + 1]}m²`);
    } else {
      labels.push(`${bins[i]}-${bins[i + 1]}m²`);
    }
  }
  labels.push(`> ${bins[bins.length - 1]}m²`);
  return labels;
}

export const APARTMENT_AREA_LABELS = generateAreaLabels(CHCC_BINS);
export const HOUSE_AREA_LABELS = generateAreaLabels(NHA_O_BINS);
export const LAND_AREA_LABELS = generateAreaLabels(LAND_BINS);

export const PRICE_RANGES = [
  "<3 tỷ",
  "3-5 tỷ",
  "5-7 tỷ",
  "7-10 tỷ",
  "10-15 tỷ",
  "15-20 tỷ",
  ">20 tỷ",
];

export const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 },
  },
};

export const cardVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: "spring", stiffness: 100, damping: 10 },
  },
} as const;
