import './MessageBubble.css';

function MessageBubble({ message, isStreaming = false, displayedText = '' }) {
  const isUser = message.type === 'user';

  // Determine which text to render for bot messages
  const botText = String(isStreaming ? displayedText : message.text || '');

  // Parse bot text to render bold and lists
  const renderBotText = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let listItems = [];
    let listType = null; // 'ul' or 'ol'

    const flushList = () => {
      if (listItems.length > 0) {
        if (listType === 'ol') {
          elements.push(
            <ol key={`list-${elements.length}`} className="msg-list msg-list--ordered">
              {listItems.map((item, i) => (
                <li key={i}>{parseBold(item)}</li>
              ))}
            </ol>
          );
        } else {
          elements.push(
            <ul key={`list-${elements.length}`} className="msg-list msg-list--unordered">
              {listItems.map((item, i) => (
                <li key={i}>{parseBold(item)}</li>
              ))}
            </ul>
          );
        }
        listItems = [];
        listType = null;
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      // Bullet list: starts with "· " or "- "
      const bulletMatch = trimmed.match(/^[·•\-]\s+(.+)/);
      if (bulletMatch) {
        if (listType === 'ol') flushList();
        listType = 'ul';
        listItems.push(bulletMatch[1]);
        continue;
      }

      // Numbered list: starts with "1. ", "2. ", etc.
      const numMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
      if (numMatch) {
        if (listType === 'ul') flushList();
        listType = 'ol';
        listItems.push(numMatch[2]);
        continue;
      }

      // Regular line
      flushList();

      if (trimmed === '') {
        elements.push(<br key={`br-${i}`} />);
      } else {
        elements.push(
          <p key={`p-${i}`} className="msg-paragraph">
            {parseBold(trimmed)}
          </p>
        );
      }
    }

    flushList();
    return elements;
  };

  // Parse **bold** text
  const parseBold = (text) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div className={`message ${isUser ? 'message--user' : 'message--bot'}`}>
      <div className={`message__bubble ${isUser ? 'message__bubble--user' : 'message__bubble--bot'}`}>
        {isUser ? (
          <p className="message__text">{message.text}</p>
        ) : (
          <div className="message__content">
            {renderBotText(botText)}
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
