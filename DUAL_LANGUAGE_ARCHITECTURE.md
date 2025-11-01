# BC Calculator MCP Server - Dual Language Architecture Plan

## Executive Summary

This document outlines the architecture for transforming the existing TypeScript-only bc-calculator MCP server into a **dual-language educational comparison project**. The project will maintain both TypeScript and Python implementations side-by-side, allowing developers to learn from comparing equivalent MCP server implementations in both languages.

## Project Goals

1. **Educational Value**: Demonstrate idiomatic MCP server patterns in both TypeScript and Python
2. **Functional Equivalence**: Both implementations provide identical MCP tools, resources, and capabilities
3. **Best Practices**: Each implementation follows language-specific best practices (not direct translations)
4. **Documentation**: Comprehensive docs for both implementations with comparison guides
5. **Maintainability**: Clean separation allowing independent evolution of each implementation

## Current State Analysis

### Existing Structure
```
/home/travis/.local/share/Roo-Code/MCP/bc-calculator/
├── package.json              # TypeScript dependencies
├── tsconfig.json            # TypeScript config
├── README.md                # Current docs (TS-focused)
├── ARCHITECTURE.md          # Current architecture
├── IMPLEMENTATION_GUIDE.md  # TS implementation guide
├── QUICK_REFERENCE.md       # TS quick reference
├── PROJECT_SUMMARY.md       # Current summary
├── src/                     # TypeScript source (5 files)
│   ├── index.ts
│   ├── types.ts
│   ├── bc-process.ts
│   ├── bc-process-pool.ts
│   └── input-validator.ts
└── build/                   # Compiled JS output
```

### Issues with Current Structure
- Source files directly in `src/` will conflict with Python package structure
- No clear language separation
- TypeScript-centric documentation
- Build configuration assumes single language

## Target Architecture

### New Directory Structure

```
/home/travis/.local/share/Roo-Code/MCP/bc-calculator/
├── package.json                    # TypeScript dependencies
├── tsconfig.json                   # Updated: rootDir → src/ts
├── pyproject.toml                  # Python project config (NEW)
├── requirements.txt                # Python dependencies (NEW)
├── .gitignore                      # Updated: Add Python entries
│
├── Documentation (Language-Neutral & Specific)
├── README.md                       # Overview + links to both impls
├── README_PYTHON.md                # Python-specific guide (NEW)
├── ARCHITECTURE.md                 # TS architecture (existing)
├── ARCHITECTURE_PYTHON.md          # Python architecture (NEW)
├── IMPLEMENTATION_GUIDE.md         # TS implementation (existing)
├── IMPLEMENTATION_GUIDE_PYTHON.md  # Python implementation (NEW)
├── QUICK_REFERENCE.md              # TS quick ref (existing)
├── QUICK_REFERENCE_PYTHON.md       # Python quick ref (NEW)
├── PROJECT_SUMMARY.md              # Updated: Dual-language summary
├── COMPARISON_GUIDE.md             # NEW: Compare approaches
│
├── TypeScript Implementation
├── src/
│   └── ts/                         # TypeScript source (MOVED)
│       ├── index.ts
│       ├── types.ts
│       ├── bc-process.ts
│       ├── bc-process-pool.ts
│       └── input-validator.ts
├── build/                          # Compiled TypeScript output
│
└── Python Implementation
    └── src/
        └── python/                 # Python package (NEW)
            ├── __init__.py
            ├── __main__.py         # MCP server entry
            ├── types.py            # Type definitions
            ├── bc_process.py       # Single BC process
            ├── bc_process_pool.py  # Process pool manager
            └── input_validator.py  # Security validation
```

## Phase 1: Repository Restructuring

### Step 1.1: Create Directory Structure

```bash
# Create new directories
mkdir -p src/ts
mkdir -p src/python
```

### Step 1.2: Move TypeScript Files

Move all `.ts` files from `src/` to `src/ts/`:
- `src/index.ts` → `src/ts/index.ts`
- `src/types.ts` → `src/ts/types.ts`
- `src/bc-process.ts` → `src/ts/bc-process.ts`
- `src/bc-process-pool.ts` → `src/ts/bc-process-pool.ts`
- `src/input-validator.ts` → `src/ts/input-validator.ts`

### Step 1.3: Update TypeScript Configuration

**tsconfig.json changes:**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./build",
    "rootDir": "./src/ts",        // CHANGED: Was "./src"
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/ts/**/*"],     // CHANGED: Was "src/**/*"
  "exclude": ["node_modules", "build", "src/python"]  // ADDED: Exclude Python
}
```

**package.json changes:**
```json
{
  "scripts": {
    "build": "tsc && node -e \"const fs = require('fs'); if (fs.existsSync('build/index.js')) fs.chmodSync('build/index.js', '755')\"",
    "build:ts": "npm run build",  // Alias for clarity
    "watch": "tsc --watch",
    "prepare": "npm run build"
  }
}
```

### Step 1.4: Update .gitignore

Add Python-specific entries:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv
*.egg-info/
dist/
build-python/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

### Step 1.5: Verification

1. Run `npm run build` - should compile to `build/` successfully
2. Verify MCP server still works with updated paths
3. Check that no TypeScript code changed (only locations)

## Phase 2: Python Implementation Design

### Module Architecture Comparison

| Component | TypeScript | Python Equivalent |
|-----------|-----------|-------------------|
| Type System | TypeScript interfaces | `dataclasses` + `TypedDict` |
| Async | Promises + async/await | `asyncio` + async/await |
| Process Mgmt | `child_process` | `asyncio.subprocess` |
| Pooling | Array + state tracking | `asyncio.Semaphore` + list |
| Validation | Regex + whitelist | `re` module + validation |
| MCP SDK | `@modelcontextprotocol/sdk` | `mcp` Python package |

### Python Package Structure

```
src/python/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point (if run as module)
├── server.py                # MCP server implementation
├── types.py                 # Type definitions
├── bc_process.py            # Single BC process wrapper
├── bc_process_pool.py       # Process pool manager
└── input_validator.py       # Security validation
```

### Key Python Design Decisions

#### 1. Type Definitions (types.py)

**TypeScript approach:**
```typescript
interface CalculationRequest {
  expression: string;
  precision?: number;
  timeout?: number;
}

interface CalculationResult {
  result: string;
  expression: string;
  precision: number;
  executionTimeMs?: number;
}
```

**Python approach (using dataclasses):**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CalculationRequest:
    expression: str
    precision: Optional[int] = 20
    timeout: Optional[int] = 30000

@dataclass
class CalculationResult:
    result: str
    expression: str
    precision: int
    execution_time_ms: Optional[float] = None
```

**Rationale**: Python `dataclasses` provide similar functionality to TS interfaces with built-in equality, string representation, and type hints.

#### 2. Process Management (bc_process.py)

**TypeScript approach:**
```typescript
class BCProcess {
  private process: ChildProcess;
  private isReady: boolean = false;
  
  async start(): Promise<void> { /* spawn with stdio pipes */ }
  async evaluate(expr: string): Promise<string> { /* write/read */ }
}
```

**Python approach (using asyncio):**
```python
import asyncio
from asyncio.subprocess import Process

class BCProcess:
    def __init__(self):
        self._process: Optional[Process] = None
        self._is_ready: bool = False
        self._lock: asyncio.Lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Spawn BC process with asyncio.create_subprocess_exec"""
        self._process = await asyncio.create_subprocess_exec(
            'bc', '-l',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self._is_ready = True
    
    async def evaluate(self, expression: str, timeout: int = 30000) -> str:
        """Send expression and read result with timeout"""
        async with self._lock:
            # Write to stdin with timeout
            # Read from stdout with timeout
            pass
```

**Rationale**: 
- Use `asyncio.create_subprocess_exec` instead of Node's `spawn`
- `asyncio.Lock` for thread-safe access instead of promise chaining
- Use `asyncio.wait_for()` for timeout handling

#### 3. Process Pool (bc_process_pool.py)

**TypeScript approach:**
```typescript
class BCProcessPool {
  private processes: BCProcess[] = [];
  private availableProcesses: BCProcess[] = [];
  
  async acquireProcess(): Promise<BCProcess> {
    // Wait for available or create new
  }
  
  releaseProcess(process: BCProcess): void {
    this.availableProcesses.push(process);
  }
}
```

