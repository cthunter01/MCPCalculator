# BC Calculator MCP Server - Implementation Guide

## Quick Start Implementation Steps

### Phase 1: Project Bootstrap (Todos 1-3)

#### Step 1: Create Project Directory
```bash
mkdir -p /home/travis/.local/share/Roo-Code/MCP/bc-calculator/src
cd /home/travis/.local/share/Roo-Code/MCP/bc-calculator
```

#### Step 2: Initialize package.json
```json
{
  "name": "bc-calculator-mcp",
  "version": "1.0.0",
  "description": "MCP server for BC (Basic Calculator) integration",
  "type": "module",
  "main": "build/index.js",
  "bin": {
    "bc-calculator": "./build/index.js"
  },
  "scripts": {
    "build": "tsc && node -e \"require('fs').chmodSync('build/index.js', '755')\"",
    "watch": "tsc --watch",
    "prepare": "npm run build"
  },
  "keywords": ["mcp", "calculator", "bc", "math"],
  "author": "",
  "license": "MIT",
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.4"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "typescript": "^5.3.0"
  }
}
```

#### Step 3: Create tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "build"]
}
```

### Phase 2: Core Types (Foundation)

#### File: src/types.ts
```typescript
export interface CalculationRequest {
  expression: string;
  precision?: number;
  timeout?: number;
}

export interface CalculationResult {
  result: string;
  expression: string;
  precision: number;
  executionTimeMs?: number;
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
  sanitized?: string;
}

export interface BCProcessOptions {
  precision: number;
  timeout: number;
  useMathLibrary: boolean;
}

export interface ProcessPoolConfig {
  poolSize: number;
  defaultPrecision: number;
  defaultTimeout: number;
}

export class BCCalculatorError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'BCCalculatorError';
  }
}
```

### Phase 3: Input Validation (Security Critical)

#### File: src/input-validator.ts

**Key Requirements**:
- Prevent command injection
- Validate expression safety
- Sanitize input while preserving BC syntax
- Clear error messages

**Implementation Pattern**:
```typescript
export class InputValidator {
  // Maximum expression length (10KB)
  private static readonly MAX_LENGTH = 10000;
  
  // Allowed characters: numbers, letters, math operators, BC syntax
  private static readonly ALLOWED_CHARS = 
    /^[0-9a-zA-Z+\-*\/^().,;\s=<>!&|%{}[\]]+$/;
  
