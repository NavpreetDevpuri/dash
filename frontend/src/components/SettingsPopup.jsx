// src/components/SettingsPopup.jsx
import React, { useState, useEffect } from 'react';
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
  IconButton,
  MenuItem,
  Select,
  Snackbar,
  Alert,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

const fetchMemories = () =>
  new Promise((resolve) =>
    setTimeout(
      () =>
        resolve([
          { id: 1, text: 'Memory 1' },
          { id: 2, text: 'Memory 2' },
        ]),
      600
    )
  );

const SettingsPopup = ({ open, onClose }) => {
  const categories = ['Models', 'Memories'];
  const [selectedCategory, setSelectedCategory] = useState('Models');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('OpenAI');
  const [memories, setMemories] = useState([]);
  const [editMemId, setEditMemId] = useState(null);
  const [editMemText, setEditMemText] = useState('');
  const [newMemoryText, setNewMemoryText] = useState('');
  const [showSnackbar, setShowSnackbar] = useState(false);

  useEffect(() => {
    if (selectedCategory === 'Memories') {
      const stored = localStorage.getItem('memories');
      if (stored) {
        setMemories(JSON.parse(stored));
      } else {
        fetchMemories().then((mems) => {
          setMemories(mems);
          localStorage.setItem('memories', JSON.stringify(mems));
        });
      }
    }
  }, [selectedCategory]);

  useEffect(() => {
    if (selectedCategory === 'Memories') {
      localStorage.setItem('memories', JSON.stringify(memories));
    }
  }, [memories, selectedCategory]);

  const handleSaveModel = () => {
    // Dummy save
    setShowSnackbar(true);
  };

  const handleEditMemory = (mem) => {
    setEditMemId(mem.id);
    setEditMemText(mem.text);
  };

  const handleSaveMemory = () => {
    setMemories((prev) =>
      prev.map((m) => (m.id === editMemId ? { ...m, text: editMemText } : m))
    );
    setEditMemId(null);
    setEditMemText('');
  };

  const handleDeleteMemory = (memId) => {
    setMemories((prev) => prev.filter((m) => m.id !== memId));
  };

  const handleAddMemory = () => {
    if (newMemoryText.trim() === '') return;
    const newMemory = {
      id: Date.now(),
      text: newMemoryText.trim(),
    };
    setMemories((prev) => [...prev, newMemory]);
    setNewMemoryText('');
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <Box sx={{ position: 'relative' }}>
        <DialogTitle>Settings</DialogTitle>
        <IconButton
          sx={{ position: 'absolute', right: 8, top: 8 }}
          onClick={onClose}
        >
          <CloseIcon />
        </IconButton>
      </Box>

      <DialogContent>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Box sx={{ width: '30%', borderRight: '1px solid #444' }}>
            <List>
              {categories.map((cat) => (
                <ListItem
                  button
                  key={cat}
                  selected={selectedCategory === cat}
                  onClick={() => setSelectedCategory(cat)}
                >
                  <ListItemText primary={cat} />
                </ListItem>
              ))}
            </List>
          </Box>
          <Box sx={{ width: '70%', pl: 2 }}>
            {selectedCategory === 'Models' && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="body1">Select Model:</Typography>
                <Select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  fullWidth
                >
                  <MenuItem value="OpenAI">OpenAI</MenuItem>
                  <MenuItem value="Other">Other</MenuItem>
                </Select>
                <Typography variant="body1">API Key:</Typography>
                <TextField
                  type="password"
                  fullWidth
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter API Key"
                />
                <Button variant="contained" onClick={handleSaveModel}>
                  Save
                </Button>
              </Box>
            )}

            {selectedCategory === 'Memories' && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="body1">Memories:</Typography>

                {memories.map((mem) => (
                  <Box
                    key={mem.id}
                    sx={{
                      p: 1,
                      border: '1px solid #555',
                      borderRadius: 1,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1,
                    }}
                  >
                    {editMemId === mem.id ? (
                      <TextField
                        value={editMemText}
                        onChange={(e) => setEditMemText(e.target.value)}
                        variant="standard"
                        multiline
                        rows={2}
                        sx={{ flexGrow: 1, mr: 1 }}
                      />
                    ) : (
                      <Typography variant="body2" sx={{ mr: 1, whiteSpace: 'pre-wrap' }}>
                        {mem.text}
                      </Typography>
                    )}
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {editMemId === mem.id ? (
                        <Button
                          variant="contained"
                          size="small"
                          onClick={handleSaveMemory}
                        >
                          Update
                        </Button>
                      ) : (
                        <IconButton
                          size="small"
                          onClick={() => handleEditMemory(mem)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      )}
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteMemory(mem.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>
                ))}

                {/* Multi-line input for new memory */}
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <TextField
                    fullWidth
                    variant="outlined"
                    size="small"
                    multiline
                    rows={3}
                    placeholder="Add new memory"
                    value={newMemoryText}
                    onChange={(e) => setNewMemoryText(e.target.value)}
                  />
                  <Button variant="contained" onClick={handleAddMemory}>
                    Add
                  </Button>
                </Box>
              </Box>
            )}
          </Box>
        </Box>
      </DialogContent>

      <Snackbar
        open={showSnackbar}
        autoHideDuration={2000}
        onClose={() => setShowSnackbar(false)}
      >
        <Alert
          onClose={() => setShowSnackbar(false)}
          severity="success"
          sx={{ width: '100%' }}
        >
          Successfully saved
        </Alert>
      </Snackbar>
    </Dialog>
  );
};

export default SettingsPopup;