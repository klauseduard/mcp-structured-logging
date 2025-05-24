# Simple MCP Structured Logging Server

A minimal Model Context Protocol (MCP) server that allows AI agents like Claude to log structured events to files and query recent logs. Perfect for debugging AI workflows, creating audit trails, and tracking AI decision-making processes.

## ✨ Features

- **🔄 Structured logging** in JSON Lines format for easy parsing
- **📅 Daily log files** automatically created (`logs/YYYY-MM-DD.jsonl`)
- **🛠️ Three simple MCP tools** ready for AI agents
- **🔍 Query recent entries** with optional filtering by level/count
- **⚡ Minimal dependencies** and single-file implementation (~270 lines)
- **🧪 Comprehensive test suite** with 19 test cases

## 🚀 Quick Start

### 1. Clone and Setup Virtual Environment
```bash
git clone <your-repo-url> mcp-structured-logging
cd mcp-structured-logging

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Test the Server
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run tests to verify everything works
python test_server.py

# Start the server (for testing)
python server.py
```

## 📦 Installation for AI Assistants

### 🎯 Cursor IDE Integration

1. **Install the server with virtual environment**:
```bash
cd ~/Documents/mcp-servers  # or your preferred location
git clone <repo-url> structured-logging
cd structured-logging

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Cursor MCP via JSON file**:

**Global Configuration** (available in all projects):
Create or edit `~/.cursor/mcp.json`:

**macOS/Linux:**
```json
{
  "mcpServers": {
    "structured-logging": {
      "command": "/full/path/to/structured-logging/venv/bin/python",
      "args": ["/full/path/to/structured-logging/server.py"],
      "cwd": "/full/path/to/structured-logging"
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "structured-logging": {
      "command": "C:\\full\\path\\to\\structured-logging\\venv\\Scripts\\python.exe",
      "args": ["C:\\full\\path\\to\\structured-logging\\server.py"],
      "cwd": "C:\\full\\path\\to\\structured-logging"
    }
  }
}
```

**Project-Specific Configuration** (only for current project):
Create `.cursor/mcp.json` in your project root with the same format.

3. **Restart Cursor** and the logging tools will be available to Claude!

### 🤖 Claude AI Web Interface (Remote MCP) - **NEW!**

As of May 2025, Claude AI web interface supports remote MCP servers directly. This is the easiest method for most users.

1. **Make your server accessible via HTTP** (for remote access):
```bash
# Install additional dependency for HTTP server
pip install fastapi uvicorn

# Create a simple HTTP wrapper (optional - for remote access)
# For local testing, you can skip this and use stdio transport
```

2. **Connect via Claude AI Web Interface**:
   - Go to [claude.ai](https://claude.ai) and sign in (requires Max, Team, or Enterprise plan)
   - Click your profile icon → **Settings** → **Integrations**
   - Click **"Add More"** to add a new MCP server
   - For local testing, you can use stdio transport directly

3. **For local stdio transport** (recommended for development):
   - In Claude web interface, add your local server
   - Use the same JSON configuration format as desktop
   - Claude will handle the stdio communication automatically

4. **Test the connection**:
   - Start a new chat
   - Click the **"Search & Tools"** button at the bottom
   - Look for "structured-logging" in the available tools
   - Try: *"Log an info event that I'm testing the MCP integration"*

### 🖥️ Claude Desktop App Integration

For users who prefer the desktop application:

1. **Setup server with virtual environment**:
```bash
# If not already done
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Locate Claude config file**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. **Add server configuration using virtual environment Python**:

**macOS/Linux**:
```json
{
  "mcpServers": {
    "structured-logging": {
      "command": "/full/path/to/mcp-structured-logging/venv/bin/python",
      "args": ["/full/path/to/mcp-structured-logging/server.py"],
      "cwd": "/full/path/to/mcp-structured-logging"
    }
  }
}
```

**Windows**:
```json
{
  "mcpServers": {
    "structured-logging": {
      "command": "C:\\full\\path\\to\\mcp-structured-logging\\venv\\Scripts\\python.exe",
      "args": ["C:\\full\\path\\to\\mcp-structured-logging\\server.py"],
      "cwd": "C:\\full\\path\\to\\mcp-structured-logging"
    }
  }
}
```

4. **Restart Claude Desktop** - the tools will appear automatically!

### 🚀 JetBrains IDEs (IntelliJ, PyCharm, etc.)

For JetBrains IDEs with AI Assistant:

1. **Setup the MCP server** (same virtual environment setup as above)

2. **Configure in IDE**:
   - Open **Settings** → **Tools** → **AI Assistant** → **Model Context Protocol (MCP)**
   - Or in AI chat, type `/` and select **"Add Command"**

3. **Add server configuration**:
   - **Server name**: `structured-logging`
   - **Command**: `/full/path/to/venv/bin/python`
   - **Arguments**: `/full/path/to/server.py`
   - **Working directory**: `/full/path/to/project`

4. **Test the integration**:
   - Enable **Codebase mode** in AI Assistant
   - In AI chat, type `/` to see available MCP commands
   - Try: `/log_event` to use the logging tools

### 🐍 Python MCP Client

For custom integrations or testing:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_logging():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        cwd="/path/to/mcp-structured-logging"
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Use the logging tools
            result = await session.call_tool("log_event", {
                "level": "info",
                "message": "Test from Python client",
                "context": {"client": "python"}
            })
            print(result)

asyncio.run(test_logging())
```

## 🛠️ MCP Tools Reference

### 1. `log_event` - General Purpose Logging
Write a structured log entry to the daily log file.

**Parameters:**
- `level` (required): `"debug"`, `"info"`, `"warn"`, or `"error"`
- `message` (required): The main log message
- `context` (optional): Additional structured data as a JSON object

**Example Usage in Claude:**
> "Please log that the user started a new chat session with context about their timezone"

**Result:**
```json
{
  "timestamp": "2025-05-24T10:30:00Z",
  "level": "info", 
  "message": "User started new chat session",
  "context": {
    "timezone": "UTC-8",
    "session_id": "abc123",
    "user_agent": "Claude Desktop"
  }
}
```

### 2. `log_error` - Error Tracking
Log errors with detailed information and stack traces.

**Parameters:**
- `message` (required): Error description
- `error_details` (required): Detailed error information or stack trace
- `context` (optional): Additional context about when/where the error occurred

**Example Usage in Claude:**
> "Log an error - the API call to weather service failed with a timeout"

**Result:**
```json
{
  "timestamp": "2025-05-24T10:30:00Z",
  "level": "error",
  "message": "Weather API call failed", 
  "context": {
    "error_details": "requests.exceptions.Timeout: HTTPSConnectionPool timeout",
    "api_endpoint": "https://api.weather.com/v1/current",
    "timeout_duration": "30s"
  }
}
```

### 3. `query_logs` - Log Analysis
Query recent log entries from all log files.

**Parameters:**
- `count` (optional): Number of entries to return (default: 50, max: 1000)
- `level_filter` (optional): Filter by `"debug"`, `"info"`, `"warn"`, or `"error"`

**Example Usage in Claude:**
> "Show me the last 10 error entries from the logs"

**Returns:**
```json
{
  "total_entries": 3,
  "entries": [
    {
      "timestamp": "2025-05-24T10:30:00Z",
      "level": "error",
      "message": "API timeout occurred",
      "context": {...}
    }
  ]
}
```

## 📊 Log Entry Format

Each log entry is stored as a JSON object on a single line (JSON Lines format):

```json
{
  "timestamp": "2025-05-24T10:30:00Z",  // ISO format with timezone
  "level": "info",                      // debug|info|warn|error  
  "message": "User completed checkout", // Human-readable message
  "context": {                          // Structured metadata
    "user_id": "123",
    "session_id": "abc", 
    "amount": 29.99,
    "payment_method": "stripe"
  }
}
```

## 🗂️ File Structure

```
mcp-structured-logging/
├── server.py           # Main MCP server (266 lines)
├── test_server.py      # Comprehensive test suite (406 lines)
├── requirements.txt    # Dependencies (mcp, pydantic)
├── venv/              # Virtual environment (created by you)
│   ├── bin/python      # Python interpreter for MCP config
│   └── ...            # Virtual environment files
├── logs/              # Log files directory
│   ├── 2025-05-24.jsonl  # Today's logs
│   ├── 2025-05-23.jsonl  # Yesterday's logs
│   └── ...               # Historical daily files
└── README.md          # This documentation
```

## 🎯 Real-World Usage Examples

### AI Workflow Debugging
```
Claude: I'll help you debug this API issue. Let me log each step...

[Uses log_event to track each API call attempt]
[Uses log_error when calls fail]
[Uses query_logs to analyze patterns]

"I can see from the logs that all failures happen around 2pm - this suggests a rate limiting issue during peak hours."
```

### Audit Trail Creation
```
Claude: I'll document all the changes I make to your codebase...

[Logs each file modification with context]
[Logs reasoning for each change]
[Creates searchable audit trail]

Later: "What did Claude change in the authentication module last week?"
[query_logs with appropriate filters shows all auth-related changes]
```

### Performance Monitoring
```
Claude: I'll track how long each operation takes...

[Logs start/end times for operations]
[Includes performance metrics in context]
[Enables analysis of slow operations]
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests (19 test cases)
python test_server.py

# Run specific test categories
python -m unittest test_server.TestCoreLoggingFunctions -v
python -m unittest test_server.TestMCPTools -v
python -m unittest test_server.TestEdgeCases -v

# Test MCP integration
python -c "
import asyncio
from server import call_tool
async def test():
    result = await call_tool('log_event', {'level': 'info', 'message': 'Test'})
    print('✅ MCP integration working:', result[0].text)
asyncio.run(test())
"
```

**Test Coverage:**
- ✅ Core logging functions (3 tests)
- ✅ Log reading & querying (4 tests) 
- ✅ Pydantic model validation (5 tests)
- ✅ MCP tool integration (5 tests)
- ✅ Edge cases & error handling (2 tests)

## 🔧 Troubleshooting

### Virtual Environment Issues
```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify you're in the virtual environment
which python  # Should show path to venv/bin/python
pip list  # Should show mcp and pydantic

# If packages missing, reinstall
pip install -r requirements.txt
```

### Server Won't Start
```bash
# Always use virtual environment Python
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Check Python/dependencies
python --version  # Should be 3.8+
pip list | grep mcp
pip install -r requirements.txt

# Test server syntax
python -m py_compile server.py
```

### Claude Can't See Tools
1. **Check config file location**:
   - **Cursor**: `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project)
   - **Claude Desktop**: `claude_desktop_config.json` (see paths above)
   - **Claude Web**: Settings → Integrations (web interface)
   - **JetBrains**: Settings → Tools → AI Assistant → MCP
