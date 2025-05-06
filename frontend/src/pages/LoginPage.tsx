import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Tabs,
  Tab,
  Alert,
  InputAdornment,
  IconButton,
  Avatar,
  Grid,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  LockOutlined,
  Visibility,
  VisibilityOff,
  PersonAdd,
  Login as LoginIcon
} from '@mui/icons-material';
import apiService from '../services/apiService';

// Tab Panel component
interface TabPanelProps {
  children: React.ReactNode;
  value: number;
  index: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`auth-tabpanel-${index}`}
      aria-labelledby={`auth-tab-${index}`}
      {...other}
      style={{ padding: '24px 0' }}
    >
      {value === index && children}
    </div>
  );
};

const LoginPage = () => {
  const navigate = useNavigate();
  
  // State
  const [activeTab, setActiveTab] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Login form state
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  });
  
  // Register form state
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    fullName: '',
    password: '',
    confirmPassword: ''
  });
  
  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    setError(null);
    setSuccess(null);
  };
  
  // Toggle password visibility
  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };
  
  const handleToggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };
  
  // Handle login form changes
  const handleLoginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLoginForm({
      ...loginForm,
      [e.target.name]: e.target.value
    });
  };
  
  // Handle register form changes
  const handleRegisterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRegisterForm({
      ...registerForm,
      [e.target.name]: e.target.value
    });
  };
  
  // Handle login submission
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    // Validate form
    if (!loginForm.username || !loginForm.password) {
      setError('Please fill in all fields');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Call login API
      const response = await apiService.login(loginForm.username, loginForm.password);
      
      // Save tokens in localStorage
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      
      setSuccess('Login successful! Redirecting...');
      
      // Redirect to homepage after a short delay
      setTimeout(() => {
        navigate('/');
        window.location.reload(); // Reload to update header
      }, 1500);
      
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle register submission
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    // Validate form
    if (!registerForm.username || !registerForm.email || 
        !registerForm.password || !registerForm.confirmPassword) {
      setError('Please fill in all required fields');
      return;
    }
    
    if (registerForm.password !== registerForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (registerForm.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Call register API
      const response = await apiService.register({
        username: registerForm.username,
        email: registerForm.email,
        full_name: registerForm.fullName,
        password: registerForm.password
      });
      
      // Save tokens in localStorage
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      
      setSuccess('Registration successful! Redirecting...');
      
      // Redirect to homepage after a short delay
      setTimeout(() => {
        navigate('/');
        window.location.reload(); // Reload to update header
      }, 1500);
      
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Container maxWidth="sm">
      <Box sx={{ my: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Avatar sx={{ m: 1, bgcolor: 'primary.main', width: 56, height: 56 }}>
          <LockOutlined fontSize="large" />
        </Avatar>
        
        <Typography component="h1" variant="h4" gutterBottom>
          Welcome
        </Typography>
        
        <Paper 
          elevation={3} 
          sx={{ 
            width: '100%', 
            mt: 3, 
            borderRadius: 2,
            overflow: 'hidden'
          }}
        >
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange} 
            variant="fullWidth"
            textColor="primary"
            indicatorColor="primary"
            aria-label="auth tabs"
          >
            <Tab label="Login" />
            <Tab label="Register" />
          </Tabs>
          
          {/* Display error message if any */}
          {error && (
            <Alert severity="error" sx={{ mx: 3, mt: 2 }}>
              {error}
            </Alert>
          )}
          
          {/* Display success message if any */}
          {success && (
            <Alert severity="success" sx={{ mx: 3, mt: 2 }}>
              {success}
            </Alert>
          )}
          
          {/* Login Tab */}
          <TabPanel value={activeTab} index={0}>
            <Box 
              component="form" 
              onSubmit={handleLogin}
              sx={{ px: 3, pb: 3 }}
            >
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={loginForm.username}
                onChange={handleLoginChange}
                disabled={isLoading}
              />
              
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={loginForm.password}
                onChange={handleLoginChange}
                disabled={isLoading}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleTogglePasswordVisibility}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
              />
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{ mt: 3, mb: 2 }}
                disabled={isLoading}
                startIcon={isLoading ? <CircularProgress size={20} /> : <LoginIcon />}
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </Button>
            </Box>
          </TabPanel>
          
          {/* Register Tab */}
          <TabPanel value={activeTab} index={1}>
            <Box 
              component="form" 
              onSubmit={handleRegister}
              sx={{ px: 3, pb: 3 }}
            >
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    id="register-username"
                    label="Username"
                    name="username"
                    autoComplete="username"
                    value={registerForm.username}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    id="register-email"
                    label="Email Address"
                    name="email"
                    autoComplete="email"
                    type="email"
                    value={registerForm.email}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    margin="normal"
                    fullWidth
                    id="register-fullName"
                    label="Full Name"
                    name="fullName"
                    autoComplete="name"
                    value={registerForm.fullName}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    name="password"
                    label="Password"
                    type={showPassword ? 'text' : 'password'}
                    id="register-password"
                    autoComplete="new-password"
                    value={registerForm.password}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            aria-label="toggle password visibility"
                            onClick={handleTogglePasswordVisibility}
                            edge="end"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    name="confirmPassword"
                    label="Confirm Password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    id="register-confirm-password"
                    autoComplete="new-password"
                    value={registerForm.confirmPassword}
                    onChange={handleRegisterChange}
                    disabled={isLoading}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            aria-label="toggle password visibility"
                            onClick={handleToggleConfirmPasswordVisibility}
                            edge="end"
                          >
                            {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>
              </Grid>
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{ mt: 3, mb: 2 }}
                disabled={isLoading}
                startIcon={isLoading ? <CircularProgress size={20} /> : <PersonAdd />}
              >
                {isLoading ? 'Registering...' : 'Register'}
              </Button>
            </Box>
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage;