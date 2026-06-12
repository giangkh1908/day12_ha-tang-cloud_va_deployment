# Productionization Plan — Moni AI Agent

> Dựa trên bài Day 12: Hạ tầng Cloud và Deployment  
> Áp dụng cho dự án Day06-C401-TeamE4 (Moni - AI Personal Finance Assistant)

---

## Kiến trúc hiện tại

```
User Browser → React (Vite :5173) → Vite Proxy → FastAPI (:8000) → ReAct Agent → LLM API
                                                                              → Finance Tools
                                                                              → finance_data.json
```

## Kiến trúc mục tiêu (Production)

```
User Browser → Vercel (CDN) ─→ Frontend (React build, static)
                             └→ API proxy → Railway (FastAPI backend)
                                                  └→ ReAct Agent
                                                           └→ LLM API
                                                           └→ Finance Tools + JSON data

- Backend: Docker → Railway → API URL: https://moni-agent.railway.app
- Frontend: Vite build → Vercel → URL: https://moni-agent.vercel.app
```

---

## Step-by-Step Plan

### Step 1: Cấu trúc thư mục mới

```
Day06-C401-TeamE4/
├── backend/                          # Docker build context cho backend
│   ├── Dockerfile                    # Multi-stage backend (python:3.11-slim)
│   └── requirements.txt
│
├── codebase/
│   ├── src/                          # Python backend code (FastAPI + ReAct Agent)
│   │   ├── api/main.py               # Production-ready: health, auth, rate limit, cost guard
│   │   ├── agent/agent.py
│   │   ├── core/                     # LLM providers
│   │   ├── tools/finance_tools.py
│   │   ├── data/finance_data.json
│   │   └── telemetry/
│   └── frontend/                     # React frontend (deploy lên Vercel)
│       ├── src/
│       ├── vercel.json               # Vercel deploy config
│       └── package.json
│
├── docker-compose.yml                # Backend service (local test)
├── railway.toml                      # Railway deploy config
├── .dockerignore
└── .gitignore
```

### Step 2: Backend — Thêm production features

**File: `backend/src/api/main.py`** (sửa)

```python
# Thêm:
# 1. Health check: GET /health
# 2. Readiness probe: GET /ready
# 3. Graceful shutdown (SIGTERM)
# 4. API Key authentication (X-API-Key header)
# 5. Rate limiting (Sliding Window, 30 req/min)
# 6. Cost guard (daily budget $5)
# 7. Security headers (middleware)
# 8. Structured JSON logging (đã có)
# 9. PORT từ env var
# 10. 0.0.0.0 binding
```

### Step 3: Backend Dockerfile (Multi-stage)

```
Stage 1 (builder):  python:3.11-slim + pip install
Stage 2 (runtime):  python:3.11-slim + non-root user + copy site-packages
```

### Step 4: Frontend — VITE_API_URL env

- `chatService.js` dùng `import.meta.env.VITE_API_URL || ''`
- Dev: không set → Vite proxy → localhost:8000
- Prod (Vercel): set `VITE_API_URL=https://moni-agent.railway.app` trong Vercel Dashboard

### Step 5: Vercel config (`vercel.json`)

- Build: Vite build → output `dist/`
- Rewrites: tất cả route fallback về `index.html` (SPA)
- Deploy: Vercel CLI hoặc GitHub integration

### Step 6: docker-compose.yml (backend-only, local test)

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    healthcheck: /health
```

### Step 7: Railway deployment (backend API)

- `railway.toml` → `backend/Dockerfile`
- Railway build Docker → deploy → public URL
- Set env vars: `OPENAI_API_KEY`, `MONI_API_KEY`, `ENVIRONMENT=production`

### Step 8: Vercel deployment (frontend)

- Deploy thư mục `codebase/frontend/`
- Set `VITE_API_URL` = Railway URL trong Vercel Dashboard
- Vercel build → deploy → public URL

---

## File đã tạo/sửa

| # | File | Action | Mô tả |
|---|------|--------|-------|
| 1 | `backend/Dockerfile` | Tạo mới | Multi-stage backend (python:3.11-slim) |
| 2 | `backend/requirements.txt` | Tạo mới | Dependencies |
| 3 | `codebase/src/api/main.py` | Sửa | Thêm /health, /ready, /metrics, auth, rate limit, cost guard, graceful shutdown |
| 4 | `codebase/frontend/src/services/chatService.js` | Sửa | Dùng `VITE_API_URL` env var thay vì hardcode |
| 5 | `codebase/frontend/vercel.json` | Tạo mới | Vercel deploy config (build + SPA rewrite) |
| 6 | `docker-compose.yml` | Tạo mới | Backend service cho local test |
| 7 | `railway.toml` | Tạo mới | Railway deploy config |
| 8 | `.dockerignore` | Tạo mới | Docker ignore rules |
| 9 | `.env.production.example` | Tạo mới | Production env mẫu |

---

Anh thấy plan này ổn chưa? Nếu OK em sẽ bắt tay vào code từng file.
