# BÁO CÁO ĐỒ ÁN Y KHOA - Medical Chatbot
> Lê Hữu Hoàng - 24520539

> Nguyễn Tuấn Hùng - 24521606

## 1. Phân loại người dùng
- Nhóm 1: Người dùng phổ thông (Bệnh nhân, người quan tâm đến sức khỏe), không có hoặc có ít kiến thức chuyên môn y khoa. Họ cần thông tin dễ hiểu, chính xác để tự chăm sóc sức khỏe hoặc tìm hiểu trước khi đi khám.
- Nhóm 2: Người dùng chuyên môn (Sinh viên y khoa, Dược sĩ, Nghiên cứu sinh, Bác sĩ), có kiến thức nền tảng vững chắc. Yêu cầu thông tin chuyên sâu, có tính hàn lâm, cần trích dẫn nguồn gốc rõ ràng để phục vụ học tập, nghiên cứu hoặc tham khảo lâm sàng.
## 2. Phân tích Use-cases
### Nhóm 1: Người dùng phổ thông
- Use-case 1: Tra cứu triệu chứng sơ bộ, nhập các triệu chứng đang gặp phải (ví dụ: đau đầu, buồn nôn) để bot gợi ý các nguyên nhân có thể xảy ra và lời khuyên (khi nào cần gặp bác sĩ).
- Use-case 2: Tìm hiểu thông tin cơ bản về thuốc, sử dụng tính năng tra cứu thuốc (RxNorm) để biết công dụng, liều dùng cơ bản của loại thuốc mình vừa được kê đơn.
- Use-case 3: Kiểm tra cảnh báo / tác dụng phụ của thuốc, truy vấn qua OpenFDA để xem thuốc có bị thu hồi hay có tác dụng phụ nguy hiểm nào không.
- Use-case 4: Quản lý sức khỏe cá nhân, dùng tính năng Bookmarks để lưu lại các câu trả lời về chế độ ăn uống, cách phòng bệnh để mở ra xem lại khi cần.

### Nhóm 2: Người dùng chuyên môn
- Use-case 5: Tra cứu mã bệnh theo chuẩn quốc tế, nhập tên bệnh để lấy chính xác mã ICD-11 phục vụ cho việc làm bệnh án hoặc nghiên cứu dịch tễ
- Use-case 6: Tìm kiếm tài liệu y sinh & bài báo khoa học, yêu cầu bot tổng hợp thông tin về một bệnh lý cụ thể và trích xuất các mã [PMID:xxx] từ PubMed để làm tài liệu tham khảo cho tiểu luận/nghiên cứu.
- Use-case 7: Cập nhật thử nghiệm lâm sàng mới nhất, tra cứu các phương pháp điều trị mới đang được thử nghiệm (ClinicalTrials.gov) cho các căn bệnh phức tạp (ví dụ: ung thư).
- Use-case 8: Xem lại lịch sử nghiên cứu (Chat History), mở lại các phiên chat cũ có chứa các luồng suy luận y khoa phức tạp mà bot đã tổng hợp trước đó.
## 3. Tính năng giữ chân người dùng
- Chống "Ảo giác": Nỗi sợ lớn nhất khi hỏi AI về y tế là AI bịa ra thông tin. Việc đồ án bắt buộc gắn thẻ [PMID], [FDA], [ICD-11] vào cuối mỗi luận điểm giúp người dùng (đặc biệt là giới chuyên môn) có niềm tin tuyệt đối vào hệ thống. Họ sẽ quay lại vì đây là một "trợ lý nghiên cứu" chứ không chỉ là "chatbot trò chuyện".
- Khả năng xác minh tức thì: Người dùng có thể copy các mã trích dẫn này để tự kiểm chứng.
- Hệ sinh thái lưu trữ: Khi người dùng đã lưu (bookmark) một số bài báo khoa học hay mã ICD quan trọng trên tài khoản của họ, họ sẽ có xu hướng quay lại website để truy cập "thư viện kiến thức" cá nhân này thay vì phải đi tìm kiếm lại từ đầu trên Google.
## Phân tích Cạnh tranh & Chiến lược khác biệt
### Đối thủ là ai?
- Đối thủ trực tiếp: Các Chatbot AI y tế hiện có trên thị trường hoặc các LLM lớn (như ChatGPT, Claude, Gemini) khi người dùng sử dụng để hỏi đáp bệnh lý. Tuy nhiên, các AI này thường mắc lỗi "ảo giác" (hallucination) và thiếu tính xác thực chuyên sâu.
- Đối thủ gián tiếp: Các trang web tra cứu y tế tĩnh (WebMD, cổng thông tin bệnh viện) hoặc các công cụ tìm kiếm thông thường (Google). Các phần mềm quản lý bệnh án (EMR/HIS) truyền thống tại các bệnh viện hiện nay (vốn yêu cầu nhập liệu thủ công).
### Lợi thế cạnh tranh
- Chủ động và Linh hoạt hơn (Agentic RAG): Vượt trội hơn các web tra cứu thụ động hoặc RAG truyền thống. CLARA không chỉ tìm kiếm và trả lời, mà gồm nhiều Agent "tự lập kế hoạch" và "phối hợp" như một buổi hội chẩn chuyên khoa thực sự.
- Tính chính xác và Tin cậy cao (Lập luận đa bước): Mỗi bước đều phải được xác thực bằng cơ sở dữ liệu y khoa (EBM) trước khi đi tiếp.
- Thời gian thực (Real-time): Cập nhật y văn thế giới và phác đồ mới nhất đến thẳng giường bệnh (point-of-care) chỉ trong vài giây.
- Tự động hóa nhập liệu: Có khả năng chuyển đổi trực tiếp lời kể, dữ liệu phi cấu trúc thành hồ sơ bệnh án có cấu trúc.
### Chống sao chép
- Thuật toán & Kiến trúc lõi phức tạp: Việc xây dựng luồng lập luận đa bước (Multi-step reasoning) và cấu trúc Agentic RAG không hề đơn giản như việc chỉ gọi API của OpenAI. Nó đòi hỏi kỹ thuật chia nhỏ tác vụ và kiểm soát RAG nghiêm ngặt ở từng nút thắt.
- Xử lý ngôn ngữ tự nhiên đặc thù lâm sàng: Rất khó để một nhóm khác lập tức copy khả năng "lắng nghe" văn cảnh trò chuyện phi cấu trúc của người bệnh mà tự động trích xuất, chuẩn hóa và gán đúng các mã y khoa quốc tế khắt khe như ICD-11 (chẩn đoán bệnh) và RxNorm (thuốc).
### ĐIểm độc đáo
- `Hệ thống AI mô phỏng "Hội chẩn đa khoa" tích hợp Medical Scribe cá nhân hóa sâu`: Đây là giải pháp ĐẦU TIÊN kết hợp khả năng tự động nghe/đọc lời kể bệnh nhân -> chuẩn hóa thành hồ sơ y tế quốc tế (ICD-11/RxNorm) -> tự động đối chiếu với phác đồ y văn thế giới (EBM) để đưa ra phương án điều trị đa bệnh lý (người mắc nhiều bệnh cùng lúc) ngay tại thời gian thực.

