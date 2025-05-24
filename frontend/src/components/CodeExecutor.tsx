import { useState, useRef, useEffect } from 'react';
import { Box, Button, Paper, Typography, CircularProgress, Alert, AlertTitle, Tabs, Tab, useTheme, Tooltip, Chip, TextField, IconButton, Menu, MenuItem } from '@mui/material';
import { PlayArrow, Refresh, Code, FileDownload, ContentCopy, Terminal, CheckCircle, Description, Fullscreen, ExpandMore, ExpandLess } from '@mui/icons-material';
import Editor from '@monaco-editor/react';
import '../RetroTheme.css';
import { executeLocalCode, executeRemoteCode } from '../services/codeExecutionService';

interface CodeExecutorProps {
  code: string;
  language: string;
  onChange?: (code: string) => void;
  readOnly?: boolean;
  showToolbar?: boolean;
  filename?: string;
  minHeight?: string;
  showGenerateDoc?: boolean;
  onGenerateDoc?: () => void;
  onFullscreen?: () => void;
}

interface ExecutionResult {
  status: 'running' | 'success' | 'error' | 'idle';
  output?: string;
  error?: string;
  executionTime?: number;
}

// Languages that can be executed in the browser
const EXECUTABLE_LANGUAGES = ['javascript', 'typescript'];

// Languages that can be executed via backend API
const BACKEND_EXECUTABLE_LANGUAGES = ['python', 'java', 'c', 'cpp', 'csharp', 'go', 'rust', 'ruby'];

// All executable languages
const ALL_EXECUTABLE_LANGUAGES = [...EXECUTABLE_LANGUAGES, ...BACKEND_EXECUTABLE_LANGUAGES];

// Language display names
const LANGUAGE_NAMES: Record<string, string> = {
  python: 'Python',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  java: 'Java',
  c: 'C',
  cpp: 'C++',
  csharp: 'C#',
  go: 'Go', 
  rust: 'Rust',
  ruby: 'Ruby'
};

// Helper function to convert language to file extension
const getFileExtension = (language: string): string => {
  const extensions: Record<string, string> = {
    python: 'py',
    javascript: 'js',
    typescript: 'ts',
    java: 'java',
    'c#': 'cs',
    'c++': 'cpp',
    cpp: 'cpp',
    c: 'c',
    go: 'go',
    rust: 'rs',
    ruby: 'rb'
  };
  
  return extensions[language.toLowerCase()] || 'txt';
};

