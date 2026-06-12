// Chat Service - Abstraction layer for API calls
// Switch USE_MOCK to false when backend is ready

const USE_MOCK = false;
const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

// ==================== MOCK DATA ====================
const MOCK_RESPONSES = [
  {
    text: `Đây là phân tích chi tiêu của bạn trong năm 2026:

· Tổng số tiền đã chi: **73.000đ**
· Số giao dịch: **1**
· Trung bình chi tiêu mỗi ngày: **200đ**

Nếu bạn muốn xem chi tiết theo từng nhóm chi tiêu hoặc so sánh với năm trước, hãy cho Moni biết nhé!`,
    uiAction: null,
    uiData: null,
  },
  {
    text: `Mình đã chuẩn bị một kế hoạch tiết kiệm đề xuất. Bạn cần tiết kiệm khoảng **1.666.667 VND** mỗi tháng để đạt mục tiêu **5.000.000 VND** trong 3 tháng. Hãy kiểm tra thông tin trong thẻ kế hoạch và bấm "Tạo kế hoạch" nếu bạn đồng ý.`,
    uiAction: 'SHOW_SAVING_PLAN_DRAFT',
    uiData: {
      plan: {
        id: 'G_MOCK_1',
        goal_name: 'Tiết kiệm 5 triệu trong 3 tháng',
        goal_amount: 5000000,
        goal_amount_text: '5.000.000 VND',
        months: 3,
        monthly_required: 1666667,
        monthly_required_text: '1.666.667 VND',
        start_date: '2026-06-01',
        reminder_day: 5,
        status: 'draft',
      },
    },
  },
  {
    text: `Ngân sách tổng của bạn đã được thiết lập là **1.000.000đ** cho tháng này.

Hiện tại bạn đã chi tiêu **140.000đ**, còn lại **860.000đ** để sử dụng trong tháng.`,
    uiAction: null,
    uiData: null,
  },
];

let responseIndex = 0;

// ==================== MOCK IMPLEMENTATION ====================
async function mockSendMessage(message) {
  const delay = 800 + Math.random() * 700;
  await new Promise((resolve) => setTimeout(resolve, delay));

  const response = MOCK_RESPONSES[responseIndex % MOCK_RESPONSES.length];
  responseIndex++;

  return {
    text: response.text,
    uiAction: response.uiAction,
    uiData: response.uiData,
  };
}

// ==================== REAL API IMPLEMENTATION ====================
async function realSendMessage(message, conversationHistory) {
  const response = await fetch(`${API_BASE_URL}/agent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: message,
      max_steps: 10,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();
  const answer =
    typeof data.answer === 'string'
      ? data.answer
      : JSON.stringify(data.answer);

  return {
    text: answer,
    uiAction: data.ui_action || null,
    uiData: data.data || null,
  };
}

// ==================== PUBLIC API ====================

/**
 * Send a message and get a response
 * @param {string} message - User's message text
 * @param {Array} conversationHistory - Previous messages for context
 * @returns {Promise<{text: string, uiAction: string|null, uiData: object|null}>}
 */
export async function sendMessage(message, conversationHistory = []) {
  if (USE_MOCK) {
    return mockSendMessage(message);
  }

  return realSendMessage(message, conversationHistory);
}

/**
 * Get the current mock mode status
 * @returns {boolean}
 */
export function isMockMode() {
  return USE_MOCK;
}

/**
 * Directly save a confirmed saving plan (bypasses LLM agent)
 * @param {object} plan - Plan details { goal_name, goal_amount, months, start_date, reminder_day }
 * @returns {Promise<{success: boolean, ui_action: string, data: object, plan: object}>}
 */
export async function savePlan(plan) {
  if (USE_MOCK) {
    // Mock: simulate a successful save
    await new Promise((resolve) => setTimeout(resolve, 600));
    return {
      success: true,
      ui_action: 'SHOW_SAVING_PLAN_SUCCESS',
      data: { plan: { ...plan, status: 'active', saved_amount: 0, saved_amount_text: '0 VND', progress_percent: 0 } },
      plan: { ...plan, status: 'active' },
    };
  }

  const response = await fetch(`${API_BASE_URL}/save-plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      goal_name: plan.goal_name,
      goal_amount: plan.goal_amount,
      months: plan.months,
      start_date: plan.start_date || null,
      reminder_day: plan.reminder_day || 5,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${response.status}`);
  }

  return response.json();
}
