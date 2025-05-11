import axios from 'axios';

// Base URL for API endpoints - use environment variable with fallback
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Make sure all endpoints have trailing slashes to match FastAPI routes
const ensureTrailingSlash = (url: string) => url.endsWith('/') ? url : `${url}/`;

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
  serper_api_key?: string;
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
}

// Export a singleton instance
export const apiService = new ApiService();

export default apiService;