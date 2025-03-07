(dash) (base) navpreetdevpuri@Navpreet-Singh-Devpuri-MBP---CE31D dash % cd frontend
(dash) (base) navpreetdevpuri@Navpreet-Singh-Devpuri-MBP---CE31D frontend % npm install react-wavify

added 1 package, and audited 1388 packages in 3s

276 packages are looking for funding
  run `npm fund` for details

12 vulnerabilities (6 moderate, 6 high)

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.
(dash) (base) navpreetdevpuri@Navpreet-Singh-Devpuri-MBP---CE31D frontend % find . -type d -name node_modules -prune -o -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.css" \) -exec echo "{}" \; -exec cat "{}" \;
./src/contexts/AuthContext.js
// src/contexts/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import {
  signInApi,
  signUpApi,
  logoutApi,
} from '../mockApi';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('token');
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
      setToken(storedToken);
    }
  }, []);

  useEffect(() => {
    if (user && token) {
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    }
  }, [user, token]);

  const signIn = async (email, password) => {
    setLoading(true);
    const response = await signInApi(email, password);
    setLoading(false);

    if (response.success) {
      setUser(response.user);
      setToken(response.token);
      return { success: true };
    } else {
      return { success: false, error: response.error };
    }
  };

  const signUp = async (email, password) => {
    setLoading(true);
    const response = await signUpApi(email, password);
    setLoading(false);

    if (response.success) {
      setUser(response.user);
      setToken(response.token);
      return { success: true };
    } else {
      return { success: false, error: response.error };
    }
  };

  const logout = async () => {
    setLoading(true);
    await logoutApi();
    setLoading(false);
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        signIn,
        signUp,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};./src/reportWebVitals.js
const reportWebVitals = onPerfEntry => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    });
  }
};

export default reportWebVitals;
./src/App.css
.App {
  text-align: center;
}

.App-logo {
  height: 40vmin;
  pointer-events: none;
}

@media (prefers-reduced-motion: no-preference) {
  .App-logo {
    animation: App-logo-spin infinite 20s linear;
  }
}

.App-header {
  background-color: #282c34;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
  color: white;
}

.App-link {
  color: #61dafb;
}

@keyframes App-logo-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
./src/index.js
// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';
import './index.css';


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <App />
    </ThemeProvider>
  </React.StrictMode>
);./src/theme.js
// src/theme.js
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#1976d2' },
    secondary: { main: '#9c27b0' },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    allVariants: { color: '#fff' },
  },
});

export default theme;./src/index.css
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
./src/components/SearchPopup.jsx
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

export default SearchPopup;./src/components/MessageBubble.jsx
// src/components/MessageBubble.jsx
import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

function highlightText(text, term) {
  if (!term) return text;
  const re = new RegExp(term, 'gi');
  return text.replace(re, (match) => `<mark style="background-color: yellow;">${match}</mark>`);
}

