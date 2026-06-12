# src/tools/finance_tools.py

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, date
from typing import Any, Dict, List, Optional


DEFAULT_DATA_PATH = str(Path(__file__).parent.parent / "data" / "finance_data.json")


# -----------------------------
# Internal helpers
# -----------------------------

def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD date string. Return None if value is empty."""
    if value in (None, "", "null"):
        return None

    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid date format '{value}'. Expected YYYY-MM-DD.") from exc


def _format_vnd(amount: float | int) -> str:
    """Format number as Vietnamese currency text."""
    amount_int = int(round(float(amount)))
    return f"{amount_int:,}".replace(",", ".") + " VND"


def _load_data(data_path: str = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    path = Path(data_path)

    if not path.exists():
        return {
            "success": False,
            "error": "FILE_NOT_FOUND",
            "message": f"Finance data file not found: {data_path}",
        }

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": "JSON_READ_ERROR",
            "message": f"Invalid JSON file: {exc}",
        }

    if not isinstance(data, dict):
        return {
            "success": False,
            "error": "INVALID_DATA_SCHEMA",
            "message": "Finance data must be a JSON object.",
        }

    data.setdefault("user", {})
    data.setdefault("wallet", {})
    data.setdefault("transactions", [])
    data.setdefault("moni_notes", [])
    data.setdefault("saving_goals", [])

    return {
        "success": True,
        "data": data,
    }


def _save_data(data: Dict[str, Any], data_path: str = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    path = Path(data_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        return {
            "success": False,
            "error": "JSON_WRITE_ERROR",
            "message": f"Could not write finance data: {exc}",
        }

    return {
        "success": True,
        "message": "Finance data saved successfully.",
    }


def _get_transactions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    transactions = data.get("transactions", [])
    if not isinstance(transactions, list):
        return []
    return [tx for tx in transactions if isinstance(tx, dict)]


def _filter_transactions(
    transactions: List[Dict[str, Any]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    merchant: Optional[str] = None,
) -> List[Dict[str, Any]]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)

    category_norm = category.lower().strip() if category else None
    type_norm = transaction_type.lower().strip() if transaction_type else None
    merchant_norm = merchant.lower().strip() if merchant else None

    filtered = []

    for tx in transactions:
        tx_date_raw = tx.get("date")
        if not tx_date_raw:
            continue

        try:
            tx_date = _parse_date(tx_date_raw)
        except ValueError:
            continue

        if start and tx_date < start:
            continue

        if end and tx_date > end:
            continue

        if category_norm and str(tx.get("category", "")).lower().strip() != category_norm:
            continue

        if type_norm and str(tx.get("type", "")).lower().strip() != type_norm:
            continue

        if merchant_norm and merchant_norm not in str(tx.get("merchant", "")).lower():
            continue

        filtered.append(tx)

    filtered.sort(key=lambda item: item.get("date", ""))
    return filtered


def _sum_amount(transactions: List[Dict[str, Any]], tx_type: Optional[str] = None) -> float:
    total = 0.0

    for tx in transactions:
        if tx_type is not None and tx.get("type") != tx_type:
            continue

        try:
            total += float(tx.get("amount", 0))
        except (TypeError, ValueError):
            continue

    return total

def _calculate_goal_progress(goal: Dict[str, Any]) -> Dict[str, Any]:
    goal_amount = float(goal.get("goal_amount", 0) or 0)
    deposits = goal.get("deposits", [])

    saved_amount = 0.0
    for deposit in deposits:
        try:
            saved_amount += float(deposit.get("amount", 0))
        except (TypeError, ValueError):
            continue

    progress_percent = 0
    if goal_amount > 0:
        progress_percent = min(100, round(saved_amount / goal_amount * 100, 2))

    goal["saved_amount"] = int(saved_amount)
    goal["saved_amount_text"] = _format_vnd(saved_amount)
    goal["progress_percent"] = progress_percent
    goal["remaining_amount"] = max(0, int(goal_amount - saved_amount))
    goal["remaining_amount_text"] = _format_vnd(max(0, goal_amount - saved_amount))

    if progress_percent >= 100:
        goal["status"] = "completed"
    elif goal.get("status") == "completed":
        goal["status"] = "active"

    return goal


# -----------------------------
# Public tools for ReAct agent
# -----------------------------

def get_current_balance(data_path: str = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    """
    Get the user's current mock wallet balance from finance JSON.
    """

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    data = loaded["data"]
    wallet = data.get("wallet", {})
    balance = wallet.get("current_balance", 0)
    currency = data.get("user", {}).get("currency", "VND")

    try:
        balance_number = float(balance)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "INVALID_BALANCE",
            "message": "Wallet current_balance must be a number.",
        }

    return {
        "success": True,
        "ui_action": None,
        "current_balance": int(balance_number),
        "current_balance_text": _format_vnd(balance_number) if currency == "VND" else f"{balance_number} {currency}",
        "currency": currency,
        "last_updated": wallet.get("last_updated"),
        "message": "Current balance loaded successfully.",
    }


def list_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    merchant: Optional[str] = None,
    limit: int = 20,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    List transactions filtered by date range, category, type, or merchant.
    """

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    try:
        transactions = _filter_transactions(
            _get_transactions(loaded["data"]),
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type,
            merchant=merchant,
        )
    except ValueError as exc:
        return {
            "success": False,
            "error": "INVALID_DATE",
            "message": str(exc),
        }

    safe_limit = max(1, min(int(limit), 100))
    selected = transactions[:safe_limit]

    return {
        "success": True,
        "ui_action": None,
        "count": len(transactions),
        "returned": len(selected),
        "transactions": selected,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "category": category,
            "transaction_type": transaction_type,
            "merchant": merchant,
            "limit": safe_limit,
        },
        "message": f"Found {len(transactions)} transaction(s).",
    }