2. **Verify account requirements**:
   - **Claude Web**: Requires Max, Team, or Enterprise plan for Integrations
   - **Other platforms**: Check subscription requirements
3. **Verify JSON syntax** - use a JSON validator to check for syntax errors
4. **Verify absolute paths** in configuration - including venv Python path
5. **Restart application** after config changes
6. **Check logs directory permissions**
7. **Ensure virtual environment path is correct**:
   ```bash
   # Find your venv Python path
   cd /path/to/mcp-structured-logging
   source venv/bin/activate
   which python  # Copy this path to your config
   ```
8. **Test MCP server directly**:
   ```bash
   # Test that your server starts correctly
   source venv/bin/activate
   python server.py
   # Should start without errors
   ```
9. **Check for tools in UI**:
   - **Claude Web/Desktop**: Look for "Search & Tools" button
   - **Cursor**: Check tool availability in chat
   - **JetBrains**: Type `/` in AI chat to see available commands

### Permission Issues
```bash
# Ensure logs directory is writable
chmod 755 logs/
ls -la logs/  # Should show write permissions
```

### Debug Mode
```bash
# Run server with verbose output for debugging
python server.py --debug  # (if you add debug flag)

# Or check the logs manually
tail -f logs/$(date +%Y-%m-%d).jsonl
```

