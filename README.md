# BC Calculator MCP Server

A Model Context Protocol (MCP) server that provides numerical computation capabilities by integrating with the Unix `bc` (Basic Calculator) command-line tool. This server exposes arbitrary precision arithmetic operations, mathematical functions, and complex expressions through the MCP protocol.

## Features

- ✨ **Arbitrary Precision Arithmetic**: Support for calculations with configurable decimal precision (0-100 digits)
- 🧮 **Advanced Math Functions**: Access to bc's math library including sqrt, sin, cos, arctan, natural log, exponential
- 🔄 **Concurrent Processing**: Process pool management for handling multiple calculations simultaneously
- 🛡️ **Security First**: Input validation and sanitization to prevent command injection
- ⚡ **Performance Optimized**: Process pooling for fast response times
- 🎯 **MCP Compliant**: Full MCP protocol implementation with tool discovery and JSON-RPC communication

## Installation

### Prerequisites

- **Node.js** (v18 or higher)
- **TypeScript** (v5.3 or higher)
- **bc** calculator (standard on most Unix systems)

Verify bc is installed:
```bash
which bc
bc --version
```

If not installed:
```bash
# Ubuntu/Debian
sudo apt-get install bc

# macOS
brew install bc

# Fedora/RHEL
sudo dnf install bc
```

### Setup

1. **Navigate to MCP servers directory**:
```bash
cd /home/travis/.local/share/Roo-Code/MCP
```

2. **Bootstrap the project** (if using create-server):
```bash
npx @modelcontextprotocol/create-server bc-calculator
cd bc-calculator
```

Or manually create the project structure:
```bash
mkdir -p bc-calculator/src
cd bc-calculator
```

3. **Install dependencies**:
```bash
npm install
```

4. **Build the server**:
```bash
npm run build
```

5. **Configure MCP settings**:

Add to `~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json`:

```json
{
  "mcpServers": {
    "bc-calculator": {
      "command": "node",
      "args": ["/home/travis/.local/share/Roo-Code/MCP/bc-calculator/build/index.js"]
    }
  }
}
```

## Usage

### Available Tools

#### 1. `calculate`

Evaluate basic mathematical expressions with configurable precision.

**Parameters**:
- `expression` (string, required): Mathematical expression to evaluate
- `precision` (number, optional): Decimal places for the result (default: 20, range: 0-100)

**Examples**:

```javascript
// Basic arithmetic
calculate({ expression: "2 + 2" })
// → { result: "4", expression: "2 + 2", precision: 20 }

// Division with precision
calculate({ expression: "355/113", precision: 15 })
// → { result: "3.141592920353982", expression: "355/113", precision: 15 }

// Powers and roots
calculate({ expression: "2^10" })
// → { result: "1024", expression: "2^10", precision: 20 }

calculate({ expression: "sqrt(2)", precision: 10 })
// → { result: "1.4142135623", expression: "sqrt(2)", precision: 10 }
```

#### 2. `calculate_advanced`

Execute advanced BC scripts with variables, functions, and control flow.

**Parameters**:
- `script` (string, required): Multi-line BC script
- `precision` (number, optional): Decimal places for results (default: 20)

**Examples**:

```javascript
// Variables
calculate_advanced({
  script: `
    a = 5
    b = 10
    a * b + sqrt(a)
  `,
  precision: 5
})

// Computing pi
calculate_advanced({
  script: `
    scale=15
    pi = 4*a(1)
    pi
  `
})
// → { result: "3.141592653589793", ... }

// Fibonacci sequence
calculate_advanced({
  script: `
    a = 0
    b = 1
    for (i = 0; i < 10; i++) {
      c = a + b
      a = b
      b = c
    }
    b
  `
})
```

#### 3. `set_precision`

Set the default precision for subsequent calculations.

**Parameters**:
- `precision` (number, required): Number of decimal places (0-100)

**Example**:

```javascript
set_precision({ precision: 50 })
// All subsequent calculations will use 50 decimal places
```

### Mathematical Functions (with -l flag)

When using the math library, these functions are available:

| Function | Description | Example |
|----------|-------------|---------|
| `sqrt(x)` | Square root | `sqrt(2)` → 1.41421... |
| `s(x)` | Sine (radians) | `s(3.14159/2)` → 1.0 |
| `c(x)` | Cosine (radians) | `c(0)` → 1.0 |
| `a(x)` | Arctangent (radians) | `a(1)` → 0.78539... |
| `l(x)` | Natural logarithm | `l(2.71828)` → 1.0 |
| `e(x)` | Exponential (e^x) | `e(1)` → 2.71828... |

### Supported Operators

- **Arithmetic**: `+`, `-`, `*`, `/`, `^` (power), `%` (modulo)
- **Comparison**: `<`, `>`, `<=`, `>=`, `==`, `!=`
- **Logical**: `&&`, `||`, `!`
- **Assignment**: `=`
- **Increment/Decrement**: `++`, `--`

### BC Language Features

- **Variables**: `a = 5; b = 10; a + b`
- **Arrays**: `a[0] = 1; a[1] = 2`
- **Conditionals**: `if (x > 0) { ... }`
- **Loops**: `while (i < 10) { ... }`, `for (i=0; i<10; i++) { ... }`
- **Functions**: Define custom functions with `define`

## Architecture

### Process Pool

