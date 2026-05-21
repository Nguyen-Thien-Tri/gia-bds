import React, { useState, useEffect } from "react";

const UserTestimonials = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const testimonials = [
    {
      id: 1,
      text: "Website giúp tôi tiết kiệm rất nhiều thời gian khi tìm kiếm nhà ở. Với các biểu đồ trực quan, tôi có thể so sánh giá nhà giữa các quận với nhau một cách nhanh chóng và đưa ra quyết định tìm mua dễ dàng hơn!",
      author: "Nguyễn Văn Huy",
      location: "Hà Nội",
      avatar: "/Lê Hoàng Nam.jpg",
    },
    {
      id: 2,
      text: "Trang web này không chỉ hữu ích cho người mua mà còn cho cả người bán. Tôi đã có thể tìm được người mua nhà trong thời gian ngắn hơn nhờ thông tin giá bất động sản rõ ràng từ website.",
      author: "Đỗ Minh Tú",
      location: "Hải Phòng",
      avatar: "/Đỗ Minh Tú.jpg",
    },
  ];

  return (
    <div className="xl:container max-w-6xl mx-auto px-4 py-12 bg-gradient-to-br from-slate-50 to-blue-50 relative">
      <div
        className={`transition-all duration-1000 ${
          isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
        }`}
      >
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-800 mb-4">
            Đánh giá từ người dùng
          </h2>
          <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-purple-500 mx-auto rounded-full"></div>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={testimonial.id}
              className={`group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-200 border border-slate-100 hover:border-blue-200 transform hover:-translate-y-2 flex flex-col min-h-[300px] ${
                isVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-8"
              }`}
            >
              {/* Quote Icon */}
              <div className="p-8 pb-4">
                <div className="mb-6">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <svg
                      className="w-6 h-6 text-white"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h4v10h-10z" />
                    </svg>
                  </div>
                </div>

                {/* Testimonial Text */}
                <blockquote className="text-slate-700 text-lg leading-relaxed group-hover:text-slate-800 transition-colors duration-300">
                  "{testimonial.text}"
                </blockquote>
              </div>

              {/* Fixed Bottom Section */}
              <div className="mt-auto p-8 pt-4">
                {/* Author Info */}
                <div className="flex items-center mb-4">
                  <div className="relative">
                    <img
                      src={testimonial.avatar}
                      alt={testimonial.author}
                      className="w-14 h-14 rounded-full object-cover ring-4 ring-white shadow-md group-hover:ring-blue-100 transition-all duration-300"
                    />
                  </div>
                  <div className="ml-4">
                    <h4 className="font-semibold text-slate-800 group-hover:text-blue-700 transition-colors duration-300">
                      {testimonial.author}
                    </h4>
                    <p className="text-slate-500 text-sm flex items-center">
                      <svg
                        className="w-4 h-4 mr-1 text-slate-400"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                      </svg>
                      {testimonial.location}
                    </p>
                  </div>
                </div>

                {/* Rating Stars */}
                <div className="flex justify-end">
                  <div className="flex space-x-1">
                    {[...Array(5)].map((_, i) => (
                      <svg
                        key={i}
                        className="w-5 h-5 text-yellow-400 group-hover:text-yellow-500 transition-colors duration-300"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Floating Elements */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-blue-200 rounded-full opacity-20 animate-pulse"></div>
      <div className="absolute bottom-20 right-10 w-16 h-16 bg-purple-200 rounded-full opacity-20 animate-pulse delay-1000"></div>
    </div>
  );
};

export default UserTestimonials;
