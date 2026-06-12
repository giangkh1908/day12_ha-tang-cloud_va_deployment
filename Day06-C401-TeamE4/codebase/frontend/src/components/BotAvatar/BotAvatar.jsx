import './BotAvatar.css';

function BotAvatar() {
  return (
    <div className="bot-avatar" id="bot-avatar">
      <div className="bot-avatar__bubble">
        <div className="bot-avatar__face">
          <div className="bot-avatar__eyes">
            <span className="bot-avatar__eye"></span>
            <span className="bot-avatar__eye"></span>
          </div>
          <div className="bot-avatar__mouth"></div>
        </div>
        {/* Decorative sparkle */}
        <div className="bot-avatar__sparkle">✦</div>
      </div>
    </div>
  );
}

export default BotAvatar;
