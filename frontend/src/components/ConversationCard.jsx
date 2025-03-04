// src/components/ConversationCard.jsx
import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import InfoIcon from '@mui/icons-material/Info';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';

const ConversationCard = ({ details }) => {
  const [openPopup, setOpenPopup] = useState(false);

  const handleIconClick = () => {
    // For demonstration, we always open the pop-up
    setOpenPopup(true);
  };

  const handleClosePopup = () => {
    setOpenPopup(false);
  };

  return (
    <>
      <Paper
        sx={{
          position: 'sticky',
          top: 64, // below TopBar height
          zIndex: 10,
          margin: 2,
          padding: 2,
          bgcolor: 'secondary.main',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <IconButton color="inherit" onClick={handleIconClick}>
          <InfoIcon />
        </IconButton>
        <Typography variant="subtitle1" sx={{ ml: 1 }}>
          {details.title}
        </Typography>
      </Paper>
      <Dialog open={openPopup} onClose={handleClosePopup}>
        <DialogTitle>Conversation Details</DialogTitle>
        <DialogContent>
          <Typography variant="body1">{details.content}</Typography>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ConversationCard;