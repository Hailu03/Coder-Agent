import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { stripHtml } from "string-strip-html";
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
  ListItem,
  useMediaQuery
} from '@mui/material';
import TipTapEditor from '../components/TipTapEditor';
import SolveHistory from '../components/SolveHistory';
import Grid from '@mui/material/Grid';
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
  FormatIndentIncrease,
  History
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
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // Form state
  const [requirements, setRequirements] = useState('');
  const [language, setLanguage] = useState('python');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [requirementsFullscreen, setRequirementsFullscreen] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [sseConnection, setSseConnection] = useState<{ disconnect: () => void } | null>(null);
  
  // Authentication check
  useEffect(() => {
    // Check if user is logged in, if not redirect to login page
    if (!apiService.isLoggedIn()) {
      navigate('/login', { state: { from: '/solve', message: 'Please log in to access the Solve page' } });
    }
    
    // Clean up SSE connection when component unmounts
    return () => {
      if (sseConnection) {
        sseConnection.disconnect();
      }
    };
  }, [navigate, sseConnection]);
  
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
    
    try {      // Submit request to the API
      const response = await apiService.solveProblem({
        requirements: requirements.trim(),
        language
      });
        // Get the task ID from the response
      const taskId = response.task_id;
      setCurrentTaskId(taskId);
        // Set up SSE connection for real-time updates
      console.log(`Setting up SSE connection for task ID: ${taskId}`);
      const connection = apiService.connectToTaskUpdates((data) => {
        // Only process updates for this task
        if (data.task_id === taskId) {
          console.log('Received task update:', data);
          
          const { status, detailed_status } = data;
          
          if (status === 'completed' || status === 'failed') {
            setIsSubmitting(false);
            console.log(`Task ${taskId} ${status}`);
            
            if (status === 'completed') {
              // Navigate to result page if task completed successfully
              console.log(`Navigating to result page for task ${taskId}`);
              navigate(`/result/${taskId}`);
            } else {
              // Show error if task failed
              setError('Failed to generate code. Please try again.');
              setActiveStep(0);
            }
          } else if (status === 'processing') {
            // Update steps based on the detailed status if available
            if (detailed_status) {
              const phase = detailed_status.phase;
              
              // Map phase to step number
              if (phase === 'planning') {
                setActiveStep(1); // Planning & Research step
              } else if (phase === 'research') {
                setActiveStep(1); // Still in Research phase (same UI step)
                // Log to verify we're receiving research phase updates
                console.log('Research phase update received:', detailed_status);
              } else if (phase === 'code_generation') {
                setActiveStep(2); // Code Generation step
                console.log('Code generation phase update received:', detailed_status);
              } else if (phase === 'test_execution') {
                setActiveStep(3); // Test Execution step
                console.log('Test execution phase update received:', detailed_status);
              } else if (phase === 'refinement' || phase.startsWith('refinement_')) {
                setActiveStep(4); // Code Refinement step
                console.log('Refinement phase update received:', detailed_status);
              } else if (phase === 'completed') {
                setActiveStep(4); // Keep at final step until navigation
                console.log('Completion phase update received:', detailed_status);
              } else if (phase === 'failed') {
                console.log('Task failed:', detailed_status);
                setError('Failed to generate code. Please try again.');
                setIsSubmitting(false);
                setActiveStep(0);
              }
            } else {
              // Fallback to default behavior if detailed status is not available
              setActiveStep(1); // Default to Planning & Research
            }
          }
        }      }, (error) => {
        console.error('SSE connection error:', error);
        
        // Provide more detailed error information
        if (error instanceof Event && error.target instanceof EventSource) {
          const eventSource = error.target;
          console.log('EventSource readyState:', eventSource.readyState);
        }
        
        setError('Lost connection to server. Please try again. Check the console for details.');
        setIsSubmitting(false);
        setActiveStep(0);
      });
      
      // Save connection for cleanup later
      setSseConnection(connection);
      
    } catch (err: any) {
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
        setError(`Error submitting requirements: ${err.message || 'Unknown error'}`);
      }
      
      setActiveStep(0);
    }
  };
  return (
    <Container maxWidth="xl" sx={{ minHeight: '0vh', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          Solve Your Programming Problem
        </Typography>
        <Typography variant="h6" component="h2" gutterBottom align="center" color="text.secondary">
          Our AI agents will collaborate to generate high-quality, optimized code
        </Typography>
        
        <Grid container spacing={3} sx={{ mt: 2, height: '70vh' }}>
          {/* History Sidebar - Hidden on mobile */}
          {!isMobile && (
            <Grid item xs={12} md={3} sx={{ height: '100%' }}>
              <Paper
                elevation={2}
                sx={{
                  height: '100%',
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <Box
                  sx={{
                    p: 1.5,
                    borderBottom: `1px solid ${theme.palette.divider}`,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <History sx={{ mr: 1 }} fontSize="small" />
                  <Typography variant="subtitle1" component="h3">
                    Solution History
                  </Typography>
                </Box>
                <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                  <SolveHistory />
                </Box>
              </Paper>
            </Grid>
          )}
          
          {/* Main Content */}
          <Grid item xs={12} md={!isMobile ? 9 : 12} sx={{ height: '100%', maxWidth: '800px' }}>
            <Paper
              elevation={3}
              sx={{
                p: 4,
                borderRadius: 2,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
              }}
            >
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
              
              {/* Requirements Input - Compact Preview */}
              <Box sx={{ position: 'relative', mb: 3}}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    borderRadius: 1,
                    border: `1px solid ${theme.palette.divider}`,
                    '&:hover': {
                      borderColor: theme.palette.primary.main,
                      boxShadow: `0 0 0 1px ${theme.palette.primary.main}`,
                    },
                    position: 'relative',
                    minHeight: '200px',
                  }}
                  onClick={() => setRequirementsFullscreen(true)}
                >
                  <Typography variant="subtitle1" gutterBottom>
                    Programming Problem Requirements
                  </Typography>
                  <Box
                    sx={{
                      flex: 1,
                      minHeight: '120px',
                      maxHeight: '80px',
                      overflow: 'auto',
                      position: 'relative',
                      px: 1,
                      py: 0.5,
                      color: theme.palette.text.primary,
                      fontSize: '1rem',
                      fontWeight: 400,
                      lineHeight: 1.6,
                      background: 'transparent',
                      textAlign: 'left',
                      '& h1, & h2, & h3': { fontSize: '1.1rem', fontWeight: 600, m: 0 },
                      '& ul, & ol': { pl: 2, m: 0 },
                      '& li': { pl: 1, m: 0 },
                      '& p': { m: 0 },
                      ...(requirements && {
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          height: '32px',
                          background: theme.palette.mode === 'dark'
                            ? 'linear-gradient(transparent, rgba(18, 18, 18, 0.95))'
                            : 'linear-gradient(transparent, rgba(255, 255, 255, 0.95))',
                          pointerEvents: 'none',
                        }
                      })
                    }}
                  >
                    {requirements ? (
                      <div
                        style={{
                          width: '100%',
                          fontSize: '1rem',
                          fontWeight: 400,
                          lineHeight: 1.6,
                          textAlign: 'left',
                          whiteSpace: 'pre-line',
                          wordBreak: 'break-word'
                        }}
                        dangerouslySetInnerHTML={{ __html: requirements }}
                      />
                    ) : (
                      <Typography color="textSecondary" variant="body2" sx={{ fontStyle: 'italic', textAlign: 'left' }}>
                        Click to describe your programming problem or paste task details...
                      </Typography>
                    )}
                  </Box>
                                    <Tooltip title="Open Editor">
                    <IconButton                  sx={{
                        position: 'absolute',
                        bottom: 8,
                        right: 8,
                        backgroundColor: theme.palette.mode === 'dark'
                          ? 'rgba(66, 66, 66, 0.7)'
                          : 'rgba(255, 255, 255, 0.7)',
                        '&:hover': {
                          backgroundColor: theme.palette.mode === 'dark'
                            ? 'rgba(66, 66, 66, 0.9)'
                            : 'rgba(255, 255, 255, 0.9)',
                        }
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setRequirementsFullscreen(true);
                      }}
                    >
                      <Fullscreen />
                    </IconButton>
                  </Tooltip>
                </Paper>
              </Box>
              
              {/* Fullscreen Requirements Dialog with TipTap Editor */}
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
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: theme.palette.mode === 'dark' ? '#23272f' : '#f7f7fa',
                      borderBottom: `1px solid ${theme.palette.divider}`,
                      px: 2,
                      py: 1.5,
                      borderTopLeftRadius: 8,
                      borderTopRightRadius: 8,
                      minHeight: 56,
                      mb: 0
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Description fontSize="medium" sx={{ mr: 1, color: theme.palette.text.secondary }} />
                      <Typography variant="h6" sx={{ fontWeight: 500 }}>
                        Requirements Editor
                      </Typography>
                    </Box>
                    <Tooltip title="Exit Full Screen">
                    <IconButton 
                      onClick={() => setRequirementsFullscreen(false)}
                      size="small"
                      sx={{
                        ml: 1,
                        color: theme.palette.text.secondary
                      }}
                    >
                      <Close fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  </Box>
                  
                  {/* Editor Area */}              <Paper 
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
                    <TipTapEditor
                      value={requirements}
                      onChange={setRequirements}
                      placeholder="Describe the programming problem or paste the task from sources like LeetCode, HackerRank, etc."
                      fullWidth
                      fullHeight
                      minHeight="500px"
                    />
                  </Paper>
                  
                  {/* Bottom Toolbar */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Format text using the editor toolbar. Changes will be preserved when you exit.
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
                <Box sx={{ mt: 1, textAlign: 'center' }}>
                  <Typography variant="body1" color="text.secondary">
                    {activeStep === 1 
                      ? 'Our agents are analyzing your problem, researching solutions, and planning the best approach...'
                      : activeStep === 2
                      ? 'Generating clean, optimized code based on the plan and research...'
                      : activeStep === 3
                      ? 'Executing code against test cases to verify correctness...'
                      : 'Refining code based on test results and agent collaboration...'}
                  </Typography>
                  {/* <Box sx={{ display: 'flex', justifyContent: 'center', mt: 0 }}>
                    <CircularProgress color="secondary" />
                  </Box> */}
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default SolvePage;