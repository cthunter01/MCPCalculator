"""
Input validation and sanitization module for BC Calculator
Prevents command injection and ensures safe input to BC
"""

import re
from typing import Pattern

from .types import ValidationResult


class InputValidator:
    """Validator for BC calculator expressions with security checks"""
    
    # Maximum expression length (10KB)
    MAX_LENGTH: int = 10000
    
    # Allowed characters: numbers, letters, math operators, BC syntax
    ALLOWED_CHARS: Pattern[str] = re.compile(r'^[0-9a-zA-Z+\-*/^().,;\s=<>!&|%{}\[\]]+$')
    
    # Dangerous patterns that could lead to command injection or system abuse
    DANGEROUS_PATTERNS: list[Pattern[str]] = [
        re.compile(r'system\s*\(', re.IGNORECASE),  # system() calls
        re.compile(r'exec\s*\(', re.IGNORECASE),    # exec() calls
        re.compile(r'`'),                            # Backticks (command substitution)
        re.compile(r'\$\('),                         # Command substitution
        re.compile(r'>\s*[/\w]'),                    # File redirects (output)
        re.compile(r'<\s*[/\w]'),                    # File redirects (input)
        re.compile(r'\|\s*[/\w]'),                   # Pipes to other commands
        re.compile(r';\s*(?:bash|sh|rm|cat|ls|pwd|chmod|chown)', re.IGNORECASE),  # Dangerous shell commands
    ]
    
    @classmethod
    def validate(cls, expression: str) -> ValidationResult:
        """
        Validate an expression for safety and correctness
        
        Args:
            expression: The expression to validate
            
        Returns:
            ValidationResult with validation status and optional error message
        """
        # 1. Check for null/undefined/empty
        if not expression:
            return ValidationResult(
                valid=False,
                error="Expression cannot be null or empty"
            )
        
        # 2. Check length
        if len(expression) > cls.MAX_LENGTH:
            return ValidationResult(
                valid=False,
                error=f"Expression too long (max {cls.MAX_LENGTH} characters, got {len(expression)})"
            )
        
        # 3. Check for empty input after trimming
        trimmed = expression.strip()
        if not trimmed:
            return ValidationResult(
                valid=False,
                error="Expression cannot be empty"
            )
        
        # 4. Check allowed characters
        if not cls.ALLOWED_CHARS.match(trimmed):
            return ValidationResult(
                valid=False,
                error="Expression contains invalid characters. Only alphanumeric characters and mathematical operators are allowed."
            )
        
        # 5. Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(trimmed):
                return ValidationResult(
                    valid=False,
                    error="Expression contains disallowed patterns that could be unsafe"
                )
        
        # 6. Basic BC syntax validation
        validation = cls._validate_bc_syntax(trimmed)
        if not validation.valid:
            return validation
        
        return ValidationResult(
            valid=True,
            sanitized=trimmed
        )
    
    @classmethod
    def _validate_bc_syntax(cls, expression: str) -> ValidationResult:
        """
        Perform basic BC syntax validation
        
        Args:
            expression: The expression to validate
            
        Returns:
            ValidationResult
        """
        # Check for balanced parentheses, braces, and brackets
        paren_count = 0
        brace_count = 0
        bracket_count = 0
        
        for char in expression:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            
            # Check for negative counts (closing before opening)
            if paren_count < 0:
                return ValidationResult(
                    valid=False,
                    error="Unbalanced parentheses: closing parenthesis before opening"
                )
            if brace_count < 0:
                return ValidationResult(
                    valid=False,
                    error="Unbalanced braces: closing brace before opening"
                )
            if bracket_count < 0:
                return ValidationResult(
                    valid=False,
                    error="Unbalanced brackets: closing bracket before opening"
                )
        
        # Check final counts
        if paren_count != 0:
            return ValidationResult(
                valid=False,
                error=f"Unbalanced parentheses: {'missing closing' if paren_count > 0 else 'extra closing'} parenthesis"
            )
        if brace_count != 0:
            return ValidationResult(
                valid=False,
                error=f"Unbalanced braces: {'missing closing' if brace_count > 0 else 'extra closing'} brace"
            )
        if bracket_count != 0:
            return ValidationResult(
                valid=False,
                error=f"Unbalanced brackets: {'missing closing' if bracket_count > 0 else 'extra closing'} bracket"
            )
        
        return ValidationResult(valid=True)
    
    @classmethod
    def sanitize(cls, expression: str) -> str:
        """
        Sanitize an expression (currently just trims whitespace)
        Additional sanitization can be added if needed
        
        Args:
            expression: The expression to sanitize
            
        Returns:
            Sanitized expression
        """
        return expression.strip()