const MessageBubble = ({ text, attachment, sender, highlightTerm }) => {
  const isUser = sender === 'user';
  // highlight search term
  const highlightedContent = highlightText(text, highlightTerm);

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
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" color="secondary">
              File: {attachment.name}
            </Typography>
            {/* 
              If it's an image, you could do a preview:
              <img src={URL.createObjectURL(attachment)} alt="attachment" />
              But that only works if the user consents, or if you do more advanced logic.
            */}
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

export default MessageBubble;./src/components/SettingsPopup.jsx
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

export default SettingsPopup;./src/components/ConversationHeader.jsx
// src/components/ConversationHeader.jsx
import React, { useState } from 'react';
import { Box, Typography, IconButton, Dialog, DialogTitle, DialogContent, TextField } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import InfoIcon from '@mui/icons-material/Info';
import CloseIcon from '@mui/icons-material/Close';

const ConversationHeader = ({
  details,
  onUpdateTitle,
  onDeleteConversation,
  isPinned,
}) => {
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
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Typography variant="h6" sx={{ mr: 1 }}>
            {/* Add an icon before title */}
            {isPinned ? '⭐' : '💬'}
          </Typography>
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
          {isPinned && (
            <IconButton onClick={() => setOpenInfo(true)}>
              <InfoIcon />
            </IconButton>
          )}
        </Box>
      </Box>
      <Dialog
        open={openInfo}
        onClose={() => setOpenInfo(false)}
        fullWidth
        maxWidth="md"
      >
        <Box sx={{ position: 'relative' }}>
          <DialogTitle>Conversation Info</DialogTitle>
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setOpenInfo(false)}
          >
            <CloseIcon />
          </IconButton>
        </Box>
        <DialogContent>
          <Typography variant="body1">{details.content}</Typography>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ConversationHeader;./src/components/ProfilePopup.jsx
// src/components/ProfilePopup.jsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Typography,
  IconButton,
  Box,
  TextField,
  Tooltip,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import CheckIcon from '@mui/icons-material/Check';

const ProfilePopup = ({ open, onClose }) => {
  // Initialize profile info (could later be fetched/saved from backend or localStorage)
  const [profile, setProfile] = useState({
    name: 'John Doe',
    phone: '+1 123 456 7890',
    email: 'john.doe@example.com',
  });

  const [editMode, setEditMode] = useState({
    name: false,
    phone: false,
    email: false,
  });

  // Handle field updates (autosave on update)
  const handleFieldUpdate = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
    setEditMode((prev) => ({ ...prev, [field]: false }));
    // Optionally, persist updated profile to localStorage here
    localStorage.setItem('profile', JSON.stringify({ ...profile, [field]: value }));
  };

  // On mount, try to load profile from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('profile');
    if (stored) {
      setProfile(JSON.parse(stored));
    }
  }, []);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <Box sx={{ position: 'relative', p: 2 }}>
        <DialogTitle>Profile</DialogTitle>
        <IconButton
          sx={{ position: 'absolute', right: 8, top: 8 }}
          onClick={onClose}
        >
          <CloseIcon />
        </IconButton>
      </Box>
      <DialogContent>
        {/* Name Field */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {editMode.name ? (
            <>
              <TextField
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                variant="standard"
                fullWidth
              />
              <IconButton onClick={() => handleFieldUpdate('name', profile.name)}>
                <CheckIcon />
              </IconButton>
            </>
          ) : (
            <>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                Name: {profile.name}
              </Typography>
              <Tooltip title="Edit Name">
                <IconButton onClick={() => setEditMode((prev) => ({ ...prev, name: true }))}>
                  <EditIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
        {/* Phone Number Field */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {editMode.phone ? (
            <>
              <TextField
                value={profile.phone}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                variant="standard"
                fullWidth
              />
              <IconButton onClick={() => handleFieldUpdate('phone', profile.phone)}>
                <CheckIcon />
              </IconButton>
            </>
          ) : (
            <>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                Phone number: {profile.phone}
              </Typography>
              <Tooltip title="Edit Phone number">
                <IconButton onClick={() => setEditMode((prev) => ({ ...prev, phone: true }))}>
                  <EditIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
        {/* Email ID Field */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {editMode.email ? (
            <>
              <TextField
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                variant="standard"
                fullWidth
              />
              <IconButton onClick={() => handleFieldUpdate('email', profile.email)}>
                <CheckIcon />
              </IconButton>
            </>
          ) : (
            <>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                Email ID: {profile.email}
              </Typography>
              <Tooltip title="Edit Email ID">
                <IconButton onClick={() => setEditMode((prev) => ({ ...prev, email: true }))}>
                  <EditIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default ProfilePopup;./src/components/Layout/Sidebar.jsx
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

export default Sidebar;./src/components/Layout/TopBar.jsx
// src/components/Layout/TopBar.jsx
import React, { useState } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import SearchPopup from '../SearchPopup';
import SettingsPopup from '../SettingsPopup';
import ProfilePopup from '../ProfilePopup';

const TopBar = ({
  sidebarOpen,
  onToggleSidebar,
  onNewConversation,
  onLogout,
  openSearch,
  setOpenSearch,
  openSettings,
  setOpenSettings,
  onSelectConversation, // NEW: from Layout
}) => {
  const [openProfile, setOpenProfile] = useState(false);

  return (
    <>
      <AppBar position="static" color="primary" sx={{ m: 0 }}>
        <Toolbar sx={{ justifyContent: 'space-between', p: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton color="inherit" onClick={onToggleSidebar}>
              {sidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            </IconButton>
            <IconButton color="inherit" onClick={onNewConversation}>
              <AddIcon />
            </IconButton>
            <IconButton color="inherit" onClick={() => setOpenSearch(true)}>
              <SearchIcon />
            </IconButton>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton color="inherit" onClick={() => setOpenProfile(true)}>
              <AccountCircleIcon />
            </IconButton>
            <IconButton color="inherit" onClick={() => setOpenSettings(true)}>
              <SettingsIcon />
            </IconButton>
            <IconButton color="inherit" onClick={onLogout}>
              <LogoutIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Updated SearchPopup so it can call onSelectConversation */}
      <SearchPopup
        open={openSearch}
        onClose={() => setOpenSearch(false)}
        onSelectConversation={onSelectConversation}
      />

      <SettingsPopup open={openSettings} onClose={() => setOpenSettings(false)} />
      <ProfilePopup open={openProfile} onClose={() => setOpenProfile(false)} />
    </>
  );
};

export default TopBar;./src/components/Layout/index.jsx
// src/components/Layout/index.jsx
import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';
import { fetchMessagesApi, sendMessageApi } from '../../mockApi';

// Some default pinned conversation content
const pinnedDefaultMessages = {
  1: [
    {
      id: 1001,
      sender: 'bot',
      text: 'Your food is preparing... It will be delivered within 10 mins.',
    },
    {
      id: 1002,
      sender: 'user',
      text: 'Thanks for the update!',
    },
  ],
  2: [
    {
      id: 2001,
      sender: 'bot',
      text: 'Your dine-out booking is confirmed for tonight at 7 PM.',
    },
    {
      id: 2002,
      sender: 'user',
      text: 'Great, thanks!',
    },
  ],
  // etc. for 3, 4, 5 if you like
};

// Additional pinned "info" you want to display above the chat
const pinnedData = {
  1: {
    info: "Food is on the way, will deliver in 30 minutes (countdown here...)",
    image: "https://via.placeholder.com/150", // dummy image
  },
  2: {
    info: "Dineout booking at 8pm today",
    image: "https://via.placeholder.com/150",
  },
  3: {
    info: "Calendar pinned info, dummy text or countdown",
    image: "https://via.placeholder.com/150",
  },
  4: {
    info: "Email pinned info, dummy text",
    image: "https://via.placeholder.com/150",
  },
  5: {
    info: "Messages pinned info, dummy text",
    image: "https://via.placeholder.com/150",
  },
};

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [recentConversations, setRecentConversations] = useState([]);
  const [openSearch, setOpenSearch] = useState(false);
  const [openSettings, setOpenSettings] = useState(false);

  // For highlighting search terms
  const [highlightTerm, setHighlightTerm] = useState('');

  // Load recent conversations from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recentConversations');
    if (stored) {
      setRecentConversations(JSON.parse(stored));
    } else {
      setRecentConversations([]);
    }
  }, []);

  // Load messages for selected conversation from localStorage or dummy API
  useEffect(() => {
    if (selectedConversationId !== null) {
      const storedMessages = localStorage.getItem(`messages_${selectedConversationId}`);
      if (storedMessages) {
        setMessages(JSON.parse(storedMessages));
      } else {
        // If it's a pinned ID with default messages, load them
        if (pinnedDefaultMessages[selectedConversationId]) {
          setMessages(pinnedDefaultMessages[selectedConversationId]);
          localStorage.setItem(
            `messages_${selectedConversationId}`,
            JSON.stringify(pinnedDefaultMessages[selectedConversationId])
          );
        } else {
          // Otherwise fetch from mock API
          (async () => {
            const msgs = await fetchMessagesApi(selectedConversationId);
            setMessages(msgs);
            localStorage.setItem(`messages_${selectedConversationId}`, JSON.stringify(msgs));
          })();
        }
      }
    }
  }, [selectedConversationId]);

  // Persist messages whenever they change
  useEffect(() => {
    if (selectedConversationId !== null) {
      localStorage.setItem(`messages_${selectedConversationId}`, JSON.stringify(messages));
    }
  }, [messages, selectedConversationId]);

  const handleNewConversation = () => {
    const newConv = {
      id: Date.now(),
      title: `New Conversation ${Date.now()}`,
    };
    const updated = [newConv, ...recentConversations];
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));

    setSelectedConversationId(newConv.id);
    setMessages([]);
    return newConv.id; // Return ID so we can use it if needed
  };

  /**
   * If no conversation is selected, create a new one on the fly.
   * Then send the message to that new conversation.
   */
  const handleSendMessage = async (messageObj) => {
    let convId = selectedConversationId;
    if (!convId) {
      // create new conversation if none is selected
      convId = handleNewConversation();
    }
    const { userMessage, botReply } = await sendMessageApi(convId, messageObj);
    setMessages((prev) => [...prev, userMessage, botReply]);
  };

  const handleEditConversation = (id, newTitle) => {
    const updated = recentConversations.map((conv) =>
      conv.id === id ? { ...conv, title: newTitle } : conv
    );
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));
  };

  const handleDeleteConversation = (id) => {
    // Remove from recentConversations
    const updated = recentConversations.filter((conv) => conv.id !== id);
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));

    // If we were viewing that conversation, reset
    if (selectedConversationId === id) {
      setSelectedConversationId(null);
      setMessages([]);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  /**
   * Called when user clicks on a search result. We highlight the search term
   * and jump to the conversation.
   */
  const handleSelectConversationFromSearch = (conversationId, messageId, term) => {
    setHighlightTerm(term);
    setSelectedConversationId(conversationId);
    // If you want to auto-scroll to that message ID, you'd do it in ChatWindow with a ref
    // but this is a minimal approach
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        m: 0,
        p: 0,
      }}
    >
      <TopBar
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onNewConversation={handleNewConversation}
        onLogout={handleLogout}
        openSearch={openSearch}
        setOpenSearch={setOpenSearch}
        openSettings={openSettings}
        setOpenSettings={setOpenSettings}
        // Pass a callback so the search popup can highlight + open the conversation
        onSelectConversation={handleSelectConversationFromSearch}
      />

      <Box
        sx={{
          display: 'flex',
          flex: 1,
          minHeight: 0,
          m: 0,
          p: 0,
          bgcolor: 'background.default',
        }}
      >
        {sidebarOpen && (
          <Sidebar
            selectedId={selectedConversationId}
            onSelectConversation={setSelectedConversationId}
            recentConversations={recentConversations}
            onEditConversation={handleEditConversation}
            onDeleteConversation={handleDeleteConversation}
          />
        )}

        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <ChatWindow
            messages={messages}
            onSendMessage={handleSendMessage}
            pinnedInfo={pinnedData[selectedConversationId]} // pass pinned info if pinned
            highlightTerm={highlightTerm}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;./src/components/Layout/ChatWindow.jsx
// src/components/Layout/ChatWindow.jsx
import React, { useRef, useState, useEffect } from 'react';
import { Box, IconButton, Typography } from '@mui/material';
import MessageBubble from '../MessageBubble';
import MessageInput from '../MessageInput';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

const ChatWindow = ({ messages, onSendMessage, pinnedInfo, highlightTerm }) => {
  const containerRef = useRef(null);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      setShowScrollToBottom(scrollTop + clientHeight < scrollHeight - 20);
    }
  };

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
        position: 'relative',
      }}
    >
      {/* If pinnedInfo exists, show a top block with the pinned info */}
      {pinnedInfo && (
        <Box
          sx={{
            p: 2,
            borderBottom: '1px solid #444',
            bgcolor: 'grey.900',
          }}
        >
          <Typography variant="body1" sx={{ mb: 1 }}>
            {pinnedInfo.info}
          </Typography>
          <Box
            component="img"
            src={pinnedInfo.image}
            alt="Pinned"
            sx={{ width: 120, height: 120, objectFit: 'cover' }}
          />
        </Box>
      )}

      {/* Scrollable message area */}
      <Box
        ref={containerRef}
        onScroll={handleScroll}
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          p: 2,
          m: 0,
          bgcolor: 'background.default',
          '&::-webkit-scrollbar': { width: 8, backgroundColor: '#222' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: '#555' },
        }}
      >
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            text={msg.text}
            attachment={msg.attachment}
            sender={msg.sender}
            highlightTerm={highlightTerm}
          />
        ))}
      </Box>

      {showScrollToBottom && (
        <IconButton
          onClick={scrollToBottom}
          sx={{
            position: 'absolute',
            bottom: 80,
            right: 20,
            bgcolor: 'primary.main',
            color: '#fff',
          }}
        >
          <ArrowDownwardIcon />
        </IconButton>
      )}

      {/* Input area at the bottom */}
      <Box sx={{ borderTop: '1px solid #444', p: 1, m: 0, bgcolor: '#2b2b2b' }}>
        <MessageInput onSendMessage={onSendMessage} />
      </Box>
    </Box>
  );
};

