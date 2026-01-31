# Playwright MCP Server

A production-ready Model Context Protocol (MCP) server that provides browser automation capabilities using Playwright. Built with the `mcp-use` framework for enhanced developer experience with built-in Inspector UI and comprehensive error handling.

## Overview

This MCP server exposes 6 powerful browser automation tools that allow AI assistants like Claude to interact with web pages, extract information, and perform automated testing. All operations are performed in a managed Chromium browser instance with robust error handling and timeout management.

**Key Features:**
- 🎭 **Playwright Integration** - Full async Playwright API support
- 🔍 **Built-in Inspector UI** - Test tools interactively at `http://localhost:8000/inspector`
- 📡 **Auto-discovery** - OpenMCP metadata endpoint at `/openmcp.json`
- 🛡️ **Robust Error Handling** - Clear, actionable error messages with suggestions
- 🔄 **Crash Recovery** - Automatic browser restart on failures
- ⚙️ **Highly Configurable** - All timeouts and settings via environment variables
- 🐛 **Debug Mode** - Enhanced logging and `/docs` endpoint

## Features

### 6 Browser Automation Tools

1. **navigate** - Navigate to URLs with configurable wait conditions
2. **click_element** - Click elements by CSS selector
3. **fill_input** - Fill form inputs with text
4. **extract_text** - Extract text content from elements
5. **screenshot** - Take viewport or full-page screenshots
6. **get_page_info** - Get current page URL, title, and viewport size

All tools return standardized responses with either success data or detailed error information.

## Installation

### Prerequisites

- Python 3.13 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

```bash
cd "C:\Users\David Jr\playwright-mcp-server"
```

2. **Create a virtual environment**

```bash
python -m venv venv
```

3. **Activate the virtual environment**

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Install Playwright browsers**

```bash
playwright install chromium
```

6. **Configure environment variables**

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` to customize settings (optional - defaults work out of the box).

## Quick Start

### Running the Server

```bash
python src/server.py
```

You should see output like:

```
============================================================
🚀 Playwright Automation Server v1.0.0
============================================================

📊 Inspector UI:    http://localhost:8000/inspector
📄 API Docs:        http://localhost:8000/docs
📋 OpenMCP:         http://localhost:8000/openmcp.json
🔌 MCP Endpoint:    http://localhost:8000/mcp

💡 Open http://localhost:8000/inspector in your browser
   to test all 6 browser automation tools interactively
   Press CTRL+C to stop the server

============================================================
```

### Accessing the Inspector UI

**What to do:**
1. Copy the Inspector URL: `http://localhost:8000/inspector`
2. Paste it into your web browser (Chrome, Firefox, Edge, Safari, etc.)
3. The Inspector UI will open where you can test all tools

**Note:** If you see `0.0.0.0` in any URL, replace it with `localhost` in your browser.

The Inspector UI allows you to:
- See all available tools and their parameters
- Test tools interactively with a web form
- View real-time responses and errors
- Explore the OpenMCP metadata

**How to use the Inspector:**
1. You'll see a list of 6 tools (navigate, click_element, fill_input, etc.)
2. Click on a tool to see its description and parameters
3. Fill in the parameters (example: url = "https://example.com")
4. Click "Execute" to run the tool
5. View the results in the response panel

### Testing with the Manual Test Script

```bash
python tests/manual_test.py
```

This runs a complete integration test suite covering all tools.

## Usage Examples

### Tool 1: Navigate

Navigate to a URL and wait for page load:

```python
await navigate("https://example.com")
# Returns:
# {
#   "success": True,
#   "url": "https://example.com/",
#   "title": "Example Domain"
# }
```

Navigate with custom wait condition:

```python
await navigate("https://example.com", wait_until="networkidle")
```

**Wait conditions:**
- `"load"` - Wait for the load event (default)
- `"domcontentloaded"` - Wait for DOMContentLoaded event
- `"networkidle"` - Wait until network is idle (no requests for 500ms)

### Tool 2: Click Element

Click an element by CSS selector:

```python
await click_element("button.submit")
# Returns:
# {
#   "success": True,
#   "selector": "button.submit",
#   "element_text": "Submit Form"
# }
```

### Tool 3: Fill Input

Fill a form input with text:

```python
await fill_input("input[name='email']", "user@example.com")
# Returns:
# {
#   "success": True,
#   "selector": "input[name='email']",
#   "text_length": 16
# }
```

### Tool 4: Extract Text

Extract text content from an element:

```python
await extract_text("h1")
# Returns:
# {
#   "success": True,
#   "selector": "h1",
#   "text": "Example Domain",
#   "text_length": 14
# }
```

### Tool 5: Screenshot

Take a viewport screenshot:

```python
await screenshot("./screenshots/homepage.png")
# Returns:
# {
#   "success": True,
#   "path": "C:\\Users\\David Jr\\playwright-mcp-server\\screenshots\\homepage.png",
#   "file_size": 52341,
#   "full_page": False,
#   "viewport": {"width": 1920, "height": 1080}
# }
```

Take a full-page screenshot:

```python
await screenshot("./screenshots/full.png", full_page=True)
```

**Supported formats:** `.png`, `.jpg`, `.jpeg`

