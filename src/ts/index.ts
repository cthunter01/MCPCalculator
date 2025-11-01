#!/usr/bin/env node

/**
 * BC Calculator MCP Server
 * Provides arbitrary precision mathematical calculations using the BC calculator
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { BCProcessPool } from './bc-process-pool.js';
import { InputValidator } from './input-validator.js';
import { BCCalculatorError } from './types.js';

// Initialize process pool with configuration
const pool = new BCProcessPool({
  poolSize: 3,              // 3 concurrent BC processes
  defaultPrecision: 20,     // 20 decimal places by default
  defaultTimeout: 30000     // 30 second timeout
});

// Track global precision setting
let globalPrecision = 20;

// Create MCP server
const server = new Server(
  {
    name: 'bc-calculator',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * Tool definitions for the BC calculator
 */
const TOOLS: Tool[] = [
  {
    name: 'calculate',
    description: 'Evaluate mathematical expressions using BC calculator with arbitrary precision arithmetic. ' +
                 'Supports basic operations (+, -, *, /, ^, %), comparisons, and math library functions ' +
                 '(sqrt, sine, cosine, arctan, log, exp).',
    inputSchema: {
      type: 'object',
      properties: {
        expression: {
          type: 'string',
          description: 'Mathematical expression to evaluate (e.g., "2+2", "sqrt(144)", "355/113")'
        },
        precision: {
          type: 'number',
          description: 'Number of decimal places for the result (0-100, default: 20)',
          minimum: 0,
          maximum: 100
        }
      },
      required: ['expression']
    }
  },
  {
    name: 'calculate_advanced',
    description: 'Execute advanced BC scripts with variables, functions, and control flow. ' +
                 'Supports multi-line scripts, variable assignments, loops, and conditionals.',
    inputSchema: {
      type: 'object',
      properties: {
        script: {
          type: 'string',
          description: 'Multi-line BC script with variables, loops, or functions'
        },
        precision: {
          type: 'number',
          description: 'Number of decimal places for results (0-100, default: 20)',
          minimum: 0,
          maximum: 100
        }
      },
      required: ['script']
    }
  },
  {
    name: 'set_precision',
    description: 'Set the default precision (decimal places) for subsequent calculations. ' +
                 'This affects all calculations until changed again.',
    inputSchema: {
      type: 'object',
      properties: {
        precision: {
          type: 'number',
          description: 'Number of decimal places (0-100)',
          minimum: 0,
          maximum: 100
        }
      },
      required: ['precision']
    }
  }
];

/**
 * List available tools
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS
  };
});

/**
 * Handle tool execution requests
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'calculate':
        return await handleCalculate(args);
      
      case 'calculate_advanced':
        return await handleCalculateAdvanced(args);
      
      case 'set_precision':
        return await handleSetPrecision(args);
      
      default:
        return {
          content: [{
            type: 'text',
            text: `Unknown tool: ${name}`
          }],
          isError: true
        };
    }
  } catch (error) {
    return {
      content: [{
        type: 'text',
        text: `Error: ${error instanceof Error ? error.message : String(error)}`
      }],
      isError: true
    };
  }
});

/**
 * Handle basic calculation requests
 */
async function handleCalculate(args: unknown): Promise<any> {
  const startTime = Date.now();
  
  // Validate arguments
  if (!args || typeof args !== 'object') {
    return {
      content: [{
        type: 'text',
        text: 'Invalid arguments: expected an object'
      }],
      isError: true
    };
  }

  const { expression, precision = globalPrecision } = args as {
    expression?: string;
    precision?: number;
  };

  if (!expression) {
    return {
      content: [{
        type: 'text',
        text: 'Missing required argument: expression'
      }],
      isError: true
    };
  }

  // Validate precision
  if (precision !== undefined && (precision < 0 || precision > 100)) {
    return {
      content: [{
        type: 'text',
        text: 'Invalid precision: must be between 0 and 100'
      }],
      isError: true
    };
  }

  try {
    // Validate input expression
    const validation = InputValidator.validate(expression);
    if (!validation.valid) {
      return {
        content: [{
          type: 'text',
          text: `Validation error: ${validation.error}`
        }],
        isError: true
      };
    }

    // Acquire process from pool
    const process = await pool.acquireProcess();
    
    try {
      // Set precision if different from current
      await process.setPrecision(precision);
      
      // Evaluate expression
      const result = await process.evaluate(validation.sanitized!);
      
      // Release process back to pool
      pool.releaseProcess(process);
      
      const executionTime = Date.now() - startTime;
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            result,
            expression,
            precision,
            executionTimeMs: executionTime
          }, null, 2)
        }]
      };
    } catch (error) {
      // Always release process even on error
      pool.releaseProcess(process);
      throw error;
    }
  } catch (error) {
    if (error instanceof BCCalculatorError) {
      return {
        content: [{
          type: 'text',
          text: `BC Calculator Error [${error.code}]: ${error.message}`
        }],
        isError: true
      };
    }
    
    return {
      content: [{
        type: 'text',
        text: `Calculation error: ${error instanceof Error ? error.message : String(error)}`
      }],
      isError: true
    };
  }
}