export default ChatWindow;./src/components/MessageInput.jsx
// src/components/MessageInput.jsx
import React, { useState, useRef } from 'react';
import { Box, TextField, IconButton, Chip, Typography, Tooltip } from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import MicIcon from '@mui/icons-material/Mic';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import HeadsetMicIcon from '@mui/icons-material/HeadsetMic';
import SendIcon from '@mui/icons-material/Send';
// Waveform library (install it first: npm install react-wavify)
import Wavify from 'react-wavify';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachment, setAttachment] = useState(null);

  // For speech recognition
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);

  // If you want partial transcripts:
  const [interimTranscript, setInterimTranscript] = useState('');

  const handleSpeechToggle = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech Recognition not supported in your browser.');
      return;
    }

    if (!isListening) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.continuous = true;
      recognition.interimResults = true;

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
        console.error('Speech recognition error:', e);
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
      setIsListening(true);
    } else {
      // Stop listening
      recognitionRef.current?.stop();
      setIsListening(false);
      setInterimTranscript('');
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
          <Chip label={`Selected file: ${attachment.name}`} />
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
          <IconButton onClick={handleSpeechToggle} sx={{ color: '#fff' }}>
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

      {/* If listening, show a waveform instead of just text */}
      {isListening && (
        <Box sx={{ mt: 1 }}>
          <Wavify
            fill="#f79862"
            paused={false}
            options={{
              height: 20,
              amplitude: 30,
              speed: 0.15,
              points: 3,
            }}
            style={{ width: '100%', height: '40px' }}
          />
        </Box>
      )}
    </Box>
  );
};

