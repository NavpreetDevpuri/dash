// src/components/SearchPopup.jsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  List,
  ListItem,
  ListItemText,
  Typography,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

const SearchPopup = ({ open, onClose, onSelectConversation }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (!open) {
      setQuery('');
      setResults([]);
      return;
    }
  }, [open]);

  useEffect(() => {
    if (query.trim() === '') {
      setResults([]);
      return;
    }
    // Gather all messages from localStorage
    const allResults = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      // messages_<conversationId>
      if (key.startsWith('messages_')) {
        const convId = key.replace('messages_', '');
        const msgs = JSON.parse(localStorage.getItem(key)) || [];
        msgs.forEach((m) => {
          if (m.text.toLowerCase().includes(query.toLowerCase())) {
            allResults.push({
              conversationId: convId,
              messageId: m.id,
              text: m.text,
            });
          }
        });
      }
    }
    setResults(allResults);
  }, [query]);

  const handleResultClick = (result) => {
    // Pass the conversation ID, message ID, and the search term
    onSelectConversation(result.conversationId, result.messageId, query);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <DialogTitle>
        Search
        <IconButton
          sx={{ position: 'absolute', right: 8, top: 8 }}
          onClick={onClose}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search messages..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ mb: 2 }}
        />
        {results.length > 0 ? (
          <List>
            {results.map((result, index) => (
              <ListItem
                button
                key={`${result.conversationId}-${result.messageId}-${index}`}
                onClick={() => handleResultClick(result)}
              >
                <ListItemText
                  primary={
                    <Typography noWrap>
                      {result.text.length > 40
                        ? '...' + result.text.substring(0, 40) + '...'
                        : result.text}
                    </Typography>
                  }
                  secondary={`Conv ID: ${result.conversationId}`}
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2">No results found.</Typography>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default SearchPopup;