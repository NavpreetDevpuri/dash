// src/components/MessageInput.jsx
import React, { useState, useRef } from 'react';
import { Box, TextField, IconButton, Chip, Tooltip } from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import MicIcon from '@mui/icons-material/Mic';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import HeadsetMicIcon from '@mui/icons-material/HeadsetMic';
import SendIcon from '@mui/icons-material/Send';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachment, setAttachment] = useState(null);

  // For speech recognition
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);

  // If you want partial transcripts:
  const [interimTranscript, setInterimTranscript] = useState('');

  const handleSpeechToggle = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech Recognition not supported in your browser.');
      return;
    }

    if (!isListening) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += transcript;
          } else {
            interim += transcript;
          }
        }

        // Add final text to our message
        if (final) {
          setMessage((prev) => (prev ? (prev + ' ' + final).trim() : final.trim()));
        }

        // Keep track of partial text
        setInterimTranscript(interim);
      };

      recognition.onerror = (e) => {
        console.error('Speech recognition error:', e);
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
      setIsListening(true);
    } else {
      // Stop listening
      recognitionRef.current?.stop();
      setIsListening(false);
      setInterimTranscript('');
    }
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
    // If there's nothing to send, do nothing
    if (!message.trim() && !attachment) return;

    // Build the message object
    const messageObj = {
      text: message.trim(),
      attachment: attachment,
    };

    onSendMessage(messageObj);

    // Clear local state
    setMessage('');
    setAttachment(null);
    setInterimTranscript('');
  };

  const handleKeyPress = (e) => {
    // Multi-line input. Send on "Enter" only if SHIFT is not pressed.
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Display text + any partial transcript
  const displayValue = isListening
    ? message + (interimTranscript ? ' ' + interimTranscript : '')
    : message;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {attachment && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={`Selected file: ${attachment.name}`}
            variant="outlined"
            sx={{ color: '#fff', borderColor: '#ccc' }}
          />
        </Box>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip title="Attach a file">
          <IconButton onClick={handleAttachmentClick} sx={{ color: '#fff' }}>
            <AttachFileIcon />
          </IconButton>
        </Tooltip>
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
          multiline
          minRows={1}
          value={displayValue}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          onKeyPress={handleKeyPress}
          sx={{
            bgcolor: '#2d2d2d',
            borderRadius: 1,
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: '#ccc',
              },
            },
            '& .MuiOutlinedInput-input': {
              color: '#fff',
            },
          }}
        />

        <Tooltip title={isListening ? 'Stop Recording' : 'Start Recording'}>
          <IconButton onClick={handleSpeechToggle} sx={{ color: '#fff' }}>
            {isListening ? <StopCircleIcon /> : <MicIcon />}
          </IconButton>
        </Tooltip>

        <IconButton sx={{ color: '#fff' }}>
          <HeadsetMicIcon />
        </IconButton>

        {(message.trim() || attachment) && (
          <Tooltip title="Send">
            <IconButton onClick={handleSend} sx={{ color: '#fff' }}>
              <SendIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* If listening, show a simple bar animation instead of waveform */}
      {isListening && (
        <Box
          sx={{
            mt: 1,
            display: 'flex',
            alignItems: 'flex-end',
            gap: '4px',
            height: '24px',
          }}
        >
          {/* Each bar uses a keyframe animation from index.css */}
          <Box
            sx={{
              width: '4px',
              backgroundColor: 'limegreen',
              animation: 'barAnimation 1s infinite',
              animationDelay: '0.0s',
            }}
          />
          <Box
            sx={{
              width: '4px',
              backgroundColor: 'limegreen',
              animation: 'barAnimation 1s infinite',
              animationDelay: '0.1s',
            }}
          />
          <Box
            sx={{
              width: '4px',
              backgroundColor: 'limegreen',
              animation: 'barAnimation 1s infinite',
              animationDelay: '0.2s',
            }}
          />
          <Box
            sx={{
              width: '4px',
              backgroundColor: 'limegreen',
              animation: 'barAnimation 1s infinite',
              animationDelay: '0.3s',
            }}
          />
          <Box
            sx={{
              width: '4px',
              backgroundColor: 'limegreen',
              animation: 'barAnimation 1s infinite',
              animationDelay: '0.4s',
            }}
          />
        </Box>
      )}
    </Box>
  );
};

export default MessageInput;