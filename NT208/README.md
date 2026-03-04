# 🏥 CLARA Medical Chatbot — Agentic RAG

> Chatbot tra cứu y khoa thông minh sử dụng kiến trúc **Agentic RAG** (Retrieval-Augmented Generation) dựa trên [CLARA — Clinical Agent for Retrieval & Analysis](https://arxiv.org/abs/2503.05754).

**Môn học:** NT208 — Lập trình Web
**Trường:** Đại học Công nghệ Thông tin — ĐHQG TP.HCM (UIT)

---

## ✨ Tính năng chính

| Tính năng | Mô tả |
|-----------|--------|
| 💬 **Chat Y khoa thông minh** | Hỏi đáp y khoa với AI, mọi câu trả lời đều trích dẫn nguồn uy tín |
| 🔬 **5 nguồn dữ liệu y khoa** | PubMed, ICD-11, RxNorm, ClinicalTrials.gov, OpenFDA |
| 📚 **Trích dẫn tự động** | `[PMID:xxx]` `[ICD-11:xxx]` `[RxCUI:xxx]` `[NCT:xxx]` `[FDA:xxx]` |
| 💊 **Tra cứu thuốc** | Tìm kiếm thuốc qua RxNorm (NLM) |
| 📋 **Tra mã bệnh ICD-11** | Tra cứu phân loại bệnh theo chuẩn WHO |
| 🔖 **Bookmarks** | Lưu lại câu trả lời quan trọng để xem lại |
| 🔐 **Xác thực JWT** | Đăng ký, đăng nhập, phân quyền |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐        ┌────────────────────────────────────────────────┐
│   Next.js 14    │  HTTP  │              FastAPI Backend                   │
│   Frontend      │◄──────►│                                                │
│   (Port 3000)   │        │  ┌──────────────┐    ┌───────────────────┐    │
└─────────────────┘        │  │ Orchestrator  │───►│   LLM Service     │    │
                           │  │ (RAG Pipeline)│    │ (OpenAI-compat.)  │    │
                           │  └──────┬────────┘    └───────────────────┘    │
                           │         │                                      │
                           │  ┌──────▼──────────────────────────────────┐   │
                           │  │      5 Medical API Services              │   │
                           │  │                                          │   │
                           │  │  📄 PubMed    🏥 ICD-11    💊 RxNorm    │   │
                           │  │  🔬 ClinicalTrials.gov   ⚠️ OpenFDA    │   │
                           │  └──────────────────────────────────────────┘   │
                           │                                                │
                           │  ┌──────────────────┐                          │
                           │  │  SQLite Database  │                          │
                           │  │  (Users, Chats,   │                          │
                           │  │   Bookmarks)      │                          │
                           │  └──────────────────┘                          │
                           └────────────────────────────────────────────────┘
```

### 🔄 Pipeline RAG (đơn giản hóa từ 14 bước CLARA):

```
User Query → 1. Phân tích Intent + Entities (LLM)
           → 2. Auto-chọn nguồn dữ liệu theo loại câu hỏi
           → 3. Gọi Medical APIs (song song)
           → 4. Tổng hợp + Trích dẫn (LLM)
           → 5. Trả response + Disclaimer y khoa
```

**Ví dụ auto-chọn nguồn:**
- 🤒 Hỏi triệu chứng → PubMed + ICD-11 + ClinicalTrials
- 💊 Hỏi về thuốc → RxNorm + PubMed + OpenFDA
- 🔬 Hỏi thử nghiệm → ClinicalTrials + PubMed
- 🩺 Hỏi điều trị → PubMed + ClinicalTrials + OpenFDA

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, Radix UI |
| **Backend** | Python FastAPI, SQLAlchemy (async), Pydantic v2 |
| **Database** | SQLite + aiosqlite |
| **AI/LLM** | Bất kỳ OpenAI-compatible API nào (OpenAI, Groq, Together...) |
| **Medical APIs** | PubMed, WHO ICD-11, NLM RxNorm, ClinicalTrials.gov, OpenFDA |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |

---

## 📁 Cấu trúc thư mục

```
NT208/
├── README.md
├── PLAN.md
├── CLARA.txt                         ← Tài liệu kiến trúc CLARA gốc
├── .gitignore
│
├── backend/
│   ├── .env.example                  ← Mẫu cấu hình (copy thành .env)
│   ├── requirements.txt
│   ├── main.py                       ← FastAPI entry point
│   ├── config.py                     ← Pydantic Settings
│   ├── database/
│   │   ├── connection.py             ← Async SQLAlchemy engine
│   │   └── models.py                 ← 4 models: User, Conversation, Message, Bookmark
│   ├── models/
│   │   └── schemas.py                ← Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py                   ← JWT register/login/me
│   │   ├── chat.py                   ← Chat CRUD + bookmarks
│   │   ├── drugs.py                  ← Drug search
│   │   └── icd.py                    ← ICD-11 search + detail
│   └── services/
│       ├── orchestrator.py           ← RAG pipeline (core logic)
│       ├── llm_service.py            ← LLM integration (OpenAI-compatible)
│       ├── pubmed_service.py         ← PubMed E-utilities API
│       ├── icd_service.py            ← WHO ICD-11 API
│       ├── rxnorm_service.py         ← RxNorm/RxNav API
│       ├── clinicaltrials_service.py ← ClinicalTrials.gov API v2
│       └── openfda_service.py        ← OpenFDA API
│
└── frontend/
    ├── .env.local                    ← NEXT_PUBLIC_API_URL
    ├── package.json
    ├── tailwind.config.ts
    └── src/
        ├── lib/
        │   ├── api.ts                ← API client (fetch + JWT)
        │   └── utils.ts
        ├── components/
        │   ├── ui/                   ← Button, Input, Card
        │   ├── chat/                 ← ChatMessage, ChatInput
        │   └── layout/              ← Sidebar
        └── app/
            ├── page.tsx              ← Landing page
            ├── login/page.tsx
            ├── register/page.tsx
            └── (protected)/
                ├── chat/page.tsx         ← 💬 Chat Y khoa
                ├── drug-lookup/page.tsx  ← 💊 Tra cứu thuốc
                ├── icd-lookup/page.tsx   ← 📋 Tra mã ICD-11
                └── bookmarks/page.tsx    ← 🔖 Bookmarks
```

---

## 🚀 Hướng dẫn cài đặt & chạy

### 📋 Yêu cầu hệ thống

| Phần mềm | Phiên bản tối thiểu |
|-----------|-------------------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |


```env
# Điền API key của bạn (OpenAI, Groq, Together, hoặc bất kỳ OpenAI-compatible API)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

> 💡 **Gợi ý LLM API miễn phí/rẻ:**
> - [Groq](https://groq.com) — miễn phí, nhanh (`OPENAI_BASE_URL=https://api.groq.com/openai/v1`, model: `llama-3.3-70b-versatile`)
> - [Together AI](https://together.ai) — $5 credit miễn phí
> - [OpenRouter](https://openrouter.ai) — nhiều model, có free tier

```bash
# Chạy backend server
uvicorn main:app --reload --port 8000
```

✅ Backend sẽ chạy tại: **http://localhost:8000**
📖 Swagger API docs: **http://localhost:8000/docs**

### Bước 3: Cài đặt Frontend

```bash
# Mở terminal mới
cd frontend

# Cài đặt dependencies
npm install

# (File .env.local đã có sẵn, mặc định trỏ về localhost:8000)
# Nếu backend chạy port khác, sửa file .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Chạy frontend
npm run dev
```

✅ Frontend sẽ chạy tại: **http://localhost:3000**

### Bước 4: Sử dụng

1. 🌐 Mở trình duyệt → **http://localhost:3000**
2. 📝 Click **"Đăng ký"** → tạo tài khoản mới
3. 🔐 **Đăng nhập** với tài khoản vừa tạo
4. 💬 Vào **"Chat Y khoa"** → bắt đầu hỏi!

---

## 💬 Ví dụ câu hỏi

| Loại | Câu hỏi mẫu | Nguồn dữ liệu |
|------|-------------|---------------|
| 🤒 Triệu chứng | "Tôi uống bia bị nổi ngứa là bị gì?" | PubMed + ICD-11 + ClinicalTrials |
| 💊 Thuốc | "Thuốc Aspirin có tác dụng phụ gì?" | RxNorm + PubMed + OpenFDA |
| 🔬 Thử nghiệm | "Thử nghiệm lâm sàng mới về ung thư phổi?" | ClinicalTrials + PubMed |
| 🩺 Bệnh | "Triệu chứng tiểu đường type 2 là gì?" | PubMed + ICD-11 |
| 💉 Điều trị | "Điều trị tăng huyết áp như thế nào?" | PubMed + ClinicalTrials + OpenFDA |

---

## ⚙️ Cấu hình `.env` chi tiết

```env
# ━━━━━━ LLM API (BẮT BUỘC) ━━━━━━
OPENAI_API_KEY=your-api-key           # API key
OPENAI_BASE_URL=https://api.openai.com/v1  # Endpoint URL
OPENAI_MODEL=gpt-4o-mini              # Tên model
OPENAI_VERIFY_SSL=true                # SSL verification

# ━━━━━━ JWT (tùy chỉnh cho bảo mật) ━━━━━━
JWT_SECRET_KEY=your-secret-key        # ĐỔI giá trị này!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 giờ

# ━━━━━━ Database ━━━━━━
DATABASE_URL=sqlite+aiosqlite:///./medical_chatbot.db

# ━━━━━━ Medical APIs (OPTIONAL) ━━━━━━
# ICD-11: đăng ký miễn phí tại https://icd.who.int/icdapi
# Nếu để trống → tự động dùng fallback endpoint (không cần đăng ký)
ICD_CLIENT_ID=
ICD_CLIENT_SECRET=

# PubMed: có key thì rate limit 10 req/s, không có thì 3 req/s
PUBMED_API_KEY=

# ━━━━━━ App ━━━━━━
APP_NAME=Medical Chatbot
APP_ENV=development
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

> 📌 **Lưu ý:** Chỉ cần điền `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` là chạy được. Các Medical API (PubMed, ICD-11, RxNorm, ClinicalTrials, OpenFDA) đều **miễn phí và không cần API key**.

---

## 🔌 5 Medical APIs

| # | API | Dữ liệu | Key? | Docs |
|---|-----|---------|------|------|
| 1 | **PubMed E-utilities** | Bài báo nghiên cứu y sinh | ❌ Không cần | [Link](https://www.ncbi.nlm.nih.gov/books/NBK25501/) |
| 2 | **WHO ICD-11** | Phân loại bệnh quốc tế | ❌ Có fallback | [Link](https://icd.who.int/icdapi) |
| 3 | **NLM RxNorm** | Thông tin thuốc chuẩn hóa | ❌ Không cần | [Link](https://rxnav.nlm.nih.gov/RxNormAPIs.html) |
| 4 | **ClinicalTrials.gov** | Thử nghiệm lâm sàng | ❌ Không cần | [Link](https://clinicaltrials.gov/data-api/about-api) |
| 5 | **OpenFDA** | Tác dụng phụ, thu hồi thuốc | ❌ Không cần | [Link](https://open.fda.gov/apis/) |

---

## 🐛 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|-----|------------|----------|
| `Failed to fetch` khi đăng ký | Backend chưa chạy hoặc sai port | Kiểm tra backend đang chạy ở port 8000 |
| Chat trả về "Xin lỗi, đã xảy ra lỗi" | API key LLM sai hoặc hết hạn | Kiểm tra `OPENAI_API_KEY` trong `.env` |
| `CORS error` trong console | Frontend/Backend khác port | Thêm URL frontend vào `CORS_ORIGINS` |
| PubMed trả về ít kết quả | Rate limit (3 req/s) | Đợi 1-2s rồi thử lại, hoặc thêm `PUBMED_API_KEY` |
| Port 3000 đã bị chiếm | Có app khác dùng port 3000 | `npx kill-port 3000` hoặc đổi port frontend |

---

## 📚 Tham khảo

- [CLARA: Clinical Agent for Retrieval & Analysis](https://arxiv.org/abs/2503.05754) — Kiến trúc Agentic RAG gốc
- [PubMed E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [WHO ICD-11 API](https://icd.who.int/icdapi)
- [NLM RxNorm API](https://rxnav.nlm.nih.gov/RxNormAPIs.html)
- [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/about-api)
- [OpenFDA API](https://open.fda.gov/apis/)

---

## ⚕️ Disclaimer

> **⚠️ Thông tin do chatbot cung cấp chỉ mang tính tham khảo cho học tập và nghiên cứu. KHÔNG thay thế tư vấn y khoa chuyên nghiệp. Nếu bạn có vấn đề sức khỏe, hãy liên hệ bác sĩ.**

---

## 📄 License

MIT License — Dự án học tập, sử dụng tự do.
