"""
API endpoints for code execution.
"""

import os
import sys
import tempfile
import subprocess
import logging
import shutil
import time
import resource
from typing import Dict, Any, Optional
import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from ...core.config import settings

# Configure logging
logger = logging.getLogger("api.execute")

# Execution limits
MAX_EXECUTION_TIME = 10  # Maximum execution time in seconds
MAX_OUTPUT_SIZE = 1024 * 1024  # Maximum output size in bytes (1MB)
MAX_CODE_SIZE = 100 * 1024  # Maximum code size in bytes (100KB)

router = APIRouter()

class CodeExecutionRequest(BaseModel):
    """Code execution request model."""
    code: str
    language: str
    input_data: Optional[str] = None
    
    @validator('code')
    def code_size_limit(cls, v):
        if len(v.encode('utf-8')) > MAX_CODE_SIZE:
            raise ValueError(f"Code size exceeds the limit of {MAX_CODE_SIZE // 1024}KB")
        return v
    
    @validator('language')
    def validate_language(cls, v):
        supported_languages = ["python", "py", "javascript", "js", "typescript", "ts", 
                             "java", "c#", "csharp", "c++", "cpp", "go"]
        if v.lower() not in supported_languages:
            raise ValueError(f"Unsupported language: {v}")
        return v

class CodeExecutionResponse(BaseModel):
    """Code execution response model."""
    output: str
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

@router.post("/code", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest) -> Dict[str, Any]:
    """Execute code and return the output.
    
    Args:
        request: The code execution request containing code, language, and optional input data
        
    Returns:
        Dictionary with execution output and error information
    """
    language = request.language.lower()
    code = request.code
    
    logger.info(f"Executing {language} code")
    
    # Create a unique execution directory
    execution_id = str(uuid.uuid4())
    temp_dir = os.path.join(tempfile.gettempdir(), f"code_exec_{execution_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Execute based on language
        if language in ["python", "py"]:
            return await _execute_python(code, request.input_data, temp_dir)
        elif language in ["javascript", "js"]:
            return await _execute_javascript(code, request.input_data, temp_dir)
        elif language in ["typescript", "ts"]:
            return await _execute_typescript(code, request.input_data, temp_dir)
        elif language == "java":
            return await _execute_java(code, request.input_data, temp_dir)
        elif language in ["c#", "csharp"]:
            return await _execute_csharp(code, request.input_data, temp_dir)
        elif language in ["c++", "cpp"]:
            return await _execute_cpp(code, request.input_data, temp_dir)
        elif language == "go":
            return await _execute_go(code, request.input_data, temp_dir)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return {
            "output": "",
            "error": str(e),
            "execution_time_ms": 0
        }
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory: {str(e)}")

async def _execute_python(code: str, input_data: Optional[str], temp_dir: str) -> Dict[str, Any]:
    """Execute Python code."""
    # Create Python file
    file_path = os.path.join(temp_dir, "main.py")
    with open(file_path, "w") as f:
        f.write(code)
    
    # Add a safety timeout wrapper to the code
    with open(file_path, "r") as f:
        original_code = f.read()
    
    # Wrap code with timeout handling
    timeout_wrapper = f"""
import signal
import sys
import resource

# Set resource limits
resource.setrlimit(resource.RLIMIT_CPU, ({MAX_EXECUTION_TIME}, {MAX_EXECUTION_TIME}))
resource.setrlimit(resource.RLIMIT_AS, (500 * 1024 * 1024, 500 * 1024 * 1024))  # 500MB memory limit

def timeout_handler(signum, frame):
    print('\\nExecution timed out after {MAX_EXECUTION_TIME} seconds')
    sys.exit(1)

# Set the timeout handler
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({MAX_EXECUTION_TIME})

try:
{chr(10).join('    ' + line for line in original_code.splitlines())}
finally:
    # Cancel the alarm
    signal.alarm(0)
"""
    with open(file_path, "w") as f:
        f.write(timeout_wrapper)
    
    # Execute Python code
    start_time = asyncio.get_event_loop().time()
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            limit=MAX_OUTPUT_SIZE
        )
        
        if input_data:
            stdout, stderr = await process.communicate(input=input_data.encode())
        else:
            stdout, stderr = await process.communicate()
            
        end_time = asyncio.get_event_loop().time()
        execution_time = (end_time - start_time) * 1000  # ms
        
        output = stdout.decode().strip()
        error = stderr.decode().strip() if stderr else None
        
        return {
            "output": output,
            "error": error,
            "execution_time_ms": execution_time
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Error executing Python code: {str(e)}",
            "execution_time_ms": 0
        }

