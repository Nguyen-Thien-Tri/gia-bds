# Thiết kế Hệ thống Chuyên gia AI Phân tích Bất động sản Việt Nam

Mục tiêu của hệ thống là tạo ra một "Chuyên gia AI" tự động tổng hợp, phân tích dữ liệu thị trường Bất động sản (BĐS) Việt Nam, và tự động sản xuất 10 bài blog/tháng với nội dung mang tính chuyên sâu (insight) để đăng lên website.

## 1. User Review Required
> [!IMPORTANT]  
> Xin vui lòng xem qua các đề xuất về Metric mới và các luồng Dữ liệu Internet cần thu thập. Nếu bạn đồng ý với hướng đi này, chúng ta sẽ bắt tay vào thiết kế luồng (Pipeline) cụ thể cho việc tự động hoá (tạo Cron job, xây dựng prompt cho AI, kết nối Firestore và tạo tính năng sinh bài viết).

## 2. Kiến trúc Hệ thống Đề xuất (High-Level Architecture)

Hệ thống sẽ hoạt động theo dạng **Agentic Workflow** (Luồng tác vụ tự động) kết hợp Retrieval-Augmented Generation (RAG) và Web Browsing.

* **Module 1: Data Ingestion (Thu thập & Tổng hợp Dữ liệu)**
    * **Từ Firestore & BigQuery**: AI sẽ query hoặc nhận dữ liệu tổng hợp hàng tháng thông qua một API/Cloud Function.
    * **Từ Internet (Web Browsing/Search)**: Sử dụng các công cụ tìm kiếm tự động (Google Search API, SerpApi, Web Scraping) để thu thập tin tức vĩ mô, chính sách mới nhất.
* **Module 2: Brain / Reasoning (Phân tích & Suy luận)**
    * **LLM Engine**: Sử dụng mô hình LLM mạnh mẽ (như Gemini 1.5 Pro) đóng vai trò "Chuyên gia", được hướng dẫn (prompt) bằng Persona của một chuyên gia phân tích đầu tư lão luyện.
    * Phân tích tương quan giữa số liệu nội bộ (giá, lượng tin đăng) và số liệu vĩ mô (lãi suất, quy hoạch).
* **Module 3: Content Generation (Sản xuất Nội dung)**
    * Tự động lên dàn ý (Outline) và viết bài viết hoàn chỉnh.
    * Tối ưu hoá SEO, định dạng bài viết rõ ràng, tạo tiêu đề thu hút.
* **Module 4: Orchestration & Publishing (Điều phối & Xuất bản)**
    * Lên lịch tự động (ví dụ sử dụng Cloud Scheduler/Apache Airflow) chạy định kỳ 10 lần/tháng.
    * **Tích hợp Website (Vite/React + Firebase):** Do Website của bạn đang sử dụng Vite và Firebase, Chuyên gia AI sau khi viết xong sẽ đẩy trực tiếp bài viết (dưới dạng Markdown hoặc HTML) cùng với metadata (Title, Thumbnail URL, Tags, Ngày tạo) vào một collection mới trong **Firestore** (ví dụ: `blog_posts`). Frontend Vite sẽ có một trang riêng để lấy dữ liệu từ collection này và hiển thị cho người đọc.

## 3. Đề xuất Metric Phân tích

Ngoài các metric bạn đã có trong Firestore (Giá trung bình, số lượng dự án, top quận/huyện giá cao nhất), chuyên gia AI có thể phân tích và sinh ra các góc nhìn từ các metric mới sau:

### Các Metric phát sinh thêm từ dữ liệu nội bộ (BigQuery/Firestore):
* **Tỷ trọng Nguồn cung (Supply Distribution):** Tỷ lệ % số lượng tin đăng/dự án phân bổ theo các phân khúc giá (ví dụ: bình dân, trung cấp, cao cấp).
* **Biến động Giá (MoM/YoY Price Trend):** Tốc độ tăng trưởng/giảm giá của tháng này so với tháng trước (MoM), hoặc so với cùng kỳ năm trước (YoY) cho từng khu vực.
* **Mức độ quan tâm / Lượng cung ròng:** Tốc độ tăng/giảm số lượng tin đăng bán mới tại một khu vực nhất định so với tháng trước (dấu hiệu của việc xả hàng hay găm hàng).
* **Khoảng chênh lệch giá (Price Range Spread):** Sự chênh lệch giữa giá cao nhất và thấp nhất trong cùng một loại hình/quận huyện (đánh giá mức độ hỗn loạn hoặc ổn định của thị trường).

### Các loại Dữ liệu cần thu thập thêm từ Internet:
* **Chỉ số Vĩ mô & Tín dụng:** 
  * Lãi suất vay mua nhà của các ngân hàng lớn (Vietcombank, BIDV, Techcombank...). Lãi suất giảm thường kích thích nhu cầu mua.
  * Tăng trưởng tín dụng, tỷ giá, lạm phát.
