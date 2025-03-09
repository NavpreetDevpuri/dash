// src/components/MessageInput.jsx
import React, { useState, useRef, useEffect } from 'react';
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
  const timerRef = useRef(null); // New ref for the restart timer
  
  // Add this new state to track if speech recognition should auto-restart
  const [autoRestart, setAutoRestart] = useState(false);
  
  // If you want partial transcripts:
  const [interimTranscript, setInterimTranscript] = useState('');

  // Cleanup function on component unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (err) {
          console.log('Error stopping recognition on unmount', err);
        }
      }
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  // Watch isListening state and ensure recognition is running when it should be
  useEffect(() => {
    if (isListening && autoRestart) {
      // Set a timer to restart recognition every 30 seconds to prevent timeout
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      
      timerRef.current = setTimeout(() => {
        console.log('Preemptively restarting recognition to prevent timeout');
        if (isListening && autoRestart) {
          startRecognition(true); // true indicates this is a forced restart
        }
      }, 25000); // Restart before typical 60s browser timeout
    } else {
      // Clear timer if not listening
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [isListening, autoRestart]);

  // Function to start speech recognition
  const startRecognition = (isRestart = false) => {
    // Clear any existing timers to avoid multiple timers
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.error('Speech Recognition not supported');
      setIsListening(false);
      setAutoRestart(false);
      return;
    }
    
    // Always stop any existing recognition instance first
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
        recognitionRef.current.onend = null; // Remove previous listeners
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current = null;
      } catch (err) {
        console.log('Error stopping previous recognition instance', err);
      }
    }
    
    // Create a completely new recognition instance each time
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

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
      console.error('Speech recognition error:', e.error);
      
      // Handle errors differently based on type
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
        // Permission denied - can't restart
        console.error('Microphone permission denied');
        setIsListening(false);
        setAutoRestart(false);
      } else if (e.error === 'network') {
        // Network error - try to restart
        console.error('Network error in speech recognition');
        if (autoRestart) {
          setTimeout(() => {
            if (autoRestart) startRecognition();
          }, 1000);
        }
      } else {
        // For all other errors, if autoRestart is true, we'll let onend handle it
        console.error('Other speech recognition error:', e.error);
      }
    };
    
    // Simplified onend handler
    recognition.onend = () => {
      console.log('Speech recognition ended, autoRestart:', autoRestart);
      
      // If this was a manual stop, onend will fire but we don't want to restart
      if (autoRestart) {
        // Small delay to avoid rapid restarts
        setTimeout(() => {
          if (autoRestart && isListening) {
            console.log('Auto-restarting speech recognition');
            startRecognition(true);
          } else {
            console.log('Not restarting, autoRestart or isListening changed');
          }
        }, 300);
      } else {
        console.log('Speech recognition stopped (not auto-restarting)');
        setIsListening(false);
        setInterimTranscript('');
      }
    };

    recognitionRef.current = recognition;
    
    try {
      recognition.start();
      console.log(isRestart ? 'Speech recognition restarted' : 'Speech recognition started');
      setIsListening(true);
      
      // Set a timer to force recognition restart after 25 seconds
      // This helps prevent browser timeout (typically ~60s)
      timerRef.current = setTimeout(() => {
        console.log('Preemptively restarting recognition to prevent timeout');
        if (isListening && autoRestart) {
          startRecognition(true);
        }
      }, 25000);
      
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setIsListening(false);
      setAutoRestart(false);
    }
  };

  // Function to stop speech recognition
  const stopRecognition = () => {
    console.log('Stopping speech recognition manually');
    setAutoRestart(false); // First disable auto-restart
    
    // Clear restart timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    
    // Then stop the recognition
    if (recognitionRef.current) {
      try {
        // Set onend to null to prevent it from firing and trying to restart
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
      } catch (err) {
        console.error('Error stopping recognition:', err);
      } finally {
        recognitionRef.current = null;
      }
    }
    
    setIsListening(false);
    setInterimTranscript('');
  };

  const handleSpeechToggle = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech Recognition not supported in your browser.');
      return;
    }

    if (!isListening) {
      setAutoRestart(true);
      startRecognition();
    } else {
      stopRecognition();
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
          <IconButton 
            onClick={handleSpeechToggle} 
            sx={{ 
              color: '#fff',
              animation: isListening ? 'pulse 1.5s infinite' : 'none',
              '@keyframes pulse': {
                '0%': { opacity: 1 },
                '50%': { opacity: 0.6 },
                '100%': { opacity: 1 },
              },
            }}
          >
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
    </Box>
  );
};

export default MessageInput;