export default MessageInput;./src/components/ConversationCard.jsx
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

export default ConversationCard;./src/App.test.js
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
./src/setupTests.js
// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
./src/mockApi.js
// src/mockApi.js
export async function signInApi(email, password) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  if (email === 'test@example.com' && password === 'password') {
    return {
      success: true,
      token: 'dummy-jwt-token',
      user: {
        id: 1,
        name: 'Test User',
        email,
      },
    };
  } else {
    return {
      success: false,
      error: 'Invalid credentials',
    };
  }
}

export async function signUpApi(email, password) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  return {
    success: true,
    token: 'dummy-jwt-token-signup',
    user: {
      id: 2,
      name: 'New User',
      email,
    },
  };
}

export async function fetchConversationsApi() {
  await new Promise((resolve) => setTimeout(resolve, 600));
  return [];
}

export async function fetchMessagesApi(conversationId) {
  await new Promise((resolve) => setTimeout(resolve, 600));
  // Return some dummy messages
  return [
    { id: 101, text: 'Hello from the bot!', sender: 'bot' },
    { id: 102, text: 'How can I help?', sender: 'bot' },
  ];
}

/**
 * Now accepts an object { text, attachment } instead of a plain string.
 */
export async function sendMessageApi(conversationId, messageObj) {
  await new Promise((resolve) => setTimeout(resolve, 600));

  // In a real app, you might store or process attachments differently.
  return {
    userMessage: {
      id: Math.random(),
      text: messageObj.text || '',
      attachment: messageObj.attachment || null,
      sender: 'user',
    },
    botReply: {
      id: Math.random(),
      text: `You said: "${messageObj.text}". This is a bot reply.`,
      sender: 'bot',
    },
  };
}

export async function logoutApi() {
  await new Promise((resolve) => setTimeout(resolve, 500));
  return { success: true };
}./src/pages/SignUp.jsx
// src/pages/SignUp.jsx
import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Box, Button, TextField, Typography, Container, Alert, Paper } from '@mui/material';

const SignUp = () => {
  const { signUp, loading } = useContext(AuthContext);
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const result = await signUp(email, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Sign Up failed');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
        <Typography variant="h4" gutterBottom sx={{ color: '#fff' }}>
          Sign Up
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}
        >
          <TextField
            label="Email"
            type="email"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Signing up...' : 'Sign Up'}
          </Button>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body1" sx={{ color: '#fff' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#1976d2' }}>
              Sign In
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default SignUp;./src/pages/SignIn.jsx
// src/pages/SignIn.jsx
import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Box, Button, TextField, Typography, Container, Alert, Paper } from '@mui/material';

const SignIn = () => {
  const { signIn, loading } = useContext(AuthContext);
  const navigate = useNavigate();
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const result = await signIn(email, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Sign In failed');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
        <Typography variant="h4" gutterBottom sx={{ color: '#fff' }}>
          Sign In
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Email"
            type="email"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body1" sx={{ color: '#fff' }}>
            Don't have an account?{' '}
            <Link to="/signup" style={{ color: '#1976d2' }}>
              Sign Up
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default SignIn;./src/App.js
// src/App.js
import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import Layout from './components/Layout';

function PrivateRoute({ children }) {
  const userData = localStorage.getItem('user');
  return userData ? children : <Navigate to="/login" />;
}

function App() {
  return (
(dash) (base) navpreetdevpuri@Navpreet-Singh-Devpuri-MBP---CE31D frontend % find . -type d -name node_modules -prune -o -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.css" \) -exec echo "{}" \; -exec cat "{}" \;
./src/contexts/AuthContext.js
// src/contexts/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import {
  signInApi,
  signUpApi,
  logoutApi,
} from '../mockApi';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    const storedToken = localStorage.getItem('token');
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser));
      setToken(storedToken);
    }
  }, []);

  useEffect(() => {
    if (user && token) {
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
    }
  }, [user, token]);

  const signIn = async (email, password) => {
    setLoading(true);
    const response = await signInApi(email, password);
    setLoading(false);

    if (response.success) {
      setUser(response.user);
      setToken(response.token);
      return { success: true };
    } else {
      return { success: false, error: response.error };
    }
  };

  const signUp = async (email, password) => {
    setLoading(true);
    const response = await signUpApi(email, password);
    setLoading(false);

    if (response.success) {
      setUser(response.user);
      setToken(response.token);
      return { success: true };
    } else {
      return { success: false, error: response.error };
    }
  };

  const logout = async () => {
    setLoading(true);
    await logoutApi();
    setLoading(false);
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        signIn,
        signUp,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};./src/reportWebVitals.js