* **Thông tin Quy hoạch & Hạ tầng:**
  * Tiến độ các dự án giao thông trọng điểm (cao tốc, Vành đai 3, Vành đai 4 ở HN/HCM, cầu đường mới, metro).
  * Tin tức phê duyệt quy hoạch các tỉnh thành, thay đổi cơ cấu hành chính (lên quận, thành phố).
* **Chính sách pháp luật (Legal Updates):**
  * Tác động của các luật mới có hiệu lực (Luật Đất đai, Luật Kinh doanh BĐS, Luật Nhà ở).
  * Các loại thuế, phí BĐS mới.
* **Tâm lý Thị trường (Social Sentiment) - *Nâng cao*:**
  * Thu thập bài đăng/bình luận trên các diễn đàn BĐS, Facebook Groups lớn, Otofun, Voz để xem tâm lý nhà đầu tư đang "hưng phấn" hay "bi quan", có đang đồn thổi về khu vực nào không.

## 4. Định hướng Nội dung (10 bài/tháng)

Để hệ thống tạo ra 10 bài viết đa dạng, ta có thể thiết lập các **"Nhiệm vụ (Task)"** khác nhau cho Chuyên gia AI trong 1 tháng:

1. **Báo cáo Thị trường Toàn cảnh:** (1-2 bài) Tổng quan giá BĐS tại Hà Nội / TP.HCM tháng qua, biến động lãi suất và dòng tiền.
2. **Tiêu điểm Khu vực (Spotlight):** (3-4 bài) Phân tích sâu 1 quận/huyện cụ thể đang có biến động giá mạnh nhất (dựa trên dữ liệu top tăng giá trong Firestore), kết hợp với lý do hạ tầng từ Internet để giải thích.
3. **So sánh Phân khúc:** (2 bài) Ví dụ: "Nên đầu tư chung cư nội đô hay đất nền vùng ven lúc này?", dùng dữ liệu giá trung bình/diện tích để so sánh.
4. **Góc nhìn Pháp lý / Chính sách:** (1 bài) Đánh giá một quy định mới sắp ban hành sẽ ảnh hưởng thế nào đến người bán/người mua trong tháng tới.
5. **Dự báo & Lời khuyên đầu tư:** (1 bài) Dựa trên dữ liệu tổng hợp, đưa ra chiến lược phân bổ vốn cho các nhà đầu tư trong ngắn/trung hạn.

## 5. Technical Stack & Công cụ Đề xuất

Để xây dựng hệ thống này một cách ổn định và hiện đại, tôi đề xuất các công cụ sau:

*   **Ngôn ngữ chính:** Python 3.10+
*   **AI Engine (LLM):** 
    *   **Gemini 1.5 Pro:** Lựa chọn tối ưu nhờ khả năng xử lý context window lớn (lên tới 2M tokens), rất tốt để đọc đồng thời nhiều báo cáo và dữ liệu Firestore.
    *   **LangChain / LangGraph:** Để xây dựng luồng Agentic (luồng suy nghĩ có logic, tự tìm kiếm rồi mới viết bài).
*   **Data Ingestion:**
    *   **Google Cloud SDK (Firestore & BigQuery):** Truy xuất dữ liệu nội bộ.
    *   **Serper.dev Search API:** API tìm kiếm dựa trên Google Search gốc, giúp trích xuất nội dung tin tức, chính sách địa phương một cách chính xác nhất cho thị trường Việt Nam.
*   **Automation & Deployment:**
    *   **Google Cloud Functions / Cloud Run:** Để chạy code logic phân tích.
    *   **Cloud Scheduler:** Kích hoạt luồng chạy định kỳ (Cron job).
*   **CMS Integration:**
    *   Sử dụng API của nền tảng bạn đang dùng (ví dụ: REST API của WordPress) để tự động hóa việc đăng bài.

## 6. Thiết kế chi tiết từng Module

### Module 1: Data Aggregator (Tập hợp dữ liệu)
Agent sẽ thực hiện song song 2 nhiệm vụ:
1.  **Internal Query:** Lấy các metric từ Firestore (giá trung bình, top quận/huyện).
2.  **Web Research:** Tìm kiếm theo từ khóa như "thị trường bất động sản [tỉnh/thành] tháng [tháng/năm]", "lãi suất ngân hàng [tháng/năm]", "luật đất đai mới nhất".

### Module 2: Analytical Brain (Bộ não phân tích)
Sử dụng kỹ thuật **Chain-of-Thought (Chuỗi suy nghĩ)**:
*   *Bước 1:* Đọc dữ liệu thô từ Firestore.
*   *Bước 2:* Đọc các tin tức từ Internet.
*   *Bước 3:* So sánh: "Tại sao giá ở Quận A tăng 10%? Có tin tức hạ tầng nào mới ở khu vực này không?".
*   *Bước 4:* Đưa ra các Insight độc lập (ví dụ: "Sự dịch chuyển dòng tiền từ đất nền sang căn hộ").

