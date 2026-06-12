# src/agent/agent.py

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolSpec:
    name: str
    description: str
    func: Callable[..., Any]


class ReActAgent:
    """
    ReAct Agent for a Moni-like personal finance chatbot.

    Main goals:
    - Read mock financial data from JSON through tools.
    - Answer questions about balance, transactions, spending, and saving plans.
    - Use tool observations instead of hallucinating financial data.
    - Fall back to Moni Note when a tool/API fails.
    - Never perform real financial actions such as transfer/payment.
    """

    def __init__(
        self,
        llm: Any,
        tools: List[Dict[str, Any]] | List[ToolSpec],
        max_steps: int = 6,
        verbose: bool = True,
    ) -> None:
        self.llm = llm
        self.max_steps = max_steps
        self.verbose = verbose

        self.tools: Dict[str, ToolSpec] = {}
        for tool in tools:
            if isinstance(tool, ToolSpec):
                self.tools[tool.name] = tool
            else:
                self.tools[tool["name"]] = ToolSpec(
                    name=tool["name"],
                    description=tool["description"],
                    func=tool["func"],
                )

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {tool.name}: {tool.description}"
            for tool in self.tools.values()
        )

        return f"""
You are Moni Agent, a careful personal finance assistant prototype.

You help users understand their mock financial data:
- current balance
- transaction history
- spending by category
- saving goals
- temporary fallback notes called Moni Note

Important safety and product rules:
1. You are NOT allowed to transfer money, pay bills, delete real data, or perform real banking actions.
2. You must use tools for factual financial information. Do not invent balance, transactions, dates, or amounts.
3. If the user asks for a balance, transaction, spending summary, or saving plan, use the relevant tool.
4. If a tool fails or data is unavailable, explain the issue and suggest using Moni Note as fallback.
5. If the user gives an unclear saving goal, ask a concise clarification question.
6. If the user asks for a saving plan, compute the required amount per month and explain it clearly.
7. For any final number involving money, prefer using tool results or explicitly show the simple calculation.
8. Use Vietnamese by default if the user speaks Vietnamese.
9. Keep the tone friendly, practical, and concise.
10. Do not give high-risk financial advice. Only provide budgeting and tracking support from mock data.

Saving plan workflow rules:
1. create_saving_plan only creates a draft plan. It does NOT mean the plan has been saved.
2. After create_saving_plan succeeds, explain the draft plan and ask the user to confirm by pressing the UI button.
3. Do NOT say "created successfully" unless save_saving_plan has succeeded.
4. save_saving_plan should only be used after explicit user confirmation.
5. record_saving_deposit only records mock progress in JSON. It does not move real money.
6. If a tool returns ui_action and data, preserve that information so the frontend can render the corresponding card or form.

Available tools:
{tool_descriptions}

You must follow this exact format.

When you need a tool:
Thought: explain briefly what you need.
Action:
{{"tool": "tool_name", "args": {{"arg1": "value1"}}}}

When you have enough information:
Final Answer: your final answer to the user.

If a tool result says success=false, do not pretend it succeeded.
If the user asks for a real financial action, refuse politely and offer a safe alternative such as creating a Moni Note.

When a saving plan draft is ready, your Final Answer should be concise and should not repeat too much raw JSON.
Example:
Final Answer: Mình đã chuẩn bị một kế hoạch tiết kiệm đề xuất. Bạn cần tiết kiệm khoảng 3.333.333 VND mỗi tháng để đạt mục tiêu 10.000.000 VND trong 3 tháng. Hãy kiểm tra thông tin trong thẻ kế hoạch và bấm "Tạo kế hoạch" nếu bạn đồng ý.
""".strip()

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Run the ReAct loop.

        Returns:
            {
                "answer": str,
                "trace": list,
                "tool_calls": list,
                "num_steps": int,
                "success": bool
            }
        """

        conversation = f"User question: {user_input}\n"
        trace: List[Dict[str, Any]] = []
        tool_calls: List[str] = []
        last_ui_action = None
        last_ui_data = None

        for step in range(1, self.max_steps + 1):
            llm_result = self.llm.generate(
                prompt=conversation,
                system_prompt=self.get_system_prompt(),
            )

            llm_output = self._extract_content(llm_result)
            trace_item: Dict[str, Any] = {
                "step": step,
                "prompt": conversation,
                "llm_output": llm_output,
                "llm_metadata": self._extract_metadata(llm_result),
            }
            trace.append(trace_item)

            if self.verbose:
                print(f"\n[Step {step}]")
                print(llm_output)

            final_answer = self._parse_final_answer(llm_output)
            if final_answer is not None:
                return {
                    "answer": final_answer,
                    "ui_action": last_ui_action,
                    "data": last_ui_data,
                    "trace": trace,
                    "tool_calls": tool_calls,
                    "num_steps": step,
                    "success": True,
                }

            action = self._parse_action(llm_output)

            if action is None:
                # If the model produced a natural language answer without Action,
                # treat it as final instead of forcing another loop.
                if llm_output.strip():
                    return {
                        "answer": llm_output.strip(),
                        "ui_action": last_ui_action,
                        "data": last_ui_data,
                        "trace": trace,
                        "tool_calls": tool_calls,
                        "num_steps": step,
                        "success": True,
                    }

                observation = {
                    "success": False,
                    "error": "PARSER_ERROR",
                    "message": (
                        "Could not parse a valid Action or Final Answer. "
                        "Use either Final Answer: ... or Action JSON."
                    ),
                }
                conversation += self._format_turn(llm_output, observation)
                continue

            tool_name = action.get("tool")
            args = action.get("args", {})

            observation = self._execute_tool(tool_name, args)
            tool_calls.append(tool_name)

            if isinstance(observation, dict) and observation.get("ui_action"):
                last_ui_action = observation.get("ui_action")
                last_ui_data = observation.get("data")

            # Code-level guardrail for unsafe or failed finance actions.
            guarded_answer = self._maybe_stop_after_observation(tool_name, observation)
            if guarded_answer is not None:
                trace_item["observation"] = observation
                return {
                    "answer": guarded_answer,
                    "ui_action": last_ui_action,
                    "data": last_ui_data,
                    "trace": trace,
                    "tool_calls": tool_calls,
                    "num_steps": step,
                    "success": True,
                }

            trace_item["observation"] = observation
            conversation += self._format_turn(llm_output, observation)

        fallback_answer = (
            "Mình chưa hoàn tất được trong số bước cho phép. "
            "Bạn có thể hỏi lại ngắn hơn, ví dụ: "
            "'Tháng này tôi đã tiêu bao nhiêu cho ăn uống?' hoặc "
            "'Tôi muốn tiết kiệm 5 triệu trong 3 tháng'."
        )

        return {
            "answer": fallback_answer,
            "ui_action": last_ui_action,
            "data": last_ui_data,
            "trace": trace,
            "tool_calls": tool_calls,
            "num_steps": self.max_steps,
            "success": False,
        }

    def _execute_tool(self, tool_name: Optional[str], args: Dict[str, Any]) -> Dict[str, Any]:
        if not tool_name:
            return {
                "success": False,
                "error": "MISSING_TOOL_NAME",
                "message": "No tool name was provided.",
            }

        if tool_name not in self.tools:
            return {
                "success": False,
                "error": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' does not exist.",
                "available_tools": list(self.tools.keys()),
            }

        if not isinstance(args, dict):
            return {
                "success": False,
                "error": "INVALID_ARGS",
                "message": "Tool args must be a JSON object.",
            }

        try:
            result = self.tools[tool_name].func(**args)

            if isinstance(result, dict):
                return result

            return {
                "success": True,
                "result": result,
            }

        except TypeError as e:
            return {
                "success": False,
                "error": "TOOL_ARGUMENT_ERROR",
                "message": str(e),
                "tool": tool_name,
                "args": args,
            }

        except Exception as e:
            return {
                "success": False,
                "error": "TOOL_RUNTIME_ERROR",
                "message": str(e),
                "tool": tool_name,
                "args": args,
            }

    def _maybe_stop_after_observation(
        self,
        tool_name: str,
        observation: Dict[str, Any],
    ) -> Optional[str]:
        """
        Hard guardrails after tool calls.
        This prevents the LLM from continuing when a business rule is already clear.
        """

        # If real financial action is requested and blocked.
        if observation.get("error") == "UNSAFE_FINANCIAL_ACTION":
            return (
                "Mình không thể thực hiện thao tác tài chính thật như chuyển tiền, "
                "thanh toán hoặc xoá dữ liệu. Mình có thể giúp bạn ghi chú tạm thời "
                "bằng Moni Note hoặc lập kế hoạch ngân sách mô phỏng."
            )

        # If saving/transaction data source fails, recommend fallback.
        if observation.get("error") in {
            "DATA_SOURCE_ERROR",
            "FILE_NOT_FOUND",
            "JSON_READ_ERROR",
        }:
            return (
                "Hiện tại Moni chưa đọc được dữ liệu tài chính mô phỏng. "
                "Mình có thể chuyển sang chế độ Moni Note để ghi nhận tạm thời "
                "mục tiêu hoặc giao dịch của bạn, sau đó đồng bộ lại khi hệ thống ổn định."
            )

        # If tool explicitly asks to stop.
        if observation.get("should_stop") is True:
            return observation.get(
                "final_answer",
                "Mình đã dừng lại vì tool trả về điều kiện cần xác nhận từ người dùng.",
            )

        return None

    def _parse_action(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse:
        Action:
        {"tool": "tool_name", "args": {"x": 1}}

        Also supports one-line:
        Action: {"tool": "tool_name", "args": {...}}
        """

        action_match = re.search(r"Action\s*:\s*(.*)", text, flags=re.DOTALL)
        if not action_match:
            return None

        raw = action_match.group(1).strip()

        # Remove fenced code block if present.
        raw = raw.replace("```json", "").replace("```", "").strip()

        # Try to extract the first JSON object.
        json_match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not json_match:
            return None

        json_text = json_match.group(0)

        try:
            action = json.loads(json_text)
        except json.JSONDecodeError:
            return None

        if not isinstance(action, dict):
            return None

        if "tool" not in action:
            return None

        if "args" not in action:
            action["args"] = {}

        return action

    def _parse_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer\s*:\s*(.*)", text, flags=re.DOTALL)
        if not match:
            return None

        answer = match.group(1).strip()
        return answer if answer else None

    def _format_turn(self, llm_output: str, observation: Dict[str, Any]) -> str:
        observation_text = json.dumps(
            observation,
            ensure_ascii=False,
            indent=None,
        )

        return (
            "\n\nAssistant output:\n"
            f"{llm_output}\n\n"
            "Observation:\n"
            f"{observation_text}\n"
        )

    def _extract_content(self, llm_result: Any) -> str:
        if isinstance(llm_result, dict):
            return str(llm_result.get("content", ""))
        return str(llm_result)

    def _extract_metadata(self, llm_result: Any) -> Dict[str, Any]:
        if not isinstance(llm_result, dict):
            return {}

        metadata = {}
        for key in ["provider", "model", "usage", "latency_ms"]:
            if key in llm_result:
                metadata[key] = llm_result[key]
        return metadata