## 🚧 Limitations

This is a **simple implementation** designed for POCs and development:

- ❌ No authentication or security
- ❌ No complex querying (text search, date ranges)
- ❌ No automatic log rotation or cleanup
- ❌ No distributed logging or remote storage
- ❌ No real-time log streaming
- ❌ No log compression or archiving

For production use, consider more robust logging solutions like ELK stack, Splunk, or cloud logging services.

## 🏗️ Development

### Architecture
- **Single-file server** (`server.py`) - easy to understand and modify
- **JSON Lines format** - simple, parseable, append-only
- **Daily file rotation** - automatic organization by date
- **Pydantic validation** - type safety and input validation
- **Async MCP protocol** - compatible with modern AI assistants

### Dependencies
- `mcp>=1.0.0` - Model Context Protocol framework
- `pydantic>=2.0.0` - Data validation and type hints

### Extending the Server
The server is designed to be easily extensible:

```python
# Add new log levels
VALID_LEVELS = ["debug", "info", "warn", "error", "critical"]

# Add new MCP tools
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    if name == "your_new_tool":
        # Implementation here
        pass
```

## 📄 License

MIT License - feel free to use, modify, and distribute for any purpose.

---

**🎯 Perfect for:** AI development, debugging workflows, audit trails, and understanding AI decision-making processes.

**🚀 Get started:** Configure with your AI assistant and start logging structured events in under 5 minutes! 