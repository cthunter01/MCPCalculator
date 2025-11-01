# BC Calculator MCP Server - Quick Reference

## Critical Implementation Checkpoints

### Security Must-Haves ✓

```typescript
// ❌ NEVER do this
spawn('bc', ['-l'], { shell: true })  // DANGEROUS!

// ✅ ALWAYS do this
spawn('bc', ['-l'], { shell: false }) // SAFE
```

**Input Validation Rules**:
- ✅ Maximum 10KB expression length
- ✅ Whitelist: `[0-9a-zA-Z+\-*\/^().,;\s=<>!&|%{}[\]]`
- ✅ Blacklist: `system()`, `exec()`, backticks, pipes, redirects
- ✅ Timeout: 30 seconds default

### File Checklist

Create these files in order:

```
src/
├── types.ts                 # 1. Type definitions first
├── input-validator.ts       # 2. Security layer
├── bc-process.ts           # 3. Process wrapper  
├── bc-process-pool.ts      # 4. Pool manager
└── index.ts                # 5. MCP server (uses all above)
```

### Key Code Patterns

#### Spawning BC Process
```typescript
const process = spawn('bc', ['-l'], {
  shell: false,              // ← REQUIRED for security
  stdio: ['pipe', 'pipe', 'pipe']
});

// Set precision immediately after spawn
process.stdin.write('scale=20\n');
```

#### Input Validation
```typescript
const validation = InputValidator.validate(expression);
if (!validation.valid) {
  return { isError: true, content: [{ 
    type: 'text', 
    text: validation.error 
  }]};
}
```

#### Timeout Pattern
```typescript
const timeout = setTimeout(() => {
  process.kill();
  reject(new Error('Timeout'));
}, 30000);

// Clear on success
clearTimeout(timeout);
```

#### Process Communication
```typescript
// Write to stdin
process.stdin.write(expression + '\n');

// Read from stdout (line-buffered)
let buffer = '';
process.stdout.on('data', (data: Buffer) => {
  buffer += data.toString();
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (line.trim()) {
      resolve(line.trim()); // ← Result
    }
  }
});

// Capture errors from stderr
process.stderr.on('data', (data: Buffer) => {
  const error = data.toString();
  reject(new Error(error));
});
```

## Common Pitfalls to Avoid

### ❌ DON'T
```typescript
// Don't use shell
spawn('bc -l', { shell: true })

// Don't skip validation
const result = await bc.evaluate(userInput); // UNSAFE!

// Don't forget cleanup
// ... (missing process.kill() on error)

// Don't use callbacks in 2024
process.on('data', function(data) { ... })
```

### ✅ DO
```typescript
// Use no-shell spawn with args array
spawn('bc', ['-l'], { shell: false })

// Always validate
const valid = InputValidator.validate(input);
if (!valid.valid) return error;

// Always cleanup
try {
  await evaluate(expr);
} finally {
  process.kill();
}

// Use modern async/await
const result = await new Promise<string>((resolve, reject) => {
  // ...
});
```

## Testing Checklist

### Basic Tests
- [ ] `2+2` → `4`
- [ ] `10/3` (precision=5) → `3.33333`
- [ ] `2^10` → `1024`

### Math Library Tests  
- [ ] `sqrt(2)` → `1.41421...`
- [ ] `s(0)` → `0` (sine of 0)
- [ ] `4*a(1)` → `3.14159...` (compute pi)

### Error Tests
- [ ] `2/0` → Error: divide by zero
- [ ] `system('ls')` → Validation error
- [ ] Too long expression → Validation error

### Advanced Tests
- [ ] Variables: `a=5; b=10; a+b` → `15`
- [ ] Loop: `for(i=0;i<3;i++) i` → `2`

### Stress Tests
- [ ] 3 concurrent requests
- [ ] Timeout with infinite loop
- [ ] Process recovery after crash

## MCP Tool Schemas (Copy-Paste Ready)

### calculate
```typescript
server.tool(
  'calculate',
  {
    expression: z.string()
      .describe('Mathematical expression to evaluate'),
    precision: z.number().min(0).max(100).optional()
      .describe('Decimal places (default: 20)')
  },
  async ({ expression, precision = 20 }) => {
    // Implementation here
  }
);
```

### calculate_advanced
```typescript
server.tool(
  'calculate_advanced',
  {
    script: z.string()
      .describe('Multi-line BC script with variables/functions'),
    precision: z.number().min(0).max(100).optional()
      .describe('Decimal places (default: 20)')
  },
  async ({ script, precision = 20 }) => {
    // Implementation here
  }
);
```