##  Sơ đồ Kiến trúc Hệ thống
- Các module chính và chức năng:
    - backend:
        - `main.py`: entrypoint FastAPI — khởi tạo app, CORS, đăng ký router`s, startup/shutdown events, Swagger.
        - `database/`:
            - `connection/engine`: khởi tạo async SQLAlchemy + aiosqlite.
            - `models.py`: ORM models DB (User, Conversation, Message, Bookmark).   
        - `routers/auth.py`: endpoint đăng ký/đăng nhập/tra thông tin user (JWT), bảo mật.
        - `routers/chat.py`: endpoint quản lý chat — gửi câu hỏi, lưu lịch sử, lấy/ghim bookmark.
        - `routers/drugs.py`: endpoint tra cứu thuốc (proxy tới RxNorm service).
        - `services/orchestrator.py`: pipeline RAG — phân tích intent/entities, chọn nguồn, gọi các medical APIs song song, kết hợp kết quả, gọi LLM để sinh câu trả lời có trích dẫn.
        - `services/llm_service.py`: wrapper cho LLM OpenAI-compatible (lệnh gọi API, prompt templates, streaming/response parsing).
        - `services/pubmed_service.py`: client gọi PubMed E-utilities (search, fetch abstracts/PMID).
        - `services/icd_service.py`: client WHO ICD-11 API (search/code details, fallback handling).
    - frontend
        - `src/app/*`: pages (landing, login, register) và folder (protected) chứa: `chat`, `drug-lookup`, `icd-lookup`, `bookmarks`.
        - `src/lib/api.ts`: client HTTP cho backend (fetch wrapper, attach JWT, error handling).
        - `src/lib/utils.ts`: utilities chung (format date, truncation, helpers).
        - `src/components/chat/ChatInput.tsx`: input UI, xử lý gửi tin nhắn, loading state.
        - `src/components/chat/ChatMessage.tsx`: hiển thị tin nhắn, highlight trích dẫn (PMID, RxCUI, NCT, ICD).
        - `src/components/layout/Sidebar.tsx`: sidebar điều hướng, links đến tính năng.
        - `.env.local`, `next.config.mjs`: cấu hình frontend (NEXT_PUBLIC_API_URL).
##  Thiết kế Luồng dữ liệu & UML: 
- Trong folder `diagram`
## Cơ sở dữ liệu:
- Sử dụng mô hình dữ liệu quan hệ SQL, được thiết kế qua ORM SQLAlchemy của Python với các bảng (tables), khóa chính (primary key), khóa ngoại (foreign key) và các quan hệ (relationships).
##  Minimum Viable Product (MVP)
### Lựa chọn công nghệ:
- `Backend`: python & fastAPI
    - Lí do: đây là một hệ thống AI lõi. Python là ngôn ngữ nền tảng của hệ sinh thái AI/LLM. Framework FastAPI vì nó cực kì nhanh và hỗ trợ lập trình bất đồng bộ
    - Nhờ tính năng này, hệ thống có thể gọi song song 5 y khoa mà không bị nghẽn, đồng thời xử lí mượt mà luồng dữ liệu trả về từ AI. 
-  `Frontend`: Next.js 14 & TypeScript
    - Lí do: Next.js (App Router) giúp tối ưu hóa hiệu suất tải trang và quản lý routing linh hoạt cho ứng dụng chat. TypeScript được sử dụng để kiểm soát chặt chẽ kiểu dữ liệu (Type Safety). 
    - Vì dự án phải xử lý các cục dữ liệu JSON y khoa rất phức tạp (mã bệnh, mảng trích dẫn citations), TypeScript giúp bắt lỗi ngay trong quá trình code, tránh lỗi sập giao diện khi người dùng tra cứu.
