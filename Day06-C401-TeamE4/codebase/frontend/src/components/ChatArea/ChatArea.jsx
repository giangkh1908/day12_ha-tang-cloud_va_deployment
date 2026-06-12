import { useEffect, useRef } from 'react';
import BotAvatar from '../BotAvatar/BotAvatar';
import MessageBubble from '../MessageBubble/MessageBubble';
import FeedbackBar from '../FeedbackBar/FeedbackBar';
import TypingIndicator from '../TypingIndicator/TypingIndicator';
import ActionCard from '../ActionCard/ActionCard';
import './ChatArea.css';

function ChatArea({
  messages = [],
  isBotTyping = false,
  streamingMsgId = null,
  streamingText = '',
  onActionClick = () => {},
}) {
  const messagesEndRef = useRef(null);
  const chatAreaRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive or typing/streaming state changes
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isBotTyping, streamingText]);

  const hasMessages = messages.length > 0;

  // Format timestamp: dd/mm/yyyy, HH:mm
  const formatTimestamp = (date) => {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year}, ${hours}:${minutes}`;
  };

  // Check if we should show timestamp (first message or > 5 min gap)
  const shouldShowTimestamp = (index) => {
    if (index === 0) return true;
    const current = new Date(messages[index].timestamp);
    const prev = new Date(messages[index - 1].timestamp);
    return (current - prev) > 5 * 60 * 1000; // 5 minutes
  };

  return (
    <main
      className={`chat-area ${hasMessages ? 'chat-area--has-messages' : ''}`}
      id="chat-area"
      ref={chatAreaRef}
    >
      {/* Background gradient decorations */}
      <div className="chat-area__bg-decor chat-area__bg-decor--right"></div>
      <div className="chat-area__bg-decor chat-area__bg-decor--left"></div>

      {!hasMessages && !isBotTyping ? (
        /* Welcome content */
        <div className="chat-area__welcome">
          <BotAvatar />
          <h2 className="chat-area__greeting">
            Chào Giang, mình là Trợ thủ AI
            <br />
            của riêng bạn
          </h2>
        </div>
      ) : (
        /* Messages list */
        <div className="chat-area__messages">
          {messages.map((msg, index) => (
            <div key={msg.id} className="chat-area__message-group">
              {shouldShowTimestamp(index) && (
                <div className="chat-area__timestamp">
                  {formatTimestamp(msg.timestamp)}
                </div>
              )}
              <MessageBubble
                message={msg}
                isStreaming={streamingMsgId === msg.id}
                displayedText={streamingMsgId === msg.id ? streamingText : ''}
              />
              {msg.type === 'bot' && msg.uiAction && streamingMsgId !== msg.id && (
                <ActionCard
                  uiAction={msg.uiAction}
                  uiData={msg.uiData}
                  onActionClick={(action, data) => onActionClick(action, data, msg.id)}
                />
              )}
              {msg.type === 'bot' && streamingMsgId !== msg.id && (
                <FeedbackBar messageId={msg.id} />
              )}
            </div>
          ))}

          {/* Typing indicator */}
          {isBotTyping && (
            <div className="chat-area__message-group">
              <TypingIndicator />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}
    </main>
  );
}

export default ChatArea;
