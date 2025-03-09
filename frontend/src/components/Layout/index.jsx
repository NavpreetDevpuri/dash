// src/components/Layout/index.jsx
import React, { useState, useEffect, useContext } from 'react';
import { Box } from '@mui/material';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';
import { fetchMessagesApi, sendMessageApi } from '../../mockApi';
import { AuthContext } from '../../contexts/AuthContext';

// Some default pinned conversation content
const pinnedDefaultMessages = {
  1: {
    info: "Food is on the way",      // Simplified message
    countdown: 300,                 // 5 minutes in seconds
    image: "https://via.placeholder.com/150", // Replace with your "food on the way" image
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

  const { logout } = useContext(AuthContext);

  // Load recent conversations from localStorage
  useEffect(() => {
    const storedConvos = localStorage.getItem('recentConversations');
    if (storedConvos) {
      setRecentConversations(JSON.parse(storedConvos));
    } else {
      setRecentConversations([]);
    }
  }, []);

  // Restore selected conversation on mount (if any)
  useEffect(() => {
    const storedSelectedId = localStorage.getItem('selectedConversationId');
    if (storedSelectedId) {
      setSelectedConversationId(parseInt(storedSelectedId, 10));
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
            localStorage.setItem(
              `messages_${selectedConversationId}`,
              JSON.stringify(msgs)
            );
          })();
        }
      }
    } else {
      setMessages([]);
    }
  }, [selectedConversationId]);

  // Persist messages whenever they change
  useEffect(() => {
    if (selectedConversationId !== null) {
      localStorage.setItem(
        `messages_${selectedConversationId}`,
        JSON.stringify(messages)
      );
    }
  }, [messages, selectedConversationId]);

  // Persist the selectedConversationId
  useEffect(() => {
    if (selectedConversationId !== null) {
      localStorage.setItem('selectedConversationId', selectedConversationId);
    } else {
      localStorage.removeItem('selectedConversationId');
    }
  }, [selectedConversationId]);

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
   * Show user message immediately, then fetch bot reply.
   */
  const handleSendMessage = async (messageObj) => {
    let convId = selectedConversationId;
    if (!convId) {
      // create new conversation if none is selected
      convId = handleNewConversation();
    }

    // 1) Show the user's message immediately
    const userMessage = {
      id: Math.random(),
      text: messageObj.text,
      attachment: messageObj.attachment,
      sender: 'user',
    };
    setMessages((prev) => [...prev, userMessage]);

    // 2) Get the bot reply from the mock API
    const { botReply } = await sendMessageApi(convId, messageObj);
    setMessages((prev) => [...prev, botReply]);
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

  const handleLogout = async () => {
    try {
      const response = await logout();
      
      // Even if the API call fails, proceed with local logout and redirection
      if (!response || !response.success) {
        console.warn('Backend logout failed, but proceeding with client-side logout');
      }
      
      // Navigate to login page
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
      // Still redirect to login page even if there's an error
      window.location.href = '/login';
    }
  };

  /**
   * Called when user clicks on a search result. We highlight the search term
   * and jump to the conversation.
   */
  const handleSelectConversationFromSearch = (conversationId, messageId, term) => {
    setHighlightTerm(term);
    setSelectedConversationId(parseInt(conversationId, 10));
    // If you want to auto-scroll to that message ID, you'd do it in ChatWindow with a ref
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
            pinnedInfo={pinnedDefaultMessages[selectedConversationId]} // pass pinned info if pinned
            highlightTerm={highlightTerm}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;