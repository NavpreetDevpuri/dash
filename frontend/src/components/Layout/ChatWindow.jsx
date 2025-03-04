// src/components/Layout/ChatWindow.jsx
import React, { useRef, useState, useEffect } from 'react';
import { Box, IconButton } from '@mui/material';
import MessageBubble from '../MessageBubble';
import MessageInput from '../MessageInput';
import ConversationHeader from '../ConversationHeader';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

const ChatWindow = ({
  messages,
  onSendMessage,
  conversationDetails,
  onUpdateConversationTitle,
  onDeleteConversation,
}) => {
  const containerRef = useRef(null);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      if (scrollTop + clientHeight < scrollHeight - 20) {
        setShowScrollToBottom(true);
      } else {
        setShowScrollToBottom(false);
      }
    }
  };

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', m: 0, p: 0 }}>
      {conversationDetails && conversationDetails.showHeader && (
        <ConversationHeader
          details={conversationDetails}
          onUpdateTitle={onUpdateConversationTitle}
          onDeleteConversation={onDeleteConversation}
        />
      )}
      <Box
        ref={containerRef}
        onScroll={handleScroll}
        sx={{
          flexGrow: 1,
          p: 2,
          overflowY: 'auto',
          m: 0,
          '&::-webkit-scrollbar': { width: 8, backgroundColor: '#222' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: '#555' },
          bgcolor: 'background.paper',
        }}
      >
        {messages.map((msg) => (
          <MessageBubble key={msg.id} text={msg.text} sender={msg.sender} />
        ))}
      </Box>
      {showScrollToBottom && (
        <IconButton
          onClick={scrollToBottom}
          sx={{
            position: 'fixed',
            bottom: 80,
            right: 20,
            bgcolor: 'primary.main',
            color: '#fff',
          }}
        >
          <ArrowDownwardIcon />
        </IconButton>
      )}
      <Box sx={{ borderTop: '1px solid #444', p: 1, m: 0 }}>
        <MessageInput onSendMessage={onSendMessage} />
      </Box>
    </Box>
  );
};

export default ChatWindow;