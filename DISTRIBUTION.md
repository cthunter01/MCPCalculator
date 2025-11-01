# BC Calculator MCP Server - Distribution Guide

## 🎯 Repository Ready for Distribution

This repository contains a complete, production-ready MCP server for arbitrary precision mathematical calculations using the Unix BC calculator.

## 📦 Repository Contents

```
/home/travis/Development/MCPCalculator/
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
├── package.json                 # NPM package configuration
├── tsconfig.json               # TypeScript configuration
├── README.md                    # Main documentation
├── ARCHITECTURE.md             # System design (583 lines)
├── IMPLEMENTATION_GUIDE.md     # Developer guide (688 lines)
├── QUICK_REFERENCE.md          # Quick reference (373 lines)
├── PROJECT_SUMMARY.md          # Project overview (305 lines)
├── IMPLEMENTATION_COMPLETE.md  # Implementation summary
└── src/                        # TypeScript source code
    ├── types.ts               # Type definitions
    ├── input-validator.ts     # Security validation
    ├── bc-process.ts          # Process wrapper
    ├── bc-process-pool.ts     # Pool manager
    └── index.ts               # MCP server main
```

## 🚀 Installation for End Users

### Prerequisites

1. **Node.js** (v18 or higher)
2. **BC Calculator** - Standard on most Unix systems
   ```bash
   # Check if installed
   which bc
   
   # Install if needed
   # Ubuntu/Debian
   sudo apt-get install bc
   
   # macOS
   brew install bc
   
   # Fedora/RHEL
   sudo dnf install bc
   ```

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd MCPCalculator
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Build the project**:
   ```bash
   npm run build
   ```

4. **Configure MCP settings**:
   
   Add to your MCP settings file (typically at `~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json`):
   
   ```json
   {
     "mcpServers": {
       "bc-calculator": {
         "command": "node",
         "args": [
           "/absolute/path/to/MCPCalculator/build/index.js"
         ],
         "disabled": false
       }
     }
   }
   ```
   
   Replace `/absolute/path/to/MCPCalculator` with the actual path where you cloned the repository.

5. **Restart your MCP client** to load the server

## 🎓 Usage Examples

Once installed, you'll have access to three tools:

### 1. Basic Calculation
```json
{
  "tool": "calculate",
  "arguments": {
    "expression": "355/113",
    "precision": 15
  }
}
```

Result:
```json
{
  "result": "3.141592920353982",
  "expression": "355/113",
  "precision": 15,
  "executionTimeMs": 45
}
```

### 2. Advanced Calculations
```json
{
  "tool": "calculate_advanced",
  "arguments": {
    "script": "scale=10\npi=4*a(1)\npi*2",
    "precision": 10
  }
}
```

### 3. Set Precision
```json
{
  "tool": "set_precision",
  "arguments": {
    "precision": 50
  }
}
```

## 🔧 Development

### Build Commands

```bash
# Build once
npm run build

# Watch mode (rebuild on changes)
npm run watch

# Clean rebuild
rm -rf build && npm run build
```

### Project Structure

- **src/types.ts** - Core type definitions and error classes
- **src/input-validator.ts** - Security validation (prevents command injection)
- **src/bc-process.ts** - Individual BC process wrapper with I/O handling
- **src/bc-process-pool.ts** - Process pool manager (3 concurrent processes)
- **src/index.ts** - Main MCP server with tool definitions

### Key Features

- ✅ **Security**: Input validation prevents command injection
- ✅ **Performance**: Process pool handles 3 concurrent calculations
- ✅ **Reliability**: Auto-recovery on process failures
- ✅ **Precision**: Configurable 0-100 decimal places
- ✅ **Full BC Support**: Math library functions, variables, control flow

## 📝 Publishing to GitHub/GitLab

### GitHub

```bash
# Add remote
git remote add origin https://github.com/username/bc-calculator-mcp.git

# Push to GitHub
git push -u origin master
```

### GitLab

```bash
# Add remote
git remote add origin https://gitlab.com/username/bc-calculator-mcp.git

# Push to GitLab
git push -u origin master
```

### Recommended Repository Settings

- **Name**: `bc-calculator-mcp` or `mcp-bc-calculator`
- **Description**: "MCP server for arbitrary precision mathematical calculations using BC calculator"
- **Topics/Tags**: `mcp`, `calculator`, `bc`, `math`, `arbitrary-precision`, `model-context-protocol`, `typescript`
- **License**: MIT (already included)

## 📚 Documentation

Complete documentation is included in the repository:

- **README.md** - User-facing documentation with examples
- **ARCHITECTURE.md** - System design and component architecture
- **IMPLEMENTATION_GUIDE.md** - Detailed implementation guide for developers
- **QUICK_REFERENCE.md** - Quick reference for common tasks
- **PROJECT_SUMMARY.md** - Project overview and status

## 🔐 Security

This server implements multiple security layers:

1. **Input Validation** - Character whitelist, length limits
2. **Pattern Blocking** - Prevents command injection attempts
3. **Process Isolation** - No shell execution
4. **Timeout Protection** - 30-second calculation limit
5. **Resource Limits** - Process pool size constraints

## 📊 Performance

Expected performance characteristics:

| Operation | Target Time |
|-----------|-------------|
| Simple arithmetic (2+2) | <10ms |
| Division with precision | <20ms |
| Math functions | <50ms |
| Complex scripts | <200ms |
| Concurrent requests | 3 parallel |

## 🐛 Troubleshooting

### BC Not Found
```bash
# Install BC
sudo apt-get install bc  # Ubuntu/Debian
brew install bc          # macOS
```

### Permission Denied
```bash
# Make executable
chmod +x build/index.js
```

### Module Not Found
```bash
# Ensure package.json has "type": "module"
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built on the [Model Context Protocol SDK](https://github.com/modelcontextprotocol)
- Uses the standard [GNU BC](https://www.gnu.org/software/bc/) calculator
- TypeScript for type safety and developer experience

## 📞 Support

For issues, questions, or feature requests:
1. Check the documentation in this repository
2. Review the troubleshooting section
3. Open an issue on the repository

---

**Current Git Status**: 
- ✅ Repository initialized
- ✅ Initial commit created
- ✅ All files committed
- ✅ Ready for remote push