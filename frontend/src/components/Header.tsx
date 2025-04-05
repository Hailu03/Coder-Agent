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
  Alert
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
  VisibilityOff 
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import apiService, { SettingsUpdateRequest } from '../services/apiService';

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
  const [serperApiKey, setSerperApiKey] = useState<string>('');
  
  // Password visibility states
  const [showApiKey, setShowApiKey] = useState(false);
  const [showSerperApiKey, setShowSerperApiKey] = useState(false);
  
  // Alert state
  const [alertOpen, setAlertOpen] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertSeverity, setAlertSeverity] = useState<'success' | 'error'>('success');
  const [isSettingsSaving, setIsSettingsSaving] = useState(false);
  
  // Handlers for user menu
  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserAnchorEl(event.currentTarget);
  };
  
  const handleUserMenuClose = () => {
    setUserAnchorEl(null);
  };
  
  // Handlers for settings menu
  const handleSettingsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
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
  
  const handleEditUserSave = () => {
    setUserInfo(newUserInfo);
    setEditUserDialogOpen(false);
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
      setAlertMessage('Please select a valid AI model (Gemini or OpenAI)');
      setAlertOpen(true);
      return;
    }

    try {
      setIsSettingsSaving(true);
      
      const settings: SettingsUpdateRequest = {
        ai_provider: aiModel,
        api_key: apiKey,
        serper_api_key: serperApiKey
      };
    
      const response = await apiService.updateSettings(settings);
      
      setAlertSeverity('success');
      setAlertMessage('Settings updated successfully');
      setAlertOpen(true);
      handleSettingsMenuClose();
    } catch (error) {
      console.error('Error saving settings:', error);
      setAlertSeverity('error');
      setAlertMessage('Failed to update settings. Please try again.');
      setAlertOpen(true);
    } finally {
      setIsSettingsSaving(false);
    }
  };
  
  // Handler for closing alert
  const handleAlertClose = () => {
    setAlertOpen(false);
  };

  return (
    <AppBar position="static" elevation={0} color="primary">
      <Toolbar>
        <Box display="flex" alignItems="center" component={Link} to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <Code sx={{ mr: 1 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Collaborative Coding Agents
          </Typography>
        </Box>
        
        <Box sx={{ flexGrow: 1 }} />
        
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
        >
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
          
          <MenuItem onClick={handleUserMenuClose}>
            <ListItemIcon>
              <Logout fontSize="small" />
            </ListItemIcon>
            Sign Out
          </MenuItem>
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
          <Typography variant="subtitle2" sx={{ px: 2, py: 0.5, fontWeight: 'bold' }}>
            Application Settings
          </Typography>
          
          <Divider sx={{ my: 0.5 }} />
          
          {/* Theme Toggle */}
          <MenuItem onClick={toggleDarkMode} sx={{ height: 40 }}>
            <ListItemIcon sx={{ minWidth: '30px' }}>
              {darkMode ? <Brightness7 fontSize="small" /> : <Brightness4 fontSize="small" />}
            </ListItemIcon>
            <Typography variant="body2" sx={{ fontSize: '0.9rem' }}>
              {darkMode ? 'Light Mode' : 'Dark Mode'}
            </Typography>
            <Switch 
              edge="end" 
              size="small"
              checked={darkMode} 
              onClick={(e) => e.stopPropagation()} 
              onChange={toggleDarkMode}
            />
          </MenuItem>
          
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
                  <IconButton
                    size="small"
                    aria-label="toggle api key visibility"
                    onClick={() => setShowApiKey(!showApiKey)}
                    edge="end"
                    onMouseDown={(e) => e.preventDefault()}
                  >
                    {showApiKey ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                  </IconButton>
                )
              }}
            />
            
            {/* Serper API Key Input */}
            <TextField 
              label="Serper API Key" 
              variant="outlined" 
              fullWidth 
              size="small"
              type={showSerperApiKey ? "text" : "password"}
              value={serperApiKey}
              onChange={(e) => setSerperApiKey(e.target.value)}
              onKeyDown={(e) => e.stopPropagation()}
              sx={{ mb: 1 }}
              InputProps={{ 
                style: { fontSize: '0.9rem' },
                endAdornment: (
                  <IconButton
                    size="small"
                    aria-label="toggle serper api key visibility"
                    onClick={() => setShowSerperApiKey(!showSerperApiKey)}
                    edge="end"
                    onMouseDown={(e) => e.preventDefault()}
                  >
                    {showSerperApiKey ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                  </IconButton>
                )
              }}
              InputLabelProps={{ style: { fontSize: '0.9rem' } }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5, mt: -0.5 }}>
              Used for web search functionality
            </Typography>
            
            <Button 
              variant="contained" 
              size="small" 
              fullWidth
              onClick={handleSaveSettings}
            >
              Save Settings
            </Button>
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
          autoHideDuration={4000} 
          onClose={handleAlertClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleAlertClose} severity={alertSeverity} sx={{ width: '100%' }}>
            {alertMessage}
          </Alert>
        </Snackbar>
      </Toolbar>
    </AppBar>
  );
};

export default Header;