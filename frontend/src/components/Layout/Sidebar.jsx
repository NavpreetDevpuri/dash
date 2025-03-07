// src/components/Layout/Sidebar.jsx
import React, { useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Button,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CloseIcon from '@mui/icons-material/Close';

const pinnedItems = [
  { id: 1, label: 'Food order', icon: '🍔', count: 1 },
  { id: 2, label: 'Dineout booking', icon: '🍽️', count: 2 },
  { id: 3, label: 'Calendar', icon: '📅', count: 3 },
  { id: 4, label: 'Email', icon: '📧', count: 4 },
  { id: 5, label: 'Messages', icon: '💬', count: 5 },
];

const Sidebar = ({
  selectedId,
  onSelectConversation,
  recentConversations,
  onEditConversation,
  onDeleteConversation,
}) => {
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingConv, setEditingConv] = useState(null);
  const [newTitle, setNewTitle] = useState('');

  const handleEditClick = (conv, e) => {
    e.stopPropagation();
    setEditingConv(conv);
    setNewTitle(conv.title || conv.label);
    setEditDialogOpen(true);
  };

  const handleDeleteClick = (conv, e) => {
    e.stopPropagation();
    onDeleteConversation(conv.id);
  };

  return (
    <Box
      sx={{
        width: 300,
        borderRight: '1px solid #444',
        height: 'calc(100vh - 64px)',
        bgcolor: 'background.default',
        display: 'flex',
        flexDirection: 'column',
        m: 0,
        p: 0,
      }}
    >
      {/* Pinned Items */}
      <Box
        sx={{
          flexShrink: 0,
          overflowY: 'auto',
          maxHeight: '40%',
          '&::-webkit-scrollbar': { width: 8, backgroundColor: '#222' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: '#555' },
        }}
      >
        <List>
          {pinnedItems.map((item) => (
            <React.Fragment key={item.id}>
              <ListItem
                button
                selected={item.id === selectedId}
                onClick={() => onSelectConversation(item.id)}
                secondaryAction={
                  <Typography
                    variant="caption"
                    sx={{
                      backgroundColor: 'secondary.main',
                      borderRadius: '50%',
                      padding: '4px',
                      minWidth: 24,
                      textAlign: 'center',
                      cursor: 'pointer',
                    }}
                  >
                    {item.count}
                  </Typography>
                }
              >
                <ListItemText primary={`${item.icon} ${item.label}`} />
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      </Box>

      {/* Recent Conversations Header */}
      <Box sx={{ pl: 2, py: 1, borderTop: '1px solid #444' }}>
        <Typography variant="subtitle1">Recent Conversations</Typography>
      </Box>

      {/* Recent Conversations List */}
      <Box
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          '&::-webkit-scrollbar': { width: 8, backgroundColor: '#222' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: '#555' },
        }}
      >
        <List>
          {recentConversations && recentConversations.length > 0 ? (
            recentConversations.map((conv) => (
              <React.Fragment key={conv.id}>
                <ListItem
                  button
                  selected={conv.id === selectedId}
                  onClick={() => onSelectConversation(conv.id)}
                  sx={{
                    // Start of Selection
                    backgroundColor: conv.id === selectedId ? '#555555' : 'inherit',
                    '&:hover .hover-icons': { opacity: 1, visibility: 'visible' },
                  }}
                >
                  <ListItemText primary={conv.title} />
                  <Box
                    className="hover-icons"
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      opacity: 0,
                      visibility: 'hidden',
                      transition: 'opacity 0.3s',
                    }}
                  >
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => handleEditClick(conv, e)}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => handleDeleteClick(conv, e)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))
          ) : (
            <ListItem>
              <ListItemText primary="No recent conversations yet." />
            </ListItem>
          )}
        </List>
      </Box>

      {/* Edit Conversation Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        fullWidth
        maxWidth="lg"
      >
        <DialogTitle>
          Edit Conversation Title
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setEditDialogOpen(false)}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Conversation Title"
          />
          <Box
            sx={{
              mt: 2,
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 1,
            }}
          >
            <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button
              variant="contained"
              onClick={() => {
                onEditConversation(editingConv.id, newTitle);
                setEditDialogOpen(false);
              }}
            >
              Save
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Sidebar;