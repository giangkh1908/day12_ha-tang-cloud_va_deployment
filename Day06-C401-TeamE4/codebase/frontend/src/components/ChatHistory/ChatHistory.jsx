import './ChatHistory.css';

function ChatHistory({ isOpen, onClose, conversations, onSelectConversation, onNewConversation }) {
  // Format relative time
  const getRelativeTime = (date) => {
    const now = new Date();
    const d = new Date(date);
    const diffMs = now - d;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Hôm nay';
    if (diffDays === 1) return 'Hôm qua';
    if (diffDays < 7) return `${diffDays} ngày trước`;

    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    return `${day}/${month}/${d.getFullYear()}`;
  };

  // Get first user message as title, truncated
  const getConversationTitle = (messages) => {
    const firstUserMsg = messages.find((m) => m.type === 'user');
    if (!firstUserMsg) return 'Trò chuyện mới';
    const text = firstUserMsg.text;
    return text.length > 50 ? text.slice(0, 50) + '...' : text;
  };

  return (
    <>
      {/* Overlay */}
      <div
        className={`chat-history-overlay ${isOpen ? 'chat-history-overlay--visible' : ''}`}
        onClick={onClose}
      />

      {/* Bottom Sheet */}
      <div className={`chat-history ${isOpen ? 'chat-history--open' : ''}`} id="chat-history-panel">
        {/* Header */}
        <div className="chat-history__header">
          <h2 className="chat-history__title">Lịch sử hoạt động</h2>
          <button
            className="chat-history__close-btn"
            onClick={onClose}
            aria-label="Đóng"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Conversations list */}
        <div className="chat-history__content">
          <h3 className="chat-history__section-title">Trò chuyện</h3>

          {conversations.length === 0 ? (
            <p className="chat-history__empty">Chưa có cuộc trò chuyện nào</p>
          ) : (
            <ul className="chat-history__list">
              {conversations.map((conv, index) => (
                <li key={conv.id} className="chat-history__item">
                  <button
                    className="chat-history__item-btn"
                    onClick={() => onSelectConversation(conv.id)}
                  >
                    <div className="chat-history__item-info">
                      <span className="chat-history__item-title">
                        {getConversationTitle(conv.messages)}
                      </span>
                      <span className="chat-history__item-time">
                        {getRelativeTime(conv.createdAt)}
                      </span>
                    </div>
                  </button>
                  <button
                    className="chat-history__item-menu"
                    aria-label="Tuỳ chọn"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <circle cx="6" cy="12" r="2" />
                      <circle cx="12" cy="12" r="2" />
                      <circle cx="18" cy="12" r="2" />
                    </svg>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* New conversation button */}
        <div className="chat-history__footer">
          <button
            className="chat-history__new-btn"
            id="btn-new-conversation"
            onClick={onNewConversation}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>Trò chuyện mới</span>
          </button>
        </div>
      </div>
    </>
  );
}

export default ChatHistory;