async def _execute_javascript(code: str, input_data: Optional[str], temp_dir: str) -> Dict[str, Any]:
    """Execute JavaScript code using Node.js"""
    # Create JavaScript file
    file_path = os.path.join(temp_dir, "main.js")
    with open(file_path, "w") as f:
        f.write(code)
    
    # Execute with Node.js
    start_time = asyncio.get_event_loop().time()
    try:
        process = await asyncio.create_subprocess_exec(
            "node", file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None
        )
        
        if input_data:
            stdout, stderr = await process.communicate(input=input_data.encode())
        else:
            stdout, stderr = await process.communicate()
            
        end_time = asyncio.get_event_loop().time()
        execution_time = (end_time - start_time) * 1000
        
        output = stdout.decode().strip()
        error = stderr.decode().strip() if stderr else None
        
        return {
            "output": output,
            "error": error,
            "execution_time_ms": execution_time
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Error executing JavaScript code: {str(e)}",
            "execution_time_ms": 0
        }

async def _execute_typescript(code: str, input_data: Optional[str], temp_dir: str) -> Dict[str, Any]:
    """Execute TypeScript code by compiling to JavaScript first"""
    # Create TypeScript file
    ts_file = os.path.join(temp_dir, "main.ts")
    with open(ts_file, "w") as f:
        f.write(code)
    
    js_file = os.path.join(temp_dir, "main.js")
    
    # Compile TypeScript to JavaScript
    try:
        compile_process = await asyncio.create_subprocess_exec(
            "tsc", ts_file, "--outFile", js_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, stderr = await compile_process.communicate()
        
        if compile_process.returncode != 0:
            return {
                "output": "",
                "error": f"TypeScript compilation failed: {stderr.decode().strip()}",
                "execution_time_ms": 0
            }
        
        # Execute the compiled JavaScript
        return await _execute_javascript("", input_data, temp_dir)
    except Exception as e:
        return {
            "output": "",
            "error": f"Error executing TypeScript code: {str(e)}",
            "execution_time_ms": 0
        }

async def _execute_java(code: str, input_data: Optional[str], temp_dir: str) -> Dict[str, Any]:
    """Execute Java code"""
    # Try to extract class name from code
    import re
    class_match = re.search(r"public\s+class\s+(\w+)", code)
    class_name = class_match.group(1) if class_match else "Main"
    
    # Create Java file
    java_file = os.path.join(temp_dir, f"{class_name}.java")
    with open(java_file, "w") as f:
        f.write(code)
    
    # Compile Java code
    start_time = asyncio.get_event_loop().time()
    try:
        compile_process = await asyncio.create_subprocess_exec(
            "javac", java_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, stderr = await compile_process.communicate()
        
        if compile_process.returncode != 0:
            return {
                "output": "",
                "error": f"Java compilation failed: {stderr.decode().strip()}",
                "execution_time_ms": 0
            }
        
        # Execute Java code
        cwd = os.getcwd()
        os.chdir(temp_dir)  # Change directory for Java class loading
        
        process = await asyncio.create_subprocess_exec(
            "java", class_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None
        )
        
        if input_data:
            stdout, stderr = await process.communicate(input=input_data.encode())
        else:
            stdout, stderr = await process.communicate()
            
        # Restore working directory
        os.chdir(cwd)
        
        end_time = asyncio.get_event_loop().time()
        execution_time = (end_time - start_time) * 1000
        
        output = stdout.decode().strip()
        error = stderr.decode().strip() if stderr else None
        
        return {
            "output": output,
            "error": error,
            "execution_time_ms": execution_time
        }
    except Exception as e:
        # Restore working directory in case of exception
        if 'cwd' in locals():
            os.chdir(cwd)
        
        return {
            "output": "",
            "error": f"Error executing Java code: {str(e)}",
            "execution_time_ms": 0
        }

async def _execute_csharp(code: str, input_data: Optional[str], temp_dir: str) -> Dict[str, Any]:
    """Execute C# code using dotnet"""
    # Create C# file
    file_path = os.path.join(temp_dir, "Program.cs")
    with open(file_path, "w") as f:
        f.write(code)
    
    # Create simple project
    try:
        # Initialize a new C# project
        init_process = await asyncio.create_subprocess_exec(
            "dotnet", "new", "console", "-o", temp_dir, "--force",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await init_process.communicate()
        
        # Run the program
        start_time = asyncio.get_event_loop().time()
        process = await asyncio.create_subprocess_exec(
            "dotnet", "run", "--project", temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None
        )
        
        if input_data:
            stdout, stderr = await process.communicate(input=input_data.encode())
        else:
            stdout, stderr = await process.communicate()
        
        end_time = asyncio.get_event_loop().time()
        execution_time = (end_time - start_time) * 1000
        
        output = stdout.decode().strip()
        error = stderr.decode().strip() if stderr else None
        
        return {
            "output": output,
            "error": error,
            "execution_time_ms": execution_time
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Error executing C# code: {str(e)}",
            "execution_time_ms": 0
        }

async def _execute_cpp(code: str, input_data: Optional[str], temp_dir: str) -> Dict[str, Any]:
    """Execute C++ code"""
    # Create C++ file
    file_path = os.path.join(temp_dir, "main.cpp")
    with open(file_path, "w") as f:
        f.write(code)
    
    output_path = os.path.join(temp_dir, "main")
    if os.name == "nt":  # Windows
        output_path += ".exe"
    
    # Compile C++ code
    start_time = asyncio.get_event_loop().time()
    try:
        compile_process = await asyncio.create_subprocess_exec(
            "g++", file_path, "-o", output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        _, stderr = await compile_process.communicate()
        
        if compile_process.returncode != 0:
            return {
                "output": "",
                "error": f"C++ compilation failed: {stderr.decode().strip()}",
                "execution_time_ms": 0
            }
        
        # Execute the binary
        process = await asyncio.create_subprocess_exec(
            output_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None
        )
        
        if input_data:
            stdout, stderr = await process.communicate(input=input_data.encode())
        else:
            stdout, stderr = await process.communicate()
            
        end_time = asyncio.get_event_loop().time()
        execution_time = (end_time - start_time) * 1000
        
        output = stdout.decode().strip()
        error = stderr.decode().strip() if stderr else None
        
        return {
            "output": output,
            "error": error,
            "execution_time_ms": execution_time
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Error executing C++ code: {str(e)}",
            "execution_time_ms": 0
        }

async def _execute_go(code: str, input_data: Optional[str], temp_dir: str) -> Dict[str, Any]:
    """Execute Go code"""
    # Create Go file
    file_path = os.path.join(temp_dir, "main.go")
    with open(file_path, "w") as f:
        f.write(code)
    
    # Execute Go code
    start_time = asyncio.get_event_loop().time()
    try:
        process = await asyncio.create_subprocess_exec(
            "go", "run", file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None
        )
        
        if input_data:
            stdout, stderr = await process.communicate(input=input_data.encode())
        else:
            stdout, stderr = await process.communicate()
            
        end_time = asyncio.get_event_loop().time()
        execution_time = (end_time - start_time) * 1000
        
        output = stdout.decode().strip()
        error = stderr.decode().strip() if stderr else None
        
        return {
            "output": output,
            "error": error,
            "execution_time_ms": execution_time
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Error executing Go code: {str(e)}",
            "execution_time_ms": 0
        }