The server maintains a pool of 3 BC processes to handle concurrent requests:

```
┌─────────────────────────────────────┐
│     BC Calculator MCP Server         │
├─────────────────────────────────────┤
│  Process Pool Manager                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │ BC #1   │ │ BC #2   │ │ BC #3   ││
│  │ (ready) │ │ (busy)  │ │ (ready) ││
│  └─────────┘ └─────────┘ └─────────┘│
├─────────────────────────────────────┤
│  Request Queue                       │
│  • Validation                        │
│  • Sanitization                      │
│  • Timeout Management                │
└─────────────────────────────────────┘
```

### Security Features

1. **Input Validation**
   - Character whitelist enforcement
   - Maximum expression length (10KB)
   - Dangerous pattern detection

2. **Command Injection Prevention**
   - No shell execution (spawn with `shell: false`)
   - Input sanitization before BC
   - Blocked patterns: `system()`, `exec()`, backticks, file redirects

3. **Resource Protection**
   - 30-second timeout per calculation
   - Process pool size limit (3 processes)
   - Automatic process recovery on failures

## Error Handling

The server provides detailed error messages for common issues:

### Validation Errors
```json
{
  "isError": true,
  "content": [{
    "type": "text",
    "text": "Validation error: Expression contains invalid characters"
  }]
}
```

### BC Runtime Errors
```json
{
  "isError": true,
  "content": [{
    "type": "text", 
    "text": "BC error: divide by zero"
  }]
}
```

### Timeout Errors
```json
{
  "isError": true,
  "content": [{
    "type": "text",
    "text": "Calculation timeout after 30000ms"
  }]
}
```

## Configuration

### Default Settings

- **Process Pool Size**: 3 concurrent BC processes
- **Default Precision**: 20 decimal places
- **Calculation Timeout**: 30 seconds
- **Max Expression Length**: 10,000 characters

### Environment Variables

None required - bc is a standard system utility.

### Optional: Custom Pool Size

Edit `src/index.ts` to adjust pool configuration:

```typescript
const pool = new BCProcessPool({
  poolSize: 5,          // Increase for more concurrency
  defaultPrecision: 20,
  defaultTimeout: 60000 // Increase for longer calculations
});
```

## Development

### Project Structure

```
bc-calculator/
├── package.json
├── tsconfig.json
├── README.md
├── src/
│   ├── index.ts              # MCP server entry point
│   ├── types.ts              # TypeScript definitions
│   ├── bc-process.ts         # BC process wrapper
│   ├── bc-process-pool.ts    # Process pool manager
│   ├── input-validator.ts    # Security validation
│   └── request-queue.ts      # Request management
└── build/                     # Compiled JavaScript
    └── index.js
```

### Build Commands

```bash
# Build once
npm run build

# Watch mode (rebuild on changes)
npm run watch

# Clean build
rm -rf build && npm run build
```

### Testing

```bash
# Manual testing via MCP client
# Use the Roo-Code interface to invoke tools

# Example test cases:
# 1. Basic: calculate("2+2")
# 2. Precision: calculate("22/7", precision=10)
# 3. Math: calculate("sqrt(2)*sqrt(2)", precision=15)
# 4. Error: calculate("2/0")
# 5. Advanced: calculate_advanced("a=5; b=10; a+b")
```

## Troubleshooting

### BC Not Found

**Error**: `spawn bc ENOENT`

**Solution**: Install bc calculator
```bash
sudo apt-get install bc  # Ubuntu/Debian
brew install bc          # macOS
```

### Permission Denied

**Error**: Cannot execute build/index.js

**Solution**:
```bash
chmod +x build/index.js
```

### Module Import Errors

**Error**: `Cannot find module`

**Solution**: Ensure `"type": "module"` is in package.json

### Timeout on Complex Calculations

**Symptom**: Long-running calculations fail

**Solution**: Increase timeout in tool parameters or pool config

### Process Pool Exhausted

**Symptom**: Delayed responses under heavy load

**Solution**: Increase poolSize in BCProcessPool configuration

## Performance

### Benchmarks

- **Simple arithmetic**: <10ms
- **Math functions**: <50ms  
- **Complex scripts**: <200ms
- **Concurrent requests**: 3 parallel calculations

### Optimization Tips

1. **Reuse connections**: The process pool automatically optimizes this
2. **Batch operations**: Use `calculate_advanced` for multiple related calculations
3. **Adjust precision**: Lower precision = faster calculations
4. **Increase pool**: For heavy concurrent use, increase pool size

## Contributing

Contributions welcome! Please:

1. Maintain TypeScript strict mode compliance
2. Add tests for new features
3. Update documentation
4. Follow existing code style
5. Ensure security validations remain intact

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built on the [Model Context Protocol SDK](https://github.com/modelcontextprotocol)
- Uses the standard [GNU bc](https://www.gnu.org/software/bc/) calculator
- Inspired by the need for arbitrary precision arithmetic in AI applications

## Support

For issues, questions, or feature requests:
1. Check the troubleshooting section
2. Review the implementation guide (IMPLEMENTATION_GUIDE.md)
3. Examine the architecture documentation (ARCHITECTURE.md)

## Version History

### 1.0.0 (Initial Release)
- Basic calculation support
- Advanced scripting support
- Process pool management
- Security validation
- MCP protocol compliance