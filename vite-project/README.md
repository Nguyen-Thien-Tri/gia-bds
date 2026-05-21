# Real Estate Website Project

Một dự án website bất động sản được xây dựng với React, TypeScript và Vite.

## 🚀 Công nghệ sử dụng (Tech Stack)

- **Frontend Framework**: React 19 (với Vite)
- **Ngôn ngữ**: TypeScript
- **Styling**: Tailwind CSS v4, Framer Motion (cho animations)
- **Icons**: Lucide React
- **Routing**: React Router DOM
- **Biểu đồ**: Chart.js, Recharts
- **API/HTTP**: Axios
- **Backend/BaaS**: Firebase
- **SEO/Meta tags**: React Helmet Async
- **Thông báo (Toast)**: React Hot Toast

## 📁 Cấu trúc dự án cơ bản

- `src/` - Chứa mã nguồn chính của ứng dụng.
  - `pages/` - Các trang của ứng dụng (VD: Trang chủ, Tìm kiếm, Chi tiết...).
  - `components/` - Các thành phần giao diện dùng chung (UI components).
- `public/` - Các tệp tĩnh như hình ảnh, favicon.
- `firebase.json` & `.firebaserc` - Cấu hình triển khai và thiết lập Firebase.

## 🗺️ Các Trang (Pages & Chức năng)

Website được điều hướng qua `react-router-dom` và hiện bao gồm **4 trang đang hoạt động**:

---

### 1. 🏠 Trang chủ (`/`)

Trang chính của website, được ghép từ nhiều section độc lập theo thứ tự dọc trang:

| Section | Mô tả |
|---|---|
| **HeroSection** | Banner chính hiển thị tiêu đề, mô tả và 4 thống kê tổng quan thị trường (số dự án, số BĐS đăng bán, giá trị ước tính, trung bình giá căn hộ chung cư). Dữ liệu được kéo trực tiếp từ **Firebase Firestore**, cập nhật theo tháng. Bao gồm nút kêu gọi hành động (CTA) đăng ký nhận bản tin và biểu đồ Pie nhỏ minh họa. |
| **BarChartsSection** | Hiển thị các biểu đồ cột so sánh giá BĐS giữa các khu vực nổi bật. |
| **FeaturesSection** | Giới thiệu 2 tính năng nổi bật: **Phân Tích Thị Trường** (so sánh giá BĐS theo khu vực/quận/huyện) và **Lịch Sử Giá** (xem biến động giá theo thời gian), mỗi tính năng có nút "Khám phá" dẫn tới trang biểu đồ giá bán. |
| **TargetUsersSection** | Giới thiệu đối tượng người dùng mục tiêu (người mua/thuê nhà, nhà đầu tư, chuyên gia tài chính) và thống kê số tỉnh thành được phủ sóng (60+). |
| **AnalyticsSection** | Bảng điều khiển phân tích thị trường có thể lọc theo tỉnh/thành phố. Bao gồm: 4 thẻ thống kê chính (Dự án, BĐS bán, Giá trị, Giá CHCC), biểu đồ Area theo diện tích (căn hộ, nhà ở, đất), biểu đồ Pie phân bố mức giá, và top quận/huyện giá cao theo từng loại hình BĐS. |
| **UserTestimonials** | Phần hiển thị đánh giá/nhận xét từ người dùng. |

---

### 2. 📊 Biểu đồ giá bán (`/bieu-do-gia-ban`)

Trang phân tích chi tiết giá bất động sản **bán** tại Việt Nam.

**Đơn vị giá**: triệu VND/m²

**Bộ lọc đa chiều (MultiFilters):**
- 🏙️ **Tỉnh/Thành phố**: Chọn một hoặc nhiều tỉnh thành (mặc định: Hà Nội + TP. Hồ Chí Minh)
- 🏘️ **Quận/Huyện**: Lọc theo quận/huyện cụ thể của tỉnh thành đã chọn
- 🏠 **Loại hình BĐS**: Căn hộ chung cư, Nhà ở, Đất, Nhà phố, Biệt thự,...
- 📅 **Tháng/Năm**: Chọn một hoặc nhiều tháng để so sánh (dữ liệu từ tháng 12/2025 trở đi)

**Cách hoạt động**: Sau khi chọn bộ lọc và nhấn "Xem kết quả", dữ liệu được truy vấn từ collection `price_data` trên Firestore theo từng tổ hợp tháng–tỉnh/quận–loại hình BĐS. Kết quả được hiển thị dưới dạng biểu đồ trực quan.

---

### 3. 📊 Biểu đồ giá cho thuê (`/bieu-do-gia-cho-thue`)

Trang phân tích chi tiết giá bất động sản **cho thuê** tại Việt Nam. Sử dụng cùng component `SharedRealEstateAnalytics` với trang Biểu đồ giá bán, nhưng được cấu hình với `priceType="Cho thuê"` và tập hợp loại hình BĐS cho thuê riêng.

**Đơn vị giá**: triệu VND/tháng *(tương tự như trang giá bán nhưng áp dụng cho thuê)*

Bộ lọc và cách hoạt động tương tự trang **Biểu đồ giá bán**.

---

### 4. ❓ Câu hỏi thường gặp (`/cau-hoi-thuong-gap`)

Trang giải đáp câu hỏi (FAQ) với giao diện accordion tích hợp tìm kiếm và lọc theo chuyên mục.

**Tính năng:**
- 🔍 **Tìm kiếm toàn văn**: Tìm kiếm theo từ khóa trong câu hỏi, câu trả lời và chuyên mục
- 🗂️ **Lọc theo chuyên mục**: Hiện có các chuyên mục `Số liệu`, `Liên hệ`
- 🔗 **Sao chép deeplink**: Mỗi câu hỏi có nút sao chép liên kết trực tiếp (`#faq-id`)
- 📅 **Hiển thị ngày cập nhật** của từng câu hỏi
- ♿ **Tích hợp accessibility**: `aria-expanded`, `aria-controls`, `aria-pressed`
- 🤖 **SEO**: Tự động tạo JSON-LD schema `FAQPage` cho Google Search

---

### ⏳ Các trang đang phát triển (chưa ra mắt)

| Trang | Route | Ghi chú |
|---|---|---|
| **Về chúng tôi** | `/ve-chung-toi` | Component `AboutPage.tsx` đã có, đang bị comment trong routing |
| **Định giá BĐS** | `/dinh-gia-bat-dong-san` | Component `ValuationPage.tsx` đã có, đang bị comment trong routing |

---

## 🛠️ Hướng dẫn cài đặt và chạy dự án

### Yêu cầu hệ thống

- **Node.js**: Phiên bản 18 trở lên (Khuyến nghị 20.x hoặc mới nhất)

### Các bước cài đặt

1. **Cài đặt các thư viện phụ thuộc:**
   Trong thư mục gốc của dự án, mở terminal và chạy:

   ```bash
   npm install
   ```

2. **Chạy Development Server:**

   ```bash
   npm run dev
   ```

   Ứng dụng sẽ khả dụng tại URL hiển thị trên terminal (thường là `http://localhost:5173/`).

3. **Build dự án cho Production:**

   ```bash
   npm run build
   ```

   Sản phẩm sau khi build sẽ nằm trong thư mục `dist/`.

4. **Kiểm tra lỗi (Linting):**
   ```bash
   npm run lint
   ```

## ⚙️ Thiết lập môi trường

Đảm bảo bạn đã cấu hình các biến môi trường của Firebase (nếu có) để kết nối đúng với cơ sở dữ liệu và dịch vụ Backend.
