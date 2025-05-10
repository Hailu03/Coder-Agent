"""Test Execution Agent module for the Collaborative Coding Agents application.

This module defines the Test Execution Agent that executes code against test cases
and provides feedback on test results.
"""

import logging
import json
import re
import subprocess
import tempfile
import os
import sys
import asyncio
from typing import Dict, List, Any, Optional

from .base import Agent
from ..services.ai_service import AIService
from ..utils import clean_language_name

# Configure logging
logger = logging.getLogger("agents.tester")


class TesterAgent(Agent):
    """Agent responsible for executing code against test cases and providing feedback."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the Test Execution Agent.
        
        Args:
            ai_service: AI service for interacting with language models
        """
        super().__init__(name="TesterAgent", ai_service=ai_service)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code that contains both solution and test cases.
        
        Args:
            input_data: Contains code and language
            
        Returns:
            Test results and feedback
        """
        code = input_data.get("code", "")
        language = clean_language_name(input_data.get("language", "python"))
        logger.info(f"Generated code for testing in {language}:\n\n {code}")
        
        if not code:
            logger.warning("No code provided for testing")
            return {
                "output": "No code provided",
                "summary": "No test cases provided",
                "time": "",
                "error": ""
            }
        
        # For combined solution+test code, we run the entire file at once
        logger.info("Executing combined solution and test code")
        output, execution_time, error = await self._run_code(code, language)

        # Kiểm tra cả lỗi thực thi và kết quả test failed
        if "FAILED" in output or error:
            # Trường hợp ModuleNotFoundError, gợi ý cài đặt package
            if "ModuleNotFoundError" in error:
                module_match = re.search(r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]", error)
                if module_match:
                    missing_module = module_match.group(1)
                    summary = f"Thiếu thư viện: {missing_module}. Hãy cài đặt bằng lệnh 'pip install {missing_module}'."
                else:
                    summary = f"Thiếu thư viện. Hãy cài đặt thư viện cần thiết: {error}"
            else:
                # Phân tích lỗi test thông thường
                summary = await self._analyze_test_failures(code, language, output) if "FAILED" in output else error
            isPass = False
        else:
            summary = "All tests passed."
            isPass = True
        logger.info(f"Summary: {summary}")
        
        return {
            "passed": isPass,
            "output": output.strip(),
            "summary": summary,
            "time": execution_time,
            "error": error
        }
    
    async def _run_code(self, code: str, language: str) -> tuple:
        """Run code with the provided input.
        
        Args:
            code: The source code to execute
            language: Programming language
            test_input: Input for the test case (optional)
            
        Returns:
            Tuple of (output, execution_time, error)
        """
        # Create temporary files for code and input
        with tempfile.TemporaryDirectory() as tmpdir:
            start_time = asyncio.get_event_loop().time()
            
            # Save code to file
            file_extension = self._get_file_extension(language)
            code_file = os.path.join(tmpdir, f"solution.{file_extension}")
            
            with open(code_file, "w") as f:
                f.write(code)
            
            # Execute code based on language
            try:
                if language == "python":
                    cmd = [sys.executable, code_file]
                elif language in ["javascript", "nodejs"]:
                    cmd = ["node", code_file]
                elif language == "java":
                    # Compile first
                    subprocess.run(["javac", code_file], check=True, timeout=10)
                    class_name = "Solution"  # Assume main class is Solution
                    cmd = ["java", "-cp", tmpdir, class_name]
                elif language in ["c", "cpp", "c++"]:
                    output_exe = os.path.join(tmpdir, "solution")
                    if language == "c":
                        subprocess.run(["gcc", code_file, "-o", output_exe], check=True, timeout=10)
                    else:
                        subprocess.run(["g++", code_file, "-o", output_exe], check=True, timeout=10)
                    cmd = [output_exe]
                else:
                    # Default to Python for unknown languages
                    cmd = [sys.executable, code_file]
        
                # Run without input for self-contained test scripts
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10  # 10 second timeout for test execution
                )
                    
                end_time = asyncio.get_event_loop().time()
                execution_time = (end_time - start_time) * 1000  # Convert to ms

                logger.info(f"Process: {process}")

                # Lấy cả stdout và stderr
                stdout_content = process.stdout if process.stdout else ""
                stderr_content = process.stderr if process.stderr else ""
                
                # Kết hợp stdout và stderr để phân tích cú pháp
                combined_output = stdout_content + stderr_content
                
                # Kiểm tra lỗi thiếu module/package theo từng ngôn ngữ
                if process.returncode != 0:
                    # Python - ModuleNotFoundError
                    if language.lower() in ["python", "py"] and "ModuleNotFoundError" in stderr_content:
                        module_match = re.search(r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]", stderr_content)
                        if module_match:
                            missing_module = module_match.group(1)
                            logger.info(f"Đã phát hiện module Python thiếu: {missing_module}. Thử cài đặt...")
                            success, message = self._install_missing_module(missing_module, language)
                            
                            if success:
                                logger.info(f"Đã cài đặt thành công {missing_module}, chạy lại code...")
                                process = subprocess.run(
                                    cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )
                                # Cập nhật kết quả đầu ra
                                stdout_content = process.stdout if process.stdout else ""
                                stderr_content = process.stderr if process.stderr else ""
                                combined_output = stdout_content + stderr_content
                    
                    # JavaScript/Node.js - Cannot find module
                    elif language.lower() in ["javascript", "js", "nodejs", "node"] and "Cannot find module" in stderr_content:
                        module_match = re.search(r"Cannot find module ['\"]([^'\"]+)['\"]", stderr_content)
                        if module_match:
                            missing_module = module_match.group(1)
                            logger.info(f"Đã phát hiện package Node.js thiếu: {missing_module}. Thử cài đặt...")
                            success, message = self._install_missing_module(missing_module, language)
                            
                            if success:
                                logger.info(f"Đã cài đặt thành công {missing_module}, chạy lại code...")
                                process = subprocess.run(
                                    cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )
                                # Cập nhật kết quả đầu ra
                                stdout_content = process.stdout if process.stdout else ""
                                stderr_content = process.stderr if process.stderr else ""
                                combined_output = stdout_content + stderr_content
                    
                    # Java - ClassNotFoundException/NoClassDefFoundError
                    elif language.lower() == "java" and ("ClassNotFoundException" in stderr_content or "NoClassDefFoundError" in stderr_content):
                        class_match = re.search(r"(ClassNotFoundException|NoClassDefFoundError): ([A-Za-z0-9_.]+)", stderr_content)
                        if class_match:
                            missing_class = class_match.group(2)
                            logger.info(f"Đã phát hiện class Java thiếu: {missing_class}. Cố gắng xác định package...")
                            
                            # Cố gắng xác định package tương ứng (có thể không chính xác và cần AI để gợi ý)
                            # Giả sử format: org.example.package.ClassName -> org.example.package
                            parts = missing_class.split('.')
                            if len(parts) > 1:
                                potential_package = '.'.join(parts[:-1])
                                logger.info(f"Thử cài đặt package: {potential_package}")
                                success, message = self._install_missing_module(potential_package, language)
                                
                                if success:
                                    # Chạy lại nếu thành công
                                    process = subprocess.run(
                                        cmd,
                                        capture_output=True, 
                                        text=True,
                                        timeout=10
                                    )
                                    stdout_content = process.stdout if process.stdout else ""
                                    stderr_content = process.stderr if process.stderr else ""
                                    combined_output = stdout_content + stderr_content
                
                # Xác định lỗi thực thi thực sự
                execution_error = ""
                if process.returncode != 0:
                    # Nếu có lỗi trả về, stderr có thể chứa thông tin lỗi hữu ích
                    execution_error = f"Process exited with code {process.returncode}. Stderr: {stderr_content.strip()}"

                # Cập nhật logging để phản ánh sự thay đổi
                logger.info(f"Test Results:\n {combined_output[:500]}...")
                logger.info(f"Execution time: {execution_time} ms")
                if execution_error:
                    logger.error(f"Execution Error: {execution_error}")

                # Trả về output kết hợp và lỗi thực thi (nếu có)
                return combined_output.strip(), execution_time, execution_error
                
            except subprocess.TimeoutExpired:
                return "", 10000, "Execution timed out after 10 seconds"
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                return "", 0, f"Execution failed: {error_msg}"
            except Exception as e:
                return "", 0, f"Error: {str(e)}"
            
    async def _generate_test_cases_code(self, requirements: str, code: str, language: str) -> str:
        """Generate a complete test script with solution code and test cases.
        
        Args:
            requirements: The problem requirements 
            code: The generated code solution
            language: The programming language
            
        Returns:
            A complete test script with solution code and test cases
        """
        logger.info(f"Generating test cases for the {language} code solution")

        # First extract any explicit test cases from the requirements
        test_cases = self._extract_test_cases_from_requirements(requirements)
        logger.info(f"Test cases extracted:\n {test_cases}")
        
        try:
            # Prepare language-specific instructions for testing
            if language.lower() in ["python", "py"]:
                test_framework = "unittest framework"
                file_description = "Python script"
            elif language.lower() in ["javascript", "js", "node", "nodejs"]:
                test_framework = "Jest or Mocha testing framework"
                file_description = "JavaScript file"
            elif language.lower() == "java":
                test_framework = "JUnit framework" 
                file_description = "Java file"
            elif language.lower() in ["c", "cpp", "c++"]:
                test_framework = "testing code using assertions"
                file_description = f"{language} file"
            else:
                # Default to Python for unknown languages
                test_framework = "testing framework appropriate for the language"
                file_description = f"{language} code file"
                
            # Prepare a prompt for the AI to generate a complete test script
            prompt = f"""
            Based on the following problem requirements and solution code, create a complete executable test script.
            
            REQUIREMENTS:
            {requirements}
            
            CODE SOLUTION:
            ```{language}
            {code}
            ```
            
            Create a SINGLE self-contained {file_description} that:
            1. First defines the solution code exactly as provided above
            2. Then defines a {test_framework} to test the solution 
            3. Creates test cases including the following extracted from requirements: 
            {test_cases}
            4. Adds additional test cases to cover edge cases and special situations
            5. Has a main section that runs all tests and reports success/failure for each test
            6. Prints clear output showing test results, expected vs actual values, and any errors
            
            The output should be formatted to help identify:
            - Which test failed
            - What was expected vs what was received
            - Helpful error messages explaining potential bugs
            
            The script should be 100% runnable as-is with no dependencies outside the standard library.
            
            Format your response as a single {file_description} with no additional text or markdown.
            """
            
            # Generate the complete test script using AI service
            complete_test_script = await self.ai_service.generate_text(prompt)
            
            # Clean up the response to ensure it's just the code
            markdown_pattern = f"```{language}"
            if markdown_pattern.lower() in complete_test_script.lower():
                # Look for language-specific code block
                start_idx = re.search(f"```{language}", complete_test_script, re.IGNORECASE)
                if start_idx:
                    start = start_idx.end()
                else:
                    start = complete_test_script.find("```") + 3
            elif "```" in complete_test_script:
                start = complete_test_script.find("```") + 3
            else:
                start = 0
                
            end = complete_test_script.rfind("```")
            if end != -1:
                complete_test_script = complete_test_script[start:end].strip()
            else:
                complete_test_script = complete_test_script[start:].strip()
                
            return complete_test_script

        except Exception as e:
            logger.error(f"Error generating complete test script: {str(e)}")
            # Return a basic test with just the solution code
            return f"// Solution code for {language}\n{code}\n\n// Basic test runner\nconsole.log('Error generating test cases')" if language.lower() in ["javascript", "js"] else f"# Solution code\n{code}\n\n# Basic test runner\nif __name__ == '__main__':\n    print('Error generating test cases')"
    
    async def _analyze_test_failures(self, code: str, language: str, failed_results: List[Dict[str, Any]]) -> str:
        """Analyze failed test cases and provide insights.
        
        Args:
            code: The source code
            language: Programming language
            failed_results: List of failed test results
            
        Returns:
            Analysis of test failures
        """
        if not failed_results:
            return "All tests passed."
        
        prompt = f"""
        As a code testing expert, analyze the following code and test failures in {language}:
        
        CODE:
        ```{language}
        {code}
        ```
        
        FAILED TEST CASES:
        {json.dumps(failed_results, indent=2)}
        
        Please provide a concise analysis of:
        1. The root cause of the failures
        2. Specific issues in the code
        3. Suggestions for fixing the problems
        
        Keep your analysis brief and focused on the key issues.
        """
        
        analysis = await self.generate_text(prompt)
        return analysis
    
    def _extract_test_cases_from_requirements(self, requirements: str) -> List[Dict[str, Any]]:
        """Extract test cases from requirements text.
        
        Args:
            requirements: Requirements text
            
        Returns:
            List of extracted test cases
        """
        test_cases = []
        
        # Common test case patterns
        # Cải thiện mẫu regex để chỉ lấy kết quả thực tế, không bao gồm phần giải thích
        example_pattern = r"Example[s]?[\s\d]*:[\s\n]*(Input[\s\n]*:[\s\n]*(.+?)[\s\n]*Output[\s\n]*:[\s\n]*([^\n\r]+))"
        example_matches = re.finditer(example_pattern, requirements, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(example_matches):
            test_cases.append({
                "description": f"Example {i+1}",
                "input": match.group(2).strip(),
                "expected_output": match.group(3).strip()
            })
        
        # Test case pattern with "=>"
        test_case_pattern = r"Test Case[\s\d]*:[\s\n]*(.+?)[\s\n]*=>[\s\n]*([^\n\r]+)"
        test_case_matches = re.finditer(test_case_pattern, requirements, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(test_case_matches):
            test_cases.append({
                "description": f"Test Case {i+1}",
                "input": match.group(1).strip(),
                "expected_output": match.group(2).strip()
            })
        
        return test_cases
    
    def _get_file_extension(self, language: str) -> str:
        """Get the file extension for a given programming language.
        
        Args:
            language: The programming language
            
        Returns:
            The file extension
        """
        extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "java": "java",
            "c#": "cs",
            "c++": "cpp",
            "c": "c",
            "go": "go",
            "ruby": "rb",
            "php": "php",
            "swift": "swift",
            "kotlin": "kt",
            "rust": "rs",
            "scala": "scala"
        }
        
        return extensions.get(language.lower(), "txt")
        
    def _install_missing_module(self, module_name: str, language: str = "python") -> tuple:
        """Cài đặt module/package/thư viện thiếu.
        
        Args:
            module_name: Tên module cần cài đặt
            language: Ngôn ngữ lập trình (python, javascript, java, v.v.)
            
        Returns:
            Tuple (success, message)
        """
        logger.info(f"Đang thử cài đặt thư viện thiếu cho {language}: {module_name}")
        try:
            # Xử lý theo từng ngôn ngữ
            if language.lower() in ["python", "py"]:
                # Cài đặt package bằng pip
                process = subprocess.run(
                    [sys.executable, "-m", "pip", "install", module_name],
                    capture_output=True,
                    text=True,
                    timeout=120  # Cho phép 2 phút để cài đặt
                )
                
            elif language.lower() in ["javascript", "js", "nodejs", "node"]:
                # Cài đặt package bằng npm
                process = subprocess.run(
                    ["npm", "install", module_name],
                    capture_output=True,
                    text=True,
                    timeout=180  # NPM có thể mất nhiều thời gian hơn
                )
                
            elif language.lower() == "java":
                # Java không có trình quản lý gói trực tiếp như Python/Node
                # Nhưng chúng ta có thể xử lý với Maven nếu có file pom.xml
                if os.path.exists("pom.xml"):
                    # Trường hợp dùng Maven
                    process = subprocess.run(
                        ["mvn", "dependency:get", f"-Dartifact=:{module_name}:RELEASE"],
                        capture_output=True,
                        text=True,
                        timeout=180
                    )
                else:
                    return False, f"Không thể tự động cài đặt {module_name} cho Java. Hãy thêm thư viện vào classpath."
                
            else:
                return False, f"Không hỗ trợ cài đặt tự động cho ngôn ngữ {language}. Vui lòng cài đặt {module_name} thủ công."
            
            if process.returncode == 0:
                logger.info(f"Đã cài đặt thành công: {module_name}")
                return True, f"Đã cài đặt thành công: {module_name}"
            else:
                logger.error(f"Không thể cài đặt {module_name}: {process.stderr}")
                return False, f"Không thể cài đặt {module_name}: {process.stderr}"
                
        except Exception as e:
            logger.error(f"Lỗi khi cài đặt {module_name}: {str(e)}")
            return False, f"Lỗi khi cài đặt {module_name}: {str(e)}"