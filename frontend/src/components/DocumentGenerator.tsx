import { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Paper, 
  Typography, 
  CircularProgress,
  Dialog,
  DialogContent,
  DialogActions,
  IconButton,
  Alert
} from '@mui/material';
import { Description, PictureAsPdf, Close, ArrowDownward } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';

interface DocumentGeneratorProps {
  taskId: string;
}

interface DocumentGeneratorProps {
  taskId: string;
  isOpen?: boolean;
  setIsOpen?: (isOpen: boolean) => void;
}

// Component for generating comprehensive documentation from solutions
const DocumentGenerator = ({ taskId, isOpen: externalIsOpen, setIsOpen: externalSetIsOpen }: DocumentGeneratorProps) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [documentation, setDocumentation] = useState('');
  const [error, setError] = useState<string | null>(null);
  const documentRef = useRef(null);
  const connectionRef = useRef<{ disconnect: () => void } | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Use either external or internal state for dialog open status
  const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen;
  const setIsOpen = externalSetIsOpen || setInternalIsOpen;

  const handleOpen = () => {
    setIsOpen(true);
    setError(null);
  };
  const handleClose = () => {
    // If we're generating documentation, show a confirm dialog
    if (isGenerating) {
      const confirmClose = window.confirm(
        'Documentation generation is still in progress. Closing this dialog will not stop the process, ' +
        'but you will need to reopen the dialog to see results. Are you sure you want to close?'
      );
      if (!confirmClose) return;
    }
    setIsOpen(false);
  };

  // Cleanup function to cancel SSE connection and clear timeouts
  const cleanupResources = () => {
    if (connectionRef.current) {
      console.log(`[DocGen ${taskId}] Cleaning up SSE connection`);
      connectionRef.current.disconnect();
      connectionRef.current = null;
    }
    
    if (timeoutRef.current) {
      console.log(`[DocGen ${taskId}] Clearing safety timeout`);
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };
  // Effect for cleanup when component unmounts or dialog closes
  useEffect(() => {
    // If dialog closes, only clean up resources if we're not actively generating
    if (!isOpen && !isGenerating) {
      console.log(`[DocGen ${taskId}] Dialog closed and not generating, cleaning up resources`);
      cleanupResources();
    } else if (!isOpen && isGenerating) {
      console.log(`[DocGen ${taskId}] Dialog closed but still generating, keeping connection`);
      // Don't cleanup while generating, even if dialog closes
    }
    
    // Cleanup on unmount
    return () => {
      console.log(`[DocGen ${taskId}] Component unmounting, cleaning up resources`);
      cleanupResources();
    };
  }, [isOpen, taskId, isGenerating]);

  const generateDocumentation = async () => {
    // Prevent multiple generations at once
    if (isGenerating) {
      console.log(`[DocGen ${taskId}] Already generating documentation, ignoring request`);
      return;
    }
    
    // Reset state
    setIsGenerating(true);
    setDocumentation('');
    setError(null);
    
    // Clean up any existing connections/timeouts
    cleanupResources();
    
    try {
      // Import the API service
      const apiService = (await import('../services/apiService')).default;
      
      // Start documentation generation
      console.log(`[DocGen ${taskId}] Starting documentation generation`);
      
      try {
        const response = await apiService.generateDocumentation(taskId);
        console.log(`[DocGen ${taskId}] Documentation generation initiated:`, response);
      } catch (err: any) {
        console.error(`[DocGen ${taskId}] Error starting documentation generation:`, err);
        throw new Error(`Failed to start documentation generation: ${err.message || 'Unknown error'}`);
      }
      
      // Create SSE connection to get streaming updates
      console.log(`[DocGen ${taskId}] Connecting to documentation updates stream`);
      
      const connection = apiService.connectToDocumentationUpdates(
        taskId,
        // On update handler for streaming content
        (content) => {
          console.log(`[DocGen ${taskId}] Received update:`, content);
          if (content) {
            setDocumentation(prevDoc => prevDoc + content);
          }
        },
        // On complete handler for final documentation
        (finalDocumentation) => {
          console.log(`[DocGen ${taskId}] Received complete documentation of length:`, 
            finalDocumentation ? finalDocumentation.length : 0);
          
          setIsGenerating(false);
          
          if (finalDocumentation) {
            setDocumentation(finalDocumentation);
          } else {
            console.warn(`[DocGen ${taskId}] Received empty documentation in complete event`);
            setError("Received empty documentation. The generation may have failed on the server.");
            // Keep any partial documentation if it exists
            if (!documentation) {
              setDocumentation("# Documentation Generation Failed\n\nThe server completed the documentation process but returned an empty result. Please try again.");
            }
          }
          
          // Clean up SSE connection after receiving complete
          if (connectionRef.current) {
            console.log(`[DocGen ${taskId}] Disconnecting SSE after complete event`);
            connectionRef.current.disconnect();
            connectionRef.current = null;
          }
        },
        // On error handler
        (error) => {
          console.error(`[DocGen ${taskId}] Error in documentation stream:`, error);
          setIsGenerating(false);
          setError(`Error receiving documentation: ${error.message || 'Unknown error'}`);
          
          // If we have no documentation content yet, show error message
          if (!documentation) {
            setDocumentation("# Documentation Generation Error\n\n" + 
              "An error occurred while streaming the documentation. " +
              "The server may still have generated the content. Please try again.");
          }
          
          // Clean up connection on error
          if (connectionRef.current) {
            connectionRef.current.disconnect();
            connectionRef.current = null;
          }
        }
      );
      
      // Store the connection for cleanup
      connectionRef.current = connection;      // Add safety timeouts at different intervals to ensure we catch the documentation
      const fetchDocAfterDelay = async (delayMs, attemptNumber = 1) => {
        try {
          console.log(`[DocGen ${taskId}] Attempt ${attemptNumber}: Checking for documentation via API`);
          const docResponse = await apiService.getDocumentation(taskId);
          
          if (docResponse.status === 'success' && docResponse.documentation) {
            console.log(`[DocGen ${taskId}] Successfully retrieved documentation from API on attempt ${attemptNumber}`);
            setDocumentation(docResponse.documentation);
            setIsGenerating(false);
            setError(null);
            return true;
          } else {
            console.log(`[DocGen ${taskId}] No documentation found from API (attempt ${attemptNumber}):`, docResponse);
            return false;
          }
        } catch (fetchError) {
          console.error(`[DocGen ${taskId}] Error fetching documentation (attempt ${attemptNumber}):`, fetchError);
          return false;
        }
      };
      
      // Set multiple timeouts at increasing intervals
      const setMultipleTimeouts = () => {
        // First check at 15 seconds - backend may complete quickly
        setTimeout(async () => {
          if (isGenerating && !documentation) {
            const success = await fetchDocAfterDelay(15000, 1);
            if (success) cleanupResources();
          }
        }, 15000);
        
        // Second check at 30 seconds
        setTimeout(async () => {
          if (isGenerating && !documentation) {
            const success = await fetchDocAfterDelay(30000, 2);
            if (success) cleanupResources();
          }
        }, 30000);
        
        // Final timeout at 60 seconds - give up waiting and show message
        timeoutRef.current = setTimeout(async () => {
          console.log(`[DocGen ${taskId}] Safety timeout reached (60s), ending loading state`);
          
          if (isGenerating) {
            // Last attempt to fetch documentation directly
            const success = await fetchDocAfterDelay(60000, 3);
            
            if (!success) {
              setIsGenerating(false);
              setError("Documentation generation timed out after multiple attempts.");
              
              // If we have no documentation content yet, show timeout message
              if (!documentation) {
                setDocumentation("# Documentation Generation Timeout\n\n" +
                  "The documentation process timed out after 60 seconds despite multiple retry attempts. " +
                  "The server may still be processing your request. " +
                  "You can try refreshing or generating again later.");
              }
            }
            
            // Clean up connection on final timeout regardless of outcome
            cleanupResources();
          }
        }, 60000);
      };
      
      // Start the cascade of timeouts
      setMultipleTimeouts();
      
    } catch (error: any) {
      console.error(`[DocGen ${taskId}] Error in documentation generation:`, error);
      setIsGenerating(false);
      setError(`Generation failed: ${error.message || 'Unknown error'}`);
      
      setDocumentation("# Documentation Generation Failed\n\n" +
        `The documentation generation process encountered an error: ${error.message || 'Unknown error'}\n\n` +
        "Please try again later.");
    }
  };

  const generatePDF = () => {
    if (!documentation) return;
    
    try {
      import('jspdf').then(({ default: jsPDF }) => {
        import('html-to-image').then(({ toPng }) => {
          if (!documentRef.current) return;
          
          toPng(documentRef.current)
            .then((dataUrl) => {
              const pdf = new jsPDF('p', 'mm', 'a4');
              const imgProps = pdf.getImageProperties(dataUrl);
              const pdfWidth = pdf.internal.pageSize.getWidth();
              const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
              
              pdf.addImage(dataUrl, 'PNG', 0, 0, pdfWidth, pdfHeight);
              pdf.save(`solution-documentation-${taskId}.pdf`);
            })
            .catch((error) => {
              console.error('Error generating image for PDF:', error);
              alert('Error generating PDF');
            });
        });
      });
    } catch (error) {
      console.error('Error loading PDF generation libraries:', error);
      alert('Error loading PDF generation libraries');
    }
  };  // Hàm xử lý cả việc mở dialog và bắt đầu quá trình tạo documentation
  const handleGenerateDocClick = () => {
    handleOpen();
    if (!documentation && !isGenerating) {
      setTimeout(() => {
        generateDocumentation();
      }, 300); // Đợi dialog mở xong rồi mới generate
    }
  };

  return (
    <>
      <Button
        id="generate-doc-button"
        variant="contained" 
        color="primary"
        size="large"
        startIcon={<Description />}
        onClick={handleGenerateDocClick}
        disabled={isGenerating}
        sx={{ 
          opacity: 1, // Hiển thị bình thường thay vì ẩn
          display: 'none' // Ẩn nút nhưng vẫn cho phép kích hoạt từ bên ngoài
        }}
      >
        Generate Documentation
      </Button>

      <Dialog 
        open={isOpen} 
        onClose={handleClose} 
        maxWidth="lg" 
        fullWidth
        PaperProps={{
          sx: {
            height: '85vh',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column'
          }
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          p: 2,
          borderBottom: 1, 
          borderColor: 'divider'
        }}>
          <Typography variant="h6">Solution Documentation</Typography>
          <IconButton onClick={handleClose}>
            <Close />
          </IconButton>
        </Box>

        <DialogContent sx={{ flexGrow: 1, overflow: 'auto' }}>
          {/* Error Message */}
          {error && (
            <Alert 
              severity="error" 
              sx={{ mb: 2 }}
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          )}
          
          {/* Initial State - No Documentation and Not Generating */}
          {!documentation && !isGenerating && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <Typography variant="h5" sx={{ mb: 2 }}>Generate Detailed Documentation</Typography>
              <Typography variant="body1" color="textSecondary" align="center" sx={{ mb: 4 }}>
                Create comprehensive documentation explaining all aspects of your solution including requirements,
                planning, research, implementation details, and testing results.
              </Typography>              <Button
                id="generate-doc-button"
                variant="contained" 
                color="primary"
                size="large"
                startIcon={<Description />}
                onClick={generateDocumentation}
                disabled={isGenerating}
                sx={{ display: 'flex' }} // Make it always flex to ensure proper rendering
              >
                Generate Documentation
              </Button>
            </Box>
          )}

          {/* Loading State */}
          {isGenerating && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <CircularProgress size={60} sx={{ mb: 3 }} />
              <Typography variant="h6" sx={{ mb: 1 }}>Generating Documentation...</Typography>
              <Typography variant="body2" color="textSecondary">
                This may take a few minutes. Our AI is analyzing your solution and crafting detailed documentation.
              </Typography>
              <Button
                variant="text"
                color="secondary"
                onClick={() => {
                  setIsGenerating(false);
                  cleanupResources();
                  setError("Documentation generation cancelled by user");
                }}
                sx={{ mt: 3 }}
              >
                Cancel
              </Button>
            </Box>
          )}

          {/* Documentation Display */}
          {documentation && !isGenerating && (
            <Paper
              ref={documentRef}
              sx={{
                p: 4,
                bgcolor: 'background.paper',
                // ... (existing styles)

                // Typography improvements:
                fontFamily: 'Arial', // Or any other web-safe font
                fontSize: '12pt',  // Adjust font size
                lineHeight: 1.5, // Improve readability

                // Heading styles:
                '& h1': {
                  fontSize: '24pt',
                  fontWeight: 'bold',
                  marginBottom: '10mm',
                },
                '& h2': {
                  fontSize: '18pt',
                  fontWeight: 'bold',
                  marginBottom: '8mm',
                },
                // ... styles for h3, p, etc.

                // Code block formatting:
                '& pre': {
                  fontFamily: 'Courier New', // Monospace font
                  fontSize: '10pt',
                  padding: '5mm',
                  border: '1px solid #ccc', // Add a border
                  whiteSpace: 'pre-wrap', // Allow line breaks in code
                },

                // Table styling (if applicable):
                '& table': {
                  width: '100%',
                  borderCollapse: 'collapse',
                  marginBottom: '10mm',
                },
                '& th, & td': {
                  border: '1px solid #ccc',
                  padding: '5mm',
                },

                // Other styles as needed
              }}
            >
              <ReactMarkdown>
                {documentation}
              </ReactMarkdown>
            </Paper>
          )}
        </DialogContent>

        {/* Actions when documentation is available */}
        {documentation && !isGenerating && (
          <DialogActions sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
            <Button 
              startIcon={<PictureAsPdf />} 
              onClick={generatePDF} 
              variant="contained" 
              color="primary"
            >
              Export as PDF
            </Button>
            <Button 
              startIcon={<ArrowDownward />} 
              onClick={() => {
                const blob = new Blob([documentation], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `documentation_${taskId}.md`;
                a.click();
              }} 
              variant="outlined"
            >
              Download Markdown
            </Button>
            <Button
              color="secondary"
              onClick={generateDocumentation}
            >
              Regenerate
            </Button>
          </DialogActions>
        )}
      </Dialog>
    </>
  );
};

export default DocumentGenerator;
