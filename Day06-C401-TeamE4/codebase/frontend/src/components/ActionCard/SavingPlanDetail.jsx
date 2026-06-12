import React from 'react';

const formatVND = (amount) => {
  if (amount == null) return '0 VND';
  return new Intl.NumberFormat('vi-VN').format(amount) + ' VND';
};

const statusText = {
  active: 'Đang thực hiện',
  draft: 'Bản nháp',
  completed: 'Hoàn thành',
};

export default function SavingPlanDetail({ data, onActionClick }) {
  if (!data?.plan) return null;

  const { plan } = data;
  const savedText = plan.saved_amount_text || formatVND(plan.saved_amount);
  const goalText = plan.goal_amount_text || formatVND(plan.goal_amount);
  const percent = plan.progress_percent ?? 0;
  const remainingText = plan.remaining_amount_text || formatVND(plan.remaining_amount);
  const monthlyText = plan.monthly_required_text || formatVND(plan.monthly_required);

  return (
    <div className="action-card__body">
      <div className="action-card__detail-header">
        <span className="action-card__detail-name">{plan.goal_name}</span>
        <span className={`action-card__badge action-card__badge--${plan.status}`}>
          {statusText[plan.status] || plan.status}
        </span>
      </div>

      <div className="action-card__progress">
        <div
          className="action-card__progress-bar"
          style={{ width: `${percent}%` }}
        />
      </div>
      <p className="action-card__progress-text">
        {savedText} / {goalText} ({percent}%)
      </p>

      <div className="action-card__row">
        <span className="action-card__label">Mỗi tháng</span>
        <span className="action-card__value action-card__highlight">{monthlyText}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Bắt đầu</span>
        <span className="action-card__value">{plan.start_date || 'Chưa xác định'}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Nhắc vào ngày</span>
        <span className="action-card__value">0{plan.reminder_day} hàng tháng</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Còn lại</span>
        <span className="action-card__value action-card__highlight">{remainingText}</span>
      </div>

      {plan.deposits && plan.deposits.length > 0 && (
        <>
          <div className="action-card__section-title">Lịch sử ghi nhận</div>
          <div className="action-card__deposits">
            {plan.deposits.map((deposit, idx) => (
              <div key={idx} className="action-card__deposit-item">
                <div className="action-card__deposit-date">{deposit.date}</div>
                <div className="action-card__deposit-amount">{deposit.amount_text || formatVND(deposit.amount)}</div>
                {deposit.note && (
                  <div className="action-card__deposit-note">{deposit.note}</div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      <button
        className="action-card__btn action-card__btn--primary"
        onClick={() => onActionClick('RECORD_DEPOSIT', data)}
      >
        Ghi nhận khoản tiết kiệm
      </button>
    </div>
  );
}
