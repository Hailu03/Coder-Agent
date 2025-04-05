import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Box, 
  Button, 
  Paper, 
  CircularProgress, 
  Alert,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Dialog,
  DialogContent,
  DialogActions,
  useTheme
} from '@mui/material';
import { 
  Code, 
  PlayArrow, 
  Description, 
  Speed, 
  LocalLibrary,
  ErrorOutline,
  FlashOn,
  Download,
  FormatListBulleted,
  Fullscreen,
  Close
} from '@mui/icons-material';
import axios from 'axios';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import java from 'highlight.js/lib/languages/java';
import cpp from 'highlight.js/lib/languages/cpp';
import go from 'highlight.js/lib/languages/go';
import rust from 'highlight.js/lib/languages/rust';
import ruby from 'highlight.js/lib/languages/ruby';
import 'highlight.js/styles/atom-one-dark.css';

// Register languages for syntax highlighting
hljs.registerLanguage('python', python);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('java', java);
hljs.registerLanguage('cpp', cpp);
hljs.registerLanguage('go', go);
hljs.registerLanguage('rust', rust);
hljs.registerLanguage('ruby', ruby);

// API endpoint
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Tab panel component
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`solution-tabpanel-${index}`}
      aria-labelledby={`solution-tab-${index}`}
      {...other}
      style={{ padding: '16px 0' }}
    >
      {value === index && (
        <Box>{children}</Box>
      )}
    </div>
  );
};

