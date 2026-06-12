import { useState, useCallback, useEffect, useRef } from 'react';
import Header from '../../components/Header/Header';
import ChatArea from '../../components/ChatArea/ChatArea';
import ChatInput from '../../components/ChatInput/ChatInput';
import ChatHistory from '../../components/ChatHistory/ChatHistory';
import ConfirmPlanView from '../../components/ConfirmPlanView/ConfirmPlanView';
import SuccessPlanView from '../../components/SuccessPlanView/SuccessPlanView';
import DepositModal from '../../components/DepositModal/DepositModal';
import { sendMessage, savePlan } from '../../services/chatService';
import './ChatPage.css';

// localStorage key
const STORAGE_KEY = 'moni-conversations';

// Streaming speed (ms per character)
const STREAM_SPEED = 20;

function ChatPage() {
  // All conversations: array of { id, messages, createdAt }
  const [conversations, setConversations] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Current active conversation id
  const [activeConvId, setActiveConvId] = useState(null);

  // History panel open/close
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Bot is "thinking" (showing typing indicator)
  const [isBotTyping, setIsBotTyping] = useState(false);

  // Streaming state: which message is currently streaming and its displayed text
  const [streamingMsgId, setStreamingMsgId] = useState(null);
  const [streamingText, setStreamingText] = useState('');

  // Confirmation plan view state
  const [confirmPlanData, setConfirmPlanData] = useState(null);
  const [confirmPlanMessageId, setConfirmPlanMessageId] = useState(null);

  // Success plan view state
  const [successPlanData, setSuccessPlanData] = useState(null);

  // Deposit modal state: { plan, messageId }
  const [depositModalData, setDepositModalData] = useState(null);

  // Ref for streaming interval to clean up on unmount
  const streamingRef = useRef(null);

  // Get current conversation's messages
  const activeConv = conversations.find((c) => c.id === activeConvId);
  const messages = activeConv ? activeConv.messages : [];

  // Persist conversations to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      // localStorage full or unavailable - silently ignore
    }
  }, [conversations]);

  // Cleanup streaming on unmount
  useEffect(() => {
    return () => {
      if (streamingRef.current) {
        clearInterval(streamingRef.current);
      }
    };
  }, []);

  // Start streaming effect for a bot message
  const startStreaming = useCallback((msgId, fullText) => {
    const text = String(fullText || '');
    setStreamingMsgId(msgId);
    setStreamingText('');

    let charIndex = 0;

    streamingRef.current = setInterval(() => {
      charIndex++;
      const partial = text.slice(0, charIndex);
      setStreamingText(partial);

      if (charIndex >= text.length) {
        clearInterval(streamingRef.current);
        streamingRef.current = null;
        setStreamingMsgId(null);
        setStreamingText('');
      }
    }, STREAM_SPEED);
  }, []);

  const handleSendMessage = useCallback((text) => {
    const now = new Date();
    const userMsg = {
      id: `msg-${Date.now()}`,
      type: 'user',
      text,
      timestamp: now,
    };

    // Compute target conversation ID BEFORE state update
    const existingConv = conversations.find((c) => c.id === activeConvId);
    let targetConvId = activeConvId;

    if (!existingConv) {
      // Create new conversation ID upfront
      targetConvId = `conv-${Date.now()}`;
      const newConv = {
        id: targetConvId,
        messages: [userMsg],
        createdAt: now,
      };
      setActiveConvId(targetConvId);
      setConversations((prev) => [...prev, newConv]);
    } else {
      // Add message to existing conversation
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConvId
            ? { ...c, messages: [...c.messages, userMsg] }
            : c
        )
      );
    }

    // Show typing indicator
    setIsBotTyping(true);

    // Call chat service
    sendMessage(text)
      .then((response) => {
        setIsBotTyping(false);

        const botMsg = {
          id: `msg-${Date.now()}-bot`,
          type: 'bot',
          text: response.text,
          uiAction: response.uiAction,
          uiData: response.uiData,
          timestamp: new Date(),
        };

        setConversations((prev) =>
          prev.map((c) =>
            c.id === targetConvId
              ? { ...c, messages: [...c.messages, botMsg] }
              : c
          )
        );

        // Start streaming effect after a short delay
        setTimeout(() => {
          startStreaming(botMsg.id, response.text);
        }, 100);
      })
      .catch((error) => {
        console.error('Chat service error:', error);
        setIsBotTyping(false);

        const errorMsg = {
          id: `msg-${Date.now()}-err`,
          type: 'bot',
          text: 'Xin lỗi, Moni gặp lỗi khi xử lý. Bạn thử lại nhé! 😅',
          timestamp: new Date(),
        };

        setConversations((prev) =>
          prev.map((c) =>
            c.id === targetConvId
              ? { ...c, messages: [...c.messages, errorMsg] }
              : c
          )
        );
      });
  }, [activeConvId, conversations, startStreaming]);

  const handleOpenHistory = useCallback(() => {
    setIsHistoryOpen(true);
  }, []);

  const handleCloseHistory = useCallback(() => {
    setIsHistoryOpen(false);
  }, []);

  const handleSelectConversation = useCallback((convId) => {
    setActiveConvId(convId);
    setIsHistoryOpen(false);
  }, []);

  const handleNewConversation = useCallback(() => {
    setActiveConvId(null);
    setIsHistoryOpen(false);
  }, []);

  const handleConfirmPlanSubmit = useCallback((updatedData) => {
    const { plan } = updatedData;
    
    // Close confirmation view
    setConfirmPlanData(null);

    // Show typing indicator
    setIsBotTyping(true);

    // Call the direct save-plan API (bypasses LLM agent entirely)
    savePlan(plan)
      .then((result) => {
        setIsBotTyping(false);

        // Build the saved plan object from the backend response
        const savedPlan = result.data?.plan || result.plan || plan;

        // Update the original draft card message in place
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeConvId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === confirmPlanMessageId
                      ? {
                          ...m,
                          text: 'Kế hoạch tiết kiệm đã được lưu thành công!',
                          uiAction: result.ui_action || 'SHOW_SAVING_PLAN_SUCCESS',
                          uiData: result.data || { plan: savedPlan },
                          timestamp: new Date(),
                        }
                      : m
                  ),
                }
              : c
          )
        );

        // Show full screen SuccessPlanView
        setSuccessPlanData(savedPlan);
        setConfirmPlanMessageId(null);
      })
      .catch((error) => {
        console.error('Save plan error:', error);
        setIsBotTyping(false);
        alert('Không thể lưu kế hoạch: ' + error.message);
      });
  }, [activeConvId, confirmPlanMessageId]);

  const handleSuccessViewPlans = useCallback(() => {
    setSuccessPlanData(null);
    handleSendMessage('Xem danh sách kế hoạch tiết kiệm của tôi');
  }, [handleSendMessage]);

  const handleSuccessBackToChat = useCallback(() => {
    setSuccessPlanData(null);
  }, []);

  const handleActionClick = useCallback((action, data, messageId) => {
    let text = '';

    if (action === 'CONFIRM_SAVING_PLAN') {
      // Transition to ConfirmPlanView form screen
      setConfirmPlanData(data.plan);
      setConfirmPlanMessageId(messageId);
      return;
    } else if (action === 'VIEW_SAVING_PLANS') {
      text = 'Xem danh sách kế hoạch tiết kiệm của tôi';
    } else if (action === 'VIEW_GOAL_DETAIL') {
      text = `Xem chi tiết kế hoạch tiết kiệm có mã ${data.goalId}`;
    } else if (action === 'RECORD_DEPOSIT') {
      // Open DepositModal instead of window.prompt
      setDepositModalData({ plan: data.plan, messageId });
      return;
    } else if (action === 'DISMISS') {
      // Dismiss saving plan success card and return to normal chat text
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConvId
            ? {
                ...c,
                messages: c.messages.map((m) =>
                  m.id === messageId
                    ? { ...m, uiAction: null, uiData: null }
                    : m
                ),
              }
            : c
        )
      );
      return;
    }

    if (!text) return;

    // Show typing indicator
    setIsBotTyping(true);

    // Call chat service in the background without appending a new user bubble
    sendMessage(text)
      .then((response) => {
        setIsBotTyping(false);

        // Update the card message in place
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeConvId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId
                      ? {
                          ...m,
                          text: response.text,
                          uiAction: response.uiAction,
                          uiData: response.uiData,
                          timestamp: new Date(),
                        }
                      : m
                  ),
                }
              : c
          )
        );

        // Stream the bot's new text on the updated card
        setTimeout(() => {
          startStreaming(messageId, response.text);
        }, 100);
      })
      .catch((error) => {
        console.error('Action card interaction error:', error);
        setIsBotTyping(false);
        alert('Moni gặp lỗi khi thực hiện hành động này. Thử lại nhé! 😅');
      });
  }, [activeConvId, startStreaming]);

  return (
    <div className="chat-page" id="chat-page">
      {successPlanData ? (
        <SuccessPlanView
          plan={successPlanData}
          onViewPlans={handleSuccessViewPlans}
          onBackToChat={handleSuccessBackToChat}
        />
      ) : confirmPlanData ? (
        <ConfirmPlanView
          plan={confirmPlanData}
          onConfirm={handleConfirmPlanSubmit}
          onBack={() => setConfirmPlanData(null)}
        />
      ) : (
        <>
          <Header />
          <ChatArea
            messages={messages}
            isBotTyping={isBotTyping}
            streamingMsgId={streamingMsgId}
            streamingText={streamingText}
            onActionClick={handleActionClick}
          />
          <ChatInput
            onSendMessage={handleSendMessage}
            onOpenHistory={handleOpenHistory}
          />
        </>
      )}
      <ChatHistory
        isOpen={isHistoryOpen}
        onClose={handleCloseHistory}
        conversations={conversations}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
      {depositModalData && (
        <DepositModal
          planName={depositModalData.plan.goal_name}
          onCancel={() => setDepositModalData(null)}
          onConfirm={(amount, note) => {
            const { plan, messageId } = depositModalData;
            setDepositModalData(null);
            setIsBotTyping(true);

            let text = `Ghi nhận tiết kiệm ${amount} VND cho kế hoạch tiết kiệm có mã ${plan.id}`;
            if (note) text += ` với ghi chú: "${note}"`;

            sendMessage(text)
              .then((response) => {
                setIsBotTyping(false);
                setConversations((prev) =>
                  prev.map((c) =>
                    c.id === activeConvId
                      ? {
                          ...c,
                          messages: c.messages.map((m) =>
                            m.id === messageId
                              ? { ...m, text: response.text, uiAction: response.uiAction, uiData: response.uiData, timestamp: new Date() }
                              : m
                          ),
                        }
                      : c
                  )
                );
                setTimeout(() => startStreaming(messageId, response.text), 100);
              })
              .catch((error) => {
                console.error('Deposit error:', error);
                setIsBotTyping(false);
                alert('Moni gặp lỗi khi ghi nhận tiết kiệm. Thử lại nhé!');
              });
          }}
        />
      )}
    </div>
  );
}

export default ChatPage;
