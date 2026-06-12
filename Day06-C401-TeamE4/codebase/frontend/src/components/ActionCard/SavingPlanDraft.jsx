import React from 'react';

const getMonthLabels = (startDate, months) => {
  const labels = [];
  const start = startDate ? new Date(startDate) : new Date();
  for (let i = 0; i < months; i++) {
    const d = new Date(start);
    d.setMonth(d.getMonth() + i);
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const y = d.getFullYear();
    labels.push(`Tháng ${i + 1} (${m}/${y})`);
  }
  return labels;
};

export default function SavingPlanDraft({ data, onActionClick }) {
  if (!data?.plan) return null;

  const { plan } = data;
  const monthLabels = getMonthLabels(plan.start_date, plan.months);

  return (
    <div className="action-card__body">
      <div className="action-card__row">
        <span className="action-card__label">Tên kế hoạch</span>
        <span className="action-card__value">{plan.goal_name}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Mục tiêu</span>
        <span className="action-card__value action-card__highlight">{plan.goal_amount_text}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Thời gian</span>
        <span className="action-card__value">{plan.months} tháng</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Bắt đầu</span>
        <span className="action-card__value">{plan.start_date || 'Chưa xác định'}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Mỗi tháng cần tiết kiệm</span>
        <span className="action-card__value action-card__highlight">{plan.monthly_required_text}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Nhắc vào ngày</span>
        <span className="action-card__value">0{plan.reminder_day} hàng tháng</span>
      </div>

      <div className="action-card__section-title">Phân bổ mỗi tháng</div>
      <table className="action-card__table">
        <tbody>
          {monthLabels.map((label, idx) => (
            <tr key={idx}>
              <td>{label}</td>
              <td>{plan.monthly_required_text}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <button
        className="action-card__btn action-card__btn--primary"
        onClick={() => onActionClick('CONFIRM_SAVING_PLAN', data)}
      >
        Tạo kế hoạch
      </button>
    </div>
  );
}
