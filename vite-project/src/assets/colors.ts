export const BDS_colorMap = {
  "Căn hộ chung cư": "#3B82F6", // xanh dương
  "Nhà biệt thự / Nhà liền kề": "#9333EA", // tím đậm
  "Nhà phố": "#F59E0B", // vàng cam
  Đất: "#10B981", // xanh ngọc
  "Nhà ở": "#993300", // nâu
  "Nhà trọ": "#3325b3ff", //
} as const;

export const priceColorMap = {
  "<3 tỷ": "#60A5FA", // xanh dương nhạt (giá thấp)
  "3-5 tỷ": "#34D399", // xanh lá (thân thiện, giá phổ biến)
  "5-7 tỷ": "#FACC15", // vàng (giữa thang)
  "7-10 tỷ": "#FB923C", // cam (bắt đầu cao)
  "10-15 tỷ": "#F87171", // đỏ nhạt (cao)
  "15-20 tỷ": "#A855F7", // tím (rất cao, luxury feel)
  ">20 tỷ": "#0000AA", // xanh đen đậm (luxury/premium)
} as const;
