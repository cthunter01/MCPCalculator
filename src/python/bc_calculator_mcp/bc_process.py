"""
BC Process wrapper - manages individual BC calculator process
Handles process lifecycle, I/O communication, and error handling
"""

import asyncio
import sys
from asyncio.subprocess import Process
from typing import Optional

from .types import BCCalculatorError, BCErrorCode, BCProcessOptions


class BCProcess:
    """Wrapper for a single BC calculator process"""
    
    def __init__(self, options: BCProcessOptions) -> None:
        self._options = options
        self._process: Optional[Process] = None
        self._is_ready: bool = False
        self._current_precision: int = options.precision
        self._lock: asyncio.Lock = asyncio.Lock()
        self._pending_request: bool = False
        self._output_buffer: str = ""
        self._error_buffer: str = ""
    
    async def start(self) -> None:
        """Start the BC process and initialize it"""
        try:
            # Spawn BC with math library (-l flag)
            # Important: No shell for security
            self._process = await asyncio.create_subprocess_exec(
                'bc', '-l',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait a moment for process to be ready
            await asyncio.sleep(0.1)
            
            # Mark as ready
            self._is_ready = True
            
            # Initialize precision using BC's scale variable
            await self.set_precision(self._options.precision)
            
        except FileNotFoundError:
            raise BCCalculatorError(
                "BC calculator not found. Please install bc (e.g., 'sudo apt-get install bc')",
                BCErrorCode.BC_SPAWN_ERROR
            )
        except Exception as error:
            raise BCCalculatorError(
                f"Failed to start BC process: {str(error)}",
                BCErrorCode.BC_SPAWN_ERROR,
                error
            )
    
    async def evaluate(self, expression: str, timeout: Optional[int] = None) -> str:
        """
        Evaluate a mathematical expression using BC
        
        Args:
            expression: The expression to evaluate (already validated)
            timeout: Optional timeout in milliseconds (overrides default)
            
 Returns:
            The calculated result as a string
            
        Raises:
            BCCalculatorError: If process not ready, busy, or evaluation fails
        """
        if not self._is_ready or not self._process or not self._process.stdin:
            raise BCCalculatorError(
                "BC process not ready",
                BCErrorCode.BC_NOT_READY
            )
        
        async with self._lock:
            if self._pending_request:
                raise BCCalculatorError(
                    "BC process is busy with another calculation",
                    BCErrorCode.BC_NOT_READY
                )
            
            self._pending_request = True
            timeout_sec = (timeout or self._options.timeout) / 1000.0
            
            try:
                # Clear buffers
                self._output_buffer = ""
                self._error_buffer = ""
                
                # Send expression to BC stdin
                self._process.stdin.write((expression + '\n').encode())
                await self._process.stdin.drain()
                
                # Read result with timeout
                result = await asyncio.wait_for(
                    self._read_result(),
                    timeout=timeout_sec
                )
                
                return result
                
            except asyncio.TimeoutError:
                # Kill the hung process
                self.kill()
                raise BCCalculatorError(
                    f"Calculation timeout after {timeout_sec * 1000:.0f}ms",
                    BCErrorCode.BC_TIMEOUT
                )
            except Exception as error:
                raise BCCalculatorError(
                    f"Failed to evaluate expression: {str(error)}",
                    BCErrorCode.INTERNAL_ERROR,
                    error
                )
            finally:
                self._pending_request = False
    
    async def _read_result(self) -> str:
        """Read calculation result from stdout"""
        if not self._process or not self._process.stdout:
            raise BCCalculatorError(
                "BC process stdout not available",
                BCErrorCode.BC_NOT_READY
            )
        
        # Read until we get a complete line
        while True:
            # Check for errors first
            if self._process.stderr:
                try:
                    error_data = await asyncio.wait_for(
                        self._process.stderr.read(1024),
                        timeout=0.01
                    )
                    if error_data:
                        error_text = error_data.decode().strip()
                        if error_text:
                            raise BCCalculatorError(
                                f"BC error: {error_text}",
                                BCErrorCode.BC_RUNTIME_ERROR
                            )
                except asyncio.TimeoutError:
                    pass  # No error data available
            
            # Read stdout
            line = await self._process.stdout.readline()
            if not line:
                # Process ended unexpectedly
                raise BCCalculatorError(
                    "BC process ended unexpectedly",
                    BCErrorCode.BC_PROCESS_EXIT
                )
            
            decoded = line.decode().strip()
            if decoded:
                return decoded
    
    async def set_precision(self, scale: int) -> None:
        """
        Set the precision (decimal places) for calculations
        
        Args:
            scale: Number of decimal places (0-100)
            
        Raises:
            BCCalculatorError: If scale invalid or process not ready
        """
        # Validate scale
        if scale < 0 or scale > 100:
            raise BCCalculatorError(
                f"Invalid precision: {scale}. Must be between 0 and 100",
                BCErrorCode.VALIDATION_ERROR
            )
        
        if not self._process or not self._process.stdin:
            raise BCCalculatorError(
                "BC process not ready",
                BCErrorCode.BC_NOT_READY
            )
        
        # Set scale directly - BC's scale assignment produces no output
        self._process.stdin.write(f"scale={scale}\n".encode())
        await self._process.stdin.drain()
        self._current_precision = scale
        
        # Give BC a moment to process
        await asyncio.sleep(0.05)
    
    def get_precision(self) -> int:
        """Get current precision setting"""
        return self._current_precision
    
    def is_available(self) -> bool:
        """Check if the process is available for new calculations"""
        return (
            self._is_ready 
            and not self._pending_request 
            and self._process is not None
            and self._process.returncode is None
        )
    
    def kill(self) -> None:
        """Kill the BC process"""
        if self._process:
            try:
                self._process.kill()
            except Exception:
                pass  # Ignore errors when killing
            self._process = None
            self._is_ready = False
    
    def get_pid(self) -> Optional[int]:
        """Get process ID (for debugging)"""
        return self._process.pid if self._process else None