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
logger = logging.getLogger("agents.test_executor")


class TestExecutionAgent(Agent):
    """Agent responsible for executing code against test cases and providing feedback."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the Test Execution Agent.
        
        Args:
            ai_service: AI service for interacting with language models
        """
        super().__init__(name="TestExecutionAgent", ai_service=ai_service)
    
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
                "passed": False,
                "results": [],
                "summary": "No code provided for testing"
            }
        
        # For combined solution+test code, we run the entire file at once
        logger.info("Executing combined solution and test code")
        output, execution_time, error = await self._run_code(code, language)
        
        # Process the test output results
        passed = False
        results = []
        
        if error:
            # If there's an error, the tests didn't pass
            logger.error(f"Error executing tests: {error}")
            return {
                "passed": False,
                "results": [],
                "summary": f"Error executing tests: {error}"
            }
        
        # Parse the output to extract test results
        # This parsing depends on how test results are printed in the combined code
        test_results = self._parse_test_output(output)
        
        # Calculate success rate
        passed_tests = sum(1 for result in test_results if result.get("passed", False))
        total_tests = len(test_results)
        all_passed = total_tests > 0 and passed_tests == total_tests
        
        # Generate summary
        if total_tests > 0:
            summary = f"Passed {passed_tests}/{total_tests} tests."
        else:
            summary = "No test results could be parsed from output."
            
        # If tests failed, analyze the failures
        if not all_passed and test_results:
            failed_results = [result for result in test_results if not result.get("passed", False)]
            analysis = await self._analyze_test_failures(code, language, failed_results)
            summary += f"\n\nTest failure analysis: {analysis}"
        
        return {
            "passed": all_passed,
            "results": test_results,
            "summary": summary,
            "raw_output": output  # Include raw output for debugging
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
                # Thường thì unittest xuất ra stderr, nhưng kết hợp cả hai là an toàn nhất
                combined_output = stdout_content + stderr_content 
                
                # Xác định lỗi thực thi thực sự
                execution_error = ""
                if process.returncode != 0:
                    # Nếu có lỗi trả về, stderr có thể chứa thông tin lỗi hữu ích
                    execution_error = f"Process exited with code {process.returncode}. Stderr: {stderr_content.strip()}"
                # ---- KẾT THÚC SỬA ĐỔI ----

                # Cập nhật logging để phản ánh sự thay đổi
                logger.info(f"Raw stdout: {stdout_content[:500]}..." if len(stdout_content) > 500 else f"Raw stdout: {stdout_content}")
                logger.info(f"Raw stderr: {stderr_content[:500]}..." if len(stderr_content) > 500 else f"Raw stderr: {stderr_content}")
                logger.info(f"Combined output for parsing (first 1000 chars): {combined_output[:1000]}...")
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
    
    def _compare_outputs(self, actual: str, expected: str, language: str) -> bool:
        """Compare actual output with expected output.
        
        Args:
            actual: Actual output from code execution
            expected: Expected output from test case
            language: Programming language (for language-specific comparisons)
            
        Returns:
            True if outputs match, False otherwise
        """
        # Clean and normalize outputs
        actual = actual.strip()
        expected = expected.strip()
        
        # Try exact string comparison first
        if actual == expected:
            return True
        
        # Try numeric comparison if both can be converted to numbers
        try:
            actual_num = float(actual)
            expected_num = float(expected)
            # Allow small floating point differences
            if abs(actual_num - expected_num) < 1e-9:
                return True
        except ValueError:
            pass
        
        # Try JSON comparison if both are valid JSON
        try:
            actual_json = json.loads(actual)
            expected_json = json.loads(expected)
            return actual_json == expected_json
        except json.JSONDecodeError:
            pass
        
        # Compare ignoring whitespace and case
        if actual.lower().replace(" ", "") == expected.lower().replace(" ", ""):
            return True
        
        # If all comparisons fail, outputs don't match
        return False
    
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
        example_pattern = r"Example[s]?[\s\d]*:[\s\n]*(Input[\s\n]*:[\s\n]*(.+?)[\s\n]*Output[\s\n]*:[\s\n]*(.+?)(?=Example|$))"
        example_matches = re.finditer(example_pattern, requirements, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(example_matches):
            test_cases.append({
                "description": f"Example {i+1}",
                "input": match.group(2).strip(),
                "expected_output": match.group(3).strip()
            })
        
        # Test case pattern with "=>"
        test_case_pattern = r"Test Case[\s\d]*:[\s\n]*(.+?)[\s\n]*=>[\s\n]*(.+?)[\s\n]*(?=Test Case|$)"
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
    
    def _parse_test_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse test results from the output of the combined solution and test code.
        
        Args:
            output: The raw output from running the test script
            
        Returns:
            List of parsed test results
        """
        results = []
        
        # Log the full output for debugging
        logger.info(f"Generated code for testing in python:\n{output}")
        
        # Combine stdout and stderr for parsing unittest results
        combined_output = output
        
        # Extract information from unittest output format
        # Check for "Ran X tests in Y.ZZZs"
        unittest_pattern = r"Ran (\d+) tests? in [0-9.]+s"
        unittest_match = re.search(unittest_pattern, combined_output)
        
        if unittest_match:
            test_count = int(unittest_match.group(1))
            logger.info(f"Found unittest results: {test_count} tests ran")
            
            # Check if tests passed or failed
            if "OK" in combined_output:
                # All tests passed
                results = [{
                    "test_case_id": i+1,
                    "description": f"Test {i+1}",
                    "passed": True,
                    "execution_time_ms": 0,
                    "input": "N/A",
                    "expected_output": "N/A",
                    "actual_output": "N/A",
                    "error": ""
                } for i in range(test_count)]
            else:
                # Some tests failed
                # Extract failure information
                # Look for patterns like: FAIL: test_name or "test_name (__main__.TestZigzagConversion) ... FAIL"
                failure_pattern = r"(?:FAIL|ERROR): ([^\(]+)|([a-zA-Z0-9_]+) \([^)]+\) \.\.\. (?:FAIL|ERROR)"
                failures = re.finditer(failure_pattern, combined_output)
                
                # Keep track of failed test names
                failed_tests = set()
                for match in failures:
                    failed_test_name = match.group(1) if match.group(1) else match.group(2)
                    if failed_test_name:
                        failed_tests.add(failed_test_name.strip())
                
                # If we couldn't extract any failed tests but know there were failures
                if not failed_tests and "FAILED" in combined_output:
                    failure_count_pattern = r"failures=(\d+)"
                    failure_count_match = re.search(failure_count_pattern, combined_output)
                    failure_count = int(failure_count_match.group(1)) if failure_count_match else 0
                    
                    error_count_pattern = r"errors=(\d+)"
                    error_count_match = re.search(error_count_pattern, combined_output)
                    error_count = int(error_count_match.group(1)) if error_count_match else 0
                    
                    failed_test_count = failure_count + error_count
                else:
                    failed_test_count = len(failed_tests)
                
                # Calculate passed tests
                passed_test_count = test_count - failed_test_count
                
                # Extract traceback details for failed tests
                test_case_pattern = r"FAIL: ([^\n]+).*?Traceback.*?\n.*?self\.assertEqual\([^)]+\).*?AssertionError: '([^']+)' != '([^']+)'"
                test_details = re.finditer(test_case_pattern, combined_output, re.DOTALL)
                
                # Add detailed results for failed tests
                for i, match in enumerate(test_details):
                    test_name = match.group(1).strip()
                    actual_output = match.group(2)
                    expected_output = match.group(3)
                    
                    results.append({
                        "test_case_id": i + 1,
                        "description": test_name,
                        "passed": False,
                        "execution_time_ms": 0,
                        "input": "See test case",
                        "expected_output": expected_output,
                        "actual_output": actual_output,
                        "error": f"Expected: {expected_output}, Got: {actual_output}"
                    })
                
                # Add a result for passed tests
                if passed_test_count > 0:
                    results.append({
                        "test_case_id": len(results) + 1,
                        "description": f"{passed_test_count} passed tests",
                        "passed": True,
                        "execution_time_ms": 0,
                        "input": "Various inputs",
                        "expected_output": "As expected",
                        "actual_output": "As expected",
                        "error": ""
                    })
                
                # If we couldn't extract detailed information but we know how many failed
                if not results:
                    # Add a generic result for failed tests
                    if failed_test_count > 0:
                        results.append({
                            "test_case_id": 1,
                            "description": f"{failed_test_count} tests failed",
                            "passed": False,
                            "execution_time_ms": 0,
                            "input": "N/A",
                            "expected_output": "N/A",
                            "actual_output": "See error",
                            "error": combined_output
                        })
                    
                    # Add a generic result for passed tests
                    if passed_test_count > 0:
                        results.append({
                            "test_case_id": 2 if failed_test_count > 0 else 1,
                            "description": f"{passed_test_count} tests passed",
                            "passed": True,
                            "execution_time_ms": 0,
                            "input": "N/A",
                            "expected_output": "N/A",
                            "actual_output": "N/A",
                            "error": ""
                        })
            
            return results
        
        # If no unittest results were found, try other formats
        # ...existing code for other formats...
        
        # Look for custom formatted test results
        custom_result_pattern = r"TEST RESULT: (PASS|FAIL) - ([^-]+) - Input: (.*?), Expected: (.*?), Got: (.*?)(?:\n|$)"
        custom_matches = re.finditer(custom_result_pattern, combined_output)
        
        custom_results = []
        for i, match in enumerate(custom_matches):
            status = match.group(1)
            description = match.group(2).strip()
            test_input = match.group(3).strip()
            expected = match.group(4).strip()
            actual = match.group(5).strip()
            
            custom_results.append({
                "test_case_id": i + 1,
                "description": description,
                "passed": status == "PASS",
                "execution_time_ms": 0,
                "input": test_input,
                "expected_output": expected,
                "actual_output": actual,
                "error": "" if status == "PASS" else f"Expected: {expected}, Got: {actual}"
            })
            
        if custom_results:
            return custom_results
        
        # If we still couldn't extract results, look for pass/fail counts
        if not results:
            pass_count = output.count("PASS")
            fail_count = output.count("FAIL")
            
            if pass_count > 0 or fail_count > 0:
                results = []
                
                if fail_count > 0:
                    results.append({
                        "test_case_id": 1,
                        "description": f"{fail_count} failed tests",
                        "passed": False,
                        "execution_time_ms": 0,
                        "input": "N/A",
                        "expected_output": "All tests should pass",
                        "actual_output": combined_output,
                        "error": f"{fail_count} tests failed"
                    })
                
                if pass_count > 0:
                    results.append({
                        "test_case_id": 2 if fail_count > 0 else 1,
                        "description": f"{pass_count} passed tests",
                        "passed": True,
                        "execution_time_ms": 0,
                        "input": "N/A",
                        "expected_output": "N/A",
                        "actual_output": "N/A",
                        "error": ""
                    })
        
        # If no structured test results found at all
        if not results:
            results.append({
                "test_case_id": 1,
                "description": "Test execution",
                "passed": "failed" not in combined_output.lower() and "error" not in combined_output.lower(),
                "execution_time_ms": 0,
                "input": "N/A",
                "expected_output": "N/A",
                "actual_output": combined_output,
                "error": ""
            })
        
        return results