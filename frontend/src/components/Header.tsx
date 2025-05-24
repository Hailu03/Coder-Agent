import { 
  AppBar, 
  Toolbar, 
  Typography, 
  IconButton, 
  useTheme, 
  Box, 
  Menu, 
  MenuItem, 
  Avatar, 
  Divider, 
  ListItemIcon, 
  Switch, 
  FormControlLabel, 
  TextField, 
  Button, 
  Dialog, 
  DialogActions, 
  DialogContent, 
  DialogTitle,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  Snackbar,
  Alert,
  InputAdornment
} from '@mui/material';
import { 
  Code, 
  Settings, 
  Person, 
  Logout, 
  AccountCircle, 
  Edit, 
  Brightness4, 
  Brightness7, 
  KeyboardArrowDown,
  SmartToy,
  Visibility,
  VisibilityOff, 
  Login
} from '@mui/icons-material';
import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import axios from 'axios';
import apiService, { SettingsUpdateRequest, UserResponse } from '../services/apiService';

interface HeaderProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

interface UserInfo {
  name: string;
  email: string;
  avatar?: string;
}

// Default user info
const defaultUser: UserInfo = {
  name: 'Guest User',
  email: 'guest@example.com'
};

const Header = ({ darkMode, toggleDarkMode }: HeaderProps) => {
  const theme = useTheme();
  const navigate = useNavigate();
  
  // Authentication state
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  
  // User info state
  const [userInfo, setUserInfo] = useState<UserInfo>(defaultUser);
  const [editUserDialogOpen, setEditUserDialogOpen] = useState(false);
  const [newUserInfo, setNewUserInfo] = useState<UserInfo>(userInfo);
  
  // Settings menu state
  const [settingsAnchorEl, setSettingsAnchorEl] = useState<null | HTMLElement>(null);
  const settingsMenuOpen = Boolean(settingsAnchorEl);
  
  // User menu state
  const [userAnchorEl, setUserAnchorEl] = useState<null | HTMLElement>(null);
  const userMenuOpen = Boolean(userAnchorEl);
    // AI model settings
  const [aiModel, setAiModel] = useState<string>('gemini');
  const [apiKey, setApiKey] = useState<string>('');
  
  // Password visibility states
  const [showApiKey, setShowApiKey] = useState(false);
  
  // Alert state
  const [alertOpen, setAlertOpen] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertSeverity, setAlertSeverity] = useState<'success' | 'error'>('success');
  const [isSettingsSaving, setIsSettingsSaving] = useState(false);

  // Check login status on initial load
  useEffect(() => {
    checkAuthStatus();
    
    // Load settings on mount
    loadSettings();
  }, []);
  
  // Check if user is logged in and load user data
  const checkAuthStatus = async () => {
    try {
      if (apiService.isLoggedIn()) {
        // Try to get user from localStorage first for immediate display
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const userData = JSON.parse(storedUser) as UserResponse;
          setUserInfo({
            name: userData.full_name || userData.username,
            email: userData.email,
            avatar: userData.avatar
          });
        }
        
        setIsLoggedIn(true);
        
        // Then try to refresh user data from server
        try {
          const currentUser = await apiService.getCurrentUser();
          setUserInfo({
            name: currentUser.full_name || currentUser.username,
            email: currentUser.email,
            avatar: currentUser.avatar
          });
          
          // Update stored user data
          localStorage.setItem('user', JSON.stringify(currentUser));
        } catch (err) {
          console.error('Error refreshing user data:', err);
          // If token is invalid, logout
          if (axios.isAxiosError(err) && err.response?.status === 401) {
            handleLogout();
          }
        }
      } else {
        setIsLoggedIn(false);
        setUserInfo(defaultUser);
      }
    } catch (err) {
      console.error('Error checking auth status:', err);
      setIsLoggedIn(false);
      setUserInfo(defaultUser);
    }
  };
  
  // Load settings from API
  const loadSettings = async () => {
    try {
      if (apiService.isLoggedIn()) {
        // If logged in, get full settings
        const settings = await apiService.getSettings();
        if (settings) {
          setAiModel(settings.ai_provider || 'gemini');
          // Don't set API keys directly in UI for security reasons
        }
      }
      // Removed public settings handling since the endpoint was removed
    } catch (err) {
      console.error('Error loading settings:', err);
    }
  };
  
  // Handlers for user menu
  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserAnchorEl(event.currentTarget);
  };
  
  const handleUserMenuClose = () => {
    setUserAnchorEl(null);
  };
  
  // Handlers for settings menu
  const handleSettingsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    if (!isLoggedIn) {
      // If not logged in, show login alert
      setAlertSeverity('error');
      setAlertMessage('Please log in to access settings');
      setAlertOpen(true);
      return;
    }
    setSettingsAnchorEl(event.currentTarget);
  };
  
  const handleSettingsMenuClose = () => {
    setSettingsAnchorEl(null);
  };
  
  // Handlers for user info dialog
  const handleEditUserOpen = () => {
    setNewUserInfo(userInfo);
    setEditUserDialogOpen(true);
    handleUserMenuClose();
  };
  
  const handleEditUserClose = () => {
    setEditUserDialogOpen(false);
  };
  
  // Handler for user edit save
  const handleEditUserSave = async () => {
    try {
      // Only update if logged in
      if (isLoggedIn) {
        const result = await apiService.updateUser({
          full_name: newUserInfo.name,
          email: newUserInfo.email
        });
        
        // Update local state
        setUserInfo({
          name: result.full_name || result.username,
          email: result.email,
          avatar: result.avatar
        });
        
        // Update stored user data
        localStorage.setItem('user', JSON.stringify(result));
        
        // Show success message
        setAlertSeverity('success');
        setAlertMessage('Profile updated successfully');
        setAlertOpen(true);
      }
    } catch (err: any) {
      console.error('Error updating user:', err);
      
      // Show error message
      setAlertSeverity('error');
      setAlertMessage(err.response?.data?.detail || 'Failed to update profile');
      setAlertOpen(true);
    } finally {
      setEditUserDialogOpen(false);
    }
  };
  
  // Handler for model change
  const handleModelChange = (event: SelectChangeEvent) => {
    setAiModel(event.target.value as string);
  };

  // Handler for saving settings
  const handleSaveSettings = async () => {
    // Validate settings before saving
    if (!apiKey) {
      setAlertSeverity('error');
      setAlertMessage('Please enter an API key for the selected AI model');
      setAlertOpen(true);
      return;
    }
    
    // Make sure we have the correct API key for the selected model
    if (aiModel !== 'gemini' && aiModel !== 'openai') {
      setAlertSeverity('error');
      setAlertMessage('Invalid AI provider. Must be "gemini" or "openai"');
      setAlertOpen(true);
      return;
    }
    
    try {
      setIsSettingsSaving(true);
        const settings: SettingsUpdateRequest = {
        ai_provider: aiModel,
        api_key: apiKey,
      };
      
      // Save settings via API
      const response = await apiService.updateSettings(settings);
      
      if (response.success) {
        setAlertSeverity('success');
        setAlertMessage(response.message);
        setAlertOpen(true);
        
        // Close settings menu
        handleSettingsMenuClose();
      } else {
        setAlertSeverity('error');
        setAlertMessage('Failed to update settings');
        setAlertOpen(true);
      }
    } catch (error: any) {
      console.error('Error updating settings:', error);
      setAlertSeverity('error');
      setAlertMessage(error.response?.data?.detail || 'Failed to update settings');
      setAlertOpen(true);
    } finally {
      setIsSettingsSaving(false);
    }
  };
  
  // Handler for alert close
  const handleAlertClose = () => {
    setAlertOpen(false);
  };
  
  // Handler for logout
  const handleLogout = () => {
    apiService.logout();
    setIsLoggedIn(false);
    setUserInfo(defaultUser);
    handleUserMenuClose();
    
    // Show success message
    setAlertSeverity('success');
    setAlertMessage('Logged out successfully');
    setAlertOpen(true);
  };
  
  // Handler for login button click
  const handleLoginClick = () => {
    navigate('/login');
    handleUserMenuClose();
  };

  return (
    <AppBar position="static" elevation={4}>
      <Toolbar>
        {/* Logo and App Name */}        <Box display="flex" alignItems="center" component={Link} to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <Code sx={{ mr: 1 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Collaborative Coding Agents
          </Typography>
        </Box>
        
        <Box sx={{ flexGrow: 1 }} />

        {/* Navigation Links */}
        <Box sx={{ display: 'flex', mr: 2 }}>
          <Button 
            color="inherit" 
            component={Link} 
            to="/"
            sx={{ mx: 1 }}
          >
            Home
          </Button>
          <Button 
            color="inherit" 
            component={Link} 
            to="/solve"
            sx={{ mx: 1 }}
          >
            Solve
          </Button>
        </Box>
        
        <Box sx={{ display: 'flex' }}>
          {/* User Menu Button */}
          <IconButton 
            color="inherit"
            onClick={handleUserMenuOpen}
            aria-controls={userMenuOpen ? 'user-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={userMenuOpen ? 'true' : undefined}
            aria-label="User menu"
          >
            <AccountCircle />
          </IconButton>
          
          {/* Settings Menu Button */}
          <IconButton 
            color="inherit"
            onClick={handleSettingsMenuOpen}
            aria-controls={settingsMenuOpen ? 'settings-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={settingsMenuOpen ? 'true' : undefined}
            aria-label="Settings menu"
          >
            <Settings />
          </IconButton>
        </Box>
        
        {/* User Menu */}
        <Menu
          id="user-menu"
          anchorEl={userAnchorEl}
          open={userMenuOpen}
          onClose={handleUserMenuClose}
          MenuListProps={{
            'aria-labelledby': 'user-button',
          }}
          PaperProps={{
            elevation: 3,
            sx: { 
              minWidth: 220,
              mt: 1.5,
            }
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >          {isLoggedIn ? (
            <Box component="div">
              <Box sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ mr: 1.5 }}>
                  {userInfo.name.charAt(0).toUpperCase()}
                </Avatar>
                <Box>
                  <Typography variant="subtitle1">{userInfo.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {userInfo.email}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 1 }} />
              
              <MenuItem onClick={handleEditUserOpen}>
                <ListItemIcon>
                  <Edit fontSize="small" />
                </ListItemIcon>
                Update Profile
              </MenuItem>
              
              <MenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <Logout fontSize="small" />
                </ListItemIcon>
                Sign Out
              </MenuItem>
            </Box>
          ) : (
            <MenuItem onClick={handleLoginClick}>
              <ListItemIcon>
                <Login fontSize="small" />
              </ListItemIcon>
              Sign In
            </MenuItem>
          )}
        </Menu>
        
        {/* Settings Menu */}
        <Menu
          id="settings-menu"
          anchorEl={settingsAnchorEl}
          open={settingsMenuOpen}
          onClose={handleSettingsMenuClose}
          disableAutoFocusItem={true}
          MenuListProps={{
            'aria-labelledby': 'settings-button',
            autoFocusItem: false,
            disabledItemsFocusable: false,
            disableListWrap: true,
          }}
          PaperProps={{
            elevation: 3,
            sx: { 
              width: 290,  // Fixed width
              mt: 1.5,
              p: 1
            }
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              <SmartToy sx={{ fontSize: 20, verticalAlign: 'middle', mr: 0.75 }} /> 
              AI Settings
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={darkMode}
                  onChange={toggleDarkMode}
                  color="primary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {darkMode ? 
                    <Brightness7 fontSize="small" sx={{ mr: 1 }} /> :
                    <Brightness4 fontSize="small" sx={{ mr: 1 }} />
                  }
                  <Typography variant="body2">
                    {darkMode ? "Light Mode" : "Dark Mode"}
                  </Typography>
                </Box>
              }
              sx={{ mb: 1.5 }}
            />
            
            {/* AI Model Selection */}
            <Box sx={{ px: 2, py: 0.5 }}>
              <FormControl fullWidth size="small" sx={{ mb: 1.5, mt: 0.5 }}>
                <InputLabel id="ai-model-label" sx={{ fontSize: '0.9rem' }}>AI Model</InputLabel>
                <Select
                  labelId="ai-model-label"
                  id="ai-model-select"
                  value={aiModel}
                  label="AI Model"
                  onChange={handleModelChange}
                  sx={{ fontSize: '0.9rem' }}
                >
                  <MenuItem value="gemini">Google Gemini</MenuItem>
                  <MenuItem value="openai">OpenAI GPT</MenuItem>
                </Select>
              </FormControl>
              
              {/* API Key Input */}
              <TextField 
                label="API Key" 
                variant="outlined" 
                fullWidth 
                size="small"
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                onKeyDown={(e) => e.stopPropagation()}
                sx={{ mb: 1.5, '& .MuiInputLabel-root': { fontSize: '0.9rem' } }}
                InputProps={{ 
                  style: { fontSize: '0.9rem' },
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        size="small"
                        aria-label="toggle api key visibility"
                        onClick={() => setShowApiKey(!showApiKey)}
                        edge="end"
                        onMouseDown={(e) => e.preventDefault()}
                      >
                        {showApiKey ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5, mt: -0.5 }}>
                Used for web search functionality
              </Typography>
              
              <Button 
                variant="contained" 
                size="small" 
                fullWidth
                onClick={handleSaveSettings}
                disabled={isSettingsSaving}
              >
                {isSettingsSaving ? 'Saving...' : 'Save Settings'}
              </Button>
            </Box>
          </Box>
        </Menu>
        
        {/* Edit User Dialog */}
        <Dialog open={editUserDialogOpen} onClose={handleEditUserClose}>
          <DialogTitle>Update Profile</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              id="name"
              label="Name"
              fullWidth
              variant="outlined"
              value={newUserInfo.name}
              onChange={(e) => setNewUserInfo({...newUserInfo, name: e.target.value})}
              sx={{ mb: 2, mt: 1 }}
            />
            <TextField
              margin="dense"
              id="email"
              label="Email Address"
              type="email"
              fullWidth
              variant="outlined"
              value={newUserInfo.email}
              onChange={(e) => setNewUserInfo({...newUserInfo, email: e.target.value})}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleEditUserClose}>Cancel</Button>
            <Button onClick={handleEditUserSave} variant="contained">Save</Button>
          </DialogActions>
        </Dialog>
        
        {/* Alert Snackbar */}
        <Snackbar 
          open={alertOpen} 
          autoHideDuration={6000} 
          onClose={handleAlertClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert 
            onClose={handleAlertClose} 
            severity={alertSeverity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {alertMessage}
          </Alert>
        </Snackbar>
      </Toolbar>
    </AppBar>
  );
};

export default Header;