const CodeExecutor = ({ 
  code, 
  language, 
  onChange, 
  readOnly = false, 
  showToolbar = true,
  filename = 'code',
  minHeight = "100%",
  showGenerateDoc = false,
  onGenerateDoc,
  onFullscreen
}: CodeExecutorProps) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [executionResult, setExecutionResult] = useState<ExecutionResult>({
    status: 'idle'
  });
  const [editorCode, setEditorCode] = useState(code);
  const editorRef = useRef<any>(null);
  const [copied, setCopied] = useState(false);
  const [stdinInput, setStdinInput] = useState<string>(''); // Add input state
  const [showInput, setShowInput] = useState<boolean>(false); // Toggle input visibility
  const [languageMenuAnchor, setLanguageMenuAnchor] = useState<null | HTMLElement>(null); // Language menu
  
  // Keep track of supported languages
  const [currentLanguage, setCurrentLanguage] = useState<string>(language);

  useEffect(() => {
    if (code !== editorCode) {
      setEditorCode(code);
    }
  }, [code]);
  
  // Update language if prop changes
  useEffect(() => {
    setCurrentLanguage(language);
  }, [language]);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleCodeChange = (value: string | undefined) => {
    const newCode = value || '';
    setEditorCode(newCode);
    if (onChange) {
      onChange(newCode);
    }
  };
  const executeCode = async () => {
    setExecutionResult({ status: 'running' });
    
    // Switch to output tab to show progress
    setActiveTab(1);

    try {
      let result;
      
      // JavaScript/TypeScript can be executed directly in the browser
      if (EXECUTABLE_LANGUAGES.includes(currentLanguage.toLowerCase())) {
        result = await executeLocalCode(editorCode);
        
        if (result.success) {
          setExecutionResult({
            status: 'success',
            output: result.output,
            executionTime: result.execution_time_ms
          });
        } else {
          setExecutionResult({
            status: 'error',
            error: result.error || 'Execution failed'
          });
        }
      } 
      // Other languages need to be executed through backend
      else if (BACKEND_EXECUTABLE_LANGUAGES.includes(currentLanguage.toLowerCase())) {
        result = await executeRemoteCode({
          code: editorCode,
          language: currentLanguage.toLowerCase(),
          input_data: stdinInput
        });
          if (result.success) {
          setExecutionResult({
            status: 'success',
            output: result.output,
            executionTime: result.execution_time_ms
          });
        } else {
          setExecutionResult({
            status: 'error',
            error: result.error || 'Backend execution failed'
          });
        }
      } 
      // Language not supported
      else {
        setExecutionResult({
          status: 'error',
          error: `Language ${currentLanguage} is not supported for execution.`
        });
      }

    } catch (err: any) {
      setExecutionResult({
        status: 'error',
        error: err instanceof Error ? err.message : String(err)
      });
    }
  };

  const resetExecution = () => {
    setExecutionResult({ status: 'idle' });
    setActiveTab(0); // Switch back to code tab
  };

  const downloadCode = () => {
    const extension = getFileExtension(currentLanguage);
    const element = document.createElement('a');
    const file = new Blob([editorCode], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${filename}.${extension}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(editorCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleLanguageSelect = (lang: string) => {
    setCurrentLanguage(lang);
    setLanguageMenuAnchor(null);
  };

  return (
    <Box className="retro-editor-container" sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>      {/* Editor Toolbar with macOS style buttons */}
      {showToolbar && (
        <Box className="editor-toolbar">
          <Box className="editor-buttons">
            <Box className="editor-button editor-button-red"></Box>
            <Box className="editor-button editor-button-yellow"></Box>
            <Box className="editor-button editor-button-green"></Box>
          </Box>
          <Typography className="editor-title">
            {filename}.{getFileExtension(currentLanguage)}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {/* Language Selector */}
            {!readOnly && (
              <>
                <Tooltip title="Select Language">
                  <Button
                    size="small"
                    color="inherit"
                    variant="text"
                    onClick={(e) => setLanguageMenuAnchor(e.currentTarget)}
                    sx={{ minWidth: 'unset', px: 1.5 }}
                    endIcon={languageMenuAnchor ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
                  >
                    {LANGUAGE_NAMES[currentLanguage.toLowerCase()] || currentLanguage}
                  </Button>
                </Tooltip>
                <Menu
                  anchorEl={languageMenuAnchor}
                  open={Boolean(languageMenuAnchor)}
                  onClose={() => setLanguageMenuAnchor(null)}
                >
                  {Object.entries(LANGUAGE_NAMES).map(([lang, name]) => (
                    <MenuItem 
                      key={lang} 
                      onClick={() => handleLanguageSelect(lang)}
                      selected={currentLanguage.toLowerCase() === lang.toLowerCase()}
                    >
                      {name}
                    </MenuItem>
                  ))}
                </Menu>
              </>
            )}
            
            {/* Run Code Button */}
            {!readOnly && ALL_EXECUTABLE_LANGUAGES.includes(currentLanguage.toLowerCase()) && (
              <Tooltip title="Run Code">
                <Button 
                  size="small" 
                  color="inherit"
                  variant="text"
                  onClick={executeCode}
                  sx={{ minWidth: 'unset', px: 1.5 }}
                >
                  <PlayArrow fontSize="small" />
                </Button>
              </Tooltip>
            )}
            
            {/* Generate Documentation Button */}
            {showGenerateDoc && onGenerateDoc && (
              <Tooltip title="Generate Documentation">
                <Button 
                  size="small" 
                  variant="text" 
                  color="inherit"
                  onClick={onGenerateDoc}
                  sx={{ minWidth: 'unset', px: 1.5 }}
                >
                  <Description fontSize="small" />
                </Button>
              </Tooltip>
            )}
            
            {/* Copy Code Button */}
            <Tooltip title="Copy Code">
              <Button 
                size="small" 
                variant="text" 
                color={copied ? "success" : "inherit"}
                onClick={copyToClipboard}
                sx={{ minWidth: 'unset', px: 1 }}
              >
                {copied ? <CheckCircle fontSize="small" /> : <ContentCopy fontSize="small" />}
              </Button>
            </Tooltip>
              {/* Download Button */}
            <Tooltip title="Download">
              <Button 
                size="small" 
                variant="text" 
                color="inherit" 
                onClick={downloadCode}
                sx={{ minWidth: 'unset', px: 1 }}
              >
                <FileDownload fontSize="small" />
              </Button>
            </Tooltip>
            
            {/* Fullscreen Button */}
            {onFullscreen && (
              <Tooltip title="Fullscreen">
                <Button 
                  size="small" 
                  variant="text" 
                  color="inherit"
                  onClick={onFullscreen}
                  sx={{ minWidth: 'unset', px: 1 }}
                >
                  <Fullscreen fontSize="small" />
                </Button>
              </Tooltip>
            )}
          </Box>
        </Box>
      )}

      {/* Editor or Output Tabs */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden',pb: 0, mb: 0 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, value) => setActiveTab(value)}
          variant="fullWidth"
          textColor="primary"
          indicatorColor="primary"
          sx={{ 
            borderBottom: `1px solid ${theme.palette.divider}`,
            minHeight: '48px', // Thiết lập chiều cao cố định
            marginBottom: 0 // Xóa margin bottom
          }}
        >
          <Tab label="Code" icon={<Code fontSize="small" />} iconPosition="start" />
          <Tab label="Output" icon={<Terminal fontSize="small" />} iconPosition="start" />
        </Tabs>

        <Box sx={{ 
          flex: 1, 
          display: activeTab === 0 ? 'flex' : 'none', 
          overflow: 'hidden',
          height: '100%' // Đảm bảo lấp đầy chiều cao
        }}>
          <Editor
            height="100%"
            language={currentLanguage.toLowerCase()}
            value={editorCode}
            onChange={handleCodeChange}
            onMount={handleEditorDidMount}
            theme={theme.palette.mode === 'dark' ? 'vs-dark' : 'light'}
            options={{
              readOnly: readOnly,
              automaticLayout: true,
              minimap: {
                enabled: false
              },              scrollBeyondLastLine: false,
              fontFamily: "'Fira Code', 'Consolas', monospace",
              fontLigatures: true,
              fontSize: 16,
              tabSize: 2,
              lineHeight: 1.5,
            }}
          />
        </Box>

        <Box 
          sx={{ 
            flex: 1, 
            display: activeTab === 1 ? 'flex' : 'none', 
            flexDirection: 'column',
            p: 3,
            pb: 0, 
            bgcolor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f5f5f5',
            overflow: 'auto',
            fontFamily: 'monospace',
            fontSize: '1.1rem'
          }}
        >
          {executionResult.status === 'running' && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress size={40} />
              <Typography variant="body1" sx={{ ml: 2 }}>Running...</Typography>
            </Box>
          )}
          {executionResult.status === 'idle' && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column' }}>
              <Typography variant="body1" color="textSecondary">
                Click "Run" to execute the code
              </Typography>
              <Button 
                variant="contained" 
                startIcon={<PlayArrow />} 
                onClick={executeCode}
                sx={{ mt: 2 }}
              >
                Run
              </Button>
            </Box>
          )}
          {executionResult.status === 'success' && (
            <>
              <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="subtitle1" mr={1}>Execution Output</Typography>
                  {executionResult.executionTime !== undefined && (
                    <Chip 
                      label={`${executionResult.executionTime}ms`} 
                      size="small" 
                      variant="outlined" 
                      color="primary"
                    />
                  )}
                </Box>
                <Button 
                  variant="outlined" 
                  size="small" 
                  startIcon={<Refresh />} 
                  onClick={resetExecution}
                >
                  Run Again
                </Button>
              </Box>              <Paper 
                elevation={0} 
                sx={{ 
                  p: 3, 
                  flex: 1, 
                  overflow: 'auto', 
                  fontFamily: 'monospace',
                  bgcolor: theme.palette.background.paper,
                  whiteSpace: 'pre-wrap',
                  fontSize: '16px',
                  lineHeight: '1.6',
                  borderRadius: 1,
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                {executionResult.output || 'No output'}
              </Paper>
            </>
          )}
          {executionResult.status === 'error' && (
            <>
              <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="subtitle1">Execution Error</Typography>
                <Button 
                  variant="outlined" 
                  size="small" 
                  startIcon={<Refresh />} 
                  onClick={resetExecution}
                >
                  Try Again
                </Button>
              </Box>              <Alert 
                severity="error" 
                sx={{ 
                  mb: 2,
                  '& .MuiAlert-message': {
                    fontSize: '15px',
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'monospace'
                  }
                }}
              >
                <AlertTitle>Error</AlertTitle>
                {executionResult.error}
              </Alert>
            </>
          )}
        </Box>        {/* Run button removed from here and moved to toolbar */}
      </Box>
    </Box>
  );
};

export default CodeExecutor;
