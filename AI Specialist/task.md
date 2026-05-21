# Nhiệm vụ: Xây dựng Chuyên gia AI phân tích Bất động sản

- [ ] **Giai đoạn 1: Nền tảng (Data & Basic LLM setup)**
  - [x] Thiết lập kết nối Python với Firestore/BigQuery.
  - [x] Xây dựng hàm lấy dữ liệu mẫu (các metric như giá trung bình, số dự án, v.v.).
  - [x] Cài đặt các thư viện lõi: `crewai`, `langchain-google-genai` (cho Gemini), `crewai-tools`.
  - [x] Cấu hình API Keys (Gemini, Serper) qua biến môi trường (.env).

- [ ] **Giai đoạn 2: Xây dựng Phi hành đoàn (CrewAI)**
  - [ ] Định nghĩa Tool tìm kiếm web (SearchTool với Serper).
  - [ ] Khởi tạo Agent 1: Data Analyst (Phân tích dữ liệu từ Firestore).
  - [ ] Khởi tạo Agent 2: Macro Researcher (Tìm kiếm tin tức vĩ mô, pháp lý bằng Serper).
  - [ ] Khởi tạo Agent 3: Senior Editor (Viết và tổng hợp thành bài blog SEO).
  - [ ] Định nghĩa các Task (Nhiệm vụ cụ thể) cho từng Agent.
  - [ ] Kết nối các Agent thành một `Crew` hoàn chỉnh và chạy thử nghiệm luồng (Pipeline).

- [ ] **Giai đoạn 3: Sinh hình ảnh & Hoàn thiện nội dung**
  - [ ] Tích hợp API sinh ảnh (Vertex AI Imagen hoặc DALL-E) vào quá trình viết của Senior Editor.
  - [ ] Tối ưu hóa lại Prompt (system prompt, role description) để bài viết có giọng điệu chuyên gia.

- [ ] **Giai đoạn 4: Tự động hóa & Tích hợp Website (Vite + Firebase)**
  - [ ] Viết hàm (Python) để Agent đẩy dữ liệu bài viết (Tiêu đề, Nội dung Markdown, Ảnh) trực tiếp vào collection `blog_posts` trong Firestore.
  - [ ] Bố trí code Python thành một module chạy được trên Google Cloud Functions (hoặc Cloud Run).
  - [ ] Cấu hình Google Cloud Scheduler để tự động chạy trigger 10 lần/tháng.
  - [ ] **Bên Website Vite (Frontend):** Tạo một Page mới (vd: `src/pages/TinTuc/TinTucPage.tsx`).
  - [ ] Viết logic (TypeScript) để fetch bài viết từ collection `blog_posts` trong Firestore và hiển thị ra UI.
  - [ ] Cài đặt thư viện `react-markdown` bên Vite để render nội dung bài viết từ định dạng Markdown mà AI sinh ra.
