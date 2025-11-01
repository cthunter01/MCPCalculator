#!/usr/bin/env python3
"""Quick test of Python BC Calculator implementation"""

import asyncio
import sys

# Add src/python to path
sys.path.insert(0, 'src/python')

from bc_calculator_mcp.bc_process_pool import BCProcessPool
from bc_calculator_mcp.types import ProcessPoolConfig
from bc_calculator_mcp.input_validator import InputValidator


async def test_basic_functionality():
    """Test basic pool and calculation functionality"""
    print("Starting Python BC Calculator test...")
    
    try:
        # Test input validation
        print("\n1. Testing input validation...")
        validation = InputValidator.validate("355/113")
        print(f"   ✅ Validation passed: {validation.valid}")
        
        # Initialize pool
        print("\n2. Initializing process pool...")
        pool = BCProcessPool(ProcessPoolConfig(
            pool_size=1,
            default_precision=15,
            default_timeout=5000
        ))
        await pool.initialize()
        print(f"   ✅ Pool initialized: {pool.get_status()}")
        
        # Test calculation
        print("\n3. Testing calculation...")
        process = await pool.acquire_process()
        print(f"   Acquired process with PID: {process.get_pid()}")
        
        await process.set_precision(15)
        result = await process.evaluate('355/113')
        pool.release_process(process)
        
        print(f"   ✅ Calculation result: 355/113 = {result}")
        
        # Shutdown
        print("\n4. Shutting down pool...")
        await pool.shutdown()
        print("   ✅ Pool shutdown complete")
        
        print("\n🎉 All tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_basic_functionality()))