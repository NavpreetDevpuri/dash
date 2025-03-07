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

export default ProfilePopup;