**Python approach (using Semaphore):**
```python
import asyncio
from typing import List

class BCProcessPool:
    def __init__(self, pool_size: int = 3):
        self._pool_size = pool_size
        self._processes: List[BCProcess] = []
        self._semaphore = asyncio.Semaphore(pool_size)
        self._available: asyncio.Queue[BCProcess] = asyncio.Queue()
    
    async def acquire_process(self) -> BCProcess:
        """Acquire process with semaphore-based limiting"""
        async with self._semaphore:
            if self._available.empty():
                # Spawn new process if under limit
                process = BCProcess()
                await process.start()
                self._processes.append(process)
                return process
            else:
                return await self._available.get()
    
    def release_process(self, process: BCProcess) -> None:
        """Return process to available queue"""
        await self._available.put(process)
```

**Rationale**:
- `asyncio.Semaphore` naturally handles concurrency limits
- `asyncio.Queue` for available process management
- More Pythonic than directly porting TS array manipulation

#### 4. Input Validation (input_validator.py)

**Approach**: Nearly identical logic, use Python `re` module instead of JavaScript regex.

```python
import re
from typing import Tuple

class InputValidator:
    ALLOWED_CHARS = re.compile(r'^[0-9a-zA-Z+\-*/^().,;\s=<>!&|%{}\[\]]+$')
    DANGEROUS_PATTERNS = [
        re.compile(r'system\s*\('),
        re.compile(r'exec\s*\('),
        re.compile(r'`'),
        re.compile(r'\$\('),
        re.compile(r'>\s*/|<\s*/')
    ]
    MAX_LENGTH = 10000
    
    @classmethod
    def validate(cls, expression: str) -> Tuple[bool, str]:
        """Validate expression, return (is_valid, error_message)"""
        if len(expression) > cls.MAX_LENGTH:
            return False, f"Expression too long (max {cls.MAX_LENGTH})"
        
        if not cls.ALLOWED_CHARS.match(expression):
            return False, "Expression contains invalid characters"
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(expression):
                return False, "Expression contains dangerous patterns"
        
        return True, ""
    
    @classmethod
    def sanitize(cls, expression: str) -> str:
        """Sanitize expression (currently returns as-is after validation)"""
        return expression.strip()
```

#### 5. MCP Server Entry Point (__main__.py or server.py)

**TypeScript approach:**
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({
  name: "bc-calculator",
  version: "1.0.0"
}, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [/* tool definitions */]
}));

const transport = new StdioServerTransport();
await server.connect(transport);
```

**Python approach:**
```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create server instance
server = Server("bc-calculator")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="calculate",
            description="Evaluate mathematical expressions",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression"
                    },
                    "precision": {
                        "type": "number",
                        "description": "Decimal places (0-100)",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["expression"]
            }
        ),
        # ... other tools
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""
    if name == "calculate":
        return await handle_calculate(arguments)
    # ... other tools

async def main():
    """Run MCP server with stdio transport"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

**Rationale**:
- Python MCP SDK uses decorator-based registration
- Natural async/await flow with `asyncio.run()`
- Similar stdio transport concept

### Python Package Configuration

#### pyproject.toml (Modern Python Standard)

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bc-calculator-mcp"
version = "1.0.0"
description = "MCP server for BC (Basic Calculator) with arbitrary precision"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
license = {text = "MIT"}
readme = "README_PYTHON.md"
requires-python = ">=3.10"
keywords = ["mcp", "calculator", "bc", "math", "arbitrary-precision"]

dependencies = [
    "mcp>=0.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
]

[project.scripts]
bc-calculator-py = "bc_calculator_mcp.__main__:main"

[tool.setuptools.packages.find]
where = ["src/python"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
```

#### requirements.txt (Alternative/Additional)

```txt
mcp>=0.9.0

# Development dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
mypy>=1.5.0
ruff>=0.1.0
```

### Error Handling Comparison

**TypeScript:**
```typescript
try {
  const result = await process.evaluate(expression);
  return { result, expression };
} catch (error) {
  return {
    isError: true,
    content: [{ type: "text", text: `Error: ${error.message}` }]
  };
}
```

**Python:**
```python
try:
    result = await process.evaluate(expression)
    return TextContent(type="text", text=result)
except TimeoutError as e:
    return TextContent(
        type="text",
        text=f"Calculation timeout after {timeout}ms"
    )
except Exception as e:
    return TextContent(
        type="text", 
        text=f"Error: {str(e)}"
    )
```

