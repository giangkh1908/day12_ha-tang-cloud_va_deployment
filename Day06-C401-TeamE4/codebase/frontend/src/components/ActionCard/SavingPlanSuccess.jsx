import React from 'react';

export default function SavingPlanSuccess({ data, onActionClick }) {
  if (!data?.plan) return null;

  const { plan } = data;

  return (
    <div className="action-card__body">
      <div className="action-card__success-icon">🎉</div>
      <p style={{ textAlign: 'center', fontWeight: 600, fontSize: '16px', marginBottom: '4px' }}>
        Tạo kế hoạch thành công!
      </p>
      <p style={{ textAlign: 'center', color: '#6b7280', fontSize: '13px', marginBottom: '16px' }}>
        Xem lại kế hoạch trước khi bắt đầu ghi nhận tiến độ nhé.
      </p>

      <div className="action-card__row">
        <span className="action-card__label">Mục tiêu</span>
        <span className="action-card__value action-card__highlight">{plan.goal_amount_text}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Thời gian</span>
        <span className="action-card__value">{plan.months} tháng</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Mỗi tháng</span>
        <span className="action-card__value action-card__highlight">{plan.monthly_required_text}</span>
      </div>
      <div className="action-card__row">
        <span className="action-card__label">Bắt đầu từ</span>
        <span className="action-card__value">{plan.start_date || 'Chưa xác định'}</span>
      </div>

      <div className="action-card__btn-group">
        <button
          className="action-card__btn action-card__btn--primary"
          onClick={() => onActionClick('VIEW_SAVING_PLANS', data)}
        >
          Xem kế hoạch của tôi
        </button>
        <button
          className="action-card__btn action-card__btn--secondary"
          onClick={() => onActionClick('DISMISS', data)}
        >
          Quay lại trò chuyện
        </button>
      </div>
    </div>
  );
}
