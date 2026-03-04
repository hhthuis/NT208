# Phân tích Luồng Xử lý Sơ đồ Kiến trúc Hệ thống CLARA (Agentic RAG)

## Sơ đồ này mô tả vòng đời của một truy vấn (Query) từ lúc người dùng nhập vào cho đến khi hệ thống trả về kết quả an toàn và chính xác. Quy trình được chia thành 6 lớp (Layers) nối tiếp nhau:

### 1. Lớp Tương tác (User Interaction Layer)

- Khởi tạo: Người dùng (User) nhập câu hỏi (Query) thông qua giao diện hệ thống (CLARA Interface).

- Dữ liệu lúc này ở dạng thô (Raw Data) và được đẩy xuống lớp bảo mật.

### 2. Lớp Bảo mật & Tiền xử lý (Security & Preprocessing Layer)

- Đây là chốt chặn an toàn đầu tiên.

    - Bộ lọc PII/PHI (PII/PHI Filter): Quét Raw Data để tìm thông tin cá nhân/y tế nhạy cảm.

    - Nếu chứa dữ liệu nhạy cảm (Sensitive Data): Chuyển qua Anonymization Module để ẩn danh hóa (xóa/mã hóa tên, tuổi, bệnh án cá nhân).

    - Nếu là dữ liệu sạch (Clean Data): Bỏ qua bước ẩn danh.

- Xử lý truy vấn: Cả hai luồng sau đó hội tụ tại Query Processor để chuẩn hóa câu hỏi.

### 3. Lớp Tối ưu & Lưu trữ (Optimization & Caching Layer)

- Giúp hệ thống phản hồi nhanh và tiết kiệm tài nguyên.

- Truy vấn đi vào Cache Check (Redis/Vector DB) để kiểm tra xem đã có người hỏi câu này chưa.

- Trúng Cache (Cache - Hit): Dữ liệu có sẵn, luồng chạy thẳng đến Response Streamer để trả kết quả (bỏ qua toàn bộ AI bên dưới).

- Trượt Cache (Cache - Miss): Câu hỏi mới, được chuyển xuống Async Orchestrator để bắt đầu phân tích sâu.

### 4. Lõi Xử lý Song song (Parallel Processing Core)

- Đây là "trái tim" Agentic của hệ thống.

- Bộ điều phối (Async Orchestrator): Chia nhỏ công việc và tạo ra 3 luồng chạy song song (Thread 1, 2, 3) giao cho 3 AI Agents độc lập:

    - Literature Agent: Chuyên gia tìm kiếm y văn.

    - Safety/Pharma Agent: Chuyên gia về an toàn và dược phẩm.

    - Coding Agent: Chuyên gia mã hóa lâm sàng.

    -Các Agents này gom các yêu cầu (Aggregate Requests) và gửi tập trung đến Cổng API (API Gateway).

### 5. Nguồn Tri thức Y sinh (Biomedical Knowledge)

- API Gateway thực hiện các cuộc gọi bất đồng bộ (Async Call) ra 5 cơ sở dữ liệu y khoa uy tín thế giới: PubMed/PMC, arXiv, ClinicalTrials.gov, openFDA, và ICD 11 API.

- Kết quả trả về cho hệ thống dưới định dạng chuẩn JSON/XML.

### 6. Lớp Tổng hợp & Kiểm chứng (Synthesis & Verification)

- Gộp Ngữ cảnh: Context Aggregator nhận toàn bộ JSON/XML và trộn lại thành một bộ ngữ cảnh hoàn chỉnh.

- Sinh câu trả lời: Đẩy vào Medical RAG Engine để tạo ra một bản nháp (Draft).

- Kiểm chứng Sự thật (Fact Checker Module): Bản nháp bắt buộc phải qua khâu kiểm duyệt chéo với dữ liệu gốc.

- Nếu Phát hiện Ảo giác (Hallucination Detected): Trả ngược lại RAG Engine để viết lại.

- Nếu Đã xác thực (Verified): Chấp nhận kết quả.

### 7. Lớp Đầu ra (Streaming Output Layer)

- Khi kết quả đã được Verified:

- Hiển thị: Dữ liệu được băm nhỏ (Stream Token) đẩy qua Response Streamer và hiện lên màn hình giao diện (Display) cho người dùng theo thời gian thực (hiệu ứng gõ chữ).

- Lưu trữ: Đồng thời, tài liệu hoàn chỉnh được lưu vào Document Storage, sau đó gửi tín hiệu cập nhật (Update) ngược lên Cache Check ở Lớp 3 để phục vụ các người dùng sau.