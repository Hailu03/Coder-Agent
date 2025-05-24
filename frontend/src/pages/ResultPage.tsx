import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Resizable } from 're-resizable';
import {   Container, 
  Typography, 
  Box, 
  Button, 
  Paper, 
  CircularProgress, 
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Dialog,
  DialogContent,
  useTheme,
  TextField,
  Avatar,
  InputAdornment,
  Drawer,
  Tooltip,
  useMediaQuery,
  Divider
} from '@mui/material';
import CodeExecutor from '../components/CodeExecutor';
import DocumentGenerator from '../components/DocumentGenerator';
import ConversationSidebar from '../components/ConversationSidebar';
import { 
  Code, 
  PlayArrow, 
  Description, 
  Speed, 
  LocalLibrary,
  ErrorOutline,
  FlashOn,
  FormatListBulleted,
  Close,
  Send,
  Chat,
  Psychology,
  Search,
  BugReport,
  Build,
  CheckCircle,
  Folder,
  SmartToy,
  ContentCopy,
  History,
  Add
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
import { v4 as uuidv4 } from 'uuid';
import apiService, { ChatRequest, ConversationWithMessages } from '../services/apiService';

// Register languages for syntax highlighting
hljs.registerLanguage('python', python);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('java', java);
hljs.registerLanguage('cpp', cpp);
hljs.registerLanguage('go', go);
hljs.registerLanguage('rust', rust);
hljs.registerLanguage('ruby', ruby);

// Function to render message content with code highlighting
const renderMessageContent = (message: string) => {
  // Regex to match markdown code blocks: ```language\ncode\n```
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)\n```/g;
  
  const parts = [];
  let lastIndex = 0;
  let match;
  
  // Find all code blocks in the message
  while ((match = codeBlockRegex.exec(message)) !== null) {
    // Add text before code block
    if (match.index > lastIndex) {
      parts.push(
        <Typography key={`text-${lastIndex}`} variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
          {message.substring(lastIndex, match.index)}
        </Typography>
      );
    }
    
    // Extract language and code
    const language = match[1] || 'plaintext';
    const code = match[2];
    
    // Add code block with syntax highlighting
    parts.push(
      <Box key={`code-${match.index}`} sx={{ my: 1 }}>
        <Paper variant="outlined" sx={{ position: 'relative', overflow: 'hidden' }}>
          <Box sx={{ position: 'absolute', right: 8, top: 8, zIndex: 2 }}>
            <Tooltip title="Copy code">
              <IconButton 
                size="small"
                onClick={() => {
                  navigator.clipboard.writeText(code);
                  // You could add a snackbar notification here
                }}
                sx={{ 
                  bgcolor: 'rgba(255,255,255,0.1)', 
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' } 
                }}
              >
                <ContentCopy fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
          <Box sx={{ p: 1.5, pt: 3, overflowX: 'auto' }}>
            <pre style={{ margin: 0 }}>
              <code className={language !== 'plaintext' ? `language-${language}` : ''}>
                {code}
              </code>
            </pre>
          </Box>
        </Paper>
      </Box>
    );
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text after last code block
  if (lastIndex < message.length) {
    parts.push(
      <Typography key={`text-${lastIndex}`} variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
        {message.substring(lastIndex)}
      </Typography>
    );
  }
  
  return parts.length ? parts : (
    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
      {message}
    </Typography>
  );
};

// API endpoint
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Type definitions
interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  agentType?: 'planner' | 'researcher' | 'developer' | 'tester' | 'system';
  message: string;
  timestamp: Date;
  isLoading?: boolean;
}

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
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

const ResultPage = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [solution, setSolution] = useState<any>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [codeFullscreen, setCodeFullscreen] = useState(false);
    // Chat state
  const [drawerOpen, setDrawerOpen] = useState(!isMobile);
  const [chatMessage, setChatMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);  
  
  // Conversation state
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [conversationMessages, setConversationMessages] = useState<any[]>([]);
  // Remove the sidebar and add a drawer instead
  const [showConversationDrawer, setShowConversationDrawer] = useState(false);
  
  // Animation and update state
  const [isCodeUpdating, setIsCodeUpdating] = useState(false);
    // Drawer state
  const [isOpen, setIsOpen] = useState(false);
  const [drawerWidth, setDrawerWidth] = useState(isMobile ? 350 : 600);


  // Scroll to bottom of chat when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);  // WebSocket connection reference
  const websocketRef = useRef<any>(null);
  const isWebSocketConnected = useRef(false);
  const hasInitializedWebSocket = useRef(false);
  const wsManager = apiService.getWebSocketManager();
  const messageCallbackRef = useRef<any>(null);
  const errorCallbackRef = useRef<any>(null);

  // Initialize WebSocket connection for real-time chat
  useEffect(() => {
    // Prevent multiple initializations in React Strict Mode
    if (hasInitializedWebSocket.current) {
      console.log('=== WebSocket already initialized, skipping ===');
      return;
    }

    // Only create connection if we have a taskId
    if (taskId && !isWebSocketConnected.current) {
      console.log('=== Initializing WebSocket connection for task:', taskId, '===');
      hasInitializedWebSocket.current = true;
      
      // Store callbacks in refs so we can remove them later
      const messageCallback = (data: any) => {
        console.log('=== WebSocket received data ===:', data);
        
        try {
          if (data.type && data.message) {
            // Check if this is a solution update
            if (data.solution_updated) {
              console.log('Solution update detected via WebSocket');
              // Start animation
              setIsCodeUpdating(true);
                // Use functional state update to avoid stale closure
              setSolution((prevSolution: any) => {
                if (!prevSolution) return prevSolution;
                
                const updatedSolution = { ...prevSolution };
                
                // Update code
                if (data.fixed_code) {
                  updatedSolution.code = data.fixed_code;
                } else if (data.improved_code) {
                  updatedSolution.code = data.improved_code;
                } else if (data.code) {
                  updatedSolution.code = data.code;
                }
                
                // Update all other fields
                if (data.updated_explanation) {
                  updatedSolution.explanation = data.updated_explanation;
                }
                if (data.updated_approach) {
                  updatedSolution.approach = data.updated_approach;
                }
                if (data.updated_best_practices) {
                  updatedSolution.best_practices = data.updated_best_practices;
                }
                if (data.updated_problem_analysis) {
                  updatedSolution.problem_analysis = data.updated_problem_analysis;
                }
                
                return updatedSolution;
              });
              
              // After animation duration, stop the animation
              setTimeout(() => {
                setIsCodeUpdating(false);
              }, 1500); // Animation duration
            }
            
            // Determine agent type based on response type
            let agentType: 'planner' | 'researcher' | 'developer' | 'tester' | 'system' = 'system';
            if (data.type === 'code_fix' || data.type === 'code_improvement' || data.type === 'implementation') {
              agentType = 'developer';
            } else if (data.type === 'general_answer') {
              agentType = 'researcher';
            }
            
            // Create agent response message with additional info for solution updates
            let messageText = data.message;
              if (data.solution_updated) {
              const changesInfo = data.changes_made || data.improvements_made;
              if (changesInfo && changesInfo.length > 0) {
                messageText += '\n\n**Changes made:**\n' + changesInfo.map((change: any) => `• ${change}`).join('\n');
              }
              messageText += '\n\n🔄 **All solution fields have been updated!** The code display will refresh momentarily.';
            }
            
            const agentMessage: ChatMessage = {
              id: uuidv4(),
              sender: 'agent',
              agentType: agentType,
              message: messageText,
              timestamp: new Date()
            };
            
            setChatMessages(prev => [...prev, agentMessage]);
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
          // Add error message to chat
          const errorMessage: ChatMessage = {
            id: uuidv4(),
            sender: 'agent',
            agentType: 'system',
            message: 'Sorry, there was an error processing the response. Please try again.',
            timestamp: new Date()
          };
          setChatMessages(prev => [...prev, errorMessage]);
        }
      };

      const errorCallback = (error: any) => {
        console.error('=== WebSocket error ===:', error);
        isWebSocketConnected.current = false;
      };

      // Store callbacks in refs
      messageCallbackRef.current = messageCallback;
      errorCallbackRef.current = errorCallback;
        // Connect to WebSocket for real-time chat updates
      const wsConnectionPromise = apiService.connectToChatWebSocket(messageCallback, errorCallback);      
      
      // Handle the Promise to get actual connection object
      if (wsConnectionPromise && typeof wsConnectionPromise.then === 'function') {
        wsConnectionPromise.then((connectionObject) => {
          websocketRef.current = connectionObject;
          isWebSocketConnected.current = true;
          console.log('=== WebSocket connection object resolved and stored ===');
        }).catch((error) => {
          console.error('=== Failed to establish WebSocket connection ===:', error);
          isWebSocketConnected.current = false;
        });
      } else {
        // If it's not a Promise, store directly
        websocketRef.current = wsConnectionPromise;
        isWebSocketConnected.current = true;
      }
      
      console.log('=== WebSocket connection initiated ===');
    } else {
      console.log('=== Skipping WebSocket creation ===', {
        taskId: !!taskId,
        isConnected: isWebSocketConnected.current,
        hasRef: !!websocketRef.current,
        alreadyInitialized: hasInitializedWebSocket.current
      });
    }
    
    // Cleanup function for component unmount
    return () => {
      console.log('=== Component unmounting, cleaning up WebSocket ===');
      if (websocketRef.current && messageCallbackRef.current && errorCallbackRef.current) {
        // Use WebSocketManager's removeCallbacks method for proper cleanup
        const wsManager = apiService.getWebSocketManager();
        if (wsManager && wsManager.removeCallbacks) {
          wsManager.removeCallbacks(messageCallbackRef.current, errorCallbackRef.current);
        } else {
          // Fallback to disconnect
          websocketRef.current.disconnect();
        }
        websocketRef.current = null;
        isWebSocketConnected.current = false;
        hasInitializedWebSocket.current = false;
        messageCallbackRef.current = null;
        errorCallbackRef.current = null;
      }
    };
  }, [taskId]); // Only re-run when taskId changes

  // Apply syntax highlighting to code blocks whenever messages change
  useEffect(() => {
    // Find all code blocks and highlight them
    document.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block as HTMLElement);
    });
  }, [chatMessages]);

  // Create initial chat messages from solution data
  useEffect(() => {
    if (solution) {
      const initialMessages: ChatMessage[] = [];
      
      // Add system welcome message
      initialMessages.push({
        id: uuidv4(),
        sender: 'agent',
        agentType: 'system',
        message: 'Welcome to the collaborative coding solution. You can chat with the AI agents to understand the solution better or ask questions about the code.',
        timestamp: new Date()
      });
      
      // Add planner message if available
      if (solution.planning_output?.plan) {
        initialMessages.push({
          id: uuidv4(),
          sender: 'agent',
          agentType: 'planner',
          message: `Here's my plan for solving this problem:\n\n${solution.planning_output.plan}`,
          timestamp: new Date()
        });
      }
      
      // Add researcher message if available
      if (solution.research_output?.research_findings) {
        initialMessages.push({
          id: uuidv4(),
          sender: 'agent',
          agentType: 'researcher',
          message: `I found these relevant insights during my research:\n\n${solution.research_output.research_findings}`,
          timestamp: new Date()
        });
      }
      
      setChatMessages(initialMessages);
    }
  }, [solution]);

  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };  // Thay thế sendMessage function

  const sendMessage = async () => {
  if (!chatMessage.trim()) return;
  
  // Create conversation if this is the first message
  const conversationId = await createNewConversationIfNeeded(chatMessage);
  
  // Add user message to chat
  const userMessage: ChatMessage = {
    id: uuidv4(),
    sender: 'user',
    message: chatMessage,
    timestamp: new Date()
  };
  
  setChatMessages(prev => [...prev, userMessage]);
  
  // Prepare request with task context
  const chatRequest: ChatRequest = {
    message: chatMessage,
    task_id: taskId,
    conversation_id: conversationId || undefined,
    code_context: solution?.code,
    language: solution?.language
  };
  
  // Gửi qua WebSocket hoặc REST API
  if (websocketRef.current && typeof websocketRef.current.sendMessage === 'function' && wsManager.isConnected && wsManager.isConnected()) {
    try {
      console.log('=== Using WebSocket to send message ===');
      websocketRef.current.sendMessage(chatRequest);
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      // Fallback to REST API
      sendMessageViaRestAPI(chatRequest);
    }
  } else {
    console.log('=== WebSocket not connected, using REST API fallback ===');
    // Fallback to REST API if WebSocket not available
    sendMessageViaRestAPI(chatRequest);
  }
  
  // Clear input
  setChatMessage('');
};

    // Helper function to send message via REST API
  const sendMessageViaRestAPI = async (chatRequest: ChatRequest, tempId?: string) => {
    // Create a temporary loading message if one wasn't provided
    const messageId = tempId || uuidv4();
    
    if (!tempId) {
      const loadingMessage: ChatMessage = {
        id: messageId,
        sender: 'agent',
        agentType: 'system',
        message: "Processing your request...",
        timestamp: new Date(),
        isLoading: true
      };
      
      setChatMessages(prev => [...prev, loadingMessage]);
    }
    
    try {
      // Call the backend API
      const response = await apiService.sendChatMessage(chatRequest);
      
      // Check if this is a solution update
      if (response.solution_updated) {
        // Start animation
        setIsCodeUpdating(true);
        
        // Prepare updated solution
        const updatedSolution = { ...solution };
        
        // Update code
        if (response.fixed_code) {
          updatedSolution.code = response.fixed_code;
        } else if (response.improved_code) {
          updatedSolution.code = response.improved_code;
        }
          // Update all other fields
        if (response.updated_explanation) {
          updatedSolution.explanation = response.updated_explanation;
        }
        if (response.updated_approach) {
          updatedSolution.approach = response.updated_approach;
        }
        if (response.updated_best_practices) {
          updatedSolution.best_practices = response.updated_best_practices;
        }
        if (response.updated_problem_analysis) {
          updatedSolution.problem_analysis = response.updated_problem_analysis;
        }
        
        // After animation duration, apply the update
        setTimeout(() => {
          setSolution(updatedSolution);
          setIsCodeUpdating(false);
        }, 1500); // Animation duration
      }
      
      // Determine agent type based on response type
      let agentType: 'planner' | 'researcher' | 'developer' | 'tester' | 'system' = 'system';
      if (response.type === 'code_fix' || response.type === 'code_improvement' || response.type === 'implementation') {
        agentType = 'developer';
      } else if (response.type === 'general_answer') {
        agentType = 'researcher';
      }
      
      // Create agent response message with additional info for solution updates
      let messageText = response.message;
      if (response.solution_updated) {
        const changesInfo = response.changes_made || response.improvements_made;
        if (changesInfo && changesInfo.length > 0) {
          messageText += '\n\n**Changes made:**\n' + changesInfo.map(change => `• ${change}`).join('\n');
        }
        messageText += '\n\n🔄 **All solution fields have been updated!** The code display will refresh momentarily.';
      }
      
      const agentMessage: ChatMessage = {
        id: uuidv4(),
        sender: 'agent',
        agentType: agentType,
        message: messageText,
        timestamp: new Date()
      };
      
      // Replace loading message with actual response
      setChatMessages(prev => prev.map(msg => msg.id === messageId ? agentMessage : msg));
    } catch (error) {
      console.error('Error sending chat message:', error);
      
      // Replace loading message with error message
      const errorMessage: ChatMessage = {
        id: uuidv4(),
        sender: 'agent',
        agentType: 'system',
        message: "Sorry, I encountered an error processing your request. Please try again.",
        timestamp: new Date()
      };
      
      setChatMessages(prev => prev.map(msg => msg.id === messageId ? errorMessage : msg));
    }  };
  
  // Get agent icon based on type
  const getAgentIcon = (type?: string) => {
    switch (type) {
      case 'planner':
        return <Psychology sx={{ color: theme.palette.primary.main }} />;
      case 'researcher':
        return <Search sx={{ color: theme.palette.info.main }} />;
      case 'developer':
        return <Build sx={{ color: theme.palette.success.main }} />;
      case 'tester':
        return <BugReport sx={{ color: theme.palette.warning.main }} />;
      case 'system':
      default:
        return <SmartToy sx={{ color: theme.palette.secondary.main }} />;
    }
  };
  
  // Get agent name based on type
  const getAgentName = (type?: string) => {
    switch (type) {
      case 'planner':
        return 'Planner Agent';
      case 'researcher':
        return 'Researcher Agent';
      case 'developer':
        return 'Developer Agent';
      case 'tester':
        return 'Tester Agent';
      case 'system':
      default:
        return 'System';
    }  
  };
  // === CONVERSATION MANAGEMENT FUNCTIONS ===

  const loadConversationMessages = async (conversationId: string) => {
    try {
      const conversationWithMessages = await apiService.getConversationWithMessages(conversationId);
      console.log("Raw conversation data:", conversationWithMessages);
      
      // Kiểm tra nếu không có messages
      if (!conversationWithMessages.messages || conversationWithMessages.messages.length === 0) {
        // Hiển thị thông báo conversation trống
        const emptyMessage: ChatMessage = {
          id: uuidv4(),
          sender: 'agent',
          agentType: 'system',
          message: 'This conversation is empty. Send a message to start chatting!',
          timestamp: new Date()
        };
        setChatMessages([emptyMessage]);
        setCurrentConversationId(conversationId);
        return;
      }
      // Convert backend messages to frontend ChatMessage format
      const convertedMessages: ChatMessage[] = conversationWithMessages.messages.map(msg => ({
        id: msg.id,
        sender: msg.sender as 'user' | 'agent',
        agentType: msg.agent_type as any,
        message: msg.content,
        timestamp: new Date(msg.created_at)
      }));
      
      setChatMessages(convertedMessages);
      setCurrentConversationId(conversationId);
    } catch (error) {
      console.error('Error loading conversation messages:', error);
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: uuidv4(),
        sender: 'agent',
        agentType: 'system',
        message: 'Failed to load conversation history. Please try again.',
        timestamp: new Date()
      };
      setChatMessages([errorMessage]);
    }
  };

  const handleConversationSelect = (conversationId: string) => {
    console.log('Loading conversation:', conversationId);
    loadConversationMessages(conversationId);
  };

  const handleNewConversation = () => {
    console.log('Starting new conversation');
    setCurrentConversationId(null);
    setChatMessages([]);
    
    // Add initial welcome message for new conversations
    const welcomeMessage: ChatMessage = {
      id: uuidv4(),
      sender: 'agent',
      agentType: 'system',
      message: 'Welcome to the collaborative coding solution. You can chat with the AI agents to understand the solution better or ask questions about the code.',
      timestamp: new Date()
    };
    setChatMessages([welcomeMessage]);
  };

  const createNewConversationIfNeeded = async (userMessage: string): Promise<string | null> => {
    if (currentConversationId) {
      return currentConversationId;
    }

    try {
      // Create a new conversation with the first user message as the title
      const title = userMessage.length > 50 ? userMessage.substring(0, 50) + '...' : userMessage;
      const newConversation = await apiService.createConversation({
        title,
        task_id: taskId || ''
      });
      
      setCurrentConversationId(newConversation.id);
      return newConversation.id;
    } catch (error) {
      console.error('Error creating new conversation:', error);
      return null;
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
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading solution...
        </Typography>
      </Box>
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
    <Box className="result-page-container" sx={{ height: '100%', display: 'flex' }}>
      {/* Main Content */}
      <Box sx={{ 
        flexGrow: 1, 
        height: '100%', 
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        // margin: isMobile ? 0 : '0 200px',
      }}>
        {/* Header */}
        <Box sx={{ 
          p: 1, 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: `1px solid ${theme.palette.divider}`,
          bgcolor: theme.palette.background.paper,
          height: '60px', // Giữ chiều cao header cố định
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="h5">Solution</Typography>
            <Chip 
              label={solution.language} 
              color="primary" 
              icon={<Code fontSize="small" />}
              variant="outlined" 
              size="small" // Thêm size="small" cho chip
              sx={{ ml: 1 }} // Giảm margin từ 2 xuống 1
            />
          </Box>
          {/* Tabs Navigation */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={currentTab} 
              onChange={handleTabChange} 
              variant={isMobile ? "scrollable" : "fullWidth"}
              scrollButtons="auto"
              textColor="primary"
              indicatorColor="primary"
            >
              <Tab 
                label="Code Solution" 
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
          </Box>
          <Box>
            {/* <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={downloadCode}
              sx={{ mr: 1 }}
            >
              Download
            </Button> */}
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={() => navigate('/solve')}
            >
              New Problem
            </Button>
            <IconButton 
              onClick={() => setDrawerOpen(!drawerOpen)} 
              sx={{ 
                ml: 1,
                color: !drawerOpen ? theme.palette.text.primary : 'transparent', // Làm trong suốt khi đã mở drawer
                display: !drawerOpen ? 'inline-flex' : 'none', // Ẩn hoàn toàn khi drawer mở
              }}
            >
              <Chat />
            </IconButton>
          </Box>
        </Box>
        
        
        {/* Tab Content */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 0}}>  {/* Bỏ padding p: 3 */}  
          <TabPanel value={currentTab} index={0}>
            <Box sx={{ 
              position: 'relative', 
              height: 'calc(100vh - 60px)',  
              padding: "0px",
              overflow: 'hidden' // Important for animation
            }}>
              {/* Sliding Animation Overlay */}
              {isCodeUpdating && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    bgcolor: 'rgba(33, 150, 243, 0.1)',
                    zIndex: 1000,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(33, 150, 243, 0.3), transparent)',
                      animation: 'slideLeftToRight 1.5s ease-in-out',
                    },
                    '@keyframes slideLeftToRight': {
                      '0%': {
                        transform: 'translateX(0%)'
                      },
                      '100%': {
                        transform: 'translateX(200%)'
                      }
                    }
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      bgcolor: 'rgba(255, 255, 255, 0.95)',
                      p: 2,
                      borderRadius: 2,
                      boxShadow: 3,
                      zIndex: 1001
                    }}
                  >
                    <CircularProgress size={24} />
                    <Typography variant="body1" color="primary" fontWeight="medium">
                      Updating solution...
                    </Typography>
                  </Box>
                </Box>
              )}
              
              {/* Code Display Area */}
              <Box 
                sx={{ 
                  transition: 'opacity 0.3s ease-in-out',
                  opacity: isCodeUpdating ? 0.7 : 1,
                  height: '100%'
                }}
              >
                <CodeExecutor 
                  code={solution.code || ''} 
                  language={solution.language || 'python'}
                  minHeight="calc(100vh - 200px)"
                  showGenerateDoc={true}
                  onGenerateDoc={() => {
                    // Tạo sự kiện click cho nút đã ẩn
                    const docButton = document.getElementById('generate-doc-button');
                    if (docButton) {
                      docButton.click();
                      setIsOpen(true);
                    }
                  }}
                  onFullscreen={() => setCodeFullscreen(true)}
                />
              </Box>
            </Box>
          </TabPanel>
          
          {/* Analysis Tab */}
          <TabPanel value={currentTab} index={1}>
            <Box sx={{ 
              padding: "50px 50px",  // Thêm padding cho nội dung Analysis
              maxWidth: "900px",    // Giới hạn chiều rộng tối đa
              margin: "0 auto",     // Căn giữa nội dung
            }}>
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
              {(() => {
                const approach = solution.approach;
                if (!approach) return [];
                
                // If approach is a string, split by newlines or return as single item
                if (typeof approach === 'string') {
                  const lines = approach.split('\n').filter(line => line.trim());
                  return lines.length > 1 ? lines : [approach];
                }
                
                // If approach is already an array, use it
                if (Array.isArray(approach)) {
                  return approach;
                }
                
                return [];
              })().map((step: string, index: number) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <FlashOn color="primary" />
                  </ListItemIcon>
                  <ListItemText primary={step} />
                </ListItem>
              ))}
              {(!solution.approach || (Array.isArray(solution.approach) && solution.approach.length === 0) || (typeof solution.approach === 'string' && !solution.approach.trim())) && (
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
                {(() => {
                  const libraries = solution.libraries;
                  if (!libraries) return [];
                  if (typeof libraries === 'string') {
                    return libraries.split(',').map(lib => lib.trim()).filter(lib => lib);
                  }
                  if (Array.isArray(libraries)) return libraries;
                  return [];
                })().map((lib: string, index: number) => (
                  <Chip 
                    key={index} 
                    label={lib} 
                    color="secondary" 
                    variant="outlined" 
                    icon={<LocalLibrary />} 
                  />
                ))}
                {(!solution.libraries || (Array.isArray(solution.libraries) && solution.libraries.length === 0) || (typeof solution.libraries === 'string' && !solution.libraries.trim())) && (
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
                {(() => {
                  const perf = solution.performance_considerations;
                  if (!perf) return [];
                  if (typeof perf === 'string') {
                    const lines = perf.split('\n').filter(line => line.trim());
                    return lines.length > 1 ? lines : [perf];
                  }
                  if (Array.isArray(perf)) return perf;
                  return [];
                })().map((item: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <Speed color="primary" />
                    </ListItemIcon>
                    <ListItemText primary={item} />
                  </ListItem>
                ))}                {(!solution.performance_considerations || (Array.isArray(solution.performance_considerations) && solution.performance_considerations.length === 0) || (typeof solution.performance_considerations === 'string' && !solution.performance_considerations.trim())) && (
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
                {(() => {
                  const practices = solution.best_practices;
                  if (!practices) return [];
                  if (typeof practices === 'string') {
                    const lines = practices.split('\n').filter(line => line.trim());
                    return lines.length > 1 ? lines : [practices];
                  }
                  if (Array.isArray(practices)) return practices;
                  return [];
                })().map((practice: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText primary={practice} />
                  </ListItem>                ))}
                {(!solution.best_practices || (Array.isArray(solution.best_practices) && solution.best_practices.length === 0) || (typeof solution.best_practices === 'string' && !solution.best_practices.trim())) && (
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
            <Box sx={{ 
              padding: "50px 50px",  // Thêm padding cho nội dung Analysis
              maxWidth: "900px",    // Giới hạn chiều rộng tối đa
              margin: "0 auto",     // Căn giữa nội dung
            }}>
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
        </Box>
          {/* Hidden DocumentGenerator with external state management */}
        <Box sx={{ display: 'none' }}>
          <DocumentGenerator 
            taskId={taskId || ''} 
            isOpen={isOpen}
            setIsOpen={setIsOpen}
          />
        </Box>
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
          <Box sx={{ height: 'calc(100vh - 88px)' }}>
            <CodeExecutor 
              code={solution.code || ''} 
              language={solution.language || 'python'}
              minHeight="calc(100vh - 88px)"
              showGenerateDoc={true}
              onGenerateDoc={() => {
                const docButton = document.getElementById('generate-doc-button');
                if (docButton) {
                  docButton.click();
                  setIsOpen(true); // Ensure dialog opens
                }
              }}
            />
          </Box>
        </DialogContent>
        {/* <DialogActions>
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
        </DialogActions> */}
      </Dialog>      
      
      {/* Chat Drawer */}
      <Drawer
        variant={isMobile ? 'temporary' : 'persistent'}
        open={drawerOpen}
        anchor="right"
        onClose={() => setDrawerOpen(false)}
        sx={{
          width: drawerOpen ? drawerWidth : 0,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            border: 'none',
            borderLeft: `1px solid ${theme.palette.divider}`,
            right: 0,
            left: 'auto',
            position: 'fixed',
            overflowX: 'hidden',
          },
        }}
        >          
        <Resizable
            size={{ width: drawerWidth, height: '100%' }}
            enable={{ 
              left: true,
              right: false,
              top: false, 
              bottom: false,
              topRight: false,
              bottomRight: false,
              bottomLeft: false,
              topLeft: false 
            }}
            onResizeStop={(_e, _direction, ref, _d) => {
              const newWidth = ref.offsetWidth;
              setDrawerWidth(newWidth);
            }}
            minWidth={400}
            maxWidth={800}
          >
          <Box sx={{ 
            display: 'flex', 
            height: '100%',
            bgcolor: theme.palette.background.default
          }}>
            <Box 
              sx={{ 
                position: 'absolute',
                left: 0,
                top: 0,
                bottom: 0,
                width: '5px',
                backgroundColor: 'transparent',
                cursor: 'ew-resize',
                zIndex: 1000,
                '&:hover': {
                  backgroundColor: theme.palette.primary.main,
                  opacity: 0.3
                }
              }} 
              onMouseDown={(e) => {
                e.preventDefault();
                const startX = e.clientX;
                const startWidth = drawerWidth;
                
                const handleMouseMove = (moveEvent: MouseEvent) => {
                  const newWidth = Math.min(800, Math.max(400, startWidth + startX - moveEvent.clientX));
                  setDrawerWidth(newWidth);
                };
                
                const handleMouseUp = () => {
                  document.removeEventListener('mousemove', handleMouseMove);
                  document.removeEventListener('mouseup', handleMouseUp);
                };
                
                document.addEventListener('mousemove', handleMouseMove);
                document.addEventListener('mouseup', handleMouseUp);
              }}
            />            {/* Removed conversation sidebar */}

            {/* Chat Area */}
            <Box sx={{ 
              flex: 1,
              display: 'flex', 
              flexDirection: 'column',
            }}>
              {/* Chat Header */}              <Box sx={{ 
                p: 1.5, 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: `1px solid ${theme.palette.divider}`,
                bgcolor: theme.palette.primary.main,
                color: 'white',
                borderTopLeftRadius: '10px',
                borderTopRightRadius: '10px',
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Chat sx={{ mr: 1 }} />
                  <Typography variant="h6">Agent Chat</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {/* History button */}
                  <Tooltip title="Chat History">
                    <IconButton 
                      size="small"
                      onClick={() => setShowConversationDrawer(true)}
                      sx={{ color: 'white', mr: 1 }}
                    >
                      <History fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  {/* New conversation button */}
                  <Tooltip title="New Conversation">
                    <IconButton 
                      size="small"
                      onClick={handleNewConversation}
                      sx={{ color: 'white', mr: 1 }}
                    >
                      <Add fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <IconButton 
                    size="small"
                    onClick={() => setDrawerOpen(false)}
                    sx={{ color: 'white' }}
                  >
                    <Close fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
              {/* Chat Messages */}              
              <Box sx={{ 
                flexGrow: 1, 
                p: 2, 
                overflowY: 'auto',
                scrollbarWidth: 'none', // Firefox
                msOverflowStyle: 'none', // IE/Edge
                '&::-webkit-scrollbar': { // Thêm dòng này cho Chrome/Safari
                  display: 'none'
                },
                display: 'flex',
                flexDirection: 'column',
                textAlign: 'left',
                background: theme.palette.mode === 'dark' 
                  ? 'linear-gradient(to bottom, rgba(30, 30, 47, 0.8), rgba(30, 30, 47, 0.6))'
                  : 'linear-gradient(to bottom, rgba(245, 248, 250, 0.8), rgba(255, 255, 255, 0.9))',
              }}>
              {chatMessages.map((msg) => (
                  <Box 
                    key={msg.id} 
                    sx={{ 
                      mb: 2, 
                      alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '80%'
                    }}
                  >
                    {msg.sender === 'agent' && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Avatar 
                          sx={{ 
                            width: 24, 
                            height: 24, 
                            mr: 1, 
                            bgcolor: 
                              msg.agentType === 'planner' ? theme.palette.primary.main :
                              msg.agentType === 'researcher' ? theme.palette.info.main :
                              msg.agentType === 'developer' ? theme.palette.success.main :
                              msg.agentType === 'tester' ? theme.palette.warning.main :
                              theme.palette.secondary.main
                          }}
                        >
                          {msg.isLoading ? <CircularProgress size={16} color="inherit" /> : getAgentIcon(msg.agentType)}
                        </Avatar>
                        <Typography variant="caption" color="textSecondary">
                          {msg.isLoading ? "Thinking..." : getAgentName(msg.agentType)}
                        </Typography>
                      </Box>
                    )}                      <Paper 
                      elevation={1} 
                      sx={{ 
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: msg.sender === 'user' 
                          ? theme.palette.primary.main 
                          : theme.palette.background.paper,
                        color: msg.sender === 'user' 
                          ? 'white' 
                          : theme.palette.text.primary,
                        borderTopRightRadius: msg.sender === 'user' ? 0 : 2,
                        borderTopLeftRadius: msg.sender === 'agent' ? 0 : 2,
                        boxShadow: theme.palette.mode === 'dark' 
                          ? '0 2px 10px rgba(0,0,0,0.2)' 
                          : '0 2px 10px rgba(0,0,0,0.05)',
                        border: msg.sender === 'agent' 
                          ? `1px solid ${theme.palette.divider}` 
                          : 'none',
                      }}
                    >
                      {msg.sender === 'user' ? (
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {msg.message}
                        </Typography>
                      ) : (
                        msg.isLoading ? (
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <CircularProgress size={16} sx={{ mr: 1 }} />
                            <Typography variant="body2">Processing your request...</Typography>
                          </Box>
                        ) : renderMessageContent(msg.message)
                      )}
                    </Paper>
                  </Box>
                ))}
                <div ref={messagesEndRef} />
              </Box>
                {/* Chat Input */}              
                <Box sx={{ 
                  p: 2, 
                  borderTop: `1px solid ${theme.palette.divider}`,
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(30, 30, 47, 0.9)' : 'rgba(245, 248, 250, 0.9)',
                  overflowX: 'hidden', // Thêm dòng này
                  '&::-webkit-scrollbar': { // Ẩn thanh cuộn cho Chrome/Safari
                    display: 'none'
                  },
                  scrollbarWidth: 'none', // Firefox
                  msOverflowStyle: 'none' // IE/Edge
                }}>            
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Ask about the solution..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton 
                          color="primary" 
                          onClick={sendMessage} 
                          disabled={!chatMessage.trim()}
                          sx={{
                            backgroundColor: chatMessage.trim() ? theme.palette.primary.main : 'transparent',
                            color: chatMessage.trim() ? 'white' : theme.palette.text.disabled,
                            '&:hover': {
                              backgroundColor: chatMessage.trim() ? theme.palette.primary.dark : 'transparent',
                            },
                            width: 36,
                            height: 36,
                          }}
                        >
                          <Send fontSize="small" />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  size="small"
                  multiline
                  maxRows={3}
                  sx={{ 
                    backgroundColor: theme.palette.background.paper,
                    '& .MuiOutlinedInput-root': {
                      borderRadius: '20px',
                      paddingRight: '8px',
                    },
                    // Thêm các thuộc tính này để ngăn thanh cuộn ngang
                    '& .MuiInputBase-root': {
                      overflowX: 'hidden'
                    },
                    '& .MuiInputBase-input': {
                      overflowX: 'hidden',
                      overflowY: 'auto',
                      scrollbarWidth: 'none',
                      '&::-webkit-scrollbar': {
                        display: 'none'
                      }
                    }
                  }}
                />
              </Box>
            </Box>
          </Box>
        </Resizable>
      </Drawer>

      {/* Conversation History Drawer */}      
      <Drawer
        anchor="right"
        open={showConversationDrawer}
        onClose={() => setShowConversationDrawer(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: 450,
            p: 2,
            bgcolor: theme.palette.mode === 'dark' ? '#1e1e2f' : '#f5f8fa',
          }
        }}
      >        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 2,
          pb: 2,
          borderBottom: `1px solid ${theme.palette.divider}`
        }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
            <History sx={{ mr: 1 }} /> Conversation History
          </Typography>
          <IconButton onClick={() => setShowConversationDrawer(false)}>
            <Close />
          </IconButton>
        </Box>
        
        <Button 
          variant="contained" 
          startIcon={<Add />}
          onClick={() => {
            handleNewConversation();
            setShowConversationDrawer(false);
          }}
          fullWidth
          sx={{ mb: 2 }}
        >
          New Conversation
        </Button>
        
        <Divider sx={{ mb: 2 }} />
        
        <ConversationSidebar 
          onConversationSelect={(id) => {
            handleConversationSelect(id);
            setShowConversationDrawer(false);
          }}
          onNewConversation={() => {
            handleNewConversation();
            setShowConversationDrawer(false);
          }}
          currentConversationId={currentConversationId || undefined}
          taskId={taskId}
        />
      </Drawer>
    </Box>
  );
};

export default ResultPage;
