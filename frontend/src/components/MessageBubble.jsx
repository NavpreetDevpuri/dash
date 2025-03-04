// src/components/MessageBubble.jsx
import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

const MessageBubble = ({ text, sender }) => {
  const isUser = sender === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 1,
      }}
    >
      <Paper
        sx={{
          padding: '8px 16px',
          backgroundColor: isUser ? 'primary.dark' : 'grey.800',
          color: '#fff',
          maxWidth: '60%',
        }}
      >
        <Typography variant="body1">{text}</Typography>
      </Paper>
    </Box>
  );
};

export default MessageBubble;