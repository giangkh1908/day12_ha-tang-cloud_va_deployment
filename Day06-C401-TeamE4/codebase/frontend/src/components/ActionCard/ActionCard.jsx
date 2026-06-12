import React from 'react';
import SavingPlanDraft from './SavingPlanDraft';
import SavingPlanSuccess from './SavingPlanSuccess';
import SavingPlanList from './SavingPlanList';
import SavingPlanDetail from './SavingPlanDetail';
import SavingDepositSuccess from './SavingDepositSuccess';
import './ActionCard.css';

const ACTION_CONFIG = {
  SHOW_SAVING_PLAN_DRAFT: { title: '🎯 Kế hoạch tiết kiệm đề xuất', Component: SavingPlanDraft },
  SHOW_SAVING_PLAN_SUCCESS: { title: '✅ Tạo kế hoạch thành công!', Component: SavingPlanSuccess },
  SHOW_SAVING_PLAN_LIST: { title: '📋 Kế hoạch của tôi', Component: SavingPlanList },
  SHOW_SAVING_PLAN_DETAIL: { title: '📊 Chi tiết kế hoạch', Component: SavingPlanDetail },
  SHOW_SAVING_DEPOSIT_SUCCESS: { title: '✅ Đã ghi nhận tiết kiệm', Component: SavingDepositSuccess },
};

function ActionCard({ uiAction, uiData, onActionClick }) {
  const config = ACTION_CONFIG[uiAction];

  if (!config) {
    return null;
  }

  const { title, Component } = config;

  return (
    <div className="action-card">
      <div className="action-card__header">
        <span className="action-card__title">{title}</span>
      </div>
      <Component data={uiData} onActionClick={onActionClick} />
    </div>
  );
}

export default ActionCard;
