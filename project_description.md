# Mô tả Dự án: Website Bất động sản

Dự án này là một nền tảng web hiện đại dành cho việc theo dõi, phân tích và tra cứu giá bất động sản tại Việt Nam.

## 🚀 Công nghệ sử dụng (Tech Stack)

Hệ thống được xây dựng trên các công nghệ tiên tiến nhất hiện nay:
- **Frontend**: React 19 (với Vite) đảm bảo hiệu suất cực cao và trải nghiệm mượt mà.
- **Ngôn ngữ**: TypeScript giúp mã nguồn chặt chẽ và dễ bảo trì.
- **Giao diện (Styling)**: Tailwind CSS v4 kết hợp với Framer Motion cho các hiệu ứng chuyển động (animations) cao cấp.
- **Dữ liệu & Backend**: Firebase (Firestore) cung cấp khả năng cập nhật dữ liệu thời gian thực.
- **Biểu đồ**: Chart.js và Recharts được sử dụng để trực quan hóa các dữ liệu phức tạp về giá nhà đất.

## 📁 Cấu trúc chính của dự án

- `src/`: Chứa toàn bộ logic và giao diện của ứng dụng.
- `firebase.json`: Cấu hình cho việc triển khai trên hạ tầng Google Cloud.
- `vite-project/`: Thư mục mã nguồn chính của web app.

## 🗺️ Các tính năng và trang chính

### 1. Trang chủ (Market Overview)
- Cung cấp cái nhìn tổng quan về thị trường bất động sản.
- Hiển thị các thống kê quan trọng: số lượng dự án, giá trị thị trường, và giá trung bình căn hộ.
- Bao gồm biểu đồ phân tích diện tích và các khu vực có giá cao nhất.

### 2. Phân tích giá bán & giá thuê
- Công cụ lọc đa chiều linh hoạt cho phép người dùng so sánh giá đất/nhà theo:
  - Tỉnh/Thành phố và Quận/Huyện.
  - Loại hình (Căn hộ, Nhà phố, Đất nền, Biệt thự...).
  - Thời gian (Biến động theo từng tháng).
- Dữ liệu được biểu diễn dưới dạng biểu đồ cột và đường, giúp dễ dàng nhận biết xu hướng thị trường.

### 3. Hệ thống câu hỏi thường gặp (FAQ)
- Giải đáp thắc mắc của người dùng về dữ liệu và cách sử dụng nền tảng.
- Tích hợp tìm kiếm thông minh và khả năng chia sẻ liên kết trực tiếp đến từng câu hỏi.

### 4. Các tính năng đang phát triển
- **Định giá BĐS**: Công cụ giúp người dùng ước tính giá trị tài sản dựa trên dữ liệu thị trường.
- **Giới thiệu đội ngũ**: Trang thông tin về dự án và các đối tác.

## 🛠️ Trạng thái hiện tại
Dự án đã hoàn thiện khung hạ tầng và các trang cốt lõi, hiện đang tập trung vào việc làm giàu dữ liệu từ Firestore và tối ưu hóa trải nghiệm người dùng trên các thiết bị di động.
