# BC Calculator MCP Server - Project Summary

## What We're Building

A production-ready MCP server that provides arbitrary precision mathematical calculations using the Unix `bc` calculator, with enterprise-grade security, performance, and reliability.

## 📋 Planning Documents Created

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System Design (583 lines)
   - Complete component architecture
   - Security model
   - Process management flow
   - Mermaid diagrams

2. **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Developer Guide (688 lines)
   - Step-by-step implementation
   - Code skeletons for all files
   - Testing strategy
   - Deployment instructions

3. **[README.md](README.md)** - User Documentation (429 lines)
   - Installation guide
   - Usage examples
   - API reference
   - Troubleshooting

4. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Cheat Sheet (373 lines)
   - Security checklist
   - Code patterns
   - Testing checklist
   - Common fixes

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         BC Calculator MCP Server                 │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  MCP Server (index.ts)                     │ │
│  │  • Tool: calculate                         │ │
│  │  • Tool: calculate_advanced                │ │
│  │  • Tool: set_precision                     │ │
│  └────────────┬───────────────────────────────┘ │
│               │                                  │
│  ┌────────────▼───────────────────────────────┐ │
│  │  Input Validator (input-validator.ts)     │ │
│  │  • Security: Whitelist/Blacklist          │ │
│  │  • Max length: 10KB                        │ │
│  │  • No command injection                    │ │
│  └────────────┬───────────────────────────────┘ │
│               │                                  │
│  ┌────────────▼───────────────────────────────┐ │
│  │  BC Process Pool (bc-process-pool.ts)     │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │ BC Proc  │ │ BC Proc  │ │ BC Proc  │  │ │
│  │  │ #1       │ │ #2       │ │ #3       │  │ │
│  │  │ Ready    │ │ Busy     │ │ Ready    │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘  │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  Each process (bc-process.ts):                  │
│  • Spawned with -l flag (math library)          │
│  • Precision: 20 decimals (configurable)        │
│  • Timeout: 30 seconds                          │
│  • Auto-respawn on crash                        │
└─────────────────────────────────────────────────┘
```

## 🔐 Security Design

**Multi-Layer Protection**:
1. **Input Validation Layer**
   - Character whitelist: `[0-9a-zA-Z+\-*\/^().,;\s=<>!&|%{}[\]]`
   - Blacklist patterns: `system()`, `exec()`, backticks, pipes, redirects
   - Maximum expression length: 10,000 characters

2. **Process Isolation Layer**
   - No shell execution (`shell: false`)
   - Direct BC binary spawn
   - Separate process per calculation

3. **Resource Protection Layer**
   - 30-second timeout per calculation
   - Process pool size limit (3)
   - Automatic cleanup on timeout/failure

## 📁 File Structure

```
/home/travis/.local/share/Roo-Code/MCP/bc-calculator/
├── package.json              # Dependencies & scripts
├── tsconfig.json            # TypeScript config
├── README.md                # User docs
├── ARCHITECTURE.md          # System design
├── IMPLEMENTATION_GUIDE.md  # Dev guide
├── QUICK_REFERENCE.md       # Cheat sheet
├── src/
│   ├── types.ts            # Type definitions
│   ├── input-validator.ts  # Security validation
│   ├── bc-process.ts       # Single BC process wrapper
│   ├── bc-process-pool.ts  # Process pool manager
│   └── index.ts            # MCP server main
└── build/                   # Compiled output
    └── index.js            # Executable server
