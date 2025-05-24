"""
Chat Agent module for handling user interactions.

This agent serves as the main interface between users and the system, 
coordinating with other specialized agents and maintaining conversation context.
"""

from typing import List, Dict, Any, Optional
import logging
import json
import re
from .base import Agent
from .planner import PlannerAgent
from .developer import DeveloperAgent
from .researcher import ResearcherAgent
from .tester import TesterAgent
from ..services.ai_service import AIService
from ..db.models import Task
from ..db.database import get_db
from sqlalchemy.orm import Session

# Configure logging
logger = logging.getLogger("agents.chat")


class ChatAgent(Agent):
    """
    Chat agent that interacts with users, coordinates other agents,
    and maintains conversation history and context.
    """
    
    def __init__(self, ai_service: AIService):
        """Initialize the chat agent with required services and components.
        
        Args:
            ai_service: AI service for interacting with language models
        """
        super().__init__(name="ChatAgent", ai_service=ai_service)
        self.conversation_history = []
        self.context = {}
        
        # Initialize specialized agents
        self.planner = PlannerAgent(ai_service=ai_service)
        self.developer = DeveloperAgent(ai_service=ai_service)
        self.researcher = ResearcherAgent(ai_service=ai_service)
        self.tester = TesterAgent(ai_service=ai_service)
        
        logger.info("ChatAgent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user message and coordinate with specialized agents.
        
        This is the main entry point required by the Agent ABC.
        
        Args:
            input_data: Contains the user message and optional context
            
        Returns:
            Response to the user
        """
        message = input_data.get("message", "")
        task = input_data.get("task")
        return await self.process_message(message, task)
        
    async def process_message(self, message: str, task: Optional[Task] = None) -> Dict[str, Any]:
        """
        Process incoming user message and generate a response.
        
        Args:
            message: The user's message
            task: Optional Task object containing context
            
        Returns:
            Dict containing response and any actions to take
        """
        if task and hasattr(task, 'status') and task.status != "completed":
            raise ValueError("Task must be completed before processing messages")
            
        # Add message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Analyze the message to determine intent
        intent = await self._analyze_intent(message)
        logger.info(f"Detected intent: {intent}")
        
        response = {}
        
        # Route to appropriate handler based on intent
        if intent == "say_hello":
            response = await self._handle_say_hello(message)
        elif intent == "code_error":
            response = await self._handle_code_error(message, task)
        elif intent == "code_improvement":
            response = await self._handle_code_improvement(message, task)
        elif intent == "general_question":
            response = await self._handle_general_question(message, task)
        else:
            # Default handling for general chats
            response = await self._generate_general_response(message, task)
            
        # Add response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response["message"]
        })
        
        return response
    
    async def _analyze_intent(self, message: str) -> str:
        """
        Analyze the user's message to determine intent.
        
        Args:
            message: The user message to analyze
            
        Returns:
            String representing the detected intent
        """
        prompt = f"""
        Analyze the following user message and determine the intent.
        Possible intents are:
        - say_hello: User is greeting the assistant
        - code_error: User is reporting a code error or bug
        - code_improvement: User wants to improve existing code
        - general_question: User is asking a general question about programming
        
        User message: "{message}"
        
        Intent:
        """
        
        output_schema = {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [
                        "say_hello",
                        "code_error",
                        "code_improvement",
                        "general_question",
                    ]
                }
            },
            "required": ["intent"],
            "additionalProperties": False
        }
        try:
            response = await self.generate_structured_output(prompt, output_schema)
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
        
        # Extract the intent from the response
        intent = response.get("intent", "")

        if intent == "say_hello":
            return "say_hello"
        elif intent == "code_error":
            return "code_error"
        elif intent == "code_improvement":
            return "code_improvement"
        elif intent == "general_question":
            return "general_question"
        else:
            return "unknown"
        
    async def _handle_say_hello(self, message: str) -> Dict[str, Any]:
        """
        Handle greeting messages.
        
        Args:
            message: The user message
            
        Returns:
            Dict containing a friendly response
        """
        return {
            "message": "Hello! I'm your AI programming assistant. How can I help you with your code today?",
            "type": "greeting"
        }
    
    async def _handle_code_error(self, message: str, task: Optional[Task] = None) -> Dict[str, Any]:
        """
        Handle messages about code errors.
        
        Args:
            message: The user message about errors
            task: Optional task context
            
        Returns:
            Dict containing response and fixed code
        """
        try:
            requirements = task.requirements
            explanation = task.explanation
            solution = task.solution
            code = solution.get("code", "")
            approach = solution.get("approach", "")
            language = solution.get("language", "")
            best_practices = solution.get("best_practices", "")
            problem_analysis = solution.get("problem_analysis", "")

            if not all([requirements, explanation, code, approach, language, best_practices, problem_analysis]):
                raise ValueError("Task object is missing required attributes")
            
            # Enhanced output schema to get everything in one call
            enhanced_output_schema = {
                "type": "object",
                "properties": {
                    "fixed_code": {
                        "type": "string",
                        "description": "The corrected code that fixes the reported error"
                    },
                    "fix_explanation": {
                        "type": "string", 
                        "description": "Explanation of what was wrong and how it was fixed"
                    },
                    "changes_made": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of specific changes made to fix the error"
                    },
                    "updated_explanation": {
                        "type": "string",
                        "description": "Comprehensive updated explanation of the problem and the fixed solution"
                    },
                    "updated_approach": {
                        "type": "string",
                        "description": "Updated approach that reflects the fixed implementation"
                    },
                    "updated_best_practices": {
                        "type": "string",
                        "description": "Updated best practices incorporating the fixes"
                    },
                    "updated_problem_analysis": {
                        "type": "string",
                        "description": "Updated problem analysis including lessons learned from the error"
                    }
                },
                "required": ["fixed_code", "fix_explanation", "changes_made", "updated_explanation", "updated_approach", "updated_best_practices", "updated_problem_analysis"],
                "additionalProperties": False
            }

            # Enhanced prompt to generate everything at once
            enhanced_prompt = f"""
            You are an expert in programming and debugging.
            The user has reported a {language} code error. Your task is to analyze the problem, provide a fixed solution, and update ALL related documentation.

            Requirements: 
            {requirements}

            Your previous explanation of the problem: 
            {explanation}

            Your previous problem Analysis: 
            {problem_analysis}

            Your previous approach:
            {approach}

            The code that needs fixing:
            {code}

            Your previous suggested best practices:
            {best_practices}

            User's error report:
            {message}

            Please provide:
            1. A fixed version of the code that addresses the reported issue
            2. Explanation of what was wrong and how it was fixed
            3. List of specific changes made
            4. A COMPLETELY UPDATED explanation of the entire problem and solution (not just the fix)
            5. An UPDATED approach that reflects the fixed implementation
            6. UPDATED best practices that incorporate the fixes and improvements
            7. UPDATED problem analysis that includes lessons learned from the error

            Make sure all updated fields are comprehensive and reflect the current state after the fix, not just the changes.
            """

            try:
                response = await self.generate_structured_output(enhanced_prompt, enhanced_output_schema)
                  # Update the complete solution with all fields from single response
                updated_solution = solution.copy()
                updated_solution["code"] = response.get("fixed_code", code)
                updated_solution["approach"] = response.get("updated_approach", approach)
                updated_solution["best_practices"] = response.get("updated_best_practices", best_practices)
                updated_solution["problem_analysis"] = response.get("updated_problem_analysis", problem_analysis)
                
                # Get database session
                db_session = next(get_db())
                try:
                    # Update both solution and explanation
                    task.solution = updated_solution
                    task.explanation = response.get("updated_explanation", explanation)
                    db_session.commit()
                    logger.info(f"Updated complete solution and explanation for task {task.id}")
                except Exception as db_error:
                    logger.error(f"Error updating task solution: {db_error}")
                    db_session.rollback()
                finally:
                    db_session.close()
                
                return {
                    "message": response.get("fix_explanation", "Code has been fixed successfully."),
                    "type": "code_fix",
                    "fixed_code": response.get("fixed_code", code),
                    "changes_made": response.get("changes_made", []),
                    "updated_explanation": response.get("updated_explanation", explanation),
                    "updated_approach": response.get("updated_approach", approach),
                    "updated_best_practices": response.get("updated_best_practices", best_practices),
                    "updated_problem_analysis": response.get("updated_problem_analysis", problem_analysis),
                    "solution_updated": True
                }
                
            except Exception as ai_error:
                logger.error(f"Error generating code fix: {ai_error}")
                return {
                    "message": "I encountered an error while trying to fix the code. Please try again or provide more specific details about the issue.",
                    "type": "error"
                }
            
        except AttributeError:
            raise ValueError("Task object is missing required attributes")
        except Exception as e:
            logger.error(f"Error in _handle_code_error: {e}")
            return {
                "message": "I'm sorry, I couldn't process your error report. Please ensure you have a completed task and try again.",
                "type": "error"
            }
        
    async def _handle_code_improvement(self, message: str, task: Optional[Task] = None) -> Dict[str, Any]:
        """
        Handle requests to improve code.
        
        Args:
            message: The user message requesting improvements
            task: Optional task context
            
        Returns:
            Dict containing response and improved code
        """
        try:
            logger.debug(f"Handling code improvement request: {message}")
            logger.debug(f"Task context: {task}")
            if not task or not task.solution:
                return {
                    "message": "I need a completed task with existing code to provide improvements.",
                    "type": "error"
                }
            
            solution = task.solution
            code = solution.get("code", "")
            language = solution.get("language", "")
            
            # Enhanced prompt to generate everything at once
            enhanced_prompt = f"""
            You are an expert in code optimization and best practices.
            The user wants to improve the following {language} code.

            Original requirements: {task.requirements}
            Current explanation: {task.explanation}
            Current approach: {solution.get("approach", "")}
            Current best practices: {solution.get("best_practices", "")}
            Current problem analysis: {solution.get("problem_analysis", "")}

            Current code:
            {code}

            User's improvement request:
            {message}

            Please provide:
            1. An improved version of the code that addresses the user's request
            2. List of improvements made to the code
            3. Explanation of the improvements
            4. A COMPLETELY UPDATED explanation of the entire problem and improved solution
            5. An UPDATED approach that reflects the improved implementation
            6. UPDATED best practices that incorporate the improvements
            7. UPDATED problem analysis that includes the enhancement insights

            Focus on code quality, performance, readability, and best practices.
            Make sure all updated fields are comprehensive and reflect the current state after improvements, not just the changes.
            """
            
            # Enhanced output schema to get everything in one call
            enhanced_output_schema = {
                "type": "object",
                "properties": {
                    "improved_code": {
                        "type": "string",
                        "description": "The improved version of the code"
                    },
                    "improvements_made": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of improvements made to the code"
                    },
                    "improvement_explanation": {
                        "type": "string",
                        "description": "Explanation of the improvements"
                    },
                    "updated_explanation": {
                        "type": "string",
                        "description": "Comprehensive updated explanation of the problem and the improved solution"
                    },
                    "updated_approach": {
                        "type": "string",
                        "description": "Updated approach that reflects the improved implementation"
                    },
                    "updated_best_practices": {
                        "type": "string",
                        "description": "Updated best practices incorporating the improvements"
                    },
                    "updated_problem_analysis": {
                        "type": "string",
                        "description": "Updated problem analysis including enhancement insights"
                    }
                },
                "required": ["improved_code", "improvements_made", "improvement_explanation", "updated_explanation", "updated_approach", "updated_best_practices", "updated_problem_analysis"],
                "additionalProperties": False
            }

            try:
                response = await self.generate_structured_output(enhanced_prompt, enhanced_output_schema)
                  # Update the complete solution with all fields from single response
                updated_solution = solution.copy()
                updated_solution["code"] = response.get("improved_code", code)
                updated_solution["approach"] = response.get("updated_approach", solution.get("approach", ""))
                updated_solution["best_practices"] = response.get("updated_best_practices", solution.get("best_practices", ""))
                updated_solution["problem_analysis"] = response.get("updated_problem_analysis", solution.get("problem_analysis", ""))
                
                db_session = next(get_db())
                try:
                    # Update both solution and explanation
                    task.solution = updated_solution
                    task.explanation = response.get("updated_explanation", task.explanation)
                    db_session.commit()
                    logger.info(f"Updated complete solution and explanation for task {task.id}")
                except Exception as db_error:
                    logger.error(f"Error updating task solution: {db_error}")
                    db_session.rollback()
                finally:
                    db_session.close()
                
                return {
                    "message": response.get("improvement_explanation", "Code has been improved successfully."),
                    "type": "code_improvement",
                    "improved_code": response.get("improved_code", code),
                    "improvements_made": response.get("improvements_made", []),
                    "updated_explanation": response.get("updated_explanation", task.explanation),
                    "updated_approach": response.get("updated_approach", solution.get("approach", "")),
                    "updated_best_practices": response.get("updated_best_practices", solution.get("best_practices", "")),
                    "updated_problem_analysis": response.get("updated_problem_analysis", solution.get("problem_analysis", "")),
                    "solution_updated": True
                }
                
            except Exception as ai_error:
                logger.error(f"Error generating code improvement: {ai_error}")
                return {
                    "message": "I encountered an error while trying to improve the code. Please try again.",
                    "type": "error"
                }
                
        except Exception as e:
            logger.error(f"Error in _handle_code_improvement: {e}")
            return {
                "message": "I'm sorry, I couldn't process your improvement request. Please try again.",
                "type": "error"
            }
        
    async def _handle_general_question(self, message: str, task: Optional[Task] = None) -> Dict[str, Any]:
        """
        Handle general programming questions.
        
        Args:
            message: The user's question
            task: Optional task context
            
        Returns:
            Dict containing response
        """
        try:
            context = ""
            if task and task.solution:
                solution = task.solution
                context = f"""
                Context: I'm working on a {solution.get('language', 'programming')} solution.
                Current code: {solution.get('code', 'No code available')}
                Problem: {task.requirements or 'No requirements available'}
                """
            
            prompt = f"""
            You are a helpful programming assistant. Answer the user's question clearly and concisely.
            
            {context}
            
            User's question: {message}
            
            Provide a helpful and informative response.
            """
            
            try:
                response = await self.ai_service.generate_text(prompt)
                
                return {
                    "message": response,
                    "type": "general_answer"
                }
                
            except Exception as ai_error:
                logger.error(f"Error generating response: {ai_error}")
                return {
                    "message": "I encountered an error while processing your question. Please try again.",
                    "type": "error"
                }
                
        except Exception as e:
            logger.error(f"Error in _handle_general_question: {e}")
            return {
                "message": "I'm sorry, I couldn't process your question. Please try again.",
                "type": "error"
            }
        
    async def _generate_general_response(self, message: str, task: Optional[Task] = None) -> Dict[str, Any]:
        """
        Generate a general response for other types of messages.
        
        Args:
            message: The user's message
            task: Optional task context
            
        Returns:
            Dict containing response
        """
        try:
            context = ""
            if task and task.solution:
                solution = task.solution
                context = f"I'm currently working on a {solution.get('language', 'programming')} solution. "
            
            prompt = f"""
            You are a friendly and helpful AI programming assistant.
            {context}
            
            User message: {message}
            
            Provide a helpful and engaging response. If the message is unclear or you're not sure how to help,
            ask clarifying questions or suggest what you can do to assist.
            """
            
            try:
                response = await self.ai_service.generate_text(prompt)
                
                return {
                    "message": response,
                    "type": "general_chat"
                }
                
            except Exception as ai_error:
                logger.error(f"Error generating general response: {ai_error}")
                return {
                    "message": "I'm here to help with your programming tasks. Feel free to ask me about code errors, improvements, or general programming questions!",
                    "type": "general_chat"
                }
                
        except Exception as e:
            logger.error(f"Error in _generate_general_response: {e}")
            return {
                "message": "I'm here to help! How can I assist you with your programming today?",
                "type": "general_chat"
            }