## Phase 3: Documentation Strategy

### Documentation Files to Create

#### 1. README_PYTHON.md
**Content**:
- Python-specific installation (pip, venv setup)
- Python requirements (Python 3.10+, bc utility)
- Usage examples with Python
- MCP settings configuration for Python version
- Troubleshooting Python-specific issues

#### 2. ARCHITECTURE_PYTHON.md
**Content**:
- Python module structure
- asyncio-based design patterns
- Process pool implementation with Semaphore
- Type system approach (dataclasses vs interfaces)
- Security validation implementation
- Comparison with TypeScript decisions

#### 3. IMPLEMENTATION_GUIDE_PYTHON.md
**Content**:
- Step-by-step Python implementation
- Module-by-module code walkthrough
- Testing with pytest
- Debugging asyncio code
- Performance considerations
- Deployment instructions

#### 4. QUICK_REFERENCE_PYTHON.md
**Content**:
- Python code snippets
- Common asyncio patterns
- MCP SDK Python API
- Security checklist (Python-specific)
- Testing commands
- Common issues & solutions

#### 5. COMPARISON_GUIDE.md (NEW - Root Level)
**Content**:
- Side-by-side feature comparison
- When to choose TypeScript vs Python
- Implementation pattern differences
- Performance characteristics
- Pros/cons of each approach
- Code examples showing equivalent functionality

### Documentation Placement

All language-specific documentation goes in **project root** (not in src/):

```
/home/travis/.local/share/Roo-Code/MCP/bc-calculator/
├── README.md                       # General overview + links
├── README_PYTHON.md                # Python guide
├── ARCHITECTURE.md                 # TypeScript architecture
├── ARCHITECTURE_PYTHON.md          # Python architecture
├── IMPLEMENTATION_GUIDE.md         # TypeScript implementation
├── IMPLEMENTATION_GUIDE_PYTHON.md  # Python implementation
├── QUICK_REFERENCE.md              # TypeScript quick ref
├── QUICK_REFERENCE_PYTHON.md       # Python quick ref
├── COMPARISON_GUIDE.md             # Compare both approaches
└── PROJECT_SUMMARY.md              # Updated for dual-language
```

## Phase 4: MCP Configuration

### TypeScript Configuration (Existing)

```json
{
  "mcpServers": {
    "bc-calculator-ts": {
      "command": "node",
      "args": ["/home/travis/.local/share/Roo-Code/MCP/bc-calculator/build/index.js"],
      "disabled": false
    }
  }
}
```

### Python Configuration (New)

```json
{
  "mcpServers": {
    "bc-calculator-py": {
      "command": "python3",
      "args": ["-m", "bc_calculator_mcp"],
      "cwd": "/home/travis/.local/share/Roo-Code/MCP/bc-calculator/src/python",
      "disabled": false
    }
  }
}
```

### Running Both Simultaneously

Users can enable both servers and compare behavior:

```json
{
  "mcpServers": {
    "bc-calculator-ts": {
      "command": "node",
      "args": ["/home/travis/.local/share/Roo-Code/MCP/bc-calculator/build/index.js"]
    },
    "bc-calculator-py": {
      "command": "python3",
      "args": ["-m", "bc_calculator_mcp"],
      "cwd": "/home/travis/.local/share/Roo-Code/MCP/bc-calculator/src/python"
    }
  }
}
```

## Phase 5: Testing Strategy

### Test Equivalence Matrix

| Test Case | TypeScript | Python | Expected Result |
|-----------|-----------|---------|-----------------|
| Basic arithmetic | `calculate("2+2")` | `calculate("2+2")` | "4" |
| Division w/ precision | `calculate("355/113", 15)` | `calculate("355/113", 15)` | "3.141592920353982" |
| Math functions | `calculate("sqrt(2)", 10)` | `calculate("sqrt(2)", 10)` | "1.4142135623" |
| Variables | `calculate_advanced("a=5; b=10; a+b")` | `calculate_advanced("a=5; b=10; a+b")` | "15" |
| Error: Division by 0 | `calculate("1/0")` | `calculate("1/0")` | Error message |
| Error: Invalid chars | `calculate("system('ls')")` | `calculate("system('ls')")` | Validation error |
| Timeout | Long computation | Long computation | Timeout error |
| Concurrent | 5 simultaneous | 5 simultaneous | All succeed |