def get_transaction_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    Summarize income, expense, net change, and transaction count in a date range.
    """

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    try:
        transactions = _filter_transactions(
            _get_transactions(loaded["data"]),
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
    except ValueError as exc:
        return {
            "success": False,
            "error": "INVALID_DATE",
            "message": str(exc),
        }

    total_income = _sum_amount(transactions, "income")
    total_expense = _sum_amount(transactions, "expense")
    net_change = total_income - total_expense

    return {
        "success": True,
        "transaction_count": len(transactions),
        "total_income": int(total_income),
        "total_expense": int(total_expense),
        "net_change": int(net_change),
        "total_income_text": _format_vnd(total_income),
        "total_expense_text": _format_vnd(total_expense),
        "net_change_text": _format_vnd(net_change),
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "category": category,
        },
        "message": "Transaction summary calculated successfully.",
    }


def get_category_breakdown(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    Calculate expense breakdown by category in a date range.
    Only expense transactions are included.
    """

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    try:
        transactions = _filter_transactions(
            _get_transactions(loaded["data"]),
            start_date=start_date,
            end_date=end_date,
            transaction_type="expense",
        )
    except ValueError as exc:
        return {
            "success": False,
            "error": "INVALID_DATE",
            "message": str(exc),
        }

    breakdown: Dict[str, float] = {}
    total_expense = 0.0

    for tx in transactions:
        category = str(tx.get("category", "uncategorized"))
        try:
            amount = float(tx.get("amount", 0))
        except (TypeError, ValueError):
            continue

        breakdown[category] = breakdown.get(category, 0.0) + amount
        total_expense += amount

    categories = []
    for category, amount in sorted(breakdown.items(), key=lambda item: item[1], reverse=True):
        percent = (amount / total_expense * 100) if total_expense > 0 else 0
        categories.append(
            {
                "category": category,
                "amount": int(amount),
                "amount_text": _format_vnd(amount),
                "percent": round(percent, 2),
            }
        )

    return {
        "success": True,
        "ui_action": None,
        "total_expense": int(total_expense),
        "total_expense_text": _format_vnd(total_expense),
        "categories": categories,
        "transaction_count": len(transactions),
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "message": "Category breakdown calculated successfully.",
    }