/**
 * Handle advanced calculation requests with multi-line scripts
 */
async function handleCalculateAdvanced(args: unknown): Promise<any> {
  const startTime = Date.now();
  
  // Validate arguments
  if (!args || typeof args !== 'object') {
    return {
      content: [{
        type: 'text',
        text: 'Invalid arguments: expected an object'
      }],
      isError: true
    };
  }

  const { script, precision = globalPrecision } = args as {
    script?: string;
    precision?: number;
  };

  if (!script) {
    return {
      content: [{
        type: 'text',
        text: 'Missing required argument: script'
      }],
      isError: true
    };
  }

  // Validate precision
  if (precision !== undefined && (precision < 0 || precision > 100)) {
    return {
      content: [{
        type: 'text',
        text: 'Invalid precision: must be between 0 and 100'
      }],
      isError: true
    };
  }

  try {
    // Validate input script
    const validation = InputValidator.validate(script);
    if (!validation.valid) {
      return {
        content: [{
          type: 'text',
          text: `Validation error: ${validation.error}`
        }],
        isError: true
      };
    }

    // Acquire process from pool
    const process = await pool.acquireProcess();
    
    try {
      // Set precision
      await process.setPrecision(precision);
      
      // Execute script
      const result = await process.evaluate(validation.sanitized!);
      
      // Release process
      pool.releaseProcess(process);
      
      const executionTime = Date.now() - startTime;
      
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            result,
            script: script.substring(0, 100) + (script.length > 100 ? '...' : ''),
            precision,
            executionTimeMs: executionTime
          }, null, 2)
        }]
      };
    } catch (error) {
      pool.releaseProcess(process);
      throw error;
    }
  } catch (error) {
    if (error instanceof BCCalculatorError) {
      return {
        content: [{
          type: 'text',
          text: `BC Calculator Error [${error.code}]: ${error.message}`
        }],
        isError: true
      };
    }
    
    return {
      content: [{
        type: 'text',
        text: `Script execution error: ${error instanceof Error ? error.message : String(error)}`
      }],
      isError: true
    };
  }
}

/**
 * Handle precision setting requests
 */
async function handleSetPrecision(args: unknown): Promise<any> {
  // Validate arguments
  if (!args || typeof args !== 'object') {
    return {
      content: [{
        type: 'text',
        text: 'Invalid arguments: expected an object'
      }],
      isError: true
    };
  }

  const { precision } = args as { precision?: number };

  if (precision === undefined) {
    return {
      content: [{
        type: 'text',
        text: 'Missing required argument: precision'
      }],
      isError: true
    };
  }

  // Validate precision
  if (precision < 0 || precision > 100) {
    return {
      content: [{
        type: 'text',
        text: 'Invalid precision: must be between 0 and 100'
      }],
      isError: true
    };
  }

  // Update global precision
  globalPrecision = precision;

  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        message: 'Precision updated successfully',
        precision: globalPrecision
      }, null, 2)
    }]
  };
}

/**
 * Main server initialization
 */
async function main() {
  try {
    // Initialize the BC process pool
    await pool.initialize();
    
    // Start the MCP server
    const transport = new StdioServerTransport();
    await server.connect(transport);
    
    console.error('BC Calculator MCP server running on stdio');
    console.error(`Pool status: ${JSON.stringify(pool.getStatus())}`);
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      console.error('Received SIGINT, shutting down...');
      await pool.shutdown();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      console.error('Received SIGTERM, shutting down...');
      await pool.shutdown();
      process.exit(0);
    });

  } catch (error) {
    console.error('Failed to start BC Calculator MCP server:', error);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});