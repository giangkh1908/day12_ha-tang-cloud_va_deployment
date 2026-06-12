import React from 'react';

const formatVND = (amount) => {
  if (amount == null) return '0 VND';
  return new Intl.NumberFormat('vi-VN').format(amount) + ' VND';
};

export default function SavingDepositSuccess({ data, onActionClick }) {
  if (!data?.plan || !data?.deposit) return null;

  const { plan, deposit } = data;
  const savedText = plan.saved_amount_text || formatVND(plan.saved_amount);
  const goalText = plan.goal_amount_text || formatVND(plan.goal_amount);
  const percent = plan.progress_percent ?? 0;

  return (
    <div className="action-card__body">
      <div className="action-card__deposit-info">
        <div className="action-card__deposit-icon">✅</div>
        <div>
          <strong>Đã ghi nhận {deposit.amount_text || formatVND(deposit.amount)}</strong>
          <br />
          <span style={{ fontSize: '12px', color: '#6b7280' }}>{plan.goal_name}</span>
        </div>
      </div>

      <p className="action-card__progress-label">Tiến độ cập nhật:</p>
      <div className="action-card__progress">
        <div
          className="action-card__progress-bar"
          style={{ width: `${percent}%` }}
        />
      </div>
      <p className="action-card__progress-text">
        {savedText} / {goalText} ({percent}%)
      </p>

      <button
        className="action-card__btn action-card__btn--primary"
        onClick={() => onActionClick('RECORD_DEPOSIT', data)}
      >
        Ghi nhận khoản tiết kiệm
      </button>
    </div>
  );
}
