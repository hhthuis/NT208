# Phân tích Luồng Dữ liệu (Data Flow) 
## Dựa trên sơ đồ kiến trúc tích hợp, luồng dữ liệu (Data Flow) của hệ thống được chia thành 2 luồng chính: Luồng Xác thực (Auth Data Flow) và Luồng Truy vấn Y khoa (Chat/RAG Data Flow).

### 1. Luồng Xác thực (Auth Data Flow)

- Luồng này xử lý dữ liệu đăng ký/đăng nhập của người dùng.

- Sinh dữ liệu (Client): Người dùng nhập thông tin (Email, Password) trên giao diện UI (chat, login, lookup) của Next.js.

- Truyền tải (Client ➔ Server): Frontend đóng gói dữ liệu gửi qua API HTTP POST /register or /login đến API Routers / Controllers của Backend.

- Xử lý (Backend): - Router chuyển dữ liệu (credentials) tới module Auth (JWT) để Create / validate (Tạo hoặc kiểm tra).

- Module Auth thực hiện lệnh Read/Write user (Đọc/Ghi dữ liệu người dùng) vào SQLite DB.

- Trả kết quả: Nếu hợp lệ, Backend tạo Token JWT, đóng gói thành HTTP response JSON trả về Frontend để lưu trữ ở trình duyệt.

### 2. Luồng Truy vấn Y khoa (Chat/RAG Data Flow)

- Đây là luồng dữ liệu cốt lõi khi người dùng đặt câu hỏi y khoa.

- Gửi câu hỏi (User ➔ Frontend ➔ Backend): - Người dùng nhập câu hỏi (HTTP: user actions).

- Frontend đính kèm Token bảo mật và gửi HTTP POST /chat (JWT) chứa nội dung câu hỏi (chat query) xuống API Routers / Controllers.

- Xác thực Token & Phân luồng (Backend):

- Router gửi token cho Auth (JWT) để Verify Token.

- Nếu hợp lệ, Router Forward query (chuyển tiếp câu hỏi) vào bộ não trung tâm là Orchestrator (RAG Pipeline).

- Thu thập Dữ liệu Y khoa (Orchestrator ➔ External APIs):
Orchestrator bóc tách câu hỏi và gửi các luồng dữ liệu yêu cầu tới 5 API bên ngoài. Dữ liệu trả về (Data Fetching) bao gồm:

    - Từ PubMed: Trả về PMID / abstracts (Tóm tắt bài báo).

    - Từ ICD-11: Trả về ICD codes/details (Chi tiết mã bệnh).

    - Từ RxNorm: Trả về RxCUI / drug info (Thông tin thuốc).

    - Từ ClinicalTrials: Trả về NCT / trial summary (Thử nghiệm lâm sàng).

    - Từ OpenFDA: Trả về safety/adverse data (Cảnh báo an toàn).

- Tổng hợp & Sinh câu trả lời (Orchestrator ➔ LLM Service: Orchestrator nhào nặn câu hỏi gốc của user + toàn bộ dữ liệu y khoa vừa lấy được thành một khối dữ liệu gọi là Aggregated evidence + prompt.

- Khối dữ liệu này được gửi tới LLM Service.

- LLM xử lý và trả về dữ liệu đích: Answer with citations (Câu trả lời đã gắn kèm trích dẫn).

- Lưu trữ Dữ liệu (Orchestrator ➔ SQLite DB): Song song với việc tạo câu trả lời, Orchestrator đẩy một khối dữ liệu xuống SQLite DB thông qua lệnh Save conversation / bookmarks và User records. Dữ liệu được lưu trữ cứng bao gồm: user creds, JWT, chat query, PMIDs, RxCUI, NCT, ICD codes, bookmarks.

- Hoàn trả Dữ liệu (Backend ➔ Frontend ➔ User): Orchestrator gom câu trả lời hoàn chỉnh thành Response payload (answer + citations) đưa ra Router.

- Router xuất HTTP response JSON trả về Next.js.

- Next.js Frontend nhận JSON, thực hiện Render answer / allow bookmark (hiển thị giao diện và nút lưu) lên màn hình cho người dùng.