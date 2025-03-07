// src/components/MessageBubble.jsx
import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import ImageIcon from '@mui/icons-material/Image';

function highlightText(text, term) {
  if (!term) return text;
  const re = new RegExp(term, 'gi');
  return text.replace(re, (match) => `<mark style="background-color: yellow;">${match}</mark>`);
}

const MessageBubble = ({ text, attachment, sender, highlightTerm }) => {
  const isUser = sender === 'user';
  // highlight search term
  const highlightedContent = highlightText(text, highlightTerm);

  // Determine icon based on attachment type (if any)
  let fileIcon = null;
  if (attachment) {
    const mimeType = attachment.type || ''; // e.g. "application/pdf", "image/png"
    if (mimeType.includes('pdf')) {
      fileIcon = <PictureAsPdfIcon />;
    } else if (mimeType.includes('image')) {
      fileIcon = <ImageIcon />;
    } else {
      fileIcon = <InsertDriveFileIcon />;
    }
  }

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
          overflowWrap: 'break-word',
        }}
      >
        {/* If there's an attachment, show it at the top (like ChatGPT) */}
        {attachment && (
          <Box
            sx={{
              mb: 1,
              p: 1,
              borderRadius: 1,
              backgroundColor: 'grey.700',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            {fileIcon}
            <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
              {attachment.name || 'Attached file'}
            </Typography>
          </Box>
        )}
        <Typography
          variant="body1"
          dangerouslySetInnerHTML={{ __html: highlightedContent }}
        />
      </Paper>
    </Box>
  );
};

export default MessageBubble;