# Day06-C401-TeamE4

## Danh sách thành viên

| Mã HV | Họ và tên |
|---|---|
| 2A202600803 | Trần Đức Tâm |
| 2A202600600 | Kim Hồng Giang |
| 2A202600799 | TranNgocThuy |
| 2A202600561 | Lê Quốc Bảo |
| 2A202600715 | Lê Quang Miền |

## Mô tả ngắn sản phẩm

**Trợ thủ AI - Moni** là prototype chatbot hỗ trợ quản lý tài chính cá nhân cho người trẻ, đặc biệt là sinh viên và người mới đi làm đang muốn theo dõi chi tiêu và lập kế hoạch tiết kiệm ngắn hạn.

Sản phẩm tập trung giải quyết hai vấn đề chính:

- người dùng ngại nhập liệu tài chính thủ công;
- trải nghiệm dễ bị gián đoạn khi hệ thống lỗi trong lúc đang thiết lập mục tiêu tiết kiệm.

Trong prototype hiện tại, Moni có thể:

- trò chuyện với người dùng theo giao diện chat;
- gợi ý kế hoạch tiết kiệm dựa trên mục tiêu và thời gian;
- tóm tắt chi tiêu, số dư và nhóm chi tiêu nổi bật từ dữ liệu mock;
- tạo phương án dự phòng `Moni Note` khi flow chính gặp lỗi.

Repo gồm 2 phần chính:

- `spec/`: hướng dẫn form SPEC của bài
- `codebase/`: toàn bộ code prototype frontend và backend

---

## Production Deployment

### Backend API (Railway)

**URL:** https://moni-ai-production.up.railway.app

**Endpoints:**

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| GET | `/` | Thông tin app |
| POST | `/agent` | Chat với Moni AI Agent |
| POST | `/llm` | Gọi LLM trực tiếp |
| POST | `/save-plan` | Lưu kế hoạch tiết kiệm |

**Test:**
```bash
curl https://moni-ai-production.up.railway.app/health
curl -X POST https://moni-ai-production.up.railway.app/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Số dư của tôi là bao nhiêu?", "max_steps": 5}'
```

### Frontend (Vercel)

**URL:** https://moni-agent.vercel.app

### CI/CD

GitHub Actions tự động:
- **Backend:** Test → Deploy lên Railway
- **Frontend:** Test → Build → Deploy lên Vercel


