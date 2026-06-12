import React from 'react';

const statusText = {
  active: 'Đang thực hiện',
  draft: 'Bản nháp',
  completed: 'Hoàn thành',
};

export default function SavingPlanList({ data, onActionClick }) {
  if (!data?.goals || data.goals.length === 0) {
    return (
      <div className="action-card__body">
        <p style={{ textAlign: 'center', color: '#6b7280' }}>Chưa có kế hoạch nào.</p>
      </div>
    );
  }

  return (
    <div className="action-card__body">
      <div className="action-card__list">
        {data.goals.map((goal) => (
          <div
            key={goal.id}
            className="action-card__list-item"
            onClick={() => onActionClick('VIEW_GOAL_DETAIL', { goalId: goal.id })}
          >
            <div className="action-card__list-item-header">
              <div className="action-card__list-item-left">
                <span className="action-card__list-item-name">{goal.goal_name}</span>
                <span className={`action-card__badge action-card__badge--${goal.status}`}>
                  {statusText[goal.status] || goal.status}
                </span>
              </div>
              <div className="action-card__list-item-right">
                {goal.saved_amount_text} / {goal.goal_amount_text}
              </div>
            </div>
            <div className="action-card__progress">
              <div
                className="action-card__progress-bar"
                style={{ width: `${goal.progress_percent}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
