import axios from 'axios';

// Base URL for API endpoints - use environment variable with fallback
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Make sure all endpoints have trailing slashes to match FastAPI routes
const ensureTrailingSlash = (url: string) => url.endsWith('/') ? url : `${url}/`;

// Export the API base URL getter for other components
function getApiUrl() {
  return API_BASE_URL;
}

console.log('Using API base URL:', API_BASE_URL); // Debug log to check what URL is being used

// Configure axios defaults for CORS handling
axios.defaults.headers.common['Content-Type'] = 'application/json';
// Don't set withCredentials for '*' origins
axios.defaults.withCredentials = false;

// Add request interceptor to include authorization token in all requests
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Types
export interface SolveRequest {
  requirements: string;
  language: string;
}

export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface SolutionResponse {
  solution: any;
  status: string;
  task_id: string;
  error?: string;
}

export interface TaskUpdateEvent {
  task_id: string;
  status: string;
  detailed_status?: {
    phase: string;
    progress: number;
  };
}

export interface SettingsUpdateRequest {
  ai_provider?: string;
  api_key?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  full_name: string;
  avatar?: string;
  created_at: string;
}

export interface UserRegisterRequest {
  username: string;
  email: string;
  full_name?: string;
  password: string;
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  password?: string;
  avatar?: string;
}

export interface ChatRequest {
  message: string;
  task_id?: string;
  conversation_id?: string;
  code_context?: string;
  language?: string;
  error_message?: string;
}

export interface ChatResponse {
  message: string;
  code?: string;
  actions?: Array<{
    type: string;
    label: string;
  }>;
  type: 'text' | 'code' | 'error' | 'code_fix' | 'code_improvement' | 'implementation' | 'general_answer' | 'general_response';
  conversation_id?: string;
  // New fields for complete solution updates
  fixed_code?: string;
  improved_code?: string;
  changes_made?: string[];
  improvements_made?: string[];
  updated_explanation?: string;
  updated_approach?: string;
  updated_best_practices?: string;
  updated_problem_analysis?: string;
  solution_updated?: boolean;
}

// Conversation interfaces
export interface ConversationCreate {
  task_id?: string;
  title?: string;
}

export interface ConversationResponse {
  id: string;
  user_id: number;
  task_id?: string;
  title?: string;
  status: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  sender: string;
  agent_type?: string;
  content: string;
  message_type: string;
  metadata?: any;
  created_at: string;
}

export interface ConversationWithMessages {
  id: string;
  user_id: number;
  task_id?: string;
  title?: string;
  status: string;
  created_at: string;
  updated_at: string;
  messages: MessageResponse[];
}

export interface MessageCreate {
  conversation_id: string;
  sender: string;
  agent_type?: string;
  content: string;
  message_type?: string;
  metadata?: any;
}

