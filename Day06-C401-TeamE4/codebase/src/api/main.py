import os
import signal
import time
import json
import logging
from typing import Any, Dict, Optional
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

load_dotenv()

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.tools.finance_tools import FINANCE_TOOLS, save_saving_plan

# ── Structured JSON logging ──
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("moni")

# ── Globals ──
START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# ── Rate limiter (in-memory sliding window) ──
_rate_windows: Dict[str, deque] = defaultdict(deque)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

def check_rate_limit(key: str):
    now = time.time()
    window = _rate_windows[key]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {RATE_LIMIT_PER_MINUTE} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)

# ── Cost guard ──
_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")
DAILY_BUDGET_USD = float(os.getenv("DAILY_BUDGET_USD", "5.0"))

def check_and_record_cost(input_tokens: int, output_tokens: int):
    global _daily_cost, _cost_reset_day
    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today
    if _daily_cost >= DAILY_BUDGET_USD:
        raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
    cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
    _daily_cost += cost

# ── API Key auth (optional) ──
API_KEY = os.getenv("MONI_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not API_KEY:
        return "public"
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
        )
    return api_key

# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({"event": "startup", "app": "Moni Agent", "version": "2.0.0"}))
    time.sleep(0.1)
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ── App ──
app = FastAPI(
    title="Moni Agent API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# ── Security headers middleware ──
@app.middleware("http")
async def moni_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration_ms = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration_ms,
        }))
        return response
    except Exception as e:
        _error_count += 1
        raise

# ── Models ──
class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: Optional[str] = None

class AgentRequest(PromptRequest):
    max_steps: int = Field(default=10, ge=1, le=20)

class SavePlanRequest(BaseModel):
    goal_name: str = Field(..., min_length=1)
    goal_amount: float = Field(..., gt=0)
    months: int = Field(..., ge=1, le=120)
    start_date: Optional[str] = None
    reminder_day: int = Field(default=5, ge=1, le=31)

# ── Provider factory ──
def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()

    if provider_name == "openai":
        from src.core.openai_provider import OpenAIProvider
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        return OpenAIProvider(model_name=model_name, api_key=api_key)

    if provider_name == "gemini":
        from src.core.gemini_provider import GeminiProvider
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        return GeminiProvider(model_name=model_name, api_key=api_key)

    if provider_name == "local":
        from src.core.local_provider import LocalProvider
        model_path = os.getenv("LOCAL_MODEL_PATH")
        if not model_path:
            raise HTTPException(status_code=500, detail="LOCAL_MODEL_PATH is required when DEFAULT_PROVIDER=local.")
        return LocalProvider(model_path=model_path)

    raise HTTPException(status_code=400, detail=f"Unsupported DEFAULT_PROVIDER: {provider_name}")

def get_react_agent(provider: LLMProvider = Depends(get_llm_provider)) -> ReActAgent:
    return ReActAgent(provider, FINANCE_TOOLS)

# ── Health endpoints ──
@app.get("/health")
def health():
    status = "ok"
    return {
        "status": status,
        "version": "2.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True, "uptime_seconds": round(time.time() - START_TIME, 1)}

@app.get("/metrics")
def metrics(_key: str = Depends(verify_api_key)):
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "daily_cost_usd": round(_daily_cost, 4),
        "daily_budget_usd": DAILY_BUDGET_USD,
    }

# ── Existing endpoints ──
@app.post("/llm")
def generate_with_llm(
    request: PromptRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> Dict[str, Any]:
    check_rate_limit("llm")
    try:
        result = provider.generate(request.prompt, system_prompt=request.system_prompt)
    except Exception as exc:
        _error_count += 1
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    tokens = result.get("usage", {})
    pt = tokens.get("prompt_tokens", 0) or 0
    ct = tokens.get("completion_tokens", 0) or 0
    check_and_record_cost(pt, ct)

    return {
        "success": True,
        "mode": "llm",
        "model": provider.model_name,
        "response": result.get("content", ""),
        "usage": result.get("usage", {}),
        "latency_ms": result.get("latency_ms"),
        "provider": result.get("provider"),
    }

@app.post("/agent")
def generate_with_agent(
    request: AgentRequest,
    request_obj: Request,
    agent: ReActAgent = Depends(get_react_agent),
    _key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    check_rate_limit(_key[:8])
    agent.max_steps = request.max_steps

    try:
        answer = agent.run(request.prompt)
    except Exception as exc:
        _error_count += 1
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return answer

@app.post("/save-plan")
def direct_save_plan(
    request: SavePlanRequest,
    _key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    try:
        result = save_saving_plan(
            goal_name=request.goal_name,
            goal_amount=request.goal_amount,
            months=request.months,
            start_date=request.start_date,
            reminder_day=request.reminder_day,
        )
    except Exception as exc:
        _error_count += 1
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Save failed"))

    return result

@app.get("/")
def root():
    return {
        "app": "Moni Agent",
        "version": "2.0.0",
        "endpoints": {
            "health": "GET /health",
            "ready": "GET /ready",
            "chat": "POST /agent",
            "llm": "POST /llm",
            "save_plan": "POST /save-plan",
        },
    }

# ── Graceful shutdown ──
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting Moni Agent on {host}:{port}")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        timeout_graceful_shutdown=30,
    )
