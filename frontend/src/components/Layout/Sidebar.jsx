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

// Hardcoded pinned items with icons and counts
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
}) => {
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingConv, setEditingConv] = useState(null);
  const [newTitle, setNewTitle] = useState('');

  const handleEditClick = (conv) => {
    setEditingConv(conv);
    setNewTitle(conv.title || conv.label);
    setEditDialogOpen(true);
  };

  const handleEditSave = () => {
    onEditConversation(editingConv.id, newTitle);
    setEditDialogOpen(false);
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
      {/* Pinned Items Block */}
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
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography
                      variant="caption"
                      sx={{
                        backgroundColor: 'secondary.main',
                        borderRadius: '50%',
                        padding: '4px',
                        minWidth: 24,
                        textAlign: 'center',
                      }}
                    >
                      {item.count}
                    </Typography>
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditClick(item);
                      }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Box>
                }
              >
                <ListItemText primary={`${item.icon} ${item.label}`} />
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      </Box>
      {/* Recent Conversations Block */}
      <Box
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          mt: 2,
          borderTop: '1px solid #444',
          '&::-webkit-scrollbar': { width: 8, backgroundColor: '#222' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: '#555' },
        }}
      >
        <Box sx={{ pl: 2, py: 1 }}>
          <Typography variant="subtitle1">Recent Conversations</Typography>
        </Box>
        <List>
          {recentConversations && recentConversations.length > 0 ? (
            recentConversations.map((conv) => (
              <React.Fragment key={conv.id}>
                <ListItem
                  button
                  selected={conv.id === selectedId}
                  onClick={() => onSelectConversation(conv.id)}
                  secondaryAction={
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditClick(conv);
                      }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  }
                >
                  <ListItemText primary={conv.title} />
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
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
        <DialogTitle>Edit Conversation Title</DialogTitle>
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
            <Button variant="contained" onClick={handleEditSave}>
              Save
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default Sidebar;