const reportWebVitals = onPerfEntry => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    });
  }
};

export default reportWebVitals;
./src/App.css
.App {
  text-align: center;
}

.App-logo {
  height: 40vmin;
  pointer-events: none;
}

@media (prefers-reduced-motion: no-preference) {
  .App-logo {
    animation: App-logo-spin infinite 20s linear;
  }
}

.App-header {
  background-color: #282c34;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
  color: white;
}

.App-link {
  color: #61dafb;
}

@keyframes App-logo-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
./src/index.js
// src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';
import './index.css';


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <App />
    </ThemeProvider>
  </React.StrictMode>
);./src/theme.js
// src/theme.js
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#1976d2' },
    secondary: { main: '#9c27b0' },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    allVariants: { color: '#fff' },
  },
});

export default theme;./src/index.css
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
./src/components/SearchPopup.jsx
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

export default SearchPopup;./src/components/MessageBubble.jsx
// src/components/MessageBubble.jsx
import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

function highlightText(text, term) {
  if (!term) return text;
  const re = new RegExp(term, 'gi');
  return text.replace(re, (match) => `<mark style="background-color: yellow;">${match}</mark>`);
}

const MessageBubble = ({ text, attachment, sender, highlightTerm }) => {
  const isUser = sender === 'user';
  // highlight search term
  const highlightedContent = highlightText(text, highlightTerm);

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
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" color="secondary">
              File: {attachment.name}
            </Typography>
            {/* 
              If it's an image, you could do a preview:
              <img src={URL.createObjectURL(attachment)} alt="attachment" />
              But that only works if the user consents, or if you do more advanced logic.
            */}
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

export default MessageBubble;./src/components/SettingsPopup.jsx
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

export default SettingsPopup;./src/components/ConversationHeader.jsx
// src/components/ConversationHeader.jsx
import React, { useState } from 'react';
import { Box, Typography, IconButton, Dialog, DialogTitle, DialogContent, TextField } from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import InfoIcon from '@mui/icons-material/Info';
import CloseIcon from '@mui/icons-material/Close';

const ConversationHeader = ({
  details,
  onUpdateTitle,
  onDeleteConversation,
  isPinned,
}) => {
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
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Typography variant="h6" sx={{ mr: 1 }}>
            {/* Add an icon before title */}
            {isPinned ? '⭐' : '💬'}
          </Typography>
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
          {isPinned && (
            <IconButton onClick={() => setOpenInfo(true)}>
              <InfoIcon />
            </IconButton>
          )}
        </Box>
      </Box>
      <Dialog
        open={openInfo}
        onClose={() => setOpenInfo(false)}
        fullWidth
        maxWidth="md"
      >
        <Box sx={{ position: 'relative' }}>
          <DialogTitle>Conversation Info</DialogTitle>
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setOpenInfo(false)}
          >
            <CloseIcon />
          </IconButton>
        </Box>
        <DialogContent>
          <Typography variant="body1">{details.content}</Typography>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ConversationHeader;./src/components/ProfilePopup.jsx
// src/components/ProfilePopup.jsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Typography,
  IconButton,
  Box,
  TextField,
  Tooltip,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import CheckIcon from '@mui/icons-material/Check';

const ProfilePopup = ({ open, onClose }) => {
  // Initialize profile info (could later be fetched/saved from backend or localStorage)
  const [profile, setProfile] = useState({
    name: 'John Doe',
    phone: '+1 123 456 7890',
    email: 'john.doe@example.com',
  });

  const [editMode, setEditMode] = useState({
    name: false,
    phone: false,
    email: false,
  });

  // Handle field updates (autosave on update)
  const handleFieldUpdate = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
    setEditMode((prev) => ({ ...prev, [field]: false }));
    // Optionally, persist updated profile to localStorage here
    localStorage.setItem('profile', JSON.stringify({ ...profile, [field]: value }));
  };

  // On mount, try to load profile from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('profile');
    if (stored) {
      setProfile(JSON.parse(stored));
    }
  }, []);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <Box sx={{ position: 'relative', p: 2 }}>
        <DialogTitle>Profile</DialogTitle>
        <IconButton
          sx={{ position: 'absolute', right: 8, top: 8 }}
          onClick={onClose}
        >
          <CloseIcon />
        </IconButton>
      </Box>
      <DialogContent>
        {/* Name Field */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {editMode.name ? (
            <>
              <TextField
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                variant="standard"
                fullWidth
              />
              <IconButton onClick={() => handleFieldUpdate('name', profile.name)}>
                <CheckIcon />
              </IconButton>
            </>
          ) : (
            <>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                Name: {profile.name}
              </Typography>
              <Tooltip title="Edit Name">
                <IconButton onClick={() => setEditMode((prev) => ({ ...prev, name: true }))}>
                  <EditIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
        {/* Phone Number Field */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {editMode.phone ? (
            <>
              <TextField
                value={profile.phone}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                variant="standard"
                fullWidth
              />
              <IconButton onClick={() => handleFieldUpdate('phone', profile.phone)}>
                <CheckIcon />
              </IconButton>
            </>
          ) : (
            <>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                Phone number: {profile.phone}
              </Typography>
              <Tooltip title="Edit Phone number">
                <IconButton onClick={() => setEditMode((prev) => ({ ...prev, phone: true }))}>
                  <EditIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
        {/* Email ID Field */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {editMode.email ? (
            <>
              <TextField
                value={profile.email}
                onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                variant="standard"
                fullWidth
              />
              <IconButton onClick={() => handleFieldUpdate('email', profile.email)}>
                <CheckIcon />
              </IconButton>
            </>
          ) : (
            <>
              <Typography variant="body1" sx={{ flexGrow: 1 }}>
                Email ID: {profile.email}
              </Typography>
              <Tooltip title="Edit Email ID">
                <IconButton onClick={() => setEditMode((prev) => ({ ...prev, email: true }))}>
                  <EditIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default ProfilePopup;./src/components/Layout/Sidebar.jsx
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

export default Sidebar;./src/components/Layout/TopBar.jsx
// src/components/Layout/TopBar.jsx
import React, { useState } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import SearchPopup from '../SearchPopup';
import SettingsPopup from '../SettingsPopup';
import ProfilePopup from '../ProfilePopup';

const TopBar = ({
  sidebarOpen,
  onToggleSidebar,
  onNewConversation,
  onLogout,
  openSearch,
  setOpenSearch,
  openSettings,
  setOpenSettings,
  onSelectConversation, // NEW: from Layout
}) => {
  const [openProfile, setOpenProfile] = useState(false);

  return (
    <>
      <AppBar position="static" color="primary" sx={{ m: 0 }}>
        <Toolbar sx={{ justifyContent: 'space-between', p: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton color="inherit" onClick={onToggleSidebar}>
              {sidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            </IconButton>
            <IconButton color="inherit" onClick={onNewConversation}>
              <AddIcon />
            </IconButton>
            <IconButton color="inherit" onClick={() => setOpenSearch(true)}>
              <SearchIcon />
            </IconButton>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton color="inherit" onClick={() => setOpenProfile(true)}>
              <AccountCircleIcon />
            </IconButton>
            <IconButton color="inherit" onClick={() => setOpenSettings(true)}>
              <SettingsIcon />
            </IconButton>
            <IconButton color="inherit" onClick={onLogout}>
              <LogoutIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Updated SearchPopup so it can call onSelectConversation */}
      <SearchPopup
        open={openSearch}
        onClose={() => setOpenSearch(false)}
        onSelectConversation={onSelectConversation}
      />

      <SettingsPopup open={openSettings} onClose={() => setOpenSettings(false)} />
      <ProfilePopup open={openProfile} onClose={() => setOpenProfile(false)} />
    </>
  );
};

export default TopBar;./src/components/Layout/index.jsx
// src/components/Layout/index.jsx
import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';
import { fetchMessagesApi, sendMessageApi } from '../../mockApi';

// Some default pinned conversation content
const pinnedDefaultMessages = {
  1: [
    {
      id: 1001,
      sender: 'bot',
      text: 'Your food is preparing... It will be delivered within 10 mins.',
    },
    {
      id: 1002,
      sender: 'user',
      text: 'Thanks for the update!',
    },
  ],
  2: [
    {
      id: 2001,
      sender: 'bot',
      text: 'Your dine-out booking is confirmed for tonight at 7 PM.',
    },
    {
      id: 2002,
      sender: 'user',
      text: 'Great, thanks!',
    },
  ],
  // etc. for 3, 4, 5 if you like
};

// Additional pinned "info" you want to display above the chat
const pinnedData = {
  1: {
    info: "Food is on the way, will deliver in 30 minutes (countdown here...)",
    image: "https://via.placeholder.com/150", // dummy image
  },
  2: {
    info: "Dineout booking at 8pm today",
    image: "https://via.placeholder.com/150",
  },
  3: {
    info: "Calendar pinned info, dummy text or countdown",
    image: "https://via.placeholder.com/150",
  },
  4: {
    info: "Email pinned info, dummy text",
    image: "https://via.placeholder.com/150",
  },
  5: {
    info: "Messages pinned info, dummy text",
    image: "https://via.placeholder.com/150",
  },
};

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [recentConversations, setRecentConversations] = useState([]);
  const [openSearch, setOpenSearch] = useState(false);
  const [openSettings, setOpenSettings] = useState(false);

  // For highlighting search terms
  const [highlightTerm, setHighlightTerm] = useState('');

  // Load recent conversations from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recentConversations');
    if (stored) {
      setRecentConversations(JSON.parse(stored));
    } else {
      setRecentConversations([]);
    }
  }, []);

  // Load messages for selected conversation from localStorage or dummy API
  useEffect(() => {
    if (selectedConversationId !== null) {
      const storedMessages = localStorage.getItem(`messages_${selectedConversationId}`);
      if (storedMessages) {
        setMessages(JSON.parse(storedMessages));
      } else {
        // If it's a pinned ID with default messages, load them
        if (pinnedDefaultMessages[selectedConversationId]) {
          setMessages(pinnedDefaultMessages[selectedConversationId]);
          localStorage.setItem(
            `messages_${selectedConversationId}`,
            JSON.stringify(pinnedDefaultMessages[selectedConversationId])
          );
        } else {
          // Otherwise fetch from mock API
          (async () => {
            const msgs = await fetchMessagesApi(selectedConversationId);
            setMessages(msgs);
            localStorage.setItem(`messages_${selectedConversationId}`, JSON.stringify(msgs));
          })();
        }
      }
    }
  }, [selectedConversationId]);

  // Persist messages whenever they change
  useEffect(() => {
    if (selectedConversationId !== null) {
      localStorage.setItem(`messages_${selectedConversationId}`, JSON.stringify(messages));
    }
  }, [messages, selectedConversationId]);

  const handleNewConversation = () => {
    const newConv = {
      id: Date.now(),
      title: `New Conversation ${Date.now()}`,
    };
    const updated = [newConv, ...recentConversations];
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));

    setSelectedConversationId(newConv.id);
    setMessages([]);
    return newConv.id; // Return ID so we can use it if needed
  };

  /**
   * If no conversation is selected, create a new one on the fly.
   * Then send the message to that new conversation.
   */
  const handleSendMessage = async (messageObj) => {
    let convId = selectedConversationId;
    if (!convId) {
      // create new conversation if none is selected
      convId = handleNewConversation();
    }
    const { userMessage, botReply } = await sendMessageApi(convId, messageObj);
    setMessages((prev) => [...prev, userMessage, botReply]);
  };

  const handleEditConversation = (id, newTitle) => {
    const updated = recentConversations.map((conv) =>
      conv.id === id ? { ...conv, title: newTitle } : conv
    );
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));
  };

  const handleDeleteConversation = (id) => {
    // Remove from recentConversations
    const updated = recentConversations.filter((conv) => conv.id !== id);
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));

    // If we were viewing that conversation, reset
    if (selectedConversationId === id) {
      setSelectedConversationId(null);
      setMessages([]);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  /**
   * Called when user clicks on a search result. We highlight the search term
   * and jump to the conversation.
   */
  const handleSelectConversationFromSearch = (conversationId, messageId, term) => {
    setHighlightTerm(term);
    setSelectedConversationId(conversationId);
    // If you want to auto-scroll to that message ID, you'd do it in ChatWindow with a ref
    // but this is a minimal approach
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        m: 0,
        p: 0,
      }}
    >
      <TopBar
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onNewConversation={handleNewConversation}
        onLogout={handleLogout}
        openSearch={openSearch}
        setOpenSearch={setOpenSearch}
        openSettings={openSettings}
        setOpenSettings={setOpenSettings}
        // Pass a callback so the search popup can highlight + open the conversation
        onSelectConversation={handleSelectConversationFromSearch}
      />

      <Box
        sx={{
          display: 'flex',
          flex: 1,
          minHeight: 0,
          m: 0,
          p: 0,
          bgcolor: 'background.default',
        }}
      >
        {sidebarOpen && (
          <Sidebar
            selectedId={selectedConversationId}
            onSelectConversation={setSelectedConversationId}
            recentConversations={recentConversations}
            onEditConversation={handleEditConversation}
            onDeleteConversation={handleDeleteConversation}
          />
        )}

        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <ChatWindow
            messages={messages}
            onSendMessage={handleSendMessage}
            pinnedInfo={pinnedData[selectedConversationId]} // pass pinned info if pinned
            highlightTerm={highlightTerm}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;./src/components/Layout/ChatWindow.jsx
// src/components/Layout/ChatWindow.jsx
import React, { useRef, useState, useEffect } from 'react';
import { Box, IconButton, Typography } from '@mui/material';
import MessageBubble from '../MessageBubble';
import MessageInput from '../MessageInput';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

const ChatWindow = ({ messages, onSendMessage, pinnedInfo, highlightTerm }) => {
  const containerRef = useRef(null);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      setShowScrollToBottom(scrollTop + clientHeight < scrollHeight - 20);
    }
  };

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
        position: 'relative',
      }}
    >
      {/* If pinnedInfo exists, show a top block with the pinned info */}
      {pinnedInfo && (
        <Box
          sx={{
            p: 2,
            borderBottom: '1px solid #444',
            bgcolor: 'grey.900',
          }}
        >
          <Typography variant="body1" sx={{ mb: 1 }}>
            {pinnedInfo.info}
          </Typography>
          <Box
            component="img"
            src={pinnedInfo.image}
            alt="Pinned"
            sx={{ width: 120, height: 120, objectFit: 'cover' }}
          />
        </Box>
      )}

      {/* Scrollable message area */}
      <Box
        ref={containerRef}
        onScroll={handleScroll}
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          p: 2,
          m: 0,
          bgcolor: 'background.default',
          '&::-webkit-scrollbar': { width: 8, backgroundColor: '#222' },
          '&::-webkit-scrollbar-thumb': { backgroundColor: '#555' },
        }}
      >
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            text={msg.text}
            attachment={msg.attachment}
            sender={msg.sender}
            highlightTerm={highlightTerm}
          />
        ))}
      </Box>

      {showScrollToBottom && (
        <IconButton
          onClick={scrollToBottom}
          sx={{
            position: 'absolute',
            bottom: 80,
            right: 20,
            bgcolor: 'primary.main',
            color: '#fff',
          }}
        >
          <ArrowDownwardIcon />
        </IconButton>
      )}

      {/* Input area at the bottom */}
      <Box sx={{ borderTop: '1px solid #444', p: 1, m: 0, bgcolor: '#2b2b2b' }}>
        <MessageInput onSendMessage={onSendMessage} />
      </Box>
    </Box>
  );
};

