/**
 * Input validation and sanitization module for BC Calculator
 * Prevents command injection and ensures safe input to BC
 */

import { ValidationResult } from './types.js';

export class InputValidator {
  // Maximum expression length (10KB)
  private static readonly MAX_LENGTH = 10000;
  
  // Allowed characters: numbers, letters, math operators, BC syntax
  private static readonly ALLOWED_CHARS = 
    /^[0-9a-zA-Z+\-*\/^().,;\s=<>!&|%{}[\]]+$/;
  
  // Dangerous patterns that could lead to command injection or system abuse
  private static readonly DANGEROUS_PATTERNS = [
    /system\s*\(/i,           // system() calls
    /exec\s*\(/i,             // exec() calls
    /`/,                      // Backticks (command substitution)
    /\$\(/,                   // Command substitution
    />\s*[\/\w]/,             // File redirects (output)
    /<\s*[\/\w]/,             // File redirects (input)
    /\|\s*[\/\w]/,            // Pipes to other commands
    /;\s*(?:bash|sh|rm|cat|ls|pwd|chmod|chown)/i, // Dangerous shell commands
  ];

  /**
   * Validate an expression for safety and correctness
   * @param expression The expression to validate
   * @returns ValidationResult with validation status and optional error message
   */
  static validate(expression: string): ValidationResult {
    // 1. Check for null/undefined
    if (!expression) {
      return {
        valid: false,
        error: 'Expression cannot be null or undefined'
      };
    }

    // 2. Check length
    if (expression.length > this.MAX_LENGTH) {
      return {
        valid: false,
        error: `Expression too long (max ${this.MAX_LENGTH} characters, got ${expression.length})`
      };
    }

    // 3. Check for empty input after trimming
    const trimmed = expression.trim();
    if (!trimmed) {
      return {
        valid: false,
        error: 'Expression cannot be empty'
      };
    }

    // 4. Check allowed characters
    if (!this.ALLOWED_CHARS.test(trimmed)) {
      return {
        valid: false,
        error: 'Expression contains invalid characters. Only alphanumeric characters and mathematical operators are allowed.'
      };
    }

    // 5. Check for dangerous patterns
    for (const pattern of this.DANGEROUS_PATTERNS) {
      if (pattern.test(trimmed)) {
        return {
          valid: false,
          error: 'Expression contains disallowed patterns that could be unsafe'
        };
      }
    }

    // 6. Basic BC syntax validation (optional, BC will also catch this)
    const validation = this.validateBCSyntax(trimmed);
    if (!validation.valid) {
      return validation;
    }

    return {
      valid: true,
      sanitized: trimmed
    };
  }

  /**
   * Perform basic BC syntax validation
   * @param expression The expression to validate
   * @returns ValidationResult
   */
  private static validateBCSyntax(expression: string): ValidationResult {
    // Check for balanced parentheses
    let parenCount = 0;
    let braceCount = 0;
    let bracketCount = 0;

    for (const char of expression) {
      if (char === '(') parenCount++;
      if (char === ')') parenCount--;
      if (char === '{') braceCount++;
      if (char === '}') braceCount--;
      if (char === '[') bracketCount++;
      if (char === ']') bracketCount--;

      // Check for negative counts (closing before opening)
      if (parenCount < 0) {
        return {
          valid: false,
          error: 'Unbalanced parentheses: closing parenthesis before opening'
        };
      }
      if (braceCount < 0) {
        return {
          valid: false,
          error: 'Unbalanced braces: closing brace before opening'
        };
      }
      if (bracketCount < 0) {
        return {
          valid: false,
          error: 'Unbalanced brackets: closing bracket before opening'
        };
      }
    }

    // Check final counts
    if (parenCount !== 0) {
      return {
        valid: false,
        error: `Unbalanced parentheses: ${parenCount > 0 ? 'missing closing' : 'extra closing'} parenthesis`
      };
    }
    if (braceCount !== 0) {
      return {
        valid: false,
        error: `Unbalanced braces: ${braceCount > 0 ? 'missing closing' : 'extra closing'} brace`
      };
    }
    if (bracketCount !== 0) {
      return {
        valid: false,
        error: `Unbalanced brackets: ${bracketCount > 0 ? 'missing closing' : 'extra closing'} bracket`
      };
    }

    return { valid: true };
  }

  /**
   * Sanitize an expression (currently just trims whitespace)
   * Additional sanitization can be added if needed
   * @param expression The expression to sanitize
   * @returns Sanitized expression
   */
  static sanitize(expression: string): string {
    return expression.trim();
  }
}