def create_saving_plan(
    goal_amount: int | float,
    months: int,
    current_balance: Optional[int | float] = None,
    goal_name: str = "saving_goal",
    start_date: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH,
    save_to_json: bool = False,
) -> Dict[str, Any]:
    """
    Create a simple saving plan.

    The plan calculates how much the user needs to save per month.
    If current_balance is provided, it also computes remaining amount.
    By default this tool only simulates the plan. Set save_to_json=True to persist.
    """

    try:
        goal_amount = float(goal_amount)
        months = int(months)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "INVALID_ARGUMENT",
            "message": "goal_amount must be a number and months must be an integer.",
        }

    if goal_amount <= 0:
        return {
            "success": False,
            "error": "INVALID_GOAL_AMOUNT",
            "message": "goal_amount must be greater than 0.",
        }

    if months <= 0:
        return {
            "success": False,
            "error": "INVALID_MONTHS",
            "message": "months must be greater than 0.",
        }

    balance_used = 0.0
    if current_balance is not None:
        try:
            balance_used = max(0.0, float(current_balance))
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "INVALID_CURRENT_BALANCE",
                "message": "current_balance must be a number.",
            }

    remaining_amount = max(0.0, goal_amount - balance_used)
    monthly_required = remaining_amount / months
    weekly_required = monthly_required / 4
    daily_required = monthly_required / 30

    plan = {
        "id": f"G{int(datetime.now().timestamp())}",
        "goal_name": goal_name,
        "goal_amount": int(goal_amount),
        "goal_amount_text": _format_vnd(goal_amount),
        "current_balance_used": int(balance_used),
        "current_balance_used_text": _format_vnd(balance_used),
        "remaining_amount": int(remaining_amount),
        "remaining_amount_text": _format_vnd(remaining_amount),
        "months": months,
        "monthly_required": int(round(monthly_required)),
        "monthly_required_text": _format_vnd(monthly_required),
        "weekly_required": int(round(weekly_required)),
        "weekly_required_text": _format_vnd(weekly_required),
        "daily_required": int(round(daily_required)),
        "daily_required_text": _format_vnd(daily_required),
        "start_date": start_date,
        "reminder_day": 5,
        "saved_amount": 0,
        "saved_amount_text": _format_vnd(0),
        "progress_percent": 0,
        "deposits": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "draft",
    }

    if save_to_json:
        loaded = _load_data(data_path)
        if not loaded["success"]:
            return loaded

        data = loaded["data"]
        data.setdefault("saving_goals", [])
        data["saving_goals"].append(plan)

        saved = _save_data(data, data_path)
        if not saved["success"]:
            return saved

    return {
        "success": True,
        "ui_action": "SHOW_SAVING_PLAN_DRAFT",
        "data": {
            "plan": plan
        },
        "plan": plan,
        "saved": bool(save_to_json),
        "message": (
            f"Draft saving plan created. To reach {plan['goal_amount_text']} "
            f"in {months} month(s), the user needs to save about "
            f"{plan['monthly_required_text']} per month."
        ),
    }


