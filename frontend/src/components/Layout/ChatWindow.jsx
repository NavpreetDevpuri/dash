// src/components/Layout/ChatWindow.jsx
import React, { useRef, useState, useEffect } from 'react';
import { Box, IconButton, Typography } from '@mui/material';
import MessageBubble from '../MessageBubble';
import MessageInput from '../MessageInput';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

const ChatWindow = ({ messages, onSendMessage, pinnedInfo, highlightTerm }) => {
  const containerRef = useRef(null);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  // For pinned countdown
  const [timeLeft, setTimeLeft] = useState(0);

  // Initialize timeLeft whenever pinnedInfo changes
  useEffect(() => {
    if (pinnedInfo?.countdown) {
      setTimeLeft(pinnedInfo.countdown);
    } else {
      setTimeLeft(0);
    }
  }, [pinnedInfo]);

  // Decrement timeLeft each second
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setInterval(() => {
        setTimeLeft((prev) => Math.max(prev - 1, 0));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [timeLeft]);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      setShowScrollToBottom(scrollTop + clientHeight < scrollHeight - 20);
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
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
        position: 'relative',
      }}
    >
      {/* If pinnedInfo exists, show a top block with the pinned info */}
      {pinnedInfo && (
        <Box
          sx={{
            p: 2,
            borderBottom: '1px solid #444',
            bgcolor: 'grey.900',
          }}
        >
          <Typography variant="body1" sx={{ mb: 1 }}>
            {pinnedInfo.info}
          </Typography>

          {pinnedInfo.countdown && (
            <Typography variant="body2" sx={{ mb: 1 }}>
              {timeLeft > 0
                ? `Estimated time left: ${Math.floor(timeLeft / 60)}:${(timeLeft % 60)
                    .toString()
                    .padStart(2, '0')}`
                : 'Your order has arrived!'}
            </Typography>
          )}

          {pinnedInfo.image && (
            <Box
              component="img"
              src={pinnedInfo.image}
              alt="Pinned"
              sx={{ width: 120, height: 120, objectFit: 'cover' }}
            />
          )}
        </Box>
      )}

      {/* Scrollable message area */}
      <Box
        ref={containerRef}
        onScroll={handleScroll}
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          p: 2,
          m: 0,
          bgcolor: 'background.default',
          '&::-webkit-scrollbar': { width: 8, backgroundColor: '#222' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: '#555' },
        }}
      >
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            text={msg.text}
            attachment={msg.attachment}
            sender={msg.sender}
            highlightTerm={highlightTerm}
          />
        ))}
      </Box>

      {showScrollToBottom && (
        <IconButton
          onClick={scrollToBottom}
          sx={{
            position: 'absolute',
            bottom: 80,
            right: 20,
            bgcolor: 'primary.main',
            color: '#fff',
          }}
        >
          <ArrowDownwardIcon />
        </IconButton>
      )}

      {/* Input area at the bottom */}
      <Box sx={{ borderTop: '1px solid #444', p: 1, m: 0, bgcolor: '#2b2b2b' }}>
        <MessageInput onSendMessage={onSendMessage} />
      </Box>
    </Box>
  );
};

export default ChatWindow;