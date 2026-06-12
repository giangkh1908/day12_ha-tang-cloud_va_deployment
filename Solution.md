# MISSION ANSWERS: Deploy Your AI Agent to Production

> **Day 12 — Hạ tầng Cloud và Deployment**
> **VinUniversity 2026**

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns trong `01-localhost-vs-production/develop/app.py`

| # | Vấn đề | Chi tiết |
|---|--------|----------|
| 1 | **API key hardcode** | `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"` — lộ key nếu push lên GitHub |
| 2 | **Database URL hardcode** | `DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"` — lộ credentials |
| 3 | **Port cố định** | `port=8000` — không đọc từ `PORT` env var, không deploy được lên Railway/Render |
| 4 | **Host cố định localhost** | `host="localhost"` — chỉ chạy được local, không nhận kết nối từ container |
| 5 | **Debug reload trong production** | `reload=True` — nguy hiểm khi deploy thật |
| 6 | **Không có health check** | Không có `/health` endpoint → platform không biết khi nào agent die |
| 7 | **Print thay vì logging** | `print()` không có structured format, không gửi được log aggregator |
| 8 | **Log ra secret** | `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` — log API key ra console |
| 9 | **Không graceful shutdown** | Nếu kill process, request đang xử lý bị mất |
| 10 | **Endpoint dùng query param** | `def ask_agent(question: str)` — question là query param, không phải JSON body |

### Exercise 1.3: So sánh Basic vs Advanced

| Feature | Basic (develop/) | Advanced (production/) | Tại sao quan trọng? |
|---------|-----------------|----------------------|---------------------|
| **Config** | Hardcode trong code | `config.py` đọc từ env vars | Dễ thay đổi giữa dev/staging/prod, không lộ secret |
| **Health check** | Không có | `GET /health` + `GET /ready` | Platform biết khi nào restart container |
| **Logging** | `print()` text thường | JSON structured logging (`json.dumps`) | Dễ parse trong Datadog/Loki, search được |
| **Shutdown** | Đột ngột (Ctrl+C) | Graceful: đợi request hoàn thành | Không mất dữ liệu khi deploy rolling update |
| **CORS** | Không có | Configurable via env | Bảo mật, chỉ cho phép origins được phép |
| **Port binding** | `localhost:8000` | `0.0.0.0:$PORT` | Chạy được trong Docker container |
| **Input validation** | Không có | Pydantic + raise 422 nếu thiếu | Tránh lỗi không rõ nguyên nhân |

---

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile cơ bản (`02-docker/develop/Dockerfile`)

**1. Base image là gì?** `python:3.11` — image đầy đủ (~1 GB), bao gồm cả build tools.

**2. Working directory là gì?** `/app` — nơi code được copy vào trong container.

**3. Tại sao COPY requirements.txt trước?**
Docker layer cache: nếu `requirements.txt` không thay đổi, layer cài pip được cache → build nhanh hơn. Ngược lại, nếu COPY code trước, mỗi lần sửa code đều phải cài lại dependencies.

**4. CMD vs ENTRYPOINT khác nhau thế nào?**
- `CMD`: default command, có thể override khi run (`docker run my-agent python other.py`)
- `ENTRYPOINT`: fixed command, không dễ override
- Thường dùng ENTRYPOINT cho executable, CMD cho default args

### Exercise 2.2: Build và run

```bash
# Từ project root
cd D:\Vin\day12_ha-tang-cloud_va_deployment

# Build
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run
docker run -p 8000:8000 my-agent:develop

# Test
curl -X POST "http://localhost:8000/ask?question=What+is+Docker"
```

### Exercise 2.3: Multi-stage build (`02-docker/production/Dockerfile`)

**Stage 1 (builder):**
- Base: `python:3.11-slim`
- Cài `gcc`, `libpq-dev` (build tools)
- `pip install --user` để install vào `/root/.local`

**Stage 2 (runtime):**
- Base: `python:3.11-slim` (fresh, sạch)
- Chỉ copy `site-packages` từ builder → không có build tools
- Tạo non-root user (`appuser`) — security best practice
- Image chỉ có Python + code + dependencies → **nhỏ hơn nhiều** (vài trăm MB thay vì ~1GB)

**Tại sao image nhỏ hơn?**
Build tools (gcc, headers) chiếm nhiều dung lượng nhưng chỉ cần lúc cài package. Runtime không cần chúng.

### Exercise 2.4: Docker Compose stack (`02-docker/production/docker-compose.yml`)

**Services:**
1. **agent** — FastAPI AI agent (2 workers)
2. **redis** — Session cache + rate limiting (redis:7-alpine)
3. **qdrant** — Vector database cho RAG
4. **nginx** — Reverse proxy + load balancer

