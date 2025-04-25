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
        """Execute code against test cases and provide feedback.
        
        Args:
            input_data: Contains code, language, and test cases
            
        Returns:
            Test results and feedback
        """
        code = input_data.get("code", "")
        language = clean_language_name(input_data.get("language", "python"))
        test_cases = input_data.get("test_cases", [])
        
        if not code:
            logger.warning("No code provided for testing")
            return {
                "passed": False,
                "results": [],
                "summary": "No code provided for testing"
            }
        
        if not test_cases:
            logger.warning("No test cases provided")
            return {
                "passed": False,
                "results": [],
                "summary": "No test cases provided"
            }
        
        logger.info(f"Executing {len(test_cases)} test cases for {language} code")
        
        # Execute test cases
        test_results = await self._execute_test_cases(code, language, test_cases)
        
        # Calculate overall success
        passed_tests = sum(1 for result in test_results if result.get("passed", False))
        all_passed = passed_tests == len(test_cases)
        
        # Generate summary
        summary = f"Passed {passed_tests}/{len(test_cases)} tests."
        
        if not all_passed:
            # Generate analysis for failed tests
            failed_results = [result for result in test_results if not result.get("passed", False)]
            analysis = await self._analyze_test_failures(code, language, failed_results)
            summary += f"\n\nTest failure analysis: {analysis}"
        
        return {
            "passed": all_passed,
            "results": test_results,
            "summary": summary
        }
    
    async def _execute_test_cases(self, code: str, language: str, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the code against provided test cases.
        
        Args:
            code: The source code to execute
            language: The programming language
            test_cases: List of test cases with inputs and expected outputs
            
        Returns:
            List of test results
        """
        results = []
        
        for idx, test_case in enumerate(test_cases):
            logger.info(f"Executing test case {idx+1}")
            
            try:
                # Extract test case details
                test_input = test_case.get("input", "")
                expected_output = test_case.get("expected_output", "")
                description = test_case.get("description", f"Test case {idx+1}")
                
                # Run the code with the test input
                actual_output, execution_time, error = await self._run_code(code, language, test_input)
                
                # Determine if the test passed
                passed = False
                if not error:
                    # Compare actual output with expected output
                    passed = self._compare_outputs(actual_output, expected_output, language)
                
                # Record test result
                result = {
                    "test_case_id": idx + 1,
                    "description": description,
                    "passed": passed,
                    "execution_time_ms": execution_time,
                    "input": test_input,
                    "expected_output": expected_output,
                    "actual_output": actual_output,
                    "error": error
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error executing test case {idx+1}: {str(e)}")
                results.append({
                    "test_case_id": idx + 1,
                    "description": test_case.get("description", f"Test case {idx+1}"),
                    "passed": False,
                    "execution_time_ms": 0,
                    "input": test_case.get("input", ""),
                    "expected_output": test_case.get("expected_output", ""),
                    "actual_output": "",
                    "error": str(e)
                })
        
        return results
    
    async def _run_code(self, code: str, language: str, test_input: str) -> tuple:
        """Run code with the provided input.
        
        Args:
            code: The source code to execute
            language: Programming language
            test_input: Input for the test case
            
        Returns:
            Tuple of (output, execution_time, error)
        """
        # Create temporary files for code and input
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save code to file
            file_extension = self._get_file_extension(language)
            code_file = os.path.join(tmpdir, f"solution.{file_extension}")
            input_file = os.path.join(tmpdir, "input.txt")
            
            with open(code_file, "w") as f:
                f.write(code)
            
            with open(input_file, "w") as f:
                f.write(str(test_input))
            
            # Execute code based on language
            try:
                start_time = asyncio.get_event_loop().time()
                
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
                
                # Run the code with input
                with open(input_file, "r") as infile:
                    process = subprocess.run(
                        cmd,
                        input=infile.read(),
                        capture_output=True,
                        text=True,
                        timeout=5  # 5 second timeout for execution
                    )
                
                end_time = asyncio.get_event_loop().time()
                execution_time = (end_time - start_time) * 1000  # Convert to ms
                
                output = process.stdout.strip()
                error = process.stderr.strip() if process.returncode != 0 else ""
                
                return output, execution_time, error
                
            except subprocess.TimeoutExpired:
                return "", 5000, "Execution timed out"
            except subprocess.CalledProcessError as e:
                return "", 0, f"Execution failed: {e.stderr}"
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