// API service class
class ApiService {
  /**
   * Submit a problem-solving request
   * @param request The problem requirements and language
   * @returns Task information
   */
  async solveProblem(request: SolveRequest): Promise<TaskResponse> {
    try {
      console.log('Sending solve request to:', `${API_BASE_URL}/solve`);
      console.log('Request data:', request);
      
      const response = await axios.post<TaskResponse>(ensureTrailingSlash(`${API_BASE_URL}/solve`), request, {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Solve response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error submitting problem:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Get the status of a task
   * @param taskId The ID of the task
   * @returns The task status and solution if available
   */
  async getTaskStatus(taskId: string): Promise<SolutionResponse> {
    try {
      const response = await axios.get<SolutionResponse>(ensureTrailingSlash(`${API_BASE_URL}/solve/task/${taskId}`));
      return response.data;
    } catch (error: any) {
      console.error('Error fetching task status:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Cancel a running task
   * @param taskId The ID of the task to cancel
   * @returns Status message
   */
  async cancelTask(taskId: string): Promise<{ message: string }> {
    try {
      const response = await axios.post<{ message: string }>(ensureTrailingSlash(`${API_BASE_URL}/solve/task/${taskId}/cancel`));
      return response.data;
    } catch (error: any) {
      console.error('Error canceling task:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }
  
  /**
   * Cancel a running task
   * @params taskId The ID of the task to cancel
   * @returns Status message
   */
  async getHistory(): Promise<any> {
    try {
      const response = await axios.get(ensureTrailingSlash(`${API_BASE_URL}/solve/history`));
      return response.data;
    } catch (error: any) {
      console.error('Error fetching history:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Update application settings
   * @param settings The settings to update
   * @returns Status message
   */
  async updateSettings(settings: SettingsUpdateRequest): Promise<{ success: boolean; message: string }> {
    try {
      console.log('Updating settings with:', settings);
      console.log('Using API URL:', `${API_BASE_URL}/settings`);
      
      const response = await axios.post<{ success: boolean; message: string }>(
        ensureTrailingSlash(`${API_BASE_URL}/settings`), 
        settings,
        {
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );
      
      console.log('Settings update response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error updating settings:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }
  
  /**
   * Get current application settings
   * @returns Current settings
   */
  async getSettings(): Promise<any> {
    try {
      console.log('Fetching current settings from:', `${API_BASE_URL}/settings`);
      const response = await axios.get(ensureTrailingSlash(`${API_BASE_URL}/settings`));
      console.log('Current settings:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching settings:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Login user
   * @param username Username
   * @param password Password
   * @returns Authentication token and user info
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      console.log('Logging in user:', username);
      
      // OAuth2 form submission format
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post<LoginResponse>(
        ensureTrailingSlash(`${API_BASE_URL}/auth/login`), 
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          }
        }
      );
      
      console.log('Login successful');
      
      // Store both tokens
      localStorage.setItem('token', response.data.access_token);
      
      return response.data;
    } catch (error: any) {
      console.error('Login error:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Register a new user
   * @param userData User registration data
   * @returns Authentication token and user info
   */
  async register(userData: UserRegisterRequest): Promise<LoginResponse> {
    try {
      console.log('Registering new user:', userData.username);
      
      const response = await axios.post<LoginResponse>(
        ensureTrailingSlash(`${API_BASE_URL}/auth/register`), 
        userData
      );
      
      console.log('Registration successful');
      
      // Store both tokens
      localStorage.setItem('token', response.data.access_token);
      
      return response.data;
    } catch (error: any) {
      console.error('Registration error:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }
  
  /**
   * Get current user information
   * @returns User information
   */
  async getCurrentUser(): Promise<UserResponse> {
    try {
      console.log('Fetching current user info');
      
      const response = await axios.get<UserResponse>(ensureTrailingSlash(`${API_BASE_URL}/auth/me`));
      
      console.log('Current user info fetched');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching current user:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Update user information
   * @param userData User data to update
   * @returns Updated user information
   */
  async updateUser(userData: UserUpdateRequest): Promise<UserResponse> {
    try {
      console.log('Updating user information');
      
      const response = await axios.put<UserResponse>(
        ensureTrailingSlash(`${API_BASE_URL}/auth/me`), 
        userData
      );
      
      console.log('User information updated');
      return response.data;
    } catch (error: any) {
      console.error('Error updating user:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }
  
  /**
   * Check if user is logged in
   * @returns True if logged in, false otherwise
   */
  isLoggedIn(): boolean {
    return !!localStorage.getItem('token');
  }
    /**
   * Logout user
   */
  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
  
  /**
   * Connect to the SSE endpoint for real-time task updates
   * @param onUpdate Callback function for task updates
   * @param onError Callback function for errors
   * @returns An object with a disconnect method
   */  connectToTaskUpdates(onUpdate: (data: TaskUpdateEvent) => void, onError?: (error: any) => void): { disconnect: () => void } {
    try {
      console.log('Connecting to task updates stream');
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('User not authenticated');
      }
      
      // Create EventSource with token in URL as query parameter
      // Using the special endpoint that accepts token as query param for EventSource
      const eventSource = new EventSource(`${API_BASE_URL}/events/task-updates-token?token=${token}`, {
        withCredentials: false
      });
      
      // Set up event handlers
      eventSource.addEventListener('task_update', (event: any) => {
        try {
          const data: TaskUpdateEvent = JSON.parse(event.data);
          console.log('Task update received:', data);
          onUpdate(data);
        } catch (e) {
          console.error('Error parsing task update event:', e);
        }
      });
      
      // Handle connection errors
      eventSource.addEventListener('error', (event) => {
        console.error('SSE connection error:', event);
        
        // Add extra diagnostic info to help troubleshoot
        if (eventSource.readyState === EventSource.CONNECTING) {
          console.log('EventSource is reconnecting...');
        } else if (eventSource.readyState === EventSource.CLOSED) {
          console.log('EventSource connection is closed');
          
          // Try to reconnect after a short delay if the connection is closed
          setTimeout(() => {
            // Only attempt to reconnect if the connection is still closed
            if (eventSource.readyState === EventSource.CLOSED) {
              console.log('Attempting to reconnect to SSE...');
              // We'll create a new connection by simulating a disconnect/reconnect
              eventSource.close();
              this.connectToTaskUpdates(onUpdate, onError);
            }
          }, 2000);
        }
        
        if (onError) {
          onError(event);
        }
      });
      
      // Add open event listener for debugging
      eventSource.addEventListener('open', () => {
        console.log('SSE connection opened successfully');
      });
      
      // Add ping handler to keep connection alive
      eventSource.addEventListener('ping', () => {
        // This is just to keep the connection alive
        // console.log('Ping received from server');
      });
        // Return disconnect function
      return {
        disconnect: () => {
          console.log('Disconnecting from task updates stream');
          eventSource.close();
        }
      };
    } catch (error) {
      console.error('Error connecting to task updates:', error);
      if (onError) {
        onError(error);
      }
      // Return a no-op disconnect function
      return { disconnect: () => {} };
    }
  }

  /**
   * Request generation of comprehensive documentation for a solution
   * @param taskId The task ID of the solution to generate documentation for
   * @returns The response from the API with status information
   */
  async generateDocumentation(taskId: string): Promise<any> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/documentation/generate`,
        { task_id: taskId }
      );
      return response.data;
    } catch (error) {
      console.error('Error generating documentation:', error);
      throw error;
    }
  }

  /**
   * Connect to the documentation SSE stream to receive real-time updates
   * @param taskId The task ID to stream documentation updates for
   * @param onUpdate Callback for update events
   * @param onComplete Callback for completion event
   * @param onError Callback for error events
   * @returns Object with disconnect function
   */  connectToDocumentationUpdates(
    taskId: string,
    onUpdate: (content: string) => void,
    onComplete: (documentation: string) => void,
    onError?: (error: any) => void
  ) {
    try {
      console.log(`[SSE Doc ${taskId}] Attempting to connect to documentation updates...`);
      
      const eventSource = new EventSource(
        `${API_BASE_URL}/documentation/events/${taskId}`,
        { withCredentials: true }
      );
      
      console.log(`[SSE Doc ${taskId}] EventSource created. Waiting for 'open' event.`);

      eventSource.onopen = () => { // Standard open event
        console.log(`[SSE Doc ${taskId}] Connection OPENED successfully.`);
      };

      eventSource.addEventListener('connected', (event: MessageEvent) => { // Custom connected event from backend
        console.log(`[SSE Doc ${taskId}] Received 'connected' event. Data:`, event.data);
      });      eventSource.addEventListener('update', (event: MessageEvent) => {
        console.log(`[SSE Doc ${taskId}] Received 'update' event. Raw data:`, event.data);
        try {
          const data = JSON.parse(event.data);
          console.log(`[SSE Doc ${taskId}] Parsed 'update' data:`, data);
          if (data.content) {
            onUpdate(data.content);
          } else if (data.status) {
            // If no content but status is available, use status as content
            console.log(`[SSE Doc ${taskId}] No content field found, using status as content:`, data.status);
            onUpdate(data.status);
          } else {
            console.warn(`[SSE Doc ${taskId}] 'update' event data missing 'content' and 'status' fields.`);
          }
        } catch (e) {
          console.error(`[SSE Doc ${taskId}] Error parsing 'update' event data:`, e, "Raw data:", event.data);
          try {
            // As a fallback, try to use the raw data as content
            onUpdate(`${event.data}`);
          } catch (innerError) {
            console.error(`[SSE Doc ${taskId}] Failed to use raw data as content:`, innerError);
            if (onError) onError(new Error(`Failed to parse SSE update event for task ${taskId}`));
          }
        }
      });
      
      eventSource.addEventListener('complete', (event: MessageEvent) => {
        console.log(`[SSE Doc ${taskId}] Received 'complete' event. Raw data:`, event.data);
        try {
          let parsedData = JSON.parse(event.data);
          console.log(`[SSE Doc ${taskId}] Parsed 'complete' data (1st pass):`, parsedData);

          if (typeof parsedData === 'string') {
            console.log(`[SSE Doc ${taskId}] 'complete' data is a string after first parse, attempting second parse.`);
            try {
                parsedData = JSON.parse(parsedData);
                console.log(`[SSE Doc ${taskId}] Parsed 'complete' data (2nd pass):`, parsedData);
            } catch (nestedError) {
                console.warn(`[SSE Doc ${taskId}] Second parse of 'complete' data failed. Using result from first parse. Error:`, nestedError);
            }
          }
          
          if (parsedData && parsedData.documentation) {
            console.log(`[SSE Doc ${taskId}] 'complete' event successfully processed with 'documentation' field.`);
            onComplete(parsedData.documentation);
          } else if (parsedData && parsedData.content) { 
            console.warn(`[SSE Doc ${taskId}] 'complete' event missing 'documentation' field, using 'content' as fallback.`);
            onComplete(parsedData.content);
          } else {
            console.error(`[SSE Doc ${taskId}] 'complete' event data missing 'documentation' or 'content' field. Raw data:`, event.data, "Parsed data:", parsedData);
            if(onError) {
              onError(new Error(`Invalid 'complete' event structure for task ${taskId}`));
            } else {
              // Ensure loading stops even if no onError is passed
              onComplete(""); 
            }
          }
        } catch (e) {
          console.error(`[SSE Doc ${taskId}] Error parsing 'complete' event data:`, e, "Raw data:", event.data);
          if(onError) {
            onError(e);
          } else {
            // Ensure loading stops even if no onError is passed
            onComplete("");
          }
        }
      });
      
      eventSource.onerror = (errorEvent) => { // Standard error event
        console.error(`[SSE Doc ${taskId}] Connection ERROR:`, errorEvent);
        let errorMessage = `SSE connection error for task ${taskId}.`;
        if (eventSource.readyState === EventSource.CLOSED) {
          console.log(`[SSE Doc ${taskId}] Connection was closed.`);
          errorMessage += ` State: CLOSED.`;
        } else if (eventSource.readyState === EventSource.CONNECTING) {
          console.log(`[SSE Doc ${taskId}] Connection is attempting to reconnect.`);
          errorMessage += ` State: CONNECTING.`;
        } else {
          errorMessage += ` State: ${eventSource.readyState}.`;
        }
        
        if (onError) {
          onError(new Error(errorMessage));
        }
        // Do not close the eventSource here, it might attempt to reconnect.
        // The onError callback in DocumentGenerator.tsx should handle UI changes (e.g., setIsGenerating(false)).
      };

      // Return disconnect function
      return {
        disconnect: () => {
          console.log(`[SSE Doc ${taskId}] Disconnecting from documentation updates stream.`);
          eventSource.close();
        }
      };

    } catch (error) { // Catch synchronous errors from new EventSource() itself
      console.error(`[SSE Doc ${taskId}] Failed to create EventSource:`, error);
      if (onError) {
        onError(error);
      }
      // Return a no-op disconnect function if EventSource creation failed
      return { disconnect: () => {} };
    }
  }

  /**
   * Send a message to the chat agent
   * @param request The chat request containing the message and optional context
   * @returns Chat response from the agent
   */
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      console.log('Sending chat message to:', `${API_BASE_URL}/chat/message`);
      console.log('Chat request data:', request);
      
      const response = await axios.post<ChatResponse>(ensureTrailingSlash(`${API_BASE_URL}/chat/message`), request, {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Chat response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error sending chat message:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  // ===== CONVERSATION METHODS =====

  /**
   * Get all conversations for the current user
   * @returns Array of conversations
   */
  async getConversations(): Promise<ConversationResponse[]> {
    try {
      console.log('Fetching conversations from:', `${API_BASE_URL}/conversations/`);
      
      const response = await axios.get<ConversationResponse[]>(ensureTrailingSlash(`${API_BASE_URL}/conversations/`), {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Conversations response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching conversations:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Create a new conversation
   * @param request The conversation creation request
   * @returns Created conversation
   */
  async createConversation(request: ConversationCreate): Promise<ConversationResponse> {
    try {
      console.log('Creating conversation:', `${API_BASE_URL}/conversations/`);
      console.log('Conversation request data:', request);
      
      const response = await axios.post<ConversationResponse>(ensureTrailingSlash(`${API_BASE_URL}/conversations/`), request, {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Created conversation:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error creating conversation:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }
  /**
   * Get a conversation by ID with all its messages
   * @param conversationId The ID of the conversation
   * @returns Conversation with messages
   */
  async getConversationWithMessages(conversationId: string): Promise<ConversationWithMessages> {
    try {
      console.log('Fetching conversation with messages:', `${API_BASE_URL}/conversations/${conversationId}`);
      
      const response = await axios.get<ConversationWithMessages>(ensureTrailingSlash(`${API_BASE_URL}/conversations/${conversationId}`), {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Conversation with messages:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching conversation with messages:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Update a conversation
   * @param conversationId The ID of the conversation
   * @param request The conversation update data
   * @returns Updated conversation
   */
  async updateConversation(conversationId: string, request: Partial<ConversationCreate>): Promise<ConversationResponse> {
    try {
      console.log('Updating conversation:', `${API_BASE_URL}/conversations/${conversationId}`);
      console.log('Update request data:', request);
      
      const response = await axios.put<ConversationResponse>(ensureTrailingSlash(`${API_BASE_URL}/conversations/${conversationId}`), request, {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Updated conversation:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error updating conversation:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Delete a conversation
   * @param conversationId The ID of the conversation to delete
   */
  async deleteConversation(conversationId: string): Promise<void> {
    try {
      console.log('Deleting conversation:', `${API_BASE_URL}/conversations/${conversationId}`);
      
      await axios.delete(ensureTrailingSlash(`${API_BASE_URL}/conversations/${conversationId}`), {
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Conversation deleted successfully');
    } catch (error: any) {
      console.error('Error deleting conversation:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }
  /**
   * Upload a file attachment for a message
   * @param conversationId The ID of the conversation
   * @param messageId The ID of the message
   * @param file The file to upload
   * @returns Upload response with file information
   */
  async uploadMessageAttachment(conversationId: string, messageId: string, file: File): Promise<{ id: string; message_id: string; file_name: string; file_type: string; file_size: number; created_at: string }> {
    try {
      console.log('Uploading message attachment:', file.name);
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(
        ensureTrailingSlash(`${API_BASE_URL}/conversations/${conversationId}/messages/${messageId}/attachments/`), 
        formData, 
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          }
        }
      );
      
      console.log('File upload response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error uploading file:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }  /**
   * Download a file attachment
   * @param conversationId The ID of the conversation
   * @param messageId The ID of the message
   * @param attachmentId The ID of the attachment
   * @returns File blob
   */
  async downloadMessageAttachment(conversationId: string, messageId: string, attachmentId: string): Promise<Blob> {
    try {
      console.log('Downloading message attachment:', attachmentId);
      
      const response = await axios.get(
        `${API_BASE_URL}/conversations/${conversationId}/messages/${messageId}/attachments/${attachmentId}`, 
        {
          responseType: 'blob',
        }
      );
      
      console.log('File downloaded successfully');
      return response.data;
    } catch (error: any) {
      console.error('Error downloading file:', error);
      console.error('Error details:', error.response?.data || error.message);
      throw error;
    }
  }

  // ===== WEBSOCKET METHODS =====

  /**
   * Get the WebSocket manager instance
   * @returns WebSocket manager instance
   */
  getWebSocketManager(): WebSocketManager {
    return WebSocketManager.getInstance();
  }

  /**
   * Connect to the chat WebSocket for real-time messaging
   * @param onMessage Callback for incoming messages
   * @param onError Callback for connection errors
   * @returns Promise that resolves to connection object
   */
  connectToChatWebSocket(onMessage: (data: any) => void, onError: (error: any) => void) {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('User not authenticated');
    }

    // Convert HTTP URL to WebSocket URL
    const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');
    const chatWsUrl = `${wsUrl}/chat/ws?token=${token}`;
    
    const manager = this.getWebSocketManager();
    return manager.connect(chatWsUrl, onMessage, onError);
  }
}

// WebSocket Manager - Singleton pattern to manage single connection
class WebSocketManager {
  private static instance: WebSocketManager;
  private socket: WebSocket | null = null;
  private url: string = '';
  private onMessageCallbacks: Array<(data: any) => void> = [];
  private onErrorCallbacks: Array<(error: any) => void> = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private connectionPromise: Promise<any> | null = null;

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  connect(url: string, onMessage: (data: any) => void, onError: (error: any) => void) {
    // If already connected to the same URL, just add callbacks
    if (this.socket && this.socket.readyState === WebSocket.OPEN && this.url === url) {
      console.log('WebSocket already connected, adding callbacks');
      this.onMessageCallbacks.push(onMessage);
      this.onErrorCallbacks.push(onError);
      return this.getConnectionObject();
    }

    // If currently connecting to the same URL, wait for that connection
    if (this.isConnecting && this.url === url && this.connectionPromise) {
      console.log('WebSocket is connecting, waiting for connection...');
      this.onMessageCallbacks.push(onMessage);
      this.onErrorCallbacks.push(onError);
      return this.connectionPromise;
    }

    // Close existing connection if URL is different
    if (this.socket && this.url !== url) {
      console.log('URL changed, closing existing connection');
      this.disconnect();
    }

    this.url = url;
    this.onMessageCallbacks = [onMessage];
    this.onErrorCallbacks = [onError];

    return this.createConnection();
  }

  private createConnection() {
    if (this.isConnecting) {
      console.log('Connection already in progress');
      return this.connectionPromise;
    }

    this.isConnecting = true;
    console.log('Creating new WebSocket connection to:', this.url);
    
    this.connectionPromise = new Promise((resolve, reject) => {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log('WebSocket connection established');
        this.reconnectAttempts = 0;
        this.isConnecting = false;
        resolve(this.getConnectionObject());
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket received:', data);
          this.onMessageCallbacks.forEach(callback => callback(data));
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          this.onErrorCallbacks.forEach(callback => callback(err));
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.onErrorCallbacks.forEach(callback => callback(error));
        reject(error);
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnecting = false;
        this.socket = null;
        
        // Auto-reconnect if not manually closed and haven't exceeded max attempts
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          console.log(`Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
          setTimeout(() => {
            this.reconnectAttempts++;
            this.createConnection();
          }, this.reconnectDelay);
        }
      };
    });

    return this.connectionPromise;
  }

  private getConnectionObject() {
    return {
      sendMessage: (message: ChatRequest) => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          console.log('Sending WebSocket message:', message);
          this.socket.send(JSON.stringify(message));
        } else {
          const state = this.socket ? this.socket.readyState : 'null';
          console.error(`WebSocket not open (state: ${state}), message not sent`, message);
          this.onErrorCallbacks.forEach(callback => 
            callback(new Error(`WebSocket connection not open (state: ${state})`))
          );
        }
      },
      disconnect: () => this.disconnect(),
      isConnected: () => this.socket?.readyState === WebSocket.OPEN,
      getState: () => this.socket?.readyState ?? WebSocket.CLOSED
    };
  }

  disconnect() {
    if (this.socket) {
      console.log('Manually disconnecting WebSocket');
      this.socket.close(1000, 'Manual disconnect');
      this.socket = null;
    }
    this.onMessageCallbacks = [];
    this.onErrorCallbacks = [];
    this.reconnectAttempts = 0;
    this.isConnecting = false;
    this.connectionPromise = null;
  }
  // Method to remove specific callbacks (useful for component cleanup)
  removeCallbacks(onMessage: (data: any) => void, onError: (error: any) => void) {
    this.onMessageCallbacks = this.onMessageCallbacks.filter(cb => cb !== onMessage);
    this.onErrorCallbacks = this.onErrorCallbacks.filter(cb => cb !== onError);
    
    // If no more callbacks, disconnect
    if (this.onMessageCallbacks.length === 0 && this.onErrorCallbacks.length === 0) {
      console.log('No more callbacks, disconnecting WebSocket');
      this.disconnect();
    }
  }

  // Check if WebSocket is connected
  isConnected() {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  // Get connection state
  getState() {
    return this.socket?.readyState ?? WebSocket.CLOSED;
  }
}

// Export a singleton instance
export const apiService = new ApiService();

export default apiService;