**Architecture:**
```
Client → Nginx (:80/:443) → Agent (:8000) → Redis (:6379)
                                          → Qdrant (:6333)
```

**Network:** Tất cả services chung network `internal` (bridge), chỉ Nginx expose port ra ngoài.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway (`03-cloud-deployment/railway/railway.toml`)

**Config:**
- Builder: `NIXPACKS` (auto-detect Python)
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health` (timeout 30s)
- Restart policy: ON_FAILURE, max 3 retries

**Railway tự inject:** `PORT`, `RAILWAY_PUBLIC_DOMAIN`

**Deploy steps:**
```bash
npm i -g @railway/cli
railway login
railway init
railway variables set PORT=8000 AGENT_API_KEY=my-secret-key
railway up
railway domain
```

### Exercise 3.2: Render (`03-cloud-deployment/render/render.yaml`)

**So sánh Railway vs Render:**

| Aspect | Railway | Render |
|--------|---------|--------|
| Config format | `railway.toml` | `render.yaml` (Blueprint) |
| Build | Nixpacks auto hoặc Dockerfile | `buildCommand` + `startCommand` |
| Region config | Railway tự chọn | `region: singapore` |
| Redis | Manual | Built-in Redis add-on |
| Auto-deploy | CLI | Git push → auto |

### Exercise 3.3: GCP Cloud Run (`cloudbuild.yaml` + `service.yaml`)

**CI/CD Pipeline:**

**Key features:**


---

## Part 4: API Security

### Exercise 4.1: API Key authentication (`04-api-gateway/develop/app.py`)

**API key được check ở đâu?**
Trong dependency `verify_api_key()` — check header `X-API-Key`:
```python
def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key:
        raise HTTPException(401, "Missing API key")
    if api_key != API_KEY:
        raise HTTPException(403, "Invalid API key")
    return api_key
```

**Sai key →** 403 Forbidden. **Thiếu key →** 401 Unauthorized.

**Rotate key:** Set env `AGENT_API_KEY` mới, restart app.

### Exercise 4.2: JWT authentication (`04-api-gateway/production/auth.py`)

**JWT Flow:**
1. `POST /auth/token` với `{username, password}` → server verify → trả JWT
2. Client gửi JWT trong header `Authorization: Bearer <token>`
3. Server verify signature với `SECRET_KEY` + `HS256` → extract `user_id`, `role`
4. Token có TTL 60 phút

**Demo users:**
- `student / demo123` — role: user, 10 req/min
- `teacher / teach456` — role: admin, 100 req/min

**Test:**
```bash
# Lấy token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "student", "password": "demo123"}'

# Dùng token
TOKEN="<token>"
curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

### Exercise 4.3: Rate limiting (`04-api-gateway/production/rate_limiter.py`)

**Algorithm:** **Sliding Window Counter**
- Mỗi user có 1 deque chứa timestamps của requests
- Request mới đến → xóa timestamps cũ (ngoài window 60s)
- Nếu >= max_requests → 429 Too Many Requests

**Limits:**
- User: 10 requests/phút
- Admin: 100 requests/phút

**Test:**
```bash
# Gọi liên tục 20 lần → request 11+ sẽ bị 429
for i in {1..20}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done
```

### Exercise 4.4: Cost guard (`04-api-gateway/production/cost_guard.py`)

**Logic:**
- Mỗi user có daily budget $1.00
- Global daily budget $10.00
- Tính cost dựa trên GPT-4o-mini pricing: $0.15/1M input, $0.60/1M output
- Cảnh báo khi dùng 80% budget
- Raise 402 (Payment Required) khi hết budget
- Raise 503 khi global budget exhausted

**Redis implementation (production):**
```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)
    return True
```

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks (`05-scaling-reliability/develop/app.py`)

**`GET /health` (Liveness probe):**
- Trả về status "ok" hoặc "degraded"
- Check memory via psutil
- Return uptime, version, timestamp, environment

**`GET /ready` (Readiness probe):**
- Trả về 200 + `{"ready": True}` nếu `_is_ready == True`
- Trả về 503 nếu đang startup/shutdown
- Load balancer dùng để quyết định route traffic

### Exercise 5.2: Graceful shutdown

- Signal handler bắt `SIGTERM` và `SIGINT`
- uvicorn config: `timeout_graceful_shutdown=30`
- Middleware đếm `_in_flight_requests` (increment trước, decrement trong finally)
- Shutdown lifecycle: set `_is_ready = False` → đợi in-flight requests hoàn thành (tối đa 30s)
- Từ chối request mới ngay lập tức

