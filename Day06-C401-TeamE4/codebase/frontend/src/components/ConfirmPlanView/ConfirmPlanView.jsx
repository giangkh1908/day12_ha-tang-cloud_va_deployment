import React, { useState, useMemo } from 'react';
import './ConfirmPlanView.css';

const formatVND = (amount) => {
  return new Intl.NumberFormat('vi-VN').format(amount) + 'đ';
};

const getMonthAllocations = (startDateStr, monthsCount, totalAmount) => {
  const allocations = [];
  // Parse date safely
  const start = startDateStr ? new Date(startDateStr) : new Date();
  const monthlyRequired = Math.round(totalAmount / monthsCount);

  for (let i = 0; i < monthsCount; i++) {
    const d = new Date(start);
    d.setMonth(d.getMonth() + i);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const y = d.getFullYear();
    allocations.push({
      label: `Tháng ${i + 1} (${m}/${y})`,
      amountText: formatVND(monthlyRequired),
    });
  }
  return allocations;
};

export default function ConfirmPlanView({ plan, onConfirm, onBack }) {
  if (!plan) return null;

  const [goalName, setGoalName] = useState(plan.goal_name || 'Kế hoạch tiết kiệm');
  const [months, setMonths] = useState(plan.months || 3);
  const [startDate, setStartDate] = useState(
    plan.start_date || new Date().toISOString().split('T')[0]
  );
  const [reminderDay, setReminderDay] = useState(plan.reminder_day || 5);

  const goalAmount = plan.goal_amount || 5000000;

  // Calculate allocation lists on changes
  const allocations = useMemo(() => {
    return getMonthAllocations(startDate, months, goalAmount);
  }, [startDate, months, goalAmount]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onConfirm({
      plan: {
        ...plan,
        goal_name: goalName,
        goal_amount: goalAmount,
        months: parseInt(months, 10),
        start_date: startDate,
        reminder_day: parseInt(reminderDay, 10),
        monthly_required: Math.round(goalAmount / months),
        monthly_required_text: formatVND(goalAmount / months).replace('đ', ' VND'),
      },
    });
  };

  return (
    <div className="confirm-plan-view">
      {/* Top Header */}
      <div className="confirm-plan-view__header">
        <button className="confirm-plan-view__back-btn" onClick={onBack} aria-label="Go back">
          ←
        </button>
        <span className="confirm-plan-view__header-title">Xác nhận kế hoạch</span>
      </div>

      {/* Main Content Form */}
      <form className="confirm-plan-view__body" onSubmit={handleSubmit}>
        <h2 className="confirm-plan-view__title">Xác nhận kế hoạch</h2>

        {/* Goal Name Input */}
        <div className="confirm-plan-view__form-group">
          <label className="confirm-plan-view__label">Tên kế hoạch</label>
          <div className="confirm-plan-view__input-wrapper">
            <input
              type="text"
              className="confirm-plan-view__input"
              value={goalName}
              onChange={(e) => setGoalName(e.target.value)}
              required
            />
            <span className="confirm-plan-view__input-icon">✏️</span>
          </div>
        </div>

        {/* Goal Amount Display (Read-only) */}
        <div className="confirm-plan-view__form-group">
          <label className="confirm-plan-view__label">Mục tiêu</label>
          <div className="confirm-plan-view__amount-display">
            {formatVND(goalAmount)}
          </div>
        </div>

        {/* Months Selection */}
        <div className="confirm-plan-view__form-group">
          <label className="confirm-plan-view__label">Thời gian</label>
          <select
            className="confirm-plan-view__select"
            value={months}
            onChange={(e) => setMonths(parseInt(e.target.value, 10))}
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) => (
              <option key={m} value={m}>
                {m} tháng
              </option>
            ))}
          </select>
        </div>

        {/* Start Date Datepicker */}
        <div className="confirm-plan-view__form-group">
          <label className="confirm-plan-view__label">Bắt đầu từ</label>
          <input
            type="date"
            className="confirm-plan-view__input"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />
        </div>

        {/* Reminder Day Select */}
        <div className="confirm-plan-view__form-group">
          <label className="confirm-plan-view__label">Nhắc vào ngày</label>
          <select
            className="confirm-plan-view__select"
            value={reminderDay}
            onChange={(e) => setReminderDay(parseInt(e.target.value, 10))}
          >
            {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
              <option key={day} value={day}>
                {String(day).padStart(2, '0')} hàng tháng
              </option>
            ))}
          </select>
        </div>

        {/* Allocations Breakdown Display */}
        <div className="confirm-plan-view__allocation">
          <div className="confirm-plan-view__allocation-title">Phân bổ mỗi tháng</div>
          <div className="confirm-plan-view__allocation-list">
            {allocations.map((item, idx) => (
              <div key={idx} className="confirm-plan-view__allocation-item">
                <span className="confirm-plan-view__allocation-label">{item.label}</span>
                <span className="confirm-plan-view__allocation-value">{item.amountText}</span>
              </div>
            ))}
          </div>
        </div>
      </form>

      {/* Submit Button Block */}
      <div className="confirm-plan-view__footer">
        <button
          type="button"
          className="confirm-plan-view__submit-btn"
          onClick={handleSubmit}
        >
          Xác nhận tạo kế hoạch
        </button>
      </div>
    </div>
  );
}