export default ChatWindow;./src/components/MessageInput.jsx
// src/components/MessageInput.jsx
import React, { useState, useRef } from 'react';
import { Box, TextField, IconButton, Chip, Typography, Tooltip } from '@mui/material';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import MicIcon from '@mui/icons-material/Mic';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import HeadsetMicIcon from '@mui/icons-material/HeadsetMic';
import SendIcon from '@mui/icons-material/Send';
// Waveform library (install it first: npm install react-wavify)
import Wavify from 'react-wavify';

const MessageInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');
  const [attachment, setAttachment] = useState(null);

  // For speech recognition
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);

  // If you want partial transcripts:
  const [interimTranscript, setInterimTranscript] = useState('');

  const handleSpeechToggle = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech Recognition not supported in your browser.');
      return;
    }

    if (!isListening) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.continuous = true;
      recognition.interimResults = true;

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
        console.error('Speech recognition error:', e);
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
      setIsListening(true);
    } else {
      // Stop listening
      recognitionRef.current?.stop();
      setIsListening(false);
      setInterimTranscript('');
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
          <Chip label={`Selected file: ${attachment.name}`} />
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
          <IconButton onClick={handleSpeechToggle} sx={{ color: '#fff' }}>
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

      {/* If listening, show a waveform instead of just text */}
      {isListening && (
        <Box sx={{ mt: 1 }}>
          <Wavify
            fill="#f79862"
            paused={false}
            options={{
              height: 20,
              amplitude: 30,
              speed: 0.15,
              points: 3,
            }}
            style={{ width: '100%', height: '40px' }}
          />
        </Box>
      )}
    </Box>
  );
};