def create_moni_note(
    note_type: str,
    content: str,
    amount: Optional[int | float] = None,
    date: Optional[str] = None,
    category: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    Create a temporary Moni Note as fallback.

    This tool only creates a note in mock JSON. It does not execute any real transaction.
    """

    if not note_type or not str(note_type).strip():
        return {
            "success": False,
            "error": "INVALID_NOTE_TYPE",
            "message": "note_type is required.",
        }

    if not content or not str(content).strip():
        return {
            "success": False,
            "error": "INVALID_CONTENT",
            "message": "content is required.",
        }

    if date:
        try:
            _parse_date(date)
        except ValueError as exc:
            return {
                "success": False,
                "error": "INVALID_DATE",
                "message": str(exc),
            }

    parsed_amount = None
    if amount is not None:
        try:
            parsed_amount = int(float(amount))
        except (TypeError, ValueError):
            return {
                "success": False,
                "error": "INVALID_AMOUNT",
                "message": "amount must be a number if provided.",
            }

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    data = loaded["data"]
    data.setdefault("moni_notes", [])

    note = {
        "id": f"N{int(datetime.now().timestamp())}",
        "note_type": str(note_type).strip(),
        "content": str(content).strip(),
        "amount": parsed_amount,
        "amount_text": _format_vnd(parsed_amount) if parsed_amount is not None else None,
        "date": date,
        "category": category,
        "status": "draft",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    data["moni_notes"].append(note)

    saved = _save_data(data, data_path)
    if not saved["success"]:
        return saved

    return {
        "success": True,
        "ui_action": None,
        "note": note,
        "message": "Moni Note created successfully. This is only a temporary draft note.",
    }


def save_saving_plan(
    goal_name: str,
    goal_amount: int | float,
    months: int,
    monthly_required: Optional[int | float] = None,
    start_date: Optional[str] = None,
    reminder_day: int = 5,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    Save a confirmed saving plan into finance_data.json.
    This should be called only after the user confirms the draft plan from UI.
    """

    if not goal_name or not str(goal_name).strip():
        return {
            "success": False,
            "error": "INVALID_GOAL_NAME",
            "message": "goal_name is required.",
        }

    try:
        goal_amount = float(goal_amount)
        months = int(months)
        reminder_day = int(reminder_day)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "INVALID_ARGUMENT",
            "message": "goal_amount, months, and reminder_day must be valid numbers.",
        }

    if goal_amount <= 0:
        return {
            "success": False,
            "error": "INVALID_GOAL_AMOUNT",
            "message": "goal_amount must be greater than 0.",
        }

    if months <= 0:
        return {
            "success": False,
            "error": "INVALID_MONTHS",
            "message": "months must be greater than 0.",
        }

    if not 1 <= reminder_day <= 31:
        return {
            "success": False,
            "error": "INVALID_REMINDER_DAY",
            "message": "reminder_day must be between 1 and 31.",
        }

    if start_date:
        try:
            _parse_date(start_date)
        except ValueError as exc:
            return {
                "success": False,
                "error": "INVALID_DATE",
                "message": str(exc),
            }

    if monthly_required is None:
        monthly_required = goal_amount / months

    try:
        monthly_required = float(monthly_required)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "INVALID_MONTHLY_REQUIRED",
            "message": "monthly_required must be a number.",
        }

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    data = loaded["data"]
    data.setdefault("saving_goals", [])

    goal = {
        "id": f"G{int(datetime.now().timestamp())}",
        "goal_name": str(goal_name).strip(),
        "goal_amount": int(goal_amount),
        "goal_amount_text": _format_vnd(goal_amount),
        "months": months,
        "monthly_required": int(round(monthly_required)),
        "monthly_required_text": _format_vnd(monthly_required),
        "start_date": start_date,
        "reminder_day": reminder_day,
        "saved_amount": 0,
        "saved_amount_text": _format_vnd(0),
        "remaining_amount": int(goal_amount),
        "remaining_amount_text": _format_vnd(goal_amount),
        "progress_percent": 0,
        "deposits": [],
        "status": "active",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    data["saving_goals"].append(goal)

    saved = _save_data(data, data_path)
    if not saved["success"]:
        return saved

    return {
        "success": True,
        "ui_action": "SHOW_SAVING_PLAN_SUCCESS",
        "data": {
            "plan": goal
        },
        "plan": goal,
        "message": "Saving plan saved successfully.",
    }

def list_saving_goals(
    status: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    List all saving goals from finance_data.json.
    """

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    goals = loaded["data"].get("saving_goals", [])
    if not isinstance(goals, list):
        goals = []

    normalized_goals = []
    for goal in goals:
        if not isinstance(goal, dict):
            continue

        goal = _calculate_goal_progress(goal)

        if status and goal.get("status") != status:
            continue

        normalized_goals.append(goal)

    return {
        "success": True,
        "ui_action": "SHOW_SAVING_PLAN_LIST",
        "data": {
            "goals": normalized_goals
        },
        "goals": normalized_goals,
        "count": len(normalized_goals),
        "message": f"Found {len(normalized_goals)} saving goal(s).",
    }

def get_saving_goal_detail(
    goal_id: str,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    Get detail of a saving goal by goal_id.
    """

    if not goal_id:
        return {
            "success": False,
            "error": "INVALID_GOAL_ID",
            "message": "goal_id is required.",
        }

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    goals = loaded["data"].get("saving_goals", [])

    for goal in goals:
        if isinstance(goal, dict) and goal.get("id") == goal_id:
            goal = _calculate_goal_progress(goal)

            return {
                "success": True,
                "ui_action": "SHOW_SAVING_PLAN_DETAIL",
                "data": {
                    "plan": goal
                },
                "plan": goal,
                "message": "Saving goal detail loaded successfully.",
            }

    return {
        "success": False,
        "error": "GOAL_NOT_FOUND",
        "message": f"Saving goal not found: {goal_id}",
    }

def record_saving_deposit(
    goal_id: str,
    amount: int | float,
    date: Optional[str] = None,
    note: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    Record a saving deposit for a specific saving goal.
    This only updates mock JSON. It does not move real money.
    """

    if not goal_id:
        return {
            "success": False,
            "error": "INVALID_GOAL_ID",
            "message": "goal_id is required.",
        }

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return {
            "success": False,
            "error": "INVALID_AMOUNT",
            "message": "amount must be a number.",
        }

    if amount <= 0:
        return {
            "success": False,
            "error": "INVALID_AMOUNT",
            "message": "amount must be greater than 0.",
        }

    if date:
        try:
            _parse_date(date)
        except ValueError as exc:
            return {
                "success": False,
                "error": "INVALID_DATE",
                "message": str(exc),
            }
    else:
        date = datetime.now().strftime("%Y-%m-%d")

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    data = loaded["data"]
    goals = data.get("saving_goals", [])

    for goal in goals:
        if isinstance(goal, dict) and goal.get("id") == goal_id:
            goal.setdefault("deposits", [])

            deposit = {
                "id": f"D{int(datetime.now().timestamp())}",
                "amount": int(amount),
                "amount_text": _format_vnd(amount),
                "date": date,
                "note": note,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }

            goal["deposits"].append(deposit)
            goal = _calculate_goal_progress(goal)

            saved = _save_data(data, data_path)
            if not saved["success"]:
                return saved

            return {
                "success": True,
                "ui_action": "SHOW_SAVING_DEPOSIT_SUCCESS",
                "data": {
                    "plan": goal,
                    "deposit": deposit,
                },
                "plan": goal,
                "deposit": deposit,
                "message": "Saving deposit recorded successfully.",
            }

    return {
        "success": False,
        "error": "GOAL_NOT_FOUND",
        "message": f"Saving goal not found: {goal_id}",
    }

def update_saving_plan(
    goal_id: str,
    goal_name: Optional[str] = None,
    goal_amount: Optional[int | float] = None,
    months: Optional[int] = None,
    reminder_day: Optional[int] = None,
    start_date: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH,
) -> Dict[str, Any]:
    """
    Update a saving plan. Useful for correction path.
    Example: user changes goal from 3 months to 5 months.
    """

    if not goal_id:
        return {
            "success": False,
            "error": "INVALID_GOAL_ID",
            "message": "goal_id is required.",
        }

    loaded = _load_data(data_path)
    if not loaded["success"]:
        return loaded

    data = loaded["data"]
    goals = data.get("saving_goals", [])

    for goal in goals:
        if isinstance(goal, dict) and goal.get("id") == goal_id:
            if goal_name is not None:
                if not str(goal_name).strip():
                    return {
                        "success": False,
                        "error": "INVALID_GOAL_NAME",
                        "message": "goal_name cannot be empty.",
                    }
                goal["goal_name"] = str(goal_name).strip()

            if goal_amount is not None:
                try:
                    goal_amount = float(goal_amount)
                except (TypeError, ValueError):
                    return {
                        "success": False,
                        "error": "INVALID_GOAL_AMOUNT",
                        "message": "goal_amount must be a number.",
                    }

                if goal_amount <= 0:
                    return {
                        "success": False,
                        "error": "INVALID_GOAL_AMOUNT",
                        "message": "goal_amount must be greater than 0.",
                    }

                goal["goal_amount"] = int(goal_amount)
                goal["goal_amount_text"] = _format_vnd(goal_amount)

            if months is not None:
                try:
                    months = int(months)
                except (TypeError, ValueError):
                    return {
                        "success": False,
                        "error": "INVALID_MONTHS",
                        "message": "months must be an integer.",
                    }

                if months <= 0:
                    return {
                        "success": False,
                        "error": "INVALID_MONTHS",
                        "message": "months must be greater than 0.",
                    }

                goal["months"] = months

            if reminder_day is not None:
                try:
                    reminder_day = int(reminder_day)
                except (TypeError, ValueError):
                    return {
                        "success": False,
                        "error": "INVALID_REMINDER_DAY",
                        "message": "reminder_day must be an integer.",
                    }

                if not 1 <= reminder_day <= 31:
                    return {
                        "success": False,
                        "error": "INVALID_REMINDER_DAY",
                        "message": "reminder_day must be between 1 and 31.",
                    }

                goal["reminder_day"] = reminder_day

            if start_date is not None:
                try:
                    _parse_date(start_date)
                except ValueError as exc:
                    return {
                        "success": False,
                        "error": "INVALID_DATE",
                        "message": str(exc),
                    }

                goal["start_date"] = start_date

            # Recalculate monthly required after update.
            goal_amount_value = float(goal.get("goal_amount", 0) or 0)
            months_value = int(goal.get("months", 1) or 1)
            deposits = goal.get("deposits", [])
            saved_amount = 0.0

            for deposit in deposits:
                try:
                    saved_amount += float(deposit.get("amount", 0))
                except (TypeError, ValueError):
                    continue

            remaining = max(0.0, goal_amount_value - saved_amount)
            monthly_required = remaining / months_value

            goal["monthly_required"] = int(round(monthly_required))
            goal["monthly_required_text"] = _format_vnd(monthly_required)
            goal["updated_at"] = datetime.now().isoformat(timespec="seconds")

            goal = _calculate_goal_progress(goal)

            saved = _save_data(data, data_path)
            if not saved["success"]:
                return saved

            return {
                "success": True,
                "ui_action": "SHOW_SAVING_PLAN_DETAIL",
                "data": {
                    "plan": goal
                },
                "plan": goal,
                "message": "Saving plan updated successfully.",
            }

    return {
        "success": False,
        "error": "GOAL_NOT_FOUND",
        "message": f"Saving goal not found: {goal_id}",
    }

# -----------------------------
# Ready-to-use tool registry
# -----------------------------

FINANCE_TOOLS = [
    {
        "name": "get_current_balance",
        "description": "Get the user's current mock wallet balance from finance JSON.",
        "func": get_current_balance,
    },
    {
        "name": "list_transactions",
        "description": (
            "List transactions filtered by start_date, end_date, category, "
            "transaction_type, or merchant."
        ),
        "func": list_transactions,
    },
    {
        "name": "get_transaction_summary",
        "description": (
            "Summarize total income, total expense, net change, and transaction count "
            "in a date range."
        ),
        "func": get_transaction_summary,
    },
    {
        "name": "get_category_breakdown",
        "description": "Calculate total spending by category in a date range.",
        "func": get_category_breakdown,
    },
    {
        "name": "create_saving_plan",
        "description": (
            "Create a simple saving plan from goal_amount, months, and optional current_balance."
        ),
        "func": create_saving_plan,
    },
    {
        "name": "create_moni_note",
        "description": (
            "Create a temporary Moni Note fallback. It only writes a draft note to mock JSON."
        ),
        "func": create_moni_note,
    },
    {
        "name": "save_saving_plan",
        "description": (
            "Save a confirmed saving plan to mock JSON. "
            "Use only after the user confirms the draft plan."
        ),
        "func": save_saving_plan,
    },
    {
        "name": "list_saving_goals",
        "description": "List all saving goals from mock JSON.",
        "func": list_saving_goals,
    },
    {
        "name": "get_saving_goal_detail",
        "description": "Get detail and progress of a saving goal by goal_id.",
        "func": get_saving_goal_detail,
    },
    {
        "name": "record_saving_deposit",
        "description": (
            "Record a saving deposit for a saving goal. "
            "This only updates mock JSON and does not move real money."
        ),
        "func": record_saving_deposit,
    },
    {
        "name": "update_saving_plan",
        "description": (
            "Update a saving plan, such as goal amount, months, reminder day, or start date."
        ),
        "func": update_saving_plan,
    },
]
