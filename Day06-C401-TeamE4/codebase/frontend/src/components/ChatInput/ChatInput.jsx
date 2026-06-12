import { useState } from 'react';
import './ChatInput.css';

function ChatInput({ onSendMessage, onOpenHistory }) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    onSendMessage(message.trim());
    setMessage('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-input-wrapper" id="chat-input-wrapper">
      <button
        className="chat-input__history-btn"
        id="btn-chat-history"
        aria-label="Lịch sử chat"
        title="Lịch sử chat"
        onClick={onOpenHistory}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <form className="chat-input" onSubmit={handleSubmit}>
        <span className="chat-input__sparkle-icon">✨</span>
        <input
          type="text"
          className="chat-input__field"
          id="chat-message-input"
          placeholder="Hỏi Moni bất cứ điều gì..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          autoComplete="off"
        />
        <button
          type="submit"
          className="chat-input__send-btn"
          id="btn-send-message"
          aria-label="Gửi tin nhắn"
          disabled={!message.trim()}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </form>
    </div>
  );
}

export default ChatInput;