  // Dangerous patterns that could lead to command injection
  private static readonly DANGEROUS_PATTERNS = [
    /system\s*\(/i,
    /exec\s*\(/i,
    /`/,
    /\$\(/,
    />\s*[\/\w]/,  // File redirects
    /<\s*[\/\w]/,
    /\|\s*[\/\w]/, // Pipes to other commands
  ];

  static validate(expression: string): ValidationResult {
    // 1. Check length
    if (expression.length > this.MAX_LENGTH) {
      return {
        valid: false,
        error: `Expression too long (max ${this.MAX_LENGTH} characters)`
      };
    }

    // 2. Check for empty input
    if (!expression.trim()) {
      return {
        valid: false,
        error: 'Expression cannot be empty'
      };
    }

    // 3. Sanitize whitespace
    const sanitized = expression.trim();

    // 4. Check allowed characters
    if (!this.ALLOWED_CHARS.test(sanitized)) {
      return {
        valid: false,
        error: 'Expression contains invalid characters'
      };
    }

    // 5. Check for dangerous patterns
    for (const pattern of this.DANGEROUS_PATTERNS) {
      if (pattern.test(sanitized)) {
        return {
          valid: false,
          error: 'Expression contains disallowed patterns'
        };
      }
    }

    return {
      valid: true,
      sanitized
    };
  }
}
```

### Phase 4: BC Process Wrapper (Core Component)

#### File: src/bc-process.ts

**Key Responsibilities**:
- Spawn and manage BC process lifecycle
- Handle stdin/stdout communication
- Implement timeout mechanism
- Capture errors from stderr
- Support precision configuration

**Critical Details**:
1. Spawn BC with NO shell (`shell: false`)
2. Use `-l` flag for math library
3. Set initial scale (precision)
4. Handle process cleanup properly

**Implementation Skeleton**:
```typescript
import { spawn, ChildProcess } from 'child_process';
import { BCProcessOptions, BCCalculatorError } from './types.js';

export class BCProcess {
  private process: ChildProcess | null = null;
  private isReady: boolean = false;
  private currentPrecision: number;
  private pendingResult: {
    resolve: (value: string) => void;
    reject: (error: Error) => void;
    timer?: NodeJS.Timeout;
  } | null = null;

  constructor(private options: BCProcessOptions) {
    this.currentPrecision = options.precision;
  }

  async start(): Promise<void> {
    // Spawn BC with math library
    this.process = spawn('bc', ['-l'], {
      shell: false,  // Security: no shell interpretation
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Set up event handlers
    this.setupHandlers();

    // Initialize precision
    await this.setPrecision(this.options.precision);
    
    this.isReady = true;
  }

  private setupHandlers(): void {
    if (!this.process) return;

    // Handle stdout - collect calculation results
    let buffer = '';
    this.process.stdout?.on('data', (data: Buffer) => {
      buffer += data.toString();
      
      // BC outputs results line by line
      const lines = buffer.split('\n');
      
      // Keep incomplete line in buffer
      buffer = lines.pop() || '';
      
      // Process complete lines
      for (const line of lines) {
        if (line.trim() && this.pendingResult) {
          this.resolvePendingResult(line.trim());
        }
      }
    });

    // Handle stderr - capture errors
    this.process.stderr?.on('data', (data: Buffer) => {
      const error = data.toString().trim();
      if (error && this.pendingResult) {
        this.rejectPendingResult(
          new BCCalculatorError(
            `BC error: ${error}`,
            'BC_RUNTIME_ERROR'
          )
        );
      }
    });

    // Handle process exit
    this.process.on('exit', (code) => {
      this.isReady = false;
      if (this.pendingResult) {
        this.rejectPendingResult(
          new BCCalculatorError(
            `BC process exited with code ${code}`,
            'BC_PROCESS_EXIT'
          )
        );
      }
    });
  }

  async evaluate(expression: string, timeout?: number): Promise<string> {
    if (!this.isReady || !this.process) {
      throw new BCCalculatorError(
        'BC process not ready',
        'BC_NOT_READY'
      );
    }

    const timeoutMs = timeout || this.options.timeout;

    return new Promise((resolve, reject) => {
      this.pendingResult = { resolve, reject };

      // Set timeout
      this.pendingResult.timer = setTimeout(() => {
        this.rejectPendingResult(
          new BCCalculatorError(
            `Calculation timeout after ${timeoutMs}ms`,
            'BC_TIMEOUT'
          )
        );
        this.kill(); // Kill hung process
      }, timeoutMs);

      // Send expression to BC
      this.process!.stdin?.write(expression + '\n');
    });
  }

  async setPrecision(scale: number): Promise<void> {
    await this.evaluate(`scale=${scale}`);
    this.currentPrecision = scale;
  }

  private resolvePendingResult(result: string): void {
    if (!this.pendingResult) return;
    
    const { resolve, timer } = this.pendingResult;
    if (timer) clearTimeout(timer);
    
    this.pendingResult = null;
    resolve(result);
  }

  private rejectPendingResult(error: Error): void {
    if (!this.pendingResult) return;
    
    const { reject, timer } = this.pendingResult;
    if (timer) clearTimeout(timer);
    
    this.pendingResult = null;
    reject(error);
  }

  isAvailable(): boolean {
    return this.isReady && this.pendingResult === null;
  }

  kill(): void {
    if (this.process) {
      this.process.kill();
      this.process = null;
      this.isReady = false;
    }
  }
}
```

### Phase 5: Process Pool Manager (Concurrency)

#### File: src/bc-process-pool.ts

**Key Features**:
- Maintain pool of 3 BC processes
- Automatic process respawning on failures
- Process acquisition and release
- Graceful shutdown

**Implementation Strategy**:
```typescript
import { BCProcess } from './bc-process.js';
import { ProcessPoolConfig } from './types.js';

export class BCProcessPool {
  private processes: BCProcess[] = [];
  private availableProcesses: BCProcess[] = [];
  private config: ProcessPoolConfig;

  constructor(config: ProcessPoolConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    // Create pool of processes
    const promises = [];
    for (let i = 0; i < this.config.poolSize; i++) {
      promises.push(this.createProcess());
    }
    
    await Promise.all(promises);
    console.error(`BC process pool initialized with ${this.config.poolSize} processes`);
  }

  private async createProcess(): Promise<BCProcess> {
    const process = new BCProcess({
      precision: this.config.defaultPrecision,
      timeout: this.config.defaultTimeout,
      useMathLibrary: true
    });
    
    await process.start();
    this.processes.push(process);
    this.availableProcesses.push(process);
    
    return process;
  }

  async acquireProcess(): Promise<BCProcess> {
    // Try to get available process
    while (this.availableProcesses.length === 0) {
      // Wait briefly and retry
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    const process = this.availableProcesses.shift()!;
    
    // Verify process is still healthy
    if (!process.isAvailable()) {
      // Process died, create replacement
      process.kill();
      const newProcess = await this.createProcess();
      return this.acquireProcess(); // Try again
    }

    return process;
  }

  releaseProcess(process: BCProcess): void {
    if (process.isAvailable()) {
      this.availableProcesses.push(process);
    } else {
      // Process is unhealthy, replace it
      process.kill();
      this.createProcess(); // Non-blocking replacement
    }
  }

  async shutdown(): Promise<void> {
    for (const process of this.processes) {
      process.kill();
    }
    this.processes = [];
    this.availableProcesses = [];
  }
}
```

### Phase 6: Main Server Implementation

#### File: src/index.ts

**Structure**:
```typescript
#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { BCProcessPool } from './bc-process-pool.js';
import { InputValidator } from './input-validator.js';

// Initialize process pool
const pool = new BCProcessPool({
  poolSize: 3,
  defaultPrecision: 20,
  defaultTimeout: 30000 // 30 seconds
});

// Create MCP server
const server = new McpServer({
  name: 'bc-calculator',
  version: '1.0.0'
});

// Tool 1: Basic calculation
server.tool(
  'calculate',
  {
    expression: z.string().describe('Mathematical expression to evaluate'),
    precision: z.number().min(0).max(100).optional()
      .describe('Decimal places (default: 20)')
  },
  async ({ expression, precision = 20 }) => {
    const startTime = Date.now();
    
    try {
      // Validate input
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

      // Acquire process
      const process = await pool.acquireProcess();
      
      try {
        // Set precision if different
        await process.setPrecision(precision);
        
        // Evaluate
        const result = await process.evaluate(validation.sanitized!);
        
        // Release process
        pool.releaseProcess(process);
        
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              result,
              expression,
              precision,
              executionTimeMs: Date.now() - startTime
            }, null, 2)
          }]
        };
      } catch (error) {
        pool.releaseProcess(process);
        throw error;
      }
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Calculation error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
);

// Tool 2: Advanced calculation (similar implementation)
// Tool 3: Set precision (similar implementation)

// Initialize and start server
async function main() {
  await pool.initialize();
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('BC Calculator MCP server running on stdio');
  
  // Graceful shutdown
  process.on('SIGINT', async () => {
    await pool.shutdown();
    process.exit(0);
  });
}

main().catch(console.error);
```

## Key Implementation Decisions

### 1. Why Process Pool vs Single Process?
- **Pro**: Better concurrency (3 parallel calculations)
- **Pro**: Fault isolation (one crash doesn't kill all)
- **Con**: More resource usage
- **Decision**: Use pool for better UX in multi-user scenarios

### 2. Why No Request Queue Class?
- **Simplification**: Process pool handles queuing via acquire/release
- **Decision**: Use simple Promise-based waiting in acquireProcess()

### 3. Timeout Handling
- **Default**: 30 seconds per calculation
- **Why**: Prevents infinite loops in BC scripts
- **Implementation**: Timer + process.kill() on timeout

### 4. Error Categorization
- **Validation errors**: Before BC execution
- **BC errors**: From stderr during execution
- **Timeout errors**: Process killed after timeout
- **Process errors**: BC crash or spawn failure

## Testing Approach

### Manual Tests (During Development)

1. **Basic arithmetic**:
   ```json
   {"expression": "2+2"}  // → 4
   {"expression": "10/3", "precision": 5}  // → 3.33333
   ```

2. **Math library functions**:
   ```json
   {"expression": "sqrt(2)", "precision": 10}
   {"expression": "s(3.14159/2)", "precision": 8}  // sine
   ```

3. **Advanced scripts**:
   ```json
   {
     "script": "a=5\nb=10\na+b",
     "precision": 2
   }
   ```

4. **Error cases**:
   ```json
   {"expression": "2/0"}  // Division by zero
   {"expression": "system('ls')"}  // Blocked pattern
   {"expression": "2 + + 2"}  // BC syntax error
   ```

### Automated Tests (Future)

Create test file: `src/tests/validator.test.ts`
- Test all dangerous patterns
- Test edge cases (empty string, max length, etc.)
- Test special characters handling

## Build and Deployment

### Build Command
```bash
cd /home/travis/.local/share/Roo-Code/MCP/bc-calculator
npm install
npm run build
```

### Verify Build
```bash
ls -lh build/index.js
# Should be executable (+x)
```

### MCP Settings Configuration

Add to `/home/travis/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json`:

```json
{
  "mcpServers": {
    "bc-calculator": {
      "command": "node",
      "args": ["/home/travis/.local/share/Roo-Code/MCP/bc-calculator/build/index.js"],
      "disabled": false,
      "alwaysAllow": [],
      "disabledTools": []
    }
  }
}
```

## Troubleshooting

### Issue: BC not found
- **Symptom**: "spawn bc ENOENT"
- **Fix**: Install bc: `sudo apt-get install bc` (Linux)

### Issue: Process hangs
- **Symptom**: No response from calculation
- **Check**: Timeout setting, BC expression validity
- **Fix**: Ensure timeout is set, check for infinite loops

### Issue: Permission denied
- **Symptom**: Cannot execute build/index.js
- **Fix**: `chmod +x build/index.js`

### Issue: Import errors
- **Symptom**: "Cannot find module"
- **Fix**: Ensure `"type": "module"` in package.json

## Performance Tips

1. **Reuse processes**: Pool design already optimizes this
2. **Batch calculations**: Use advanced tool for multiple expressions
3. **Cache common results**: Future enhancement
4. **Adjust pool size**: Increase for heavy concurrent use

## Security Checklist

- ✅ No shell execution (`shell: false`)
- ✅ Input validation before BC
- ✅ Dangerous pattern blocking
- ✅ Process timeout enforcement
- ✅ No file system access from BC
- ✅ Isolated process execution
- ✅ Graceful error handling

## Next Steps After Implementation

1. Test with various mathematical expressions
2. Verify timeout handling works correctly
3. Test concurrent request handling
4. Monitor process pool health
5. Create user documentation
6. Add more BC functions to examples