### Tool 6: Get Page Info

Get current page information:

```python
await get_page_info()
# Returns:
# {
#   "success": True,
#   "url": "https://example.com/",
#   "title": "Example Domain",
#   "viewport": {"width": 1920, "height": 1080}
# }
```

## Configuration Reference

All configuration is done via environment variables in the `.env` file:

### Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode with enhanced logging | `true` |
| `HOST` | Server host address | `0.0.0.0` |
| `PORT` | Server port | `8000` |

### Browser Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `HEADLESS` | Run browser in headless mode | `true` |
| `BROWSER_TIMEOUT` | Browser launch timeout (ms) | `30000` |
| `VIEWPORT_WIDTH` | Browser viewport width | `1920` |
| `VIEWPORT_HEIGHT` | Browser viewport height | `1080` |

### Operation Timeouts

| Variable | Description | Default |
|----------|-------------|---------|
| `NAVIGATION_TIMEOUT` | Page navigation timeout (ms) | `30000` |
| `ELEMENT_TIMEOUT` | Element interaction timeout (ms) | `10000` |
| `SCREENSHOT_TIMEOUT` | Screenshot capture timeout (ms) | `5000` |

### Screenshot Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SCREENSHOT_DIR` | Directory for screenshots | `./screenshots` |

## Error Handling

All tools return standardized error responses with actionable suggestions:

```python
{
  "success": False,
  "error": "Element 'button.submit' not found or not clickable within 10000ms",
  "error_type": "ElementNotFound",
  "suggestion": "Check if selector is correct and element is visible",
  "selector": "button.submit"
}
```

### Error Types

- **ValidationError** - Invalid inputs (bad URL, empty parameters, wrong types)
- **ElementNotFound** - Selector not found or element not visible/clickable
- **TimeoutError** - Operation exceeded timeout
- **NetworkError** - DNS failures, connection refused, SSL errors
- **FileSystemError** - File write permission errors
- **InvalidElementState** - Element is disabled or read-only
- **UnknownError** - Unexpected errors with details

### Common Issues and Solutions

#### Browser fails to launch

**Error:** `Failed to launch browser`

**Solution:**
1. Ensure Playwright browsers are installed: `playwright install chromium`
2. Check that you have sufficient permissions
3. Try running with `HEADLESS=false` in `.env` to see browser window

#### Element not found

**Error:** `Element not found with given selector`

**Solution:**
1. Verify the CSS selector is correct
2. Check if element is inside an iframe (not currently supported)
3. Increase `ELEMENT_TIMEOUT` if page loads slowly
4. Use browser dev tools to test your selector

#### Navigation timeout

**Error:** `Navigation timed out after 30000ms`

**Solution:**
1. Increase `NAVIGATION_TIMEOUT` in `.env`
2. Check your internet connection
3. Verify the URL is accessible
4. Try using `wait_until="domcontentloaded"` instead of `"load"`

#### Screenshot permission denied

**Error:** `Permission denied`

**Solution:**
1. Check write permissions for the target directory
2. Ensure parent directories exist (created automatically by the tool)
3. Verify you have disk space available

## Development

### Project Structure

```
playwright-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py          # Main MCP server with 6 tools
│   └── browser_manager.py # Singleton browser lifecycle management
├── tests/
│   ├── __init__.py
│   ├── test_server.py     # Unit tests
│   └── manual_test.py     # Integration test script
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── pyproject.toml         # Project metadata
```

### Running Tests

**Unit tests** (requires pytest):

```bash
pytest tests/test_server.py -v
```

**Integration tests**:

```bash
python tests/manual_test.py
```

### Code Quality

This project follows best practices:
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Async/await throughout
- ✅ Singleton pattern for browser management
- ✅ Standardized error responses
- ✅ Configuration via environment variables
- ✅ Graceful shutdown handling

### Architecture

**BrowserManager** (Singleton):
- Manages browser lifecycle
- Lazy initialization (browser starts on first use)
- Async lock prevents race conditions
- Automatic crash recovery
- Graceful cleanup on shutdown

**MCP Server**:
- Built with `mcp-use` framework
- 6 tools decorated with `@server.tool()`
- Streamable HTTP transport for Inspector UI
- Signal handlers for graceful shutdown
- Comprehensive error parsing

## Integration with Claude Desktop

To use this server with Claude Desktop, add to your Claude config:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "python",
      "args": [
        "C:\\Users\\David Jr\\playwright-mcp-server\\src\\server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\David Jr\\playwright-mcp-server\\src"
      }
    }
  }
}
```

**Note:** For production use with Claude Desktop, modify `server.py` to use `transport="stdio"` instead of `transport="streamable-http"`.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - feel free to use this in your own projects.

## Support

For issues and questions:
- Check the Troubleshooting section above
- Review the test files for usage examples
- Open an issue on GitHub

## Acknowledgments

Built with:
- [Playwright](https://playwright.dev/) - Browser automation framework
- [mcp-use](https://github.com/modelcontextprotocol/mcp-use) - Enhanced MCP server framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - Protocol specification

---

**Version:** 1.0.0
**Author:** Built with Claude Code
**Last Updated:** 2026-01-30
