// src/components/ConversationHeader.jsx
import React, { useState } from 'react';
import { Box, Typography, IconButton, Dialog, DialogTitle, DialogContent, TextField } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import InfoIcon from '@mui/icons-material/Info';

const ConversationHeader = ({ details, onUpdateTitle, onDeleteConversation }) => {
  const [editMode, setEditMode] = useState(false);
  const [title, setTitle] = useState(details.title);
  const [openInfo, setOpenInfo] = useState(false);

  const handleSave = () => {
    onUpdateTitle(title);
    setEditMode(false);
  };

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 1,
          borderBottom: '1px solid #444',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ flexGrow: 1 }}>
          {editMode ? (
            <TextField
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              variant="standard"
              InputProps={{ sx: { color: '#fff' } }}
            />
          ) : (
            <Typography variant="h6" noWrap>
              {title.length > 20 ? title.substring(0, 20) + '...' : title}
            </Typography>
          )}
        </Box>
        <Box>
          {editMode ? (
            <IconButton onClick={handleSave}>
              <EditIcon />
            </IconButton>
          ) : (
            <IconButton onClick={() => setEditMode(true)}>
              <EditIcon />
            </IconButton>
          )}
          <IconButton onClick={onDeleteConversation}>
            <DeleteIcon />
          </IconButton>
          <IconButton onClick={() => setOpenInfo(true)}>
            <InfoIcon />
          </IconButton>
        </Box>
      </Box>
      <Dialog open={openInfo} onClose={() => setOpenInfo(false)}>
        <DialogTitle>Conversation Info</DialogTitle>
        <DialogContent>
          <Typography variant="body1">{details.content}</Typography>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ConversationHeader;