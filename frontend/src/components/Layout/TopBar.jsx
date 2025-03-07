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

export default TopBar;