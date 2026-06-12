# Codebase - Tro thu AI Moni

Đây là nơi nhóm nộp toàn bộ phần code của prototype. Mục tiêu là để giảng viên và các nhóm khác nhìn được sản phẩm chạy như thế nào, và mỗi thành viên đã đóng góp ra sao.

## Cấu trúc thư mục

```
codebase/
├── frontend/              # React + Vite (giao diện chat)
│   ├── src/
│   │   ├── components/    # Các component UI
│   │   ├── pages/         # ChatPage
│   │   └── services/      # chatService.js (gọi API)
│   └── package.json
├── src/                   # Python backend (FastAPI + ReAct Agent)
│   ├── api/               # FastAPI endpoints
│   ├── agent/             # ReAct Agent logic
│   ├── core/              # LLM providers (OpenAI, Gemini, Local)
│   ├── data/              # Mock finance data (JSON)
│   ├── tools/             # Finance tools cho agent
│   └── telemetry/         # Logger
└── .env                   # Environment variables
```

## Hướng dẫn chạy

### Yêu cầu

- **Node.js** >= 18
- **Python** >= 3.10
- **pip** (Python package manager)

### Bước 1: Cài đặt Python dependencies

```bash
cd codebase
pip install fastapi uvicorn python-dotenv pydantic openai
```

### Bước 2: Cấu hình Environment Variables

Tạo file `.env` trong thư mục `codebase/`:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o

# Hoặc dùng Gemini
# GEMINI_API_KEY=your_gemini_api_key_here
# DEFAULT_PROVIDER=gemini

# Hoặc dùng Local model (GGUF)
# LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
# DEFAULT_PROVIDER=local
```

### Bước 3: Chạy Backend (Terminal 1)

```bash
cd codebase
uvicorn src.api.main:app --reload --port 8000
```

Backend sẽ chạy tại: `http://127.0.0.1:8000`

### Bước 4: Cài đặt Frontend dependencies (Terminal 2)

```bash
cd codebase/frontend
npm install
```

### Bước 5: Chạy Frontend (Terminal 2)

```bash
cd codebase/frontend
npm run dev
```

Frontend sẽ chạy tại: `http://localhost:5173`

### Bước 6: Mở ứng dụng

Truy cập `http://localhost:5173` trên trình duyệt. Nhập tin nhắn vào ô chat để trò chuyện với Moni.

---

## API Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/llm` | POST | Gọi LLM trực tiếp |
| `/agent` | POST | Gọi ReAct Agent với finance tools |

### Ví dụ gọi API

```bash
curl -X POST http://127.0.0.1:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tôi còn bao nhiêu tiền?", "max_steps": 10}'
```

---

## Công nghệ sử dụng

### Frontend
- **React 19** - UI framework
- **Vite 8** - Build tool
- **CSS** - Styling (CSS custom properties)

### Backend
- **FastAPI** - Web framework
- **OpenAI API** - LLM provider (GPT-4o)
- **ReAct Agent** - Reasoning + Acting pattern

### AI Tools
- `get_current_balance` - Xem số dư ví
- `list_transactions` - Liệt kê giao dịch
- `get_transaction_summary` - Tóm tắt thu/chi
- `get_category_breakdown` - Phân tích theo nhóm chi tiêu
- `create_saving_plan` - Lập kế hoạch tiết kiệm
- `create_moni_note` - Tạo ghi chú tạm thời

---

## Phân công

| Thành viên | Vai trò | Công việc |
|------------|---------|-----------|
| ... | ... | ... |

---

## Lưu ý

- Không commit `.env` hoặc API key thật
- Dùng `.env.example` để mô tả các biến môi trường
- Backend phải chạy trước khi mở frontend