```

## 🎯 Implementation Roadmap

### Phase 1: Foundation (Todos 1-3)
- Create project directory structure
- Initialize package.json with dependencies
- Configure TypeScript (tsconfig.json)

### Phase 2: Core Components (Todos 4-6, 13)
- Design and implement type definitions
- Build input validator with security rules
- Create BC process wrapper with I/O handling
- Implement process pool manager

### Phase 3: MCP Integration (Todos 7-9)
- Implement `calculate` tool
- Implement `calculate_advanced` tool  
- Implement `set_precision` tool

### Phase 4: Error & Resource Management (Todos 10-14)
- Add comprehensive error handling
- Implement timeout mechanism
- Add process recovery logic
- Create request queue system

### Phase 5: Deployment (Todos 15-16)
- Build TypeScript to JavaScript
- Auto-install to MCP settings
- Verify server registration

### Phase 6: Testing & Documentation (Todos 17-20)
- Test basic arithmetic
- Test advanced features
- Write unit tests
- Create final documentation

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | TypeScript 5.3+ | Type safety & modern syntax |
| Runtime | Node.js 18+ | Server execution |
| Protocol | MCP SDK 1.0.4+ | MCP compliance |
| Calculator | bc (GNU) | Arbitrary precision math |
| Process Mgmt | child_process | BC process spawning |
| Validation | Regex + Whitelist | Input security |

## 🚀 Key Features

### Functional
✅ Arbitrary precision (0-100 decimal places)
✅ Basic arithmetic (+, -, *, /, ^, %)  
✅ Math library (sqrt, sin, cos, arctan, log, exp)
✅ Variables and assignments
✅ Control flow (if, while, for)
✅ Multi-line scripts
✅ Three concurrent processes

### Non-Functional
✅ Security: Command injection prevention
✅ Performance: <50ms for typical calculations
✅ Reliability: Auto-recovery from crashes
✅ Usability: Clear error messages
✅ Maintainability: Well-documented code
✅ Testability: Comprehensive test suite

## 📊 Expected Performance

| Operation | Target | Notes |
|-----------|--------|-------|
| Simple calc (2+2) | <10ms | Fastest path |
| Division w/ precision | <20ms | Common use case |
| Math functions | <50ms | Using -l library |
| Complex scripts | <200ms | Multi-statement |
| Process spawn | <100ms | One-time cost |
| Concurrent requests | 3 parallel | Pool size limit |

## 🧪 Test Coverage Plan

### Unit Tests
- Input validation edge cases
- Dangerous pattern detection
- Expression sanitization
- Error message formatting

### Integration Tests
- All mathematical operators
- All math library functions
- Variable assignment
- Multi-line scripts
- Precision handling
- Timeout scenarios
- Concurrent requests
- Process failure recovery

### Security Tests
- Command injection attempts
- Shell metacharacter blocking
- File access prevention
- Resource exhaustion

## 📝 Configuration

### MCP Settings Entry
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

### Default Server Config
```typescript
{
  poolSize: 3,              // Concurrent BC processes
  defaultPrecision: 20,     // Decimal places
  defaultTimeout: 30000,    // Milliseconds
  maxExpressionLength: 10000 // Characters
}
```

## 🎓 Learning Resources

- **BC Manual**: `man bc` or https://www.gnu.org/software/bc/manual/html_mono/bc.html
- **MCP Docs**: https://modelcontextprotocol.io/
- **Node child_process**: https://nodejs.org/api/child_process.html
- **TypeScript**: https://www.typescriptlang.org/docs/

## ✅ Success Criteria

The implementation will be considered successful when:

1. ✅ All 20 todo items are completed
2. ✅ Server builds without TypeScript errors
3. ✅ Server appears in MCP settings
4. ✅ All three tools are functional
5. ✅ Security validation prevents dangerous inputs
6. ✅ Basic test cases pass
7. ✅ Advanced test cases pass
8. ✅ Concurrent requests work correctly
9. ✅ Error handling works as expected
10. ✅ Documentation is complete

## 📦 Deliverables

1. ✅ Planning documents (this and others)
2. ⏳ Working TypeScript source code
3. ⏳ Compiled JavaScript executable
4. ⏳ MCP configuration entry
5. ⏳ Test suite
6. ⏳ User documentation
7. ⏳ Implementation verification

## 🔄 Next Steps

Once you approve this plan, I will:

1. Switch to **Code Mode**
2. Implement all components according to the architecture
3. Build and test the server
4. Auto-install to MCP settings
5. Verify functionality with test cases
6. Provide usage examples

---

**Ready to proceed?** If you approve this plan, I'll switch to Code mode and begin implementation following the detailed guides in ARCHITECTURE.md and IMPLEMENTATION_GUIDE.md.