### set_precision
```typescript
server.tool(
  'set_precision',
  {
    precision: z.number().min(0).max(100)
      .describe('Number of decimal places')
  },
  async ({ precision }) => {
    // Implementation here
  }
);
```

## Debug Commands

```bash
# Test BC is available
which bc
bc --version

# Test BC manually
echo "scale=10; 22/7" | bc -l

# Check compiled output
ls -lh build/index.js

# View MCP settings
cat ~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json

# Rebuild on changes
npm run watch
```

## One-Liner Fixes

```bash
# Fix permissions
chmod +x build/index.js

# Reinstall deps
rm -rf node_modules package-lock.json && npm install

# Clean rebuild
rm -rf build && npm run build

# Install BC
sudo apt-get install bc  # Ubuntu/Debian
brew install bc          # macOS
```

## Performance Targets

| Operation | Target Time | Status |
|-----------|-------------|--------|
| Simple calc (2+2) | <10ms | ✓ |
| Division with precision | <20ms | ✓ |
| Math function | <50ms | ✓ |
| Advanced script | <200ms | ✓ |
| Process spawn | <100ms | ✓ |

## Architecture at a Glance

```
User Request
    ↓
InputValidator.validate()
    ↓
ProcessPool.acquireProcess()
    ↓
BCProcess.setPrecision()
    ↓
BCProcess.evaluate()
    ↓
    ← BC stdout/stderr
    ↓
ProcessPool.releaseProcess()
    ↓
Return JSON result
```

## Configuration Values

```typescript
// Recommended defaults
{
  poolSize: 3,              // Balance concurrency vs resources
  defaultPrecision: 20,     // Good for scientific calculations
  defaultTimeout: 30000,    // 30 seconds
  maxExpressionLength: 10000 // 10KB
}
```

## BC Math Library Functions

| Function | BC Syntax | Example | Result |
|----------|-----------|---------|--------|
| Sine | `s(x)` | `s(0)` | 0 |
| Cosine | `c(x)` | `c(0)` | 1 |
| Arctangent | `a(x)` | `a(1)` | 0.785398... |
| Natural log | `l(x)` | `l(2.71828)` | 1 |
| Exponential | `e(x)` | `e(1)` | 2.71828... |
| Square root | `sqrt(x)` | `sqrt(4)` | 2 |

Note: `s()`, `c()`, `a()`, `l()`, `e()` are only available with `-l` flag!

## Error Messages Reference

| Error Type | Example Message | Cause |
|------------|----------------|-------|
| Validation | "Expression contains invalid characters" | Bad input |
| BC Runtime | "BC error: divide by zero" | Math error |
| Timeout | "Calculation timeout after 30000ms" | Too long |
| Process | "BC process not ready" | Process crashed |

## Success Response Format

```json
{
  "content": [{
    "type": "text",
    "text": "{\"result\":\"4\",\"expression\":\"2+2\",\"precision\":20}"
  }]
}
```

## Error Response Format

```json
{
  "content": [{
    "type": "text", 
    "text": "Validation error: ..."
  }],
  "isError": true
}
```

## Implementation Sequence

1. ✅ **types.ts** - Core type definitions
2. ✅ **input-validator.ts** - Security first!
3. ✅ **bc-process.ts** - Single process wrapper
4. ✅ **bc-process-pool.ts** - Multi-process manager
5. ✅ **index.ts** - MCP server glue code
6. ✅ Build & test
7. ✅ Add to MCP settings
8. ✅ Verify with test cases

## Final Checks Before Deployment

- [ ] All files have proper imports/exports
- [ ] TypeScript compiles without errors
- [ ] Build output is executable (`+x`)
- [ ] MCP settings contains correct path
- [ ] BC is installed and in PATH
- [ ] Security validation is working
- [ ] Timeout mechanism tested
- [ ] Process pool initializes correctly
- [ ] All three tools respond properly
- [ ] Error handling catches edge cases

## Support Resources

- **Architecture**: `ARCHITECTURE.md` - System design
- **Implementation**: `IMPLEMENTATION_GUIDE.md` - Detailed code guide  
- **Usage**: `README.md` - User documentation
- **MCP Docs**: https://modelcontextprotocol.io/
- **BC Manual**: `man bc` or online GNU BC documentation