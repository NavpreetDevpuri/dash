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
} from '@mui/material';

const SearchPopup = ({ open, onClose }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (query.trim() === '') {
      setResults([]);
      return;
    }
    const storedConversations = JSON.parse(localStorage.getItem('recentConversations')) || [];
    const filtered = storedConversations.filter((conv) =>
      conv.title.toLowerCase().includes(query.toLowerCase())
    );
    setResults(filtered);
  }, [query]);

  const handleResultClick = (result) => {
    console.log('Navigate to conversation:', result.id);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth>
      <DialogTitle>Search Conversations</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ mb: 2 }}
        />
        {results.length > 0 ? (
          <List>
            {results.map((result) => (
              <ListItem button key={result.id} onClick={() => handleResultClick(result)}>
                <ListItemText
                  primary={
                    <Typography noWrap>
                      {result.title.length > 30
                        ? '...' + result.title.substring(0, 30) + '...'
                        : result.title}
                    </Typography>
                  }
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