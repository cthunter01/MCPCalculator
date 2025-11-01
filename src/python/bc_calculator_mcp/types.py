"""
Type definitions for BC Calculator MCP Server (Python)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


@dataclass
class CalculationRequest:
    """Request for a mathematical calculation"""
    expression: str
    precision: int = 20
    timeout: int = 30000  # milliseconds


@dataclass
class CalculationResult:
    """Result of a mathematical calculation"""
    result: str
    expression: str
    precision: int
    execution_time_ms: Optional[float] = None


@dataclass
class ValidationResult:
    """Result of input validation"""
    valid: bool
    error: Optional[str] = None
    sanitized: Optional[str] = None


@dataclass
class BCProcessOptions:
    """Options for configuring a BC process"""
    precision: int
    timeout: int
    use_math_library: bool = True


@dataclass
class ProcessPoolConfig:
    """Configuration for the BC process pool"""
    pool_size: int = 3
    default_precision: int = 20
    default_timeout: int = 30000  # milliseconds


class BCErrorCode(str, Enum):
    """Error codes for BC calculator operations"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BC_NOT_READY = "BC_NOT_READY"
    BC_RUNTIME_ERROR = "BC_RUNTIME_ERROR"
    BC_TIMEOUT = "BC_TIMEOUT"
    BC_PROCESS_EXIT = "BC_PROCESS_EXIT"
    BC_SPAWN_ERROR = "BC_SPAWN_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class BCCalculatorError(Exception):
    """Custom error class for BC calculator operations"""
    
    def __init__(
        self,
        message: str,
        code: BCErrorCode,
        details: Any = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details
        self.message = message
    
    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"
    
    def __repr__(self) -> str:
        return f"BCCalculatorError(message={self.message!r}, code={self.code!r}, details={self.details!r})"