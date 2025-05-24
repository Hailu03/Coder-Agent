/**
 * Service for code execution functionality
 */
import axios from 'axios';

interface ExecuteCodeRequest {
  code: string;
  language: string;
  input_data?: string;
}

interface ExecuteCodeResponse {
  success: boolean;
  output?: string;
  error?: string;
  execution_time_ms?: number;
  memoryUsage?: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Execute code through the backend API
 */
export const executeRemoteCode = async (request: ExecuteCodeRequest): Promise<ExecuteCodeResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/execute/code`, request, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    return {
      success: !response.data.error,
      output: response.data.output,
      error: response.data.error,
      execution_time_ms: response.data.execution_time_ms
    };
  } catch (error: any) {
    console.error('Code execution error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Unknown error occurred',
      output: 'Execution failed'
    };
  }
};

/**
 * Execute JavaScript/TypeScript code directly in the browser
 */
export const executeLocalCode = (code: string): Promise<ExecuteCodeResponse> => {
  return new Promise((resolve) => {
    try {
      // Capture console output
      const originalConsoleLog = console.log;
      const originalConsoleError = console.error;
      const originalConsoleWarn = console.warn;
      const originalConsoleInfo = console.info;
      
      let outputLogs: string[] = [];
      
      // Override console methods
      console.log = (...args) => {
        outputLogs.push(args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' '));
      };
      
      console.error = (...args) => {
        outputLogs.push(`ERROR: ${args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ')}`);
        originalConsoleError.apply(console, args);
      };
      
      console.warn = (...args) => {
        outputLogs.push(`WARN: ${args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ')}`);
        originalConsoleWarn.apply(console, args);
      };
      
      console.info = (...args) => {
        outputLogs.push(`INFO: ${args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
        ).join(' ')}`);
        originalConsoleInfo.apply(console, args);
      };
      
      // Execute the code in a try-catch block
      const startTime = performance.now();
      const executeFunction = new Function(code);
      executeFunction();
      const executionTime = performance.now() - startTime;
      
      // Restore console functions
      console.log = originalConsoleLog;
      console.error = originalConsoleError;
      console.warn = originalConsoleWarn;
      console.info = originalConsoleInfo;
      
      resolve({
        success: true,
        output: outputLogs.join('\n') || 'Code executed successfully with no output.',
        executionTime: parseFloat(executionTime.toFixed(2))
      });
    } catch (err: any) {
      // Restore console functions in case of error
      console.log = console.log;
      console.error = console.error;
      console.warn = console.warn;
      console.info = console.info;
      
      resolve({
        success: false,
        error: err.toString(),
        output: 'Execution failed'
      });
    }
  });
};
