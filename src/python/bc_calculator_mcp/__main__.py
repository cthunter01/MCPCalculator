#!/usr/bin/env python3

"""
BC Calculator MCP Server - Python Implementation
Provides arbitrary precision mathematical calculations using the BC calculator
"""

import asyncio
import json
import signal
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .bc_process_pool import BCProcessPool
from .input_validator import InputValidator
from .types import BCCalculatorError, ProcessPoolConfig

# Initialize process pool with configuration
pool = BCProcessPool(
    ProcessPoolConfig(
        pool_size=3,              # 3 concurrent BC processes
        default_precision=20,     # 20 decimal places by default
        default_timeout=30000     # 30 second timeout
    )
)

# Track global precision setting
global_precision = 20

# Create MCP server
server = Server("bc-calculator")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="calculate",
            description=(
                "Evaluate mathematical expressions using BC calculator with arbitrary precision arithmetic. "
                "Supports basic operations (+, -, *, /, ^, %), comparisons, and math library functions "
                "(sqrt, sine, cosine, arctan, log, exp)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": 'Mathematical expression to evaluate (e.g., "2+2", "sqrt(144)", "355/113")'
                    },
                    "precision": {
                        "type": "number",
                        "description": "Number of decimal places for the result (0-100, default: 20)",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["expression"]
            }
        ),
        Tool(
            name="calculate_advanced",
            description=(
                "Execute advanced BC scripts with variables, functions, and control flow. "
                "Supports multi-line scripts, variable assignments, loops, and conditionals."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Multi-line BC script with variables, loops, or functions"
                    },
                    "precision": {
                        "type": "number",
                        "description": "Number of decimal places for results (0-100, default: 20)",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["script"]
            }
        ),
        Tool(
            name="set_precision",
            description=(
                "Set the default precision (decimal places) for subsequent calculations. "
                "This affects all calculations until changed again."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "precision": {
                        "type": "number",
                        "description": "Number of decimal places (0-100)",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["precision"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution requests"""
    try:
        if name == "calculate":
            return await handle_calculate(arguments)
        elif name == "calculate_advanced":
            return await handle_calculate_advanced(arguments)
        elif name == "set_precision":
            return await handle_set_precision(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as error:
        return [TextContent(
            type="text",
            text=f"Error: {str(error)}"
        )]


async def handle_calculate(args: dict[str, Any]) -> list[TextContent]:
    """Handle basic calculation requests"""
    import time
    start_time = time.time()
    
    # Get arguments with defaults
    expression = args.get("expression")
    precision = args.get("precision", global_precision)
    
    if not expression:
        return [TextContent(
            type="text",
            text="Missing required argument: expression"
        )]
    
    # Validate precision
    if precision is not None and (precision < 0 or precision > 100):
        return [TextContent(
            type="text",
            text="Invalid precision: must be between 0 and 100"
        )]
    
    try:
        # Validate input expression
        validation = InputValidator.validate(expression)
        if not validation.valid:
            return [TextContent(
                type="text",
                text=f"Validation error: {validation.error}"
            )]
        
        # Acquire process from pool
        process = await pool.acquire_process()
        
        try:
            # Set precision if different from current
            await process.set_precision(precision)
            
            # Evaluate expression
            result = await process.evaluate(validation.sanitized or expression)
            
            # Release process back to pool
            pool.release_process(process)
            
            execution_time = (time.time() - start_time) * 1000
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "result": result,
                    "expression": expression,
                    "precision": precision,
                    "executionTimeMs": execution_time
                }, indent=2)
            )]
        except Exception as error:
            # Always release process even on error
            pool.release_process(process)
            raise
            
    except BCCalculatorError as error:
        return [TextContent(
            type="text",
            text=f"BC Calculator Error [{error.code.value}]: {error.message}"
        )]
    except Exception as error:
        return [TextContent(
            type="text",
            text=f"Calculation error: {str(error)}"
        )]


async def handle_calculate_advanced(args: dict[str, Any]) -> list[TextContent]:
    """Handle advanced calculation requests with multi-line scripts"""
    import time
    start_time = time.time()
    
    # Get arguments with defaults
    script = args.get("script")
    precision = args.get("precision", global_precision)
    
    if not script:
        return [TextContent(
            type="text",
            text="Missing required argument: script"
        )]
    
    # Validate precision
    if precision is not None and (precision < 0 or precision > 100):
        return [TextContent(
            type="text",
            text="Invalid precision: must be between 0 and 100"
        )]
    
    try:
        # Validate input script
        validation = InputValidator.validate(script)
        if not validation.valid:
            return [TextContent(
                type="text",
                text=f"Validation error: {validation.error}"
            )]
        
        # Acquire process from pool
        process = await pool.acquire_process()
        
        try:
            # Set precision
            await process.set_precision(precision)
            
            # Execute script
            result = await process.evaluate(validation.sanitized or script)
            
            # Release process
            pool.release_process(process)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Truncate script in response if too long
            script_preview = script[:100] + ("..." if len(script) > 100 else "")
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "result": result,
                    "script": script_preview,
                    "precision": precision,
                    "executionTimeMs": execution_time
                }, indent=2)
            )]
        except Exception as error:
            pool.release_process(process)
            raise
            
    except BCCalculatorError as error:
        return [TextContent(
            type="text",
            text=f"BC Calculator Error [{error.code.value}]: {error.message}"
        )]
    except Exception as error:
        return [TextContent(
            type="text",
            text=f"Script execution error: {str(error)}"
        )]


async def handle_set_precision(args: dict[str, Any]) -> list[TextContent]:
    """Handle precision setting requests"""
    global global_precision
    
    precision = args.get("precision")
    
    if precision is None:
        return [TextContent(
            type="text",
            text="Missing required argument: precision"
        )]
    
    # Validate precision
    if precision < 0 or precision > 100:
        return [TextContent(
            type="text",
            text="Invalid precision: must be between 0 and 100"
        )]
    
    # Update global precision
    global_precision = precision
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "message": "Precision updated successfully",
            "precision": global_precision
        }, indent=2)
    )]


async def main() -> None:
    """Main server initialization"""
    try:
        # Initialize the BC process pool
        await pool.initialize()
        
        # Setup signal handlers for graceful shutdown
        async def shutdown() -> None:
            print("Shutting down...", file=sys.stderr)
            await pool.shutdown()
        
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(shutdown())
            )
        
        # Start the MCP server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            print("BC Calculator MCP server running on stdio", file=sys.stderr)
            print(f"Pool status: {json.dumps(pool.get_status())}", file=sys.stderr)
            
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
            
    except Exception as error:
        print(f"Failed to start BC Calculator MCP server: {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        await pool.shutdown()


if __name__ == "__main__":
    asyncio.run(main())