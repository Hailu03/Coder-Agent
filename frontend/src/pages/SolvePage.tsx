import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Box, 
  Button, 
  Paper, 
  TextField, 
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  IconButton,
  Dialog,
  DialogContent,
  DialogActions,
  useTheme,
  Tooltip,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Menu,
  Popover,
  List,
  ListItem
} from '@mui/material';
import { 
  Send, 
  Code,
  Fullscreen,
  Close,
  Description,
  FormatBold,
  FormatItalic,
  FormatUnderlined,
  FormatListBulleted,
  FormatListNumbered,
  FormatColorText,
  FormatSize,
  Undo,
  Redo,
  FormatAlignLeft,
  FormatAlignCenter,
  FormatAlignRight,
  FormatAlignJustify,
  FormatIndentDecrease,
  FormatIndentIncrease
} from '@mui/icons-material';
import axios from 'axios';
import apiService from '../services/apiService';

// Available programming languages
const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'c#', label: 'C#' },
  { value: 'c++', label: 'C++' },
  { value: 'go', label: 'Go' },
  { value: 'rust', label: 'Rust' },
  { value: 'ruby', label: 'Ruby' },
];

// API endpoint (would typically come from environment variables)
const API_BASE_URL = 'http://localhost:8000/api/v1';

const SolvePage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  
  // Authentication check
  useEffect(() => {
    // Check if user is logged in, if not redirect to login page
    if (!apiService.isLoggedIn()) {
      navigate('/login', { state: { from: '/solve', message: 'Please log in to access the Solve page' } });
    }
  }, [navigate]);
  
  // Form state
  const [requirements, setRequirements] = useState('');
  const [language, setLanguage] = useState('python');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [requirementsFullscreen, setRequirementsFullscreen] = useState(false);
  
  // Rich text editor state
  const [formatBold, setFormatBold] = useState(false);
  const [formatItalic, setFormatItalic] = useState(false);
  const [formatUnderline, setFormatUnderline] = useState(false);
  const [textAlign, setTextAlign] = useState<string | null>('left');
  const [currentFont, setCurrentFont] = useState('default');
  const [fontSize, setFontSize] = useState('medium');
  const [anchorElFonts, setAnchorElFonts] = useState<null | HTMLElement>(null);
  const [anchorElFontSize, setAnchorElFontSize] = useState<null | HTMLElement>(null);
  const [bulletedList, setBulletedList] = useState(false);
  const [numberedList, setNumberedList] = useState(false);
  const [indentLevel, setIndentLevel] = useState(0);
  
  // Steps in the solution process
  const steps = [
    'Submit Requirements',
    'Planning & Research',
    'Code Generation',
    'Test Execution',
    'Code Refinement'
  ];

  // Handle language selection change
  const handleLanguageChange = (event: SelectChangeEvent) => {
    setLanguage(event.target.value);
  };
  
  // Format toolbar handlers
  const handleFormatChange = (format: string) => {
    switch(format) {
      case 'bold':
        setFormatBold(!formatBold);
        break;
      case 'italic':
        setFormatItalic(!formatItalic);
        break;
      case 'underline':
        setFormatUnderline(!formatUnderline);
        break;
      default:
        break;
    }
  };
  
  const handleAlignmentChange = (
    event: React.MouseEvent<HTMLElement>,
    newAlignment: string | null,
  ) => {
    setTextAlign(newAlignment);
  };
  
  const handleBulletedList = () => {
    setBulletedList(!bulletedList);
    // If enabling bulleted list, disable numbered list
    if (!bulletedList && numberedList) {
      setNumberedList(false);
    }
  };
  
  const handleNumberedList = () => {
    setNumberedList(!numberedList);
    // If enabling numbered list, disable bulleted list
    if (!numberedList && bulletedList) {
      setBulletedList(false);
    }
  };
  
  const handleIncreaseIndent = () => {
    if (indentLevel < 4) { // Limit indentation level
      setIndentLevel(indentLevel + 1);
    }
  };
  
  const handleDecreaseIndent = () => {
    if (indentLevel > 0) {
      setIndentLevel(indentLevel - 1);
    }
  };
  
  const handleFontMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElFonts(event.currentTarget);
  };
  
  const handleFontMenuClose = () => {
    setAnchorElFonts(null);
  };
  
  const handleFontSizeMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElFontSize(event.currentTarget);
  };
  
  const handleFontSizeMenuClose = () => {
    setAnchorElFontSize(null);
  };
  
  const handleFontChange = (font: string) => {
    setCurrentFont(font);
    handleFontMenuClose();
  };
  
  const handleFontSizeChange = (size: string) => {
    setFontSize(size);
    handleFontSizeMenuClose();
  };

  // Handle form submission
  const handleSubmit = async () => {
    // Validate form
    if (!requirements.trim()) {
      setError('Please enter the programming requirements');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    setActiveStep(1); // Move to planning & research step
    
    try {
      // Submit request to the API
      const response = await axios.post(`${API_BASE_URL}/solve`, {
        requirements: requirements.trim(),
        language
      });
      
      // Get the task ID from the response
      const taskId = response.data.task_id;
      
      // Poll for task completion
      const intervalId = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`${API_BASE_URL}/solve/task/${taskId}`);
          const { status } = statusResponse.data;
          
          if (status === 'completed' || status === 'failed') {
            clearInterval(intervalId);
            setIsSubmitting(false);
            
            if (status === 'completed') {
              // Navigate to result page if task completed successfully
              navigate(`/result/${taskId}`);
            } else {
              // Show error if task failed
              setError('Failed to generate code. Please try again.');
              setActiveStep(0);
            }
          } else if (status === 'processing') {
            // Update steps based on the detailed status if available
            if (statusResponse.data.detailed_status) {
              const phase = statusResponse.data.detailed_status.phase;
              
              // Map phase to step number
              if (phase === 'planning') {
                setActiveStep(1); // Planning & Research step
              } else if (phase === 'research') {
                setActiveStep(1); // Still in Research phase (same UI step)
              } else if (phase === 'code_generation') {
                setActiveStep(2); // Code Generation step
              } else if (phase === 'test_execution') {
                setActiveStep(3); // Test Execution step
              } else if (phase === 'refinement') {
                setActiveStep(4); // Code Refinement step
              } else if (phase === 'completed') {
                setActiveStep(4); // Keep at final step until navigation
              }
            } else {
              // Fallback to default behavior if detailed status is not available
              setActiveStep(1); // Default to Planning & Research
            }
          }
        } catch (err) {
          clearInterval(intervalId);
          setIsSubmitting(false);
          
          // Improved error handling with more specific error messages
          if (axios.isAxiosError(err)) {
            if (err.response) {
              // The request was made and the server responded with a status code
              // that falls out of the range of 2xx
              const statusCode = err.response.status;
              const errorMessage = err.response.data?.message || 'Unknown server error';
              setError(`Error (${statusCode}): ${errorMessage}`);
            } else if (err.request) {
              // The request was made but no response was received
              setError('No response from server. Please check your connection.');
            } else {
              // Something happened in setting up the request
              setError(`Request error: ${err.message}`);
            }
          } else {
            // For non-axios errors
            setError(`Error checking task status: ${(err as Error).message || 'Unknown error'}`);
          }
          
          setActiveStep(0);
        }
      }, 2000); // Poll every 2 seconds
      
    } catch (err) {
      setIsSubmitting(false);
      setError('Failed to submit requirements. Please try again.');
      setActiveStep(0);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          Solve Your Programming Problem
        </Typography>
        <Typography variant="h6" component="h2" gutterBottom align="center" color="text.secondary">
          Our AI agents will collaborate to generate high-quality, optimized code
        </Typography>
        
        <Paper elevation={3} sx={{ p: 4, mt: 4, borderRadius: 2 }}>
          {/* Progress Stepper */}
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          
          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {/* Requirements Input */}
          <Box sx={{ position: 'relative', mb: 3 }}>
            <TextField
              label="Programming Problem Requirements"
              multiline
              rows={8}
              fullWidth
              variant="outlined"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="Describe the programming problem or paste the task from sources like LeetCode, HackerRank, etc."
              disabled={isSubmitting}
            />
            <IconButton 
              sx={{ 
                position: 'absolute', 
                top: 8, 
                right: 8,
                backgroundColor: 'rgba(255, 255, 255, 0.7)',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                }
              }}
              onClick={() => setRequirementsFullscreen(true)}
            >
              <Fullscreen />
            </IconButton>
          </Box>
          
          {/* Fullscreen Requirements Dialog with Rich Text Editor */}
          <Dialog
            open={requirementsFullscreen}
            fullScreen
            onClose={() => setRequirementsFullscreen(false)}
          >
            <Box 
              sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                height: '100%',
                maxWidth: '850px',
                width: '90%',
                margin: '0 auto',
                p: 2
              }}
            >
              <Box 
                sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  mb: 2
                }}
              >
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                  <Description fontSize="small" sx={{ mr: 1 }} />
                  Requirements Editor
                </Typography>
                <Tooltip title="Exit Full Screen">
                  <IconButton 
                    onClick={() => setRequirementsFullscreen(false)}
                  >
                    <Close />
                  </IconButton>
                </Tooltip>
              </Box>
              
              {/* Word-like Formatting Toolbar */}
              <Paper 
                elevation={1} 
                sx={{ 
                  mb: 1,
                  p: 1,
                  borderRadius: 1,
                  border: `1px solid ${theme.palette.divider}`,
                }}
              >
                <Box sx={{ 
                  display: 'flex',
                  flexWrap: 'nowrap',  // Ngăn không cho các nút xuống dòng
                  alignItems: 'center',
                  overflowX: 'auto',   // Thêm cuộn ngang khi cần
                  '&::-webkit-scrollbar': {
                    height: '6px',
                  },
                  '&::-webkit-scrollbar-thumb': {
                    backgroundColor: theme.palette.divider,
                    borderRadius: '3px',
                  },
                  gap: 1
                }}>
                  {/* Font Selection */}
                  <Button 
                    size="small" 
                    sx={{ 
                      textTransform: 'none',
                      minWidth: '120px',
                      fontFamily: currentFont === 'default' ? 'inherit' : 
                                 currentFont === 'mono' ? 'monospace' : 
                                 currentFont === 'serif' ? 'serif' : 
                                 currentFont === 'times' ? 'Times New Roman, serif' :
                                 currentFont === 'arial' ? 'Arial, sans-serif' : 'sans-serif',
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 1,
                      whiteSpace: 'nowrap', // Ngăn không cho text xuống dòng
                    }}
                    onClick={handleFontMenuOpen}
                  >
                    {currentFont === 'default' ? 'Default Font' : 
                     currentFont === 'mono' ? 'Monospace' : 
                     currentFont === 'serif' ? 'Serif' : 
                     currentFont === 'times' ? 'Times New Roman' :
                     currentFont === 'arial' ? 'Arial' : 'Sans Serif'}
                  </Button>
                  <Menu
                    anchorEl={anchorElFonts}
                    open={Boolean(anchorElFonts)}
                    onClose={handleFontMenuClose}
                  >
                    <MenuItem onClick={() => handleFontChange('default')} sx={{ fontFamily: 'inherit' }}>
                      Default Font
                    </MenuItem>
                    <MenuItem onClick={() => handleFontChange('sans-serif')} sx={{ fontFamily: 'sans-serif' }}>
                      Sans Serif
                    </MenuItem>
                    <MenuItem onClick={() => handleFontChange('serif')} sx={{ fontFamily: 'serif' }}>
                      Serif
                    </MenuItem>
                    <MenuItem onClick={() => handleFontChange('times')} sx={{ fontFamily: 'Times New Roman, serif' }}>
                      Times New Roman
                    </MenuItem>
                    <MenuItem onClick={() => handleFontChange('arial')} sx={{ fontFamily: 'Arial, sans-serif' }}>
                      Arial
                    </MenuItem>
                    <MenuItem onClick={() => handleFontChange('mono')} sx={{ fontFamily: 'monospace' }}>
                      Monospace
                    </MenuItem>
                  </Menu>
                  
                  {/* Font Size */}
                  <Button 
                    size="small" 
                    sx={{ 
                      textTransform: 'none',
                      minWidth: '90px',
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 1,
                      whiteSpace: 'nowrap'
                    }}
                    onClick={handleFontSizeMenuOpen}
                  >
                    {fontSize === 'small' ? 'Small' : 
                     fontSize === 'medium' ? 'Medium' : 
                     fontSize === 'large' ? 'Large' : 'Extra Large'}
                  </Button>
                  <Menu
                    anchorEl={anchorElFontSize}
                    open={Boolean(anchorElFontSize)}
                    onClose={handleFontSizeMenuClose}
                  >
                    <MenuItem onClick={() => handleFontSizeChange('small')}>Small</MenuItem>
                    <MenuItem onClick={() => handleFontSizeChange('medium')}>Medium</MenuItem>
                    <MenuItem onClick={() => handleFontSizeChange('large')}>Large</MenuItem>
                    <MenuItem onClick={() => handleFontSizeChange('x-large')}>Extra Large</MenuItem>
                  </Menu>
                  
                  <Divider orientation="vertical" flexItem />
                  
                  {/* Text Formatting */}
                  <ToggleButton 
                    value="bold" 
                    selected={formatBold}
                    onChange={() => handleFormatChange('bold')}
                    size="small"
                  >
                    <FormatBold />
                  </ToggleButton>
                  <ToggleButton 
                    value="italic" 
                    selected={formatItalic}
                    onChange={() => handleFormatChange('italic')}
                    size="small"
                  >
                    <FormatItalic />
                  </ToggleButton>
                  <ToggleButton 
                    value="underline" 
                    selected={formatUnderline}
                    onChange={() => handleFormatChange('underline')}
                    size="small"
                  >
                    <FormatUnderlined />
                  </ToggleButton>
                  
                  <Divider orientation="vertical" flexItem />
                  
                  {/* Text Alignment */}
                  <ToggleButtonGroup
                    value={textAlign}
                    exclusive
                    onChange={handleAlignmentChange}
                    size="small"
                  >
                    <ToggleButton value="left">
                      <FormatAlignLeft />
                    </ToggleButton>
                    <ToggleButton value="center">
                      <FormatAlignCenter />
                    </ToggleButton>
                    <ToggleButton value="right">
                      <FormatAlignRight />
                    </ToggleButton>
                    <ToggleButton value="justify">
                      <FormatAlignJustify />
                    </ToggleButton>
                  </ToggleButtonGroup>
                  
                  <Divider orientation="vertical" flexItem />
                  
                  {/* Lists */}
                  <Tooltip title="Bulleted List">
                    <IconButton 
                      size="small" 
                      onClick={handleBulletedList}
                      color={bulletedList ? "primary" : "default"}
                    >
                      <FormatListBulleted />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Numbered List">
                    <IconButton 
                      size="small" 
                      onClick={handleNumberedList}
                      color={numberedList ? "primary" : "default"}
                    >
                      <FormatListNumbered />
                    </IconButton>
                  </Tooltip>
                  
                  <Divider orientation="vertical" flexItem />
                  
                  {/* Indentation */}
                  <Tooltip title="Decrease Indent">
                    <IconButton 
                      size="small" 
                      onClick={handleDecreaseIndent}
                      disabled={indentLevel === 0}
                    >
                      <FormatIndentDecrease />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Increase Indent">
                    <IconButton 
                      size="small" 
                      onClick={handleIncreaseIndent}
                      disabled={indentLevel >= 4}
                    >
                      <FormatIndentIncrease />
                    </IconButton>
                  </Tooltip>
                  
                  <Divider orientation="vertical" flexItem />
                  
                  {/* Undo/Redo */}
                  <Tooltip title="Undo">
                    <IconButton size="small">
                      <Undo />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Redo">
                    <IconButton size="small">
                      <Redo />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Paper>
              
              {/* Editor Area */}
              <Paper 
                elevation={2} 
                sx={{ 
                  flexGrow: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 1,
                  border: `1px solid ${theme.palette.divider}`,
                  overflow: 'hidden',
                }}
              >
                <TextField
                  autoFocus
                  multiline
                  fullWidth
                  variant="outlined"
                  value={requirements}
                  onChange={(e) => setRequirements(e.target.value)}
                  placeholder="Describe the programming problem or paste the task from sources like LeetCode, HackerRank, etc."
                  disabled={isSubmitting}
                  sx={{
                    flexGrow: 1,
                    '& .MuiOutlinedInput-notchedOutline': {
                      border: 'none',
                    },
                    '& .MuiInputBase-root': {
                      height: '100%',
                      borderRadius: 0,
                      padding: 0,
                    },
                    '& .MuiInputBase-inputMultiline': {
                      padding: `${3 + indentLevel * 10}px 3px 3px 3px`,
                      paddingLeft: indentLevel * 20 + 3,
                      lineHeight: 1.5,
                      fontSize: fontSize === 'small' ? '13px' : 
                              fontSize === 'medium' ? '15px' : 
                              fontSize === 'large' ? '18px' : '20px',
                      fontWeight: formatBold ? 'bold' : 'normal',
                      fontStyle: formatItalic ? 'italic' : 'normal',
                      textDecoration: formatUnderline ? 'underline' : 'none',
                      fontFamily: currentFont === 'default' ? 'inherit' : 
                                 currentFont === 'mono' ? 'monospace' : 
                                 currentFont === 'serif' ? 'serif' : 
                                 currentFont === 'times' ? 'Times New Roman, serif' :
                                 currentFont === 'arial' ? 'Arial, sans-serif' : 'sans-serif',
                      textAlign: textAlign || 'left',
                      height: '100% !important',
                      overflow: 'auto !important',
                      '&::-webkit-scrollbar': {
                        width: '10px',
                        height: '10px',
                        display: 'block',
                      },
                      '&::-webkit-scrollbar-thumb': {
                        backgroundColor: theme.palette.divider,
                        borderRadius: '5px',
                      },
                      '&::-webkit-scrollbar-track': {
                        backgroundColor: theme.palette.background.paper,
                      },
                    }
                  }}
                  InputProps={{
                    sx: { 
                      position: 'relative',
                      '&::before': bulletedList ? {
                        content: '""',
                        position: 'absolute',
                        top: '9px',
                        left: '14px',
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: 'currentColor',
                        display: 'block',
                        zIndex: 9
                      } : numberedList ? {
                        content: '"1."',
                        position: 'absolute',
                        top: '7px',
                        left: '7px',
                        display: 'block',
                        zIndex: 9
                      } : {}
                    }
                  }}
                />
              </Paper>
              
              {/* Bottom Toolbar */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Format text using the toolbar above. Changes will be preserved when you exit.
                </Typography>
                <Button 
                  variant="contained"
                  onClick={() => setRequirementsFullscreen(false)} 
                  color="primary"
                >
                  Done
                </Button>
              </Box>
            </Box>
          </Dialog>
          
          {/* Language Selection */}
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel id="language-select-label">Programming Language</InputLabel>
            <Select
              labelId="language-select-label"
              value={language}
              label="Programming Language"
              onChange={handleLanguageChange}
              disabled={isSubmitting}
            >
              {LANGUAGES.map((lang) => (
                <MenuItem key={lang.value} value={lang.value}>
                  {lang.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          {/* Submit Button */}
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              startIcon={isSubmitting ? <CircularProgress size={20} color="inherit" /> : <Send />}
              onClick={handleSubmit}
              disabled={isSubmitting}
              sx={{ px: 4, py: 1.5 }}
            >
              {isSubmitting ? 'Processing...' : 'Generate Solution'}
            </Button>
          </Box>
          
          {/* Loading Message */}
          {isSubmitting && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                {activeStep === 1 
                  ? 'Our agents are analyzing your problem, researching solutions, and planning the best approach...'
                  : activeStep === 2
                  ? 'Generating clean, optimized code based on the plan and research...'
                  : activeStep === 3
                  ? 'Executing code against test cases to verify correctness...'
                  : 'Refining code based on test results and agent collaboration...'}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <CircularProgress color="secondary" />
              </Box>
            </Box>
          )}
        </Paper>
        
        {/* Example Tips */}
        <Paper elevation={2} sx={{ p: 3, mt: 4, borderRadius: 2, bgcolor: theme.palette.background.default }}>
          <Typography variant="h6" gutterBottom>
            <Code sx={{ mr: 1, verticalAlign: 'middle' }} />
            Tips for Better Results
          </Typography>
          <Typography variant="body1" paragraph sx={{ textAlign: 'left' }}>
            • Be as specific as possible about the requirements and constraints
          </Typography>
          <Typography variant="body1" paragraph sx={{ textAlign: 'left' }}>
            • Include example inputs and expected outputs when relevant
          </Typography>
          <Typography variant="body1" paragraph sx={{ textAlign: 'left' }}>
            • Mention any specific libraries or approaches you prefer
          </Typography>
          <Typography variant="body1" sx={{ textAlign: 'left' }}>
            • Include any performance requirements or limitations
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
};

export default SolvePage;