const ResultPage = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [solution, setSolution] = useState<any>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [codeFullscreen, setCodeFullscreen] = useState(false);
  
  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };
  
  // Download code as a file
  const downloadCode = () => {
    if (!solution) return;
    
    const language = solution.language || 'python';
    const extension = getFileExtension(language);
    const filename = `solution.${extension}`;
    const code = solution.code || '';
    
    const element = document.createElement('a');
    const file = new Blob([code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };
  
  // Helper function to get file extension based on language
  const getFileExtension = (language: string): string => {
    const extensions: Record<string, string> = {
      python: 'py',
      javascript: 'js',
      typescript: 'ts',
      java: 'java',
      'c#': 'cs',
      'c++': 'cpp',
      go: 'go',
      rust: 'rs',
      ruby: 'rb'
    };
    
    return extensions[language] || 'txt';
  };
  
  // Highlight code syntax
  const highlightCode = (code: string, language: string): string => {
    if (!code) return '';
    try {
      if (hljs.getLanguage(language)) {
        return hljs.highlight(code, { language }).value;
      } else {
        return hljs.highlightAuto(code).value;
      }
    } catch (e) {
      console.error('Error highlighting code:', e);
      return code;
    }
  };
  
  // Fetch solution data
  useEffect(() => {
    if (!taskId) {
      setError('No task ID provided');
      setLoading(false);
      return;
    }
    
    const fetchSolution = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/solve/task/${taskId}`);
        const { status, solution: solutionData, error: errorMsg } = response.data;
        
        if (status === 'completed' && solutionData) {
          setSolution(solutionData);
        } else if (status === 'failed' || errorMsg) {
          setError(errorMsg || 'Failed to retrieve solution');
        } else if (status === 'processing' || status === 'starting') {
          // If still processing, poll again after a delay
          setTimeout(fetchSolution, 2000);
          return;
        } else {
          setError('Unexpected response from server');
        }
      } catch (err) {
        setError('Error fetching solution');
        console.error('Error fetching solution:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSolution();
  }, [taskId]);
  
  // If loading, show loading spinner
  if (loading) {
    return (
      <Container maxWidth="md">
        <Box sx={{ my: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Loading solution...
          </Typography>
        </Box>
      </Container>
    );
  }
  
  // If error, show error message
  if (error) {
    return (
      <Container maxWidth="md">
        <Box sx={{ my: 4 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate('/solve')}
            >
              Try Again
            </Button>
          </Box>
        </Box>
      </Container>
    );
  }
  
  // If no solution, show error
  if (!solution) {
    return (
      <Container maxWidth="md">
        <Box sx={{ my: 4 }}>
          <Alert severity="warning" sx={{ mb: 3 }}>
            No solution found. Please try again.
          </Alert>
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate('/solve')}
            >
              Try Again
            </Button>
          </Box>
        </Box>
      </Container>
    );
  }
  
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Solution
          </Typography>
          <Box>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<Download />}
              onClick={downloadCode}
              sx={{ mr: 1 }}
            >
              Download
            </Button>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PlayArrow />}
              onClick={() => navigate('/solve')}
            >
              New Problem
            </Button>
          </Box>
        </Box>
        
        <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden' }}>
          {/* Tabs for different views */}
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            variant="fullWidth"
            textColor="primary"
            indicatorColor="primary"
            aria-label="solution tabs"
          >
            <Tab 
              label="Code" 
              icon={<Code />} 
              iconPosition="start" 
              id="solution-tab-0" 
              aria-controls="solution-tabpanel-0" 
            />
            <Tab 
              label="Analysis" 
              icon={<Description />} 
              iconPosition="start" 
              id="solution-tab-1" 
              aria-controls="solution-tabpanel-1" 
            />
            <Tab 
              label="File Structure" 
              icon={<FormatListBulleted />} 
              iconPosition="start" 
              id="solution-tab-2" 
              aria-controls="solution-tabpanel-2" 
            />
          </Tabs>
          
          <Divider />
          
          {/* Code Tab */}
          <TabPanel value={currentTab} index={0}>
            <Box sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Code Solution
                </Typography>
                <Chip 
                  label={solution.language} 
                  color="primary" 
                  icon={<Code />} 
                  variant="outlined" 
                />
              </Box>
              
              {/* Code display with syntax highlighting */}
              <Box sx={{ position: 'relative' }}>
                <IconButton 
                  onClick={() => setCodeFullscreen(true)}
                  sx={{ 
                    position: 'absolute',
                    top: 10,
                    right: 10,
                    zIndex: 1,
                    backgroundColor: 'rgba(255, 255, 255, 0.7)',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    }
                  }}
                >
                  <Fullscreen />
                </IconButton>
                <Paper 
                  elevation={2} 
                  sx={{ 
                    p: 0, 
                    borderRadius: 1, 
                    overflow: 'hidden',
                    fontSize: '0.9rem',
                    bgcolor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f5f5f5',
                    '& pre': { 
                      margin: 0, 
                      padding: 2,
                      overflow: 'auto',
                      maxHeight: '500px',
                      textAlign: 'left'
                    },
                    '& code': {
                      textAlign: 'left',
                      display: 'block'
                    }
                  }}
                >
                  <pre>
                    <code 
                      dangerouslySetInnerHTML={{ 
                        __html: highlightCode(solution.code || '', solution.language || 'python') 
                      }} 
                    />
                  </pre>
                </Paper>
              </Box>
              
              {/* Fullscreen Code Dialog */}
              <Dialog
                open={codeFullscreen}
                fullScreen
                onClose={() => setCodeFullscreen(false)}
              >
                <DialogContent sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f5f5f5' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      Code Solution - {solution.language}
                    </Typography>
                    <IconButton onClick={() => setCodeFullscreen(false)}>
                      <Close />
                    </IconButton>
                  </Box>
                  <Box sx={{ overflow: 'auto', height: 'calc(100% - 50px)' }}>
                    <pre style={{ margin: 0, padding: '16px' }}>
                      <code 
                        dangerouslySetInnerHTML={{ 
                          __html: highlightCode(solution.code || '', solution.language || 'python') 
                        }} 
                      />
                    </pre>
                  </Box>
                </DialogContent>
                <DialogActions>
                  <Button 
                    startIcon={<Download />} 
                    onClick={downloadCode}
                    variant="outlined"
                    sx={{ mr: 1 }}
                  >
                    Download
                  </Button>
                  <Button onClick={() => setCodeFullscreen(false)} color="primary" variant="contained">
                    Close
                  </Button>
                </DialogActions>
              </Dialog>
            </Box>
          </TabPanel>
          
          {/* Analysis Tab */}
          <TabPanel value={currentTab} index={1}>
             <Box sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Problem Analysis
              </Typography>
              <Typography variant="body1" paragraph sx={{ textAlign: 'left' }}>
                {solution.problem_analysis || 'No problem analysis available.'}
              </Typography>
              
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Approach
              </Typography>
              <List>
                {(solution.approach || []).map((step: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <FlashOn color="primary" />
                    </ListItemIcon>
                    <ListItemText primary={step} />
                  </ListItem>
                ))}
                {(!solution.approach || solution.approach.length === 0) && (
                  <ListItem>
                    <ListItemIcon>
                      <ErrorOutline color="warning" />
                    </ListItemIcon>
                    <ListItemText primary="No approach details available." />
                  </ListItem>
                )}
              </List>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Libraries & Dependencies
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {(solution.libraries || []).map((lib: string, index: number) => (
                    <Chip 
                      key={index} 
                      label={lib} 
                      color="secondary" 
                      variant="outlined" 
                      icon={<LocalLibrary />} 
                    />
                  ))}
                  {(!solution.libraries || solution.libraries.length === 0) && (
                    <Typography variant="body1">
                      No specific libraries required.
                    </Typography>
                  )}
                </Box>
              </Box>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Performance Considerations
                </Typography>
                <List>
                  {(solution.performance_considerations || []).map((item: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <Speed color="primary" />
                      </ListItemIcon>
                      <ListItemText primary={item} />
                    </ListItem>
                  ))}
                  {(!solution.performance_considerations || solution.performance_considerations.length === 0) && (
                    <ListItem>
                      <ListItemIcon>
                        <ErrorOutline color="warning" />
                      </ListItemIcon>
                      <ListItemText primary="No performance considerations available." />
                    </ListItem>
                  )}
                </List>
              </Box>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Best Practices
                </Typography>
                <List>
                  {(solution.best_practices || []).map((practice: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText primary={practice} />
                    </ListItem>
                  ))}
                  {(!solution.best_practices || solution.best_practices.length === 0) && (
                    <ListItem>
                      <ListItemIcon>
                        <ErrorOutline color="warning" />
                      </ListItemIcon>
                      <ListItemText primary="No best practices available." />
                    </ListItem>
                  )}
                </List>
              </Box>
            </Box>
          </TabPanel>
          
          {/* File Structure Tab */}
          <TabPanel value={currentTab} index={2}>
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Recommended File Structure
              </Typography>
              
              {solution.file_structure && (
                <>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    Directories
                  </Typography>
                  <List>
                    {(solution.file_structure.directories || []).map((dir: any, index: number) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Folder color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={dir.path} 
                          secondary={dir.description} 
                        />
                      </ListItem>
                    ))}
                    {(!solution.file_structure.directories || solution.file_structure.directories.length === 0) && (
                      <ListItem>
                        <ListItemIcon>
                          <ErrorOutline color="warning" />
                        </ListItemIcon>
                        <ListItemText primary="No directories defined." />
                      </ListItem>
                    )}
                  </List>
                  
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
                    Files
                  </Typography>
                  <List>
                    {(solution.file_structure.files || []).map((file: any, index: number) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Description color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={file.path} 
                          secondary={
                            <>
                              {file.description}
                              {file.components && file.components.length > 0 && (
                                <Box sx={{ mt: 1 }}>
                                  <Typography variant="body2" color="textSecondary">
                                    Contains: {file.components.join(', ')}
                                  </Typography>
                                </Box>
                              )}
                            </>
                          } 
                        />
                      </ListItem>
                    ))}
                    {(!solution.file_structure.files || solution.file_structure.files.length === 0) && (
                      <ListItem>
                        <ListItemIcon>
                          <ErrorOutline color="warning" />
                        </ListItemIcon>
                        <ListItemText primary="No files defined." />
                      </ListItem>
                    )}
                  </List>
                </>
              )}
              
              {!solution.file_structure && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  No file structure information available.
                </Alert>
              )}
            </Box>
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  );
};

// For TypeScript error: Cannot find name 'CheckCircle'
import { CheckCircle, Folder } from '@mui/icons-material';

export default ResultPage;