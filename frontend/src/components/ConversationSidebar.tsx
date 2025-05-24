import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
  IconButton,
  Tooltip,
  Paper,
  CircularProgress,
  Alert,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button
} from '@mui/material';
import {
  Add,
  Chat,
  MoreVert,
  Edit,
  Delete,
  Archive,
  AccessTime,
  Message
} from '@mui/icons-material';
import { formatDistanceToNow, parseISO } from 'date-fns';
import apiService, { ConversationResponse, ConversationCreate } from '../services/apiService';

interface ConversationSidebarProps {
  currentConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onNewConversation: () => void;
  taskId?: string;
}

const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  currentConversationId,
  onConversationSelect,
  onNewConversation,
  taskId
}) => {
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedConversation, setSelectedConversation] = useState<ConversationResponse | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Load conversations on component mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getConversations();
      
      // Sort conversations by updated_at (most recent first)
      const sortedConversations = data.sort((a, b) => 
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
      
      setConversations(sortedConversations);
    } catch (err: any) {
      console.error('Error loading conversations:', err);
      setError('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConversation = async () => {
    try {
      const request: ConversationCreate = {
        task_id: taskId,
        title: taskId ? `Task Discussion - ${taskId.slice(0, 8)}` : 'New Conversation'
      };
      
      const newConversation = await apiService.createConversation(request);
      setConversations(prev => [newConversation, ...prev]);
      onConversationSelect(newConversation.id);
      onNewConversation();
    } catch (err: any) {
      console.error('Error creating conversation:', err);
      setError('Failed to create conversation');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, conversation: ConversationResponse) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedConversation(conversation);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedConversation(null);
  };

  const handleEditOpen = () => {
    if (selectedConversation) {
      setEditTitle(selectedConversation.title || '');
      setEditDialogOpen(true);
    }
    handleMenuClose();
  };

  const handleEditSave = async () => {
    if (!selectedConversation) return;

    try {
      const updatedConversation = await apiService.updateConversation(selectedConversation.id, {
        title: editTitle
      });
      
      setConversations(prev => 
        prev.map(conv => conv.id === selectedConversation.id ? updatedConversation : conv)
      );
      setEditDialogOpen(false);
    } catch (err: any) {
      console.error('Error updating conversation:', err);
      setError('Failed to update conversation');
    }
  };

  const handleDeleteOpen = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!selectedConversation) return;

    try {
      await apiService.deleteConversation(selectedConversation.id);
      setConversations(prev => prev.filter(conv => conv.id !== selectedConversation.id));
      setDeleteDialogOpen(false);
      
      // If this was the current conversation, trigger new conversation
      if (selectedConversation.id === currentConversationId) {
        onNewConversation();
      }
    } catch (err: any) {
      console.error('Error deleting conversation:', err);
      setError('Failed to delete conversation');
    }
  };

  const formatLastActivity = (dateString: string) => {
    try {
      const date = parseISO(dateString);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch (err) {
      return 'Unknown';
    }
  };

  const truncateText = (text: string, maxLength: number = 50) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>      {/* We don't need a header here since the parent component already has one */}

      {/* Error Display */}
      {error && (
        <Box sx={{ p: 2 }}>
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Box>
      )}

      {/* Conversations List */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {conversations.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No conversations yet
            </Typography>            <Button
              variant="contained"
              size="medium"
              startIcon={<Add />}
              onClick={handleCreateConversation}
              sx={{ mt: 2, px: 2, py: 1, borderRadius: '20px' }}
            >
              Start Conversation
            </Button>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {conversations.map((conversation) => (
              <React.Fragment key={conversation.id}>
                <ListItem disablePadding>                    <ListItemButton
                    selected={conversation.id === currentConversationId}
                    onClick={() => onConversationSelect(conversation.id)}
                    sx={{
                      borderRadius: '8px',
                      mx: 1,
                      my: 0.5,
                      '&.Mui-selected': {
                        backgroundColor: 'primary.light',
                        '&:hover': {
                          backgroundColor: 'primary.light',
                        },
                      },
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                        <Message fontSize="small" />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Typography variant="subtitle2" noWrap>
                          {conversation.title || 'Untitled Conversation'}
                        </Typography>
                      }
                      secondary={
                        <Box>
                          {conversation.last_message && (
                            <Typography variant="caption" color="text.secondary" noWrap>
                              {truncateText(conversation.last_message)}
                            </Typography>
                          )}
                          <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                            <AccessTime sx={{ fontSize: 12, mr: 0.5 }} />
                            <Typography variant="caption" color="text.secondary">
                              {formatLastActivity(conversation.updated_at)}
                            </Typography>
                            {conversation.message_count && conversation.message_count > 0 && (
                              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                • {conversation.message_count} messages
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      }
                    />
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, conversation)}
                      sx={{ ml: 1 }}
                    >
                      <MoreVert fontSize="small" />
                    </IconButton>
                  </ListItemButton>
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        )}
      </Box>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEditOpen}>
          <Edit sx={{ mr: 1 }} fontSize="small" />
          Edit Title
        </MenuItem>
        <MenuItem onClick={handleDeleteOpen} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} fontSize="small" />
          Delete
        </MenuItem>
      </Menu>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Conversation Title</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Title"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleEditSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Conversation</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this conversation? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConversationSidebar;
