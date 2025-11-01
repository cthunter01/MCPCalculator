"""
BC Process Pool Manager
Manages a pool of BC processes for concurrent request handling
"""

import asyncio
import sys
from typing import List

from .bc_process import BCProcess
from .types import BCCalculatorError, BCErrorCode, BCProcessOptions, ProcessPoolConfig


class BCProcessPool:
    """Manager for a pool of BC processes with concurrent access control"""
    
    def __init__(self, config: ProcessPoolConfig) -> None:
        self._config = config
        self._processes: List[BCProcess] = []
        self._available: asyncio.Queue[BCProcess] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(config.pool_size)
        self._is_initialized: bool = False
    
    async def initialize(self) -> None:
        """Initialize the process pool by spawning configured number of BC processes"""
        if self._is_initialized:
            print("BC process pool already initialized", file=sys.stderr)
            return
        
        print(f"Initializing BC process pool with {self._config.pool_size} processes...", file=sys.stderr)
        
        try:
            # Create pool of processes
            for i in range(self._config.pool_size):
                process = await self._create_process(i)
                self._processes.append(process)
                await self._available.put(process)
            
            self._is_initialized = True
            print(f"BC process pool initialized successfully with {len(self._processes)} processes", file=sys.stderr)
            
        except Exception as error:
            print(f"Failed to initialize BC process pool: {error}", file=sys.stderr)
            # Clean up any processes that were created
            await self.shutdown()
            raise BCCalculatorError(
                f"Failed to initialize BC process pool: {str(error)}",
                BCErrorCode.BC_SPAWN_ERROR,
                error
            )
    
    async def _create_process(self, index: int = -1) -> BCProcess:
        """
        Create and initialize a new BC process
        
        Args:
            index: Process index for logging
            
        Returns:
            Initialized BCProcess
            
        Raises:
            BCCalculatorError: If process creation fails
        """
        log_prefix = f"[Process {index}]" if index >= 0 else "[Process]"
        
        try:
            process = BCProcess(
                BCProcessOptions(
                    precision=self._config.default_precision,
                    timeout=self._config.default_timeout,
                    use_math_library=True
                )
            )
            
            await process.start()
            
            if index >= 0:
                print(f"{log_prefix} Started successfully (PID: {process.get_pid()})", file=sys.stderr)
            
            return process
            
        except Exception as error:
            print(f"{log_prefix} Failed to start: {error}", file=sys.stderr)
            raise
    
    async def acquire_process(self) -> BCProcess:
        """
        Acquire a process from the pool
        Waits if no processes are currently available
        
        Returns:
            Available BCProcess
            
        Raises:
            BCCalculatorError: If pool not initialized or timeout waiting
        """
        if not self._is_initialized:
            raise BCCalculatorError(
                "BC process pool not initialized",
                BCErrorCode.BC_NOT_READY
            )
        
        # Wait for an available process (with timeout)
        try:
            process = await asyncio.wait_for(
                self._available.get(),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            raise BCCalculatorError(
                "No BC processes available after waiting 30 seconds",
                BCErrorCode.BC_NOT_READY
            )
        
        # Verify process is still healthy
        if not process.is_available():
            print(f"Process {process.get_pid()} is not available, attempting recovery", file=sys.stderr)
            # Process died, create replacement
            process.kill()
            
            # Remove from processes list
            if process in self._processes:
                self._processes.remove(process)
            
            # Create new process
            new_process = await self._create_process()
            self._processes.append(new_process)
            return new_process
        
        return process
    
    def release_process(self, process: BCProcess) -> None:
        """
        Release a process back to the pool
        If the process is unhealthy, it will be replaced
        
        Args:
            process: The process to release
        """
        if process not in self._processes:
            print("Attempted to release process not in pool", file=sys.stderr)
            return
        
        if process.is_available():
            # Process is healthy, return to available pool
            try:
                self._available.put_nowait(process)
            except asyncio.QueueFull:
                # This shouldn't happen, but handle it gracefully
                print("Warning: Available queue is full", file=sys.stderr)
        else:
            # Process is unhealthy, replace it
            print(f"Process {process.get_pid()} is unhealthy, replacing...", file=sys.stderr)
            
            # Remove from processes list
            if process in self._processes:
                self._processes.remove(process)
            
            # Kill the bad process
            process.kill()
            
            # Create replacement (non-blocking)
            asyncio.create_task(self._replace_process())
    
    async def _replace_process(self) -> None:
        """Create a replacement process asynchronously"""
        try:
            new_process = await self._create_process()
            self._processes.append(new_process)
            await self._available.put(new_process)
        except Exception as error:
            print(f"Failed to create replacement process: {error}", file=sys.stderr)
    
    def get_available_count(self) -> int:
        """Get the number of available processes"""
        return self._available.qsize()
    
    def get_total_count(self) -> int:
        """Get the total number of processes in the pool"""
        return len(self._processes)
    
    def get_status(self) -> dict:
        """
        Get pool status information
        
        Returns:
            Dictionary with pool status
        """
        return {
            "initialized": self._is_initialized,
            "totalProcesses": len(self._processes),
            "availableProcesses": self._available.qsize(),
            "busyProcesses": len(self._processes) - self._available.qsize()
        }
    
    async def shutdown(self) -> None:
        """
        Shutdown the process pool
        Kills all BC processes
        """
        print("Shutting down BC process pool...", file=sys.stderr)
        
        for process in self._processes:
            process.kill()
        
        self._processes = []
        # Clear the queue
        while not self._available.empty():
            try:
                self._available.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self._is_initialized = False
        
        print("BC process pool shutdown complete", file=sys.stderr)