// src/components/SettingsPopup.jsx
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  List,
  ListItem,
  ListItemText,
  TextField,
  Button,
  Typography,
} from '@mui/material';

const settingsCategories = [
  { id: 'model', label: 'Model' },
  { id: 'apiKey', label: 'API Key' },
];

const SettingsPopup = ({ open, onClose }) => {
  const [selectedCategory, setSelectedCategory] = useState('model');
  const [apiKey, setApiKey] = useState('');

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Settings</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex' }}>
          <Box sx={{ width: '40%', borderRight: '1px solid #444', pr: 1 }}>
            <List>
              {settingsCategories.map((cat) => (
                <ListItem
                  button
                  key={cat.id}
                  selected={selectedCategory === cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                >
                  <ListItemText primary={cat.label} />
                </ListItem>
              ))}
            </List>
          </Box>
          <Box sx={{ width: '60%', pl: 1 }}>
            {selectedCategory === 'model' && (
              <Typography variant="body1">
                Select your Model: OpenAI, etc.
              </Typography>
            )}
            {selectedCategory === 'apiKey' && (
              <Box>
                <Typography variant="body1">Enter your API Key:</Typography>
                <TextField
                  type="password"
                  fullWidth
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="API Key"
                />
                <Button variant="contained" sx={{ mt: 1 }}>
                  Save
                </Button>
              </Box>
            )}
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default SettingsPopup;