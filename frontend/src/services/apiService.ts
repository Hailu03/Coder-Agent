import axios from 'axios';

// Base URL for API endpoints - use environment variable with fallback
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Make sure all endpoints have trailing slashes to match FastAPI routes
const ensureTrailingSlash = (url: string) => url.endsWith('/') ? url : `${url}/`;

console.log('Using API base URL:', API_BASE_URL); // Debug log to check what URL is being used

// Configure axios defaults for CORS handling
axios.defaults.headers.common['Content-Type'] = 'application/json';
// Don't set withCredentials for '*' origins
axios.defaults.withCredentials = false;

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

export interface SettingsUpdateRequest {
  ai_provider?: string;
  api_key?: string;
  serper_api_key?: string;
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
}

// Export a singleton instance
export const apiService = new ApiService();

export default apiService;