### Module 3: Content Writer (Biên tập nội dung)
Tối ưu bài viết theo chuẩn SEO:
*   **Từ khóa:** Tự động chèn các từ khóa về khu vực và loại hình BĐS.
*   **Cấu trúc:** [Tiêu đề hấp dẫn] -> [Tóm tắt insight] -> [Phân tích số liệu thực tế] -> [Góc nhìn chuyên gia & Tin tức bổ trợ] -> [Lời khuyên/Kết luận].

## 7. Lộ trình Triển khai (Roadmap)

### Giai đoạn 1: MVP (Tuần 1-2) - "Nền tảng"
- [ ] Thiết lập kết nối Python với Firestore để lấy dữ liệu.
- [ ] Xây dựng Prompt "Senior Real Estate Analyst" cơ bản cho Gemini.
- [ ] Chạy thử nghiệm sinh bài viết thủ công từ dữ liệu tĩnh.

### Giai đoạn 2: Automation (Tuần 3) - "Tự động hóa"
- [ ] Tích hợp Serper.dev Search API để AI tự cập nhật tin tức internet.
- [ ] Xây dựng luồng xử lý Agentic (Tìm kiếm -> Phân tích -> Viết).
- [ ] Kết nối API để đẩy bài viết lên website (Draft mode).

### Giai đoạn 3: Optimization (Tuần 4) - "Tinh chỉnh"
- [ ] Tối ưu hóa SEO và giọng văn của AI (Tone-of-voice).
- [ ] Thiết lập Cloud Scheduler để hệ thống tự động chạy 10 bài/tháng.
- [ ] Xây dựng Dashboard theo dõi hiệu quả bài viết (lượt view, tương tác).

## 8. Các Quyết định Kỹ thuật đã chốt
*   **Sinh Hình ảnh Tự động:** Tích hợp API tạo ảnh (như OpenAI DALL-E 3 hoặc Google Imagen 3 qua Vertex AI) để mỗi bài blog đều có 1-2 hình minh họa (thumbnail hoặc ảnh minh họa khái niệm vĩ mô). Prompt tạo ảnh sẽ do chính Agent sinh ra dựa trên nội dung bài viết.
*   **Hạ tầng:** Tận dụng **Google Cloud Project** hiện có của bạn. Triển khai code lên Cloud Functions (hoặc Cloud Run) và dùng Cloud Scheduler để kích hoạt lịch chạy tự động.
*   **Công cụ tìm kiếm:** Bắt đầu với gói miễn phí (2500 requests đầu) của **Serper.dev**.

## 9. Lựa chọn Framework AI (Đề xuất)
Để xây dựng "bộ não" cho chuyên gia BĐS này, chúng ta cần một Framework chuyên dụng cho Agent. Dưới đây là 3 lựa chọn phổ biến nhất hiện nay:

1.  **CrewAI (Đề xuất cao nhất cho Use-case này):**
    *   *Cách hoạt động:* Bạn tạo ra một "phi hành đoàn" (Crew) gồm nhiều Agent với các vai trò khác nhau. Ví dụ: Agent 1 là "Nhà nghiên cứu BĐS" chuyên đi tìm số liệu và đọc báo. Agent 2 là "Chuyên viên phân tích đầu tư" chuyên suy luận. Agent 3 là "Biên tập viên Content SEO" chuyên viết bài.
    *   *Ưu điểm:* Rất dễ hiểu, code cực kỳ gọn gàng. Hoạt động cực kỳ hiệu quả cho các tác vụ phối hợp sản xuất nội dung (như yêu cầu của bạn).
2.  **LangGraph (Mạnh mẽ, linh hoạt nhất):**
    *   *Cách hoạt động:* Xem luồng làm việc như một đồ thị trạng thái (State Graph). Nếu kết quả tìm kiếm chưa đủ tốt, nó có thể quay vòng lại tự tìm kiếm lại.
    *   *Ưu điểm:* Kiểm soát cực sâu vào từng bước tư duy của Agent. Rất tốt nếu luồng nghiệp vụ phức tạp.
    *   *Nhược điểm:* Đường cong học tập hơi dốc, phức tạp hơn khi setup.
3.  **LangChain (Framework nền tảng cơ bản):**
    *   *Ưu điểm:* Hệ sinh thái cực lớn, kết nối dễ dàng với mọi công cụ (Firestore, Serper, Google Search).
    *   *Nhược điểm:* Code có thể trở nên lộn xộn nếu thiết kế Agent phức tạp (hiện tại LangChain thường khuyến khích chuyển sang dùng LangGraph cho Agent).

> [!TIP]
> **Đề xuất:** Chúng ta nên sử dụng **CrewAI** (bên dưới nó vẫn chạy bằng LangChain) kết hợp với mô hình **Gemini 1.5 Pro**. Việc định nghĩa rõ "chức danh" (Vai trò) cho từng Agent trong CrewAI sẽ giúp giọng văn của bài blog có tính chuyên gia cao hơn rất nhiều.
