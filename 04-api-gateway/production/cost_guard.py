"""
Cost Guard — Bảo Vệ Budget LLM (Redis-backed)

Mục tiêu: Tránh bill bất ngờ từ LLM API.
- Đếm tokens đã dùng mỗi ngày
- Cảnh báo khi gần hết budget
- Block khi vượt budget

Trong production: lưu trong Redis để đồng bộ giữa các instance và tránh mất dữ liệu.
"""
import time
import logging
import os
import redis
from dataclasses import dataclass, field
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ============================================================
# Redis Configuration
# ============================================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    _redis = redis.from_url(REDIS_URL, decode_responses=True)
    _redis.ping()
    USE_REDIS = True
    logger.info(f"CostGuard: Connected to Redis at {REDIS_URL}")
except Exception as e:
    USE_REDIS = False
    _redis = None
    logger.warning(f"CostGuard: Redis unavailable ({e}), falling back to in-memory storage")

# Giá token (tham khảo, thay đổi theo model)
PRICE_PER_1K_INPUT_TOKENS = 0.00015   # GPT-4o-mini: $0.15/1M input
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006   # GPT-4o-mini: $0.60/1M output

@dataclass
class UsageRecord:
    user_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0
    day: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

    @property
    def total_cost_usd(self) -> float:
        input_cost = (self.input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
        output_cost = (self.output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)

class CostGuard:
    def __init__(
        self,
        daily_budget_usd: float = 1.0,       # $1/ngày per user
        global_daily_budget_usd: float = 10.0, # $10/ngày tổng cộng
        warn_at_pct: float = 0.8,              # Cảnh báo khi dùng 80%
    ):
        self.daily_budget_usd = daily_budget_usd
        self.global_daily_budget_usd = global_daily_budget_usd
        self.warn_at_pct = warn_at_pct

        # Fallback store if Redis is unavailable
        self._records: dict[str, UsageRecord] = {}
        self._global_cost = 0.0

    def _get_record(self, user_id: str) -> UsageRecord:
        today = time.strftime("%Y-%m-%d")

        if USE_REDIS:
            key = f"cost_guard:user:{today}:{user_id}"
            data = _redis.hgetall(key)
            if not data:
                return UsageRecord(user_id=user_id, day=today)

            return UsageRecord(
                user_id=user_id,
                input_tokens=int(data.get("input_tokens", 0)),
                output_tokens=int(data.get("output_tokens", 0)),
                request_count=int(data.get("request_count", 0)),
                day=today
            )

        # Fallback in-memory
        record = self._records.get(user_id)
        if not record or record.day != today:
            self._records[user_id] = UsageRecord(user_id=user_id, day=today)
        return self._records[user_id]

    def check_budget(self, user_id: str) -> None:
        """
        Kiểm tra budget trước khi gọi LLM.
        Raise 402 nếu vượt budget.
        """
        today = time.strftime("%Y-%m-%d")
        record = self._get_record(user_id)

        # 1. Global budget check
        if USE_REDIS:
            global_cost = float(_redis.get(f"cost_guard:global:{today}") or 0)
        else:
            global_cost = self._global_cost

        if global_cost >= self.global_daily_budget_usd:
            logger.critical(f"GLOBAL BUDGET EXCEEDED: ${global_cost:.4f}")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable due to budget limits. Try again tomorrow.",
            )

        # 2. Per-user budget check
        if record.total_cost_usd >= self.daily_budget_usd:
            raise HTTPException(
                status_code=402,  # Payment Required
                detail={
                    "error": "Daily budget exceeded",
                    "used_usd": record.total_cost_usd,
                    "budget_usd": self.daily_budget_usd,
                    "resets_at": "midnight UTC",
                },
            )

        # 3. Warning khi gần hết budget
        if record.total_cost_usd >= self.daily_budget_usd * self.warn_at_pct:
            logger.warning(
                f"User {user_id} at {record.total_cost_usd/self.daily_budget_usd*100:.0f}% budget"
            )

    def record_usage(
        self, user_id: str, input_tokens: int, output_tokens: int
    ) -> UsageRecord:
        """Ghi nhận usage sau khi gọi LLM xong."""
        today = time.strftime("%Y-%m-%d")

        # Calculate cost for this request
        request_cost = (input_tokens / 1000 * PRICE_PER_1K_INPUT_TOKENS +
                        output_tokens / 1000 * PRICE_PER_1K_OUTPUT_TOKENS)

        if USE_REDIS:
            # Atomically increment user usage
            user_key = f"cost_guard:user:{today}:{user_id}"
            _redis.hincrby(user_key, "input_tokens", input_tokens)
            _redis.hincrby(user_key, "output_tokens", output_tokens)
            _redis.hincrby(user_key, "request_count", 1)
            _redis.expire(user_key, 172800)  # 48h TTL

            # Atomically increment global cost
            global_key = f"cost_guard:global:{today}"
            _redis.incrbyfloat(global_key, request_cost)
            _redis.expire(global_key, 172800)  # 48h TTL

            return self._get_record(user_id)

        # Fallback in-memory
        record = self._get_record(user_id)
        record.input_tokens += input_tokens
        record.output_tokens += output_tokens
        record.request_count += 1
        self._global_cost += request_cost

        logger.info(
            f"Usage: user={user_id} req={record.request_count} "
            f"cost=${record.total_cost_usd:.4f}/{self.daily_budget_usd}"
        )
        return record

    def get_usage(self, user_id: str) -> dict:
        record = self._get_record(user_id)
        return {
            "user_id": user_id,
            "date": record.day,
            "requests": record.request_count,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "cost_usd": record.total_cost_usd,
            "budget_usd": self.daily_budget_usd,
            "budget_remaining_usd": max(0, self.daily_budget_usd - record.total_cost_usd),
            "budget_used_pct": round(record.total_cost_usd / self.daily_budget_usd * 100, 1),
        }


# Singleton
cost_guard = CostGuard(daily_budget_usd=1.0, global_daily_budget_usd=10.0)
