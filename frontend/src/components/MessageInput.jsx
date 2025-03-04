// src/components/MessageInput.jsx
import React, { useState, useRef } from 'react';
import { Box, TextField, IconButton, Chip } from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import MicIcon from '@mui/icons-material/Mic';
import HeadsetMicIcon from '@mui/icons-material/HeadsetMic';
import SendIcon from '@mui/icons-material/Send';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachment, setAttachment] = useState(null);
  const fileInputRef = useRef(null);

  const handleSpeechToText = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition not supported in your browser.');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.start();
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setMessage((prev) => prev + ' ' + transcript);
    };
  };

  const handleAttachmentClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAttachment(file);
    }
  };

  const handleSend = () => {
    if (!message.trim() && !attachment) return;
    let combinedMessage = message.trim();
    if (attachment) {
      combinedMessage += ` [Attachment: ${attachment.name}]`;
    }
    onSendMessage(combinedMessage);
    setMessage('');
    setAttachment(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {attachment && (
        <Chip
          label={`Attachment: ${attachment.name}`}
          onDelete={() => setAttachment(null)}
          sx={{ alignSelf: 'flex-start' }}
        />
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <IconButton color="inherit" onClick={handleAttachmentClick}>
          <AttachFileIcon />
        </IconButton>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <TextField
          fullWidth
          variant="outlined"
          size="small"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          onKeyPress={handleKeyPress}
          sx={{
            bgcolor: '#fff',
            borderRadius: 1,
            '& input': { color: '#000' },
          }}
        />
        <IconButton color="inherit" onClick={handleSpeechToText}>
          <MicIcon />
        </IconButton>
        <IconButton color="inherit">
          <HeadsetMicIcon />
        </IconButton>
        {(message.trim() || attachment) && (
          <IconButton color="primary" onClick={handleSend}>
            <SendIcon />
          </IconButton>
        )}
      </Box>
    </Box>
  );
};

export default MessageInput;