### TypeScript Test Verification

After restructuring, verify existing functionality:

```bash
cd /home/travis/.local/share/Roo-Code/MCP/bc-calculator
npm run build
# Test via MCP client or manual stdio interaction
```

### Python Testing Approach

```bash
# Unit tests with pytest
cd /home/travis/.local/share/Roo-Code/MCP/bc-calculator
python3 -m pytest src/python/tests/

# Type checking
python3 -m mypy src/python/

# Linting
python3 -m ruff check src/python/

# Manual testing
python3 -m bc_calculator_mcp
```

### Test Files Structure

```
src/python/
├── tests/
│   ├── __init__.py
│   ├── test_input_validator.py
│   ├── test_bc_process.py
│   ├── test_bc_process_pool.py
│   └── test_integration.py
```

## Implementation Sequence Summary

### Phase 1: Restructuring (Todos 1-6)
1. Create `src/ts/` and `src/python/` directories
2. Move all TypeScript files to `src/ts/`
3. Update `tsconfig.json` rootDir and include paths
4. Update `package.json` if needed
5. Rebuild and verify TypeScript still works
6. Update `.gitignore` for Python

### Phase 2: Python Implementation (Todos 7-14)
1. Design Python module structure
2. Create `pyproject.toml` and `requirements.txt`
3. Implement `types.py` with dataclasses
4. Implement `input_validator.py` with regex validation
5. Implement `bc_process.py` with asyncio subprocess
6. Implement `bc_process_pool.py` with Semaphore
7. Implement `server.py` or `__main__.py` as MCP entry
8. Add Python gitignore entries

### Phase 3: Documentation (Todos 15-18)
1. Create `README_PYTHON.md`
2. Create `ARCHITECTURE_PYTHON.md`
3. Create `IMPLEMENTATION_GUIDE_PYTHON.md`
4. Create `QUICK_REFERENCE_PYTHON.md`

### Phase 4: Integration (Todos 19-20)
1. Document Python MCP configuration
2. Create `COMPARISON_GUIDE.md`
3. Update `PROJECT_SUMMARY.md` for dual-language

### Phase 5: Testing (Todos 21-24)
1. Create test plan covering both implementations
2. Verify TypeScript still works after restructuring
3. Test Python implementation thoroughly
4. Final documentation updates

## Success Criteria

The dual-language implementation will be considered successful when:

✅ **Structural**
- TypeScript code moved to `src/ts/` without modification
- TypeScript builds successfully to `build/`
- Python implementation in `src/python/` as a proper package
- Both can coexist without conflicts

✅ **Functional**
- Both servers provide identical MCP tools
- Both pass the same test suite
- Both handle errors consistently
- Both implement same security validations

✅ **Documentation**
- Complete Python documentation set created
- Comparison guide explains differences
- Both setup procedures documented clearly
- Examples provided for both languages

✅ **Educational**
- Clear explanations of design choices
- Side-by-side code comparisons
- Discussion of idiomatic patterns
- Guidance on when to use each

## Key Design Principles

1. **No Direct Translation**: Python implementation uses Pythonic patterns, not TS ports
2. **Language Strengths**: Leverage each language's ecosystem and idioms
3. **Educational Focus**: Code serves as learning resource for both languages
4. **Maintainability**: Clear separation enables independent evolution
5. **Best Practices**: Each implementation exemplifies production-quality code

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Breaking existing TS code | Move files without modification, verify with tests |
| Python async complexity | Use established asyncio patterns, document thoroughly |
| Inconsistent behavior | Shared test suite ensures equivalence |
| Configuration confusion | Clear naming (bc-calculator-ts vs bc-calculator-py) |
| Documentation drift | Single source for test cases, comparison guide |

## Future Enhancements

After initial dual implementation:

1. **Shared Test Suite**: JSON test definitions used by both
2. **Performance Benchmarking**: Compare execution times
3. **Extended Examples**: More complex use cases in both
4. **CI/CD**: Automated testing for both implementations
5. **Additional Languages**: Rust, Go, or other MCP SDK languages

---

**Next Step**: Review this architecture plan, then proceed to implementation starting with Phase 1 (TypeScript restructuring).