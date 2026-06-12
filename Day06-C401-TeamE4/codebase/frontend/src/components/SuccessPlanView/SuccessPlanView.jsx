import React from 'react';
import './SuccessPlanView.css';

const formatDateDMY = (dateStr) => {
  if (!dateStr) return 'Chưa xác định';
  try {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    const date = new Date(dateStr);
    const d = String(date.getDate()).padStart(2, '0');
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const y = date.getFullYear();
    return `${d}/${m}/${y}`;
  } catch {
    return dateStr;
  }
};

const formatReminderDay = (day) => {
  if (!day) return '05 hàng tháng';
  return `${String(day).padStart(2, '0')} hàng tháng`;
};

export default function SuccessPlanView({ plan, onViewPlans, onBackToChat }) {
  if (!plan) return null;

  return (
    <div className="success-plan-view">
      {/* Top mock status bar space */}
      <div className="success-plan-view__status-space" />

      {/* Header section with green checkmark and sweating pink mascot */}
      <div className="success-plan-view__header">
        <div className="success-plan-view__check-container">
          <div className="success-plan-view__confetti success-plan-view__confetti--1">✨</div>
          <div className="success-plan-view__confetti success-plan-view__confetti--2">💎</div>
          <div className="success-plan-view__confetti success-plan-view__confetti--3">⭐</div>
          <div className="success-plan-view__confetti success-plan-view__confetti--4">🎉</div>
          
          <div className="success-plan-view__check-circle">✓</div>
        </div>
        <div className="success-plan-view__mascot">
          <span className="success-plan-view__mascot-sweat">💦</span>
        </div>
      </div>

      {/* Main Title Headers */}
      <h2 className="success-plan-view__title">Tạo kế hoạch thành công!</h2>
      <p className="success-plan-view__subtitle">
        Xem lại kế hoạch trước khi bắt đầu ghi nhận tiến độ nhé.
      </p>

      {/* Detail Plan White Rounded Card */}
      <div className="success-plan-view__card">
        <div className="success-plan-view__plan-name">{plan.goal_name}</div>
        <div className="success-plan-view__card-rows">
          <div className="success-plan-view__row">
            <span className="success-plan-view__label">Mục tiêu</span>
            <span className="success-plan-view__value">
              {plan.goal_amount_text || new Intl.NumberFormat('vi-VN').format(plan.goal_amount) + ' VND'}
            </span>
          </div>
          <div className="success-plan-view__row">
            <span className="success-plan-view__label">Thời gian</span>
            <span className="success-plan-view__value">{plan.months} tháng</span>
          </div>
          <div className="success-plan-view__row">
            <span className="success-plan-view__label">Mỗi tháng</span>
            <span className="success-plan-view__value">
              {plan.monthly_required_text || new Intl.NumberFormat('vi-VN').format(plan.monthly_required) + ' VND'}
            </span>
          </div>
          <div className="success-plan-view__row">
            <span className="success-plan-view__label">Bắt đầu từ</span>
            <span className="success-plan-view__value">{formatDateDMY(plan.start_date)}</span>
          </div>
          <div className="success-plan-view__row">
            <span className="success-plan-view__label">Nhắc vào ngày</span>
            <span className="success-plan-view__value">{formatReminderDay(plan.reminder_day)}</span>
          </div>
        </div>
      </div>

      {/* CTA Buttons Block */}
      <div className="success-plan-view__footer">
        <button
          className="success-plan-view__btn success-plan-view__btn--primary"
          onClick={onViewPlans}
        >
          Xem kế hoạch của tôi
        </button>
        <button
          className="success-plan-view__btn success-plan-view__btn--secondary"
          onClick={onBackToChat}
        >
          Quay lại trò chuyện
        </button>
      </div>

      {/* Bottom peeking cute mascot decoration */}
      <div className="success-plan-view__bottom-decor">
        <div className="success-plan-view__peeking-mascot" />
      </div>
    </div>
  );
}