export default MessageInput;./src/components/ConversationCard.jsx
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

export default ConversationCard;./src/App.test.js
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
./src/setupTests.js
// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
./src/mockApi.js
// src/mockApi.js
export async function signInApi(email, password) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  if (email === 'test@example.com' && password === 'password') {
    return {
      success: true,
      token: 'dummy-jwt-token',
      user: {
        id: 1,
        name: 'Test User',
        email,
      },
    };
  } else {
    return {
      success: false,
      error: 'Invalid credentials',
    };
  }
}

export async function signUpApi(email, password) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  return {
    success: true,
    token: 'dummy-jwt-token-signup',
    user: {
      id: 2,
      name: 'New User',
      email,
    },
  };
}

export async function fetchConversationsApi() {
  await new Promise((resolve) => setTimeout(resolve, 600));
  return [];
}

export async function fetchMessagesApi(conversationId) {
  await new Promise((resolve) => setTimeout(resolve, 600));
  // Return some dummy messages
  return [
    { id: 101, text: 'Hello from the bot!', sender: 'bot' },
    { id: 102, text: 'How can I help?', sender: 'bot' },
  ];
}

/**
 * Now accepts an object { text, attachment } instead of a plain string.
 */
export async function sendMessageApi(conversationId, messageObj) {
  await new Promise((resolve) => setTimeout(resolve, 600));

  // In a real app, you might store or process attachments differently.
  return {
    userMessage: {
      id: Math.random(),
      text: messageObj.text || '',
      attachment: messageObj.attachment || null,
      sender: 'user',
    },
    botReply: {
      id: Math.random(),
      text: `You said: "${messageObj.text}". This is a bot reply.`,
      sender: 'bot',
    },
  };
}

