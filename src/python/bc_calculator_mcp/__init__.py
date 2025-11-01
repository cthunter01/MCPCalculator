"""
BC Calculator MCP Server - Python Implementation
Provides arbitrary precision mathematical calculations using the BC calculator.
"""

from .types import (
    CalculationRequest,
    CalculationResult,
    ValidationResult,
    BCProcessOptions,
    ProcessPoolConfig,
    BCCalculatorError,
    BCErrorCode,
)

__version__ = "1.0.0"
__all__ = [
    "CalculationRequest",
    "CalculationResult",
    "ValidationResult",
    "BCProcessOptions",
    "ProcessPoolConfig",
    "BCCalculatorError",
    "BCErrorCode",
]