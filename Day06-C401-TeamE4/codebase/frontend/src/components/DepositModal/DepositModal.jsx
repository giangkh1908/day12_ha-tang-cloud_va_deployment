import React, { useState } from 'react';
import './DepositModal.css';

const formatVND = (value) => {
  if (!value) return '';
  return new Intl.NumberFormat('vi-VN').format(value);
};

export default function DepositModal({ planName, onConfirm, onCancel }) {
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');

  const handleAmountChange = (e) => {
    // Only allow digits
    const raw = e.target.value.replace(/[^0-9]/g, '');
    setAmount(raw);
  };

  const handleSubmit = () => {
    const numericAmount = parseInt(amount, 10);
    if (!numericAmount || numericAmount <= 0) return;
    onConfirm(numericAmount, note.trim() || null);
  };

  const displayAmount = amount ? formatVND(parseInt(amount, 10)) : '';

  return (
    <div className="deposit-modal__overlay" onClick={onCancel}>
      <div className="deposit-modal" onClick={(e) => e.stopPropagation()}>
        <div className="deposit-modal__header">
          <div className="deposit-modal__icon">💰</div>
          <div>
            <div className="deposit-modal__title">Ghi nhận tiết kiệm</div>
            <div className="deposit-modal__plan-name">{planName}</div>
          </div>
        </div>

        <div className="deposit-modal__form-group">
          <label className="deposit-modal__label">Số tiền (VND)</label>
          <input
            type="text"
            className="deposit-modal__input"
            placeholder="Nhập số tiền..."
            value={displayAmount}
            onChange={handleAmountChange}
            autoFocus
          />
          {amount && (
            <div className="deposit-modal__hint">
              {formatVND(parseInt(amount, 10))} VND
            </div>
          )}
        </div>

        <div className="deposit-modal__form-group">
          <label className="deposit-modal__label">Ghi chú (không bắt buộc)</label>
          <input
            type="text"
            className="deposit-modal__input deposit-modal__input--note"
            placeholder="VD: Lương tháng 6..."
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </div>

        <div className="deposit-modal__btn-group">
          <button
            className="deposit-modal__btn deposit-modal__btn--secondary"
            onClick={onCancel}
          >
            Hủy
          </button>
          <button
            className="deposit-modal__btn deposit-modal__btn--primary"
            onClick={handleSubmit}
            disabled={!amount || parseInt(amount, 10) <= 0}
          >
            Xác nhận
          </button>
        </div>
      </div>
    </div>
  );
}
