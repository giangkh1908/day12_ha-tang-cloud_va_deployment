import { useState } from 'react';
import './FeedbackBar.css';

function FeedbackBar({ messageId }) {
  const [selected, setSelected] = useState(null);

  const handleFeedback = (type) => {
    setSelected(type);
    // TODO: send feedback to backend
    console.log(`Feedback for message ${messageId}:`, type);
  };

  return (
    <div className="feedback-bar" id={`feedback-${messageId}`}>
      <span className="feedback-bar__label">Câu trả lời có hữu ích không?</span>
      <div className="feedback-bar__actions">
        <button
          className={`feedback-bar__btn ${selected === 'yes' ? 'feedback-bar__btn--active-yes' : ''}`}
          onClick={() => handleFeedback('yes')}
          disabled={selected !== null}
          aria-label="Có, hữu ích"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" />
            <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
          </svg>
          <span>Có</span>
        </button>
        <button
          className={`feedback-bar__btn ${selected === 'no' ? 'feedback-bar__btn--active-no' : ''}`}
          onClick={() => handleFeedback('no')}
          disabled={selected !== null}
          aria-label="Không hữu ích"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z" />
            <path d="M17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3" />
          </svg>
          <span>Không</span>
        </button>
      </div>
    </div>
  );
}

export default FeedbackBar;
