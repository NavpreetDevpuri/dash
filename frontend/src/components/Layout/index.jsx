// src/components/Layout/index.jsx
import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';
import TopBar from './TopBar';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';
import { fetchMessagesApi, sendMessageApi } from '../../mockApi';

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedConversationId, setSelectedConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [recentConversations, setRecentConversations] = useState([]);
  const [conversationDetails, setConversationDetails] = useState(null);
  const [openSearch, setOpenSearch] = useState(false);
  const [openSettings, setOpenSettings] = useState(false);

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
        (async () => {
          const msgs = await fetchMessagesApi(selectedConversationId);
          setMessages(msgs);
          localStorage.setItem(`messages_${selectedConversationId}`, JSON.stringify(msgs));
        })();
      }
      // For pinned categories (IDs 1–5), show conversation header with controls
      if (selectedConversationId <= 5) {
        setConversationDetails({
          title: `Pinned: ${selectedConversationId}`,
          content: `Detailed info for conversation ${selectedConversationId}.`,
          showHeader: true,
        });
      } else {
        setConversationDetails(null);
      }
    }
  }, [selectedConversationId]);

  // Persist messages whenever they change
  useEffect(() => {
    if (selectedConversationId !== null) {
      localStorage.setItem(`messages_${selectedConversationId}`, JSON.stringify(messages));
    }
  }, [messages, selectedConversationId]);

  const handleSendMessage = async (messageText) => {
    if (!selectedConversationId) return;
    const { userMessage, botReply } = await sendMessageApi(selectedConversationId, messageText);
    setMessages((prev) => [...prev, userMessage, botReply]);
  };

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
  };

  const handleEditConversation = (id, newTitle) => {
    const updated = recentConversations.map((conv) =>
      conv.id === id ? { ...conv, title: newTitle } : conv
    );
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));
    if (selectedConversationId === id && conversationDetails) {
      setConversationDetails({ ...conversationDetails, title: newTitle });
    }
  };

  const handleUpdateConversationTitle = (newTitle) => {
    if (conversationDetails) {
      setConversationDetails({ ...conversationDetails, title: newTitle });
    }
  };

  const handleDeleteConversation = () => {
    const updated = recentConversations.filter((conv) => conv.id !== selectedConversationId);
    setRecentConversations(updated);
    localStorage.setItem('recentConversations', JSON.stringify(updated));
    setSelectedConversationId(null);
    setMessages([]);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', m: 0, p: 0 }}>
      <TopBar
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onNewConversation={handleNewConversation}
        onLogout={handleLogout}
        openSearch={openSearch}
        setOpenSearch={setOpenSearch}
        openSettings={openSettings}
        setOpenSettings={setOpenSettings}
      />
      <Box sx={{ display: 'flex', flex: 1, m: 0, p: 0 }}>
        {sidebarOpen && (
          <Sidebar
            selectedId={selectedConversationId}
            onSelectConversation={setSelectedConversationId}
            recentConversations={recentConversations}
            onEditConversation={handleEditConversation}
          />
        )}
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          conversationDetails={conversationDetails}
          onUpdateConversationTitle={handleUpdateConversationTitle}
          onDeleteConversation={handleDeleteConversation}
        />
      </Box>
    </Box>
  );
};

export default Layout;