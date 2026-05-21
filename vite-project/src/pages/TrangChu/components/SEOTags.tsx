import React from "react";

const SEOTags: React.FC = () => {
  const provinces = [
    "Hà Nội",
    "Hồ Chí Minh",
    "Bình Dương",
    "Đà Nẵng",
    "Khánh Hòa",
    "Đồng Nai",
    "Hải Phòng",
    "Bà Rịa Vũng Tàu",
  ];

  const types = ["nhà", "căn hộ chung cư", "đất"];

  const tags: string[] = [];

  // Generating combinations
  types.forEach((type) => {
    provinces.forEach((province) => {
      tags.push(`giá ${type} tại ${province}`);
    });
  });

  return (
    <section className="py-8 md:py-10 px-4 md:px-5 bg-slate-50 border-t border-slate-200">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-xl font-semibold text-slate-800 mb-5 text-center">
          Tìm kiếm phổ biến
        </h2>
        <div className="flex flex-wrap gap-3 justify-center">
          {tags.map((tag, index) => (
            <span
              key={index}
              className="inline-block py-1 md:py-1.5 px-2.5 md:px-3.5 bg-white border border-slate-200 rounded-full text-[13px] md:text-sm text-slate-600 transition-all duration-200 ease-in-out cursor-default hover:bg-blue-50 hover:border-blue-400 hover:text-blue-600 hover:-translate-y-0.5 hover:shadow-sm"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SEOTags;