**Test:**
```bash
python app.py &
PID=$!
curl http://localhost:8000/ask?question=Long+task &
kill -TERM $PID
# Request vẫn hoàn thành trước khi process tắt
```

### Exercise 5.3: Stateless design (`05-scaling-reliability/production/app.py`)

**Anti-pattern (develop/):**
```python
conversation_history = {}  # state trong memory
# Khi scale lên 3 instances → mỗi instance có memory riêng → mất context!
```

**Correct pattern (production/):**
```python
def save_session(session_id, data):
    _redis.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))

def load_session(session_id):
    data = _redis.get(f"session:{session_id}")
    return json.loads(data) if data else {}
```

State trong Redis → bất kỳ instance nào cũng đọc được session → stateless.

### Exercise 5.4: Load balancing (Nginx)

```
Client → Nginx (:8080) → Agent1 (:8000)
                        → Agent2 (:8000)
                        → Agent3 (:8000)
```

- Nginx round-robin requests giữa các instances
- `proxy_next_upstream error timeout http_503` → retry nếu instance die
- `add_header X-Served-By $upstream_addr` → thấy rõ instance nào serve

```bash
docker compose up --scale agent=3
```

### Exercise 5.5: Test stateless

```bash
cd 05-scaling-reliability/production
docker compose up --scale agent=3
python test_stateless.py
```

Kết quả: Dù mỗi request được serve bởi instance khác nhau, conversation history vẫn intact nhờ Redis lưu session.

---



## Tổng kết

### Key concepts đã học:

1. **12-Factor App** — Config từ env, JSON logging, stateless processes
2. **Docker** — Multi-stage build, non-root user, HEALTHCHECK, layer caching
3. **Cloud Deployment** — Railway CLI, Render Blueprint, GCP Cloud Run CI/CD
4. **API Security** — API Key, JWT (HS256), Sliding Window Rate Limiter, Cost Guard
5. **Scaling & Reliability** — Liveness/Readiness probes, Graceful shutdown, Stateless with Redis, Nginx load balancing

### Commands tổng hợp:

```bash
# Part 1 — Run locally
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py
curl "http://localhost:8000/ask?question=Hello" -X POST

# Part 2 — Docker single-stage
cd D:\Vin\day12_ha-tang-cloud_va_deployment
docker build -f 02-docker/develop/Dockerfile -t my-agent:3.11 .
docker run -p 8000:8000 my-agent:3.11

# Part 2 — Docker multi-stage
docker build -f 02-docker/production/Dockerfile -t agent-production:3.11 .
docker images | grep agent

# Part 2 — Compose full stack
cd 02-docker/production
docker compose up

# Part 4 — API Key Auth
cd 04-api-gateway/develop
$env:AGENT_API_KEY="my-secret-key"; python app.py
curl -H "X-API-Key: my-secret-key" http://localhost:8000/ask -X POST ^
  -H "Content-Type: application/json" -d '{"question":"hello"}'

# Part 4 — JWT + Rate Limiting + Cost Guard
cd 04-api-gateway/production
python app.py
curl -X POST http://localhost:8000/auth/token ^
  -H "Content-Type: application/json" ^
  -d '{"username": "student", "password": "demo123"}'

# Part 5 — Scale stateless agent
cd 05-scaling-reliability/production
docker compose up --scale agent=3
python test_stateless.py


## 🚀 Moni Agent — Production Deployment

### Backend API (Railway)
**URL:** https://moni-ai-production.up.railway.app

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | App info |
| `/health` | GET | Health check |
| `/ready` | GET | Readiness probe |
| `/metrics` | GET | Metrics (requires API Key) |
| `/agent` | POST | Chat with Moni AI Agent |
| `/llm` | POST | Direct LLM call |
| `/save-plan` | POST | Save saving plan |

**Test:**
```bash
curl https://moni-ai-production.up.railway.app/health

curl -X POST https://moni-ai-production.up.railway.app/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Số dư của tôi là bao nhiêu?", "max_steps": 5}'
```

### Frontend (Vercel)
**URL:** https://frontend-two-jade-74.vercel.app

> ⚠️ Cần set `VITE_API_URL = https://moni-ai-production.up.railway.app` trong Vercel Dashboard (Settings → Environment Variables) → Redeploy để frontend gọi được backend.

### CI/CD
- **File:** `.github/workflows/ci-cd.yml`
- **Trigger:** Push/RP vào `main`
- **Backend:** Test → `railway up` deploy
- **Frontend:** Build → `vercel deploy --prod`
- **Secrets cần set:** `RAILWAY_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

### Kiến trúc Production
```
User → Vercel (React) → API proxy → Railway (FastAPI)
                                        └→ ReAct Agent → OpenAI LLM
                                                       → Finance Tools
```