export async function logoutApi() {
  await new Promise((resolve) => setTimeout(resolve, 500));
  return { success: true };
}./src/pages/SignUp.jsx
// src/pages/SignUp.jsx
import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Box, Button, TextField, Typography, Container, Alert, Paper } from '@mui/material';

const SignUp = () => {
  const { signUp, loading } = useContext(AuthContext);
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const result = await signUp(email, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Sign Up failed');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
        <Typography variant="h4" gutterBottom sx={{ color: '#fff' }}>
          Sign Up
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}
        >
          <TextField
            label="Email"
            type="email"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Signing up...' : 'Sign Up'}
          </Button>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body1" sx={{ color: '#fff' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#1976d2' }}>
              Sign In
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default SignUp;./src/pages/SignIn.jsx
// src/pages/SignIn.jsx
import React, { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Box, Button, TextField, Typography, Container, Alert, Paper } from '@mui/material';

const SignIn = () => {
  const { signIn, loading } = useContext(AuthContext);
  const navigate = useNavigate();
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const result = await signIn(email, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Sign In failed');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4, bgcolor: 'background.paper' }}>
        <Typography variant="h4" gutterBottom sx={{ color: '#fff' }}>
          Sign In
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            label="Email"
            type="email"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
            InputLabelProps={{ style: { color: '#fff' } }}
            InputProps={{ style: { color: '#fff' } }}
          />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body1" sx={{ color: '#fff' }}>
            Don't have an account?{' '}
            <Link to="/signup" style={{ color: '#1976d2' }}>
              Sign Up
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default SignIn;./src/App.js
// src/App.js
import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import Layout from './components/Layout';

function PrivateRoute({ children }) {
  const userData = localStorage.getItem('user');
  return userData ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;%                                                                                                                    


-----

above is the code for the app, update with below details, read properly and think hardly and give me updates codes

----

- when i refresh and start a new conversation whatever i type on text inbox it is not showing in the chat, fix it
- it shoudn't be like this "Food is on the way, will deliver in 30 minutes (countdown here...)" it should be like when i order something the app shows "Food is on the way" like swiggy, zomato etc and countdown should be like real time counting from 5 minuets to 0 minutes, find the screenshot pictures for your refrence and it should look similar like that. For time countdown, use dummi API if it needs. Also, "Food is on the way" should be in the pictures, use dummi api if possible
- remove waveform and add similar like screenshot which i attached, it should look like running because we are doing it as live
- when we add any documents, file name should be visible clearly like pdf, image etc same as chatgpt, see the attached screenshot,m it should look like that

----

TAKE YOUR TIME AND THINK HARD




