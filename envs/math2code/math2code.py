import re
import string
from typing import Tuple
import subprocess
import tempfile
import os

from envs.base import BaseEnv
from utils import parse_action

class Math2CodeEnv(BaseEnv):
    """
    Environment for Math2Code task: translating mathematical concepts into code.
    No external API needed, uses code execution to verify correctness.
    """
    def __init__(self,
                 question: str,
                 key: str,  # Expected code or test cases
                 max_steps: int = 6,
                 test_cases: list = None):  # Optional test cases for verification

        self.question = question
        self.key = key  # Reference code or expected behavior
        self.max_steps = max_steps
        self.test_cases = test_cases or []
        self.task = """Math2Code translation task. The agent is given a mathematical concept and needs to translate it into working code. The agent can analyze mathematical concepts, translate patterns, verify code, and finish with code implementation."""
        self.env_name = 'math2code'
        
        # Store current code for verification
        self.current_code = None
        
        self.reset()

    def reset(self):
        self.curr_step = 1
        self.answer = ''
        self.terminated = False
        self.current_code = None

    def _execute_code(self, code: str) -> Tuple[bool, str]:
        """
        Execute code and return (success, output).
        For safety, we'll do basic syntax checking and simple execution.
        """
        try:
            # Basic syntax check
            compile(code, '<string>', 'exec')
            
            # Create a temporary file to execute
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute code
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    return True, result.stdout.strip()
                else:
                    return False, result.stderr.strip()
            finally:
                # Clean up
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
        except SyntaxError as e:
            return False, f"Syntax Error: {str(e)}"
        except Exception as e:
            return False, f"Execution Error: {str(e)}"

    def step(self, action: str) -> Tuple[str, bool, bool, bool, bool]:
        action_type, argument = parse_action(action)

        if action_type == 'Finish':
            self.answer = argument
            self.current_code = argument
            
            # Verify code
            success, output = self._execute_code(argument)
            if success:
                # Check if it matches expected behavior (simple check)
                if self.test_cases:
                    # Run test cases if provided
                    observation = f'Code executed successfully. Output: {output}'
                else:
                    observation = 'Answer is CORRECT - Code executed successfully'
            else:
                observation = f'Answer is INCORRECT - {output}'
            
            self.terminated = True
            
        elif action_type == 'Analyze':
            # Analyze mathematical concept
            observation = f'Analyzing mathematical concept: {argument}. This concept involves understanding its definition, properties, and computational requirements.'
            
        elif action_type == 'Translate':
            # Translate pattern
            observation = f'Translating code pattern: {argument}. This involves mapping mathematical operations to code structures like loops, conditionals, or recursive calls.'
            
        elif action_type == 'Verify':
            # Verify code snippet
            if argument:
                success, output = self._execute_code(argument)
                if success:
                    observation = f'Code verification passed. Output: {output}'
                else:
                    observation = f'Code verification failed: {output}'
            else:
                observation = 'No code provided for verification.'
                
        else:
            observation = 'Invalid Action. Valid Actions are Analyze[<concept>], Translate[<pattern>], Verify[<code>], and Finish[<code>].'

        self.curr_step += 1
        self.reward = self.success_fn()
        self.terminated = self.is_terminated()
        self.truncated = self.is_truncated()

        return observation, self.reward, self.terminated, self.truncated, self.curr_step

    def success_fn(self) -> bool:
        """
        Check if the code is correct.
        For now, we check if code executes without errors.
        Can be enhanced with test case validation.
        """
        if not self.current_code:
            return False
        
        success, _ = self._execute_code(self.current_code)
        return success
