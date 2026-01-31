"""Main MCP server with 6 browser automation tools using mcp-use framework."""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp_use.server import MCPServer
from playwright.async_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

from browser_manager import BrowserManager

# Load environment variables
load_dotenv()

# Configuration
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
NAVIGATION_TIMEOUT = int(os.getenv("NAVIGATION_TIMEOUT", "30000"))
ELEMENT_TIMEOUT = int(os.getenv("ELEMENT_TIMEOUT", "10000"))
SCREENSHOT_TIMEOUT = int(os.getenv("SCREENSHOT_TIMEOUT", "5000"))
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "./screenshots")

# Initialize MCP server
server = MCPServer(
    name="Playwright Automation Server",
    version="1.0.0",
    instructions=(
        "Browser automation server using Playwright. Provides tools for web navigation, "
        "element interaction, text extraction, and screenshots. All operations are performed "
        "in a managed browser instance with comprehensive error handling."
    ),
    debug=DEBUG,
)

# Initialize browser manager
browser_manager = BrowserManager()


# Error handling utilities
def parse_playwright_error(error: Exception) -> tuple[str, str]:
    """
    Parse Playwright errors into user-friendly error types and suggestions.

    Args:
        error: The caught exception

    Returns:
        tuple[str, str]: (error_type, suggestion)
    """
    error_msg = str(error).lower()

    if "net::err_name_not_resolved" in error_msg or "dns" in error_msg:
        return "NetworkError", "DNS lookup failed. Check URL spelling and internet connection"

    if "net::err_connection_refused" in error_msg:
        return "NetworkError", "Connection refused. The server may be down or unreachable"

    if "ssl" in error_msg or "certificate" in error_msg:
        return "NetworkError", "SSL certificate error. The site may have security issues"

    if "timeout" in error_msg or isinstance(error, (TimeoutError, PlaywrightTimeoutError)):
        return "TimeoutError", "Operation timed out. Try increasing timeout or check if site is accessible"

    if "element is not visible" in error_msg:
        return "ElementNotFound", "Element exists but not visible. Try scrolling or waiting for it to appear"

    if "unable to find element" in error_msg or "no element found" in error_msg:
        return "ElementNotFound", "Element not found with given selector. Check selector syntax"

    if "element is disabled" in error_msg or "readonly" in error_msg:
        return "InvalidElementState", "Element is disabled or read-only and cannot be modified"

    return "UnknownError", "An unexpected error occurred. Check the error message for details"


def create_error_response(
    error_type: str,
    message: str,
    suggestion: str,
    **kwargs
) -> dict:
    """
    Create standardized error response.

    Args:
        error_type: Type of error (ValidationError, ElementNotFound, etc.)
        message: Error message
        suggestion: Actionable suggestion for user
        **kwargs: Additional context fields

    Returns:
        dict: Standardized error response
    """
    return {
        "success": False,
        "error": message,
        "error_type": error_type,
        "suggestion": suggestion,
        **kwargs
    }


# Tool implementations
@server.tool()
async def navigate(url: str, wait_until: str = "load") -> dict:
    """
    Navigate to a URL in the browser.

    Args:
        url: The URL to navigate to (must start with http:// or https://)
        wait_until: When to consider navigation complete. Options:
                   - "load": Wait for the load event (default)
                   - "domcontentloaded": Wait for DOMContentLoaded event
                   - "networkidle": Wait until network is idle

    Returns:
        dict: Success status with URL and title, or error details
    """
    try:
        # Validation
        if not url.startswith(("http://", "https://")):
            return create_error_response(
                "ValidationError",
                "URL must start with http:// or https://",
                "Add http:// or https:// to the URL",
                url=url
            )

        if wait_until not in ["load", "domcontentloaded", "networkidle"]:
            return create_error_response(
                "ValidationError",
                f"Invalid wait_until value: {wait_until}",
                "Use 'load', 'domcontentloaded', or 'networkidle'",
                url=url
            )

        # Execution
        page = await browser_manager.get_page()
        await page.goto(url, wait_until=wait_until, timeout=NAVIGATION_TIMEOUT)

        # Success response
        return {
            "success": True,
            "url": page.url,
            "title": await page.title()
        }

    except PlaywrightTimeoutError:
        return create_error_response(
            "TimeoutError",
            f"Navigation timed out after {NAVIGATION_TIMEOUT}ms",
            "Increase NAVIGATION_TIMEOUT or check if site is accessible",
            url=url
        )
    except Exception as e:
        error_type, suggestion = parse_playwright_error(e)
        return create_error_response(error_type, str(e), suggestion, url=url)


@server.tool()
async def click_element(selector: str) -> dict:
    """
    Click an element by CSS selector.

    Args:
        selector: CSS selector of the element to click

    Returns:
        dict: Success status with element details, or error details
    """
    try:
        # Validation
        if not selector or not selector.strip():
            return create_error_response(
                "ValidationError",
                "Selector cannot be empty",
                "Provide a valid CSS selector",
                selector=selector
            )

        # Execution
        page = await browser_manager.get_page()
        element = page.locator(selector)

        # Wait for element and click
        await element.click(timeout=ELEMENT_TIMEOUT)

        # Get element text for confirmation
        element_text = await element.text_content()

        return {
            "success": True,
            "selector": selector,
            "element_text": element_text.strip() if element_text else ""
        }

    except PlaywrightTimeoutError:
        return create_error_response(
            "ElementNotFound",
            f"Element '{selector}' not found or not clickable within {ELEMENT_TIMEOUT}ms",
            "Check if selector is correct and element is visible",
            selector=selector
        )
    except Exception as e:
        error_type, suggestion = parse_playwright_error(e)
        return create_error_response(error_type, str(e), suggestion, selector=selector)


@server.tool()
async def fill_input(selector: str, text: str) -> dict:
    """
    Fill a form input with text.

    Args:
        selector: CSS selector of the input element
        text: Text to fill into the input

    Returns:
        dict: Success status with input details, or error details
    """
    try:
        # Validation
        if not selector or not selector.strip():
            return create_error_response(
                "ValidationError",
                "Selector cannot be empty",
                "Provide a valid CSS selector",
                selector=selector
            )

        # Execution
        page = await browser_manager.get_page()
        element = page.locator(selector)

        # Clear and fill
        await element.clear(timeout=ELEMENT_TIMEOUT)
        await element.fill(text, timeout=ELEMENT_TIMEOUT)

        return {
            "success": True,
            "selector": selector,
            "text_length": len(text)
        }

    except PlaywrightTimeoutError:
        return create_error_response(
            "ElementNotFound",
            f"Input element '{selector}' not found within {ELEMENT_TIMEOUT}ms",
            "Check if selector is correct and element is visible",
            selector=selector
        )
    except Exception as e:
        error_type, suggestion = parse_playwright_error(e)
        return create_error_response(error_type, str(e), suggestion, selector=selector)


@server.tool()
async def extract_text(selector: str) -> dict:
    """
    Extract text content from an element.

    Args:
        selector: CSS selector of the element

    Returns:
        dict: Success status with extracted text, or error details
    """
    try:
        # Validation
        if not selector or not selector.strip():
            return create_error_response(
                "ValidationError",
                "Selector cannot be empty",
                "Provide a valid CSS selector",
                selector=selector
            )

        # Execution
        page = await browser_manager.get_page()
        element = page.locator(selector)

        # Wait for element and get text
        await element.wait_for(timeout=ELEMENT_TIMEOUT)
        text = await element.text_content()

        return {
            "success": True,
            "selector": selector,
            "text": text.strip() if text else "",
            "text_length": len(text.strip()) if text else 0
        }

    except PlaywrightTimeoutError:
        return create_error_response(
            "ElementNotFound",
            f"Element '{selector}' not found within {ELEMENT_TIMEOUT}ms",
            "Check if selector is correct and element exists",
            selector=selector
        )
    except Exception as e:
        error_type, suggestion = parse_playwright_error(e)
        return create_error_response(error_type, str(e), suggestion, selector=selector)


@server.tool()
async def screenshot(path: str, full_page: bool = False) -> dict:
    """
    Take a screenshot of the current page.

    Args:
        path: File path to save the screenshot (supports .png, .jpg, .jpeg)
        full_page: If True, captures the entire scrollable page. If False, captures viewport only

    Returns:
        dict: Success status with file details, or error details
    """
    try:
        # Validation
        if not path or not path.strip():
            return create_error_response(
                "ValidationError",
                "Path cannot be empty",
                "Provide a valid file path",
                path=path
            )

        # Validate file extension
        valid_extensions = ['.png', '.jpg', '.jpeg']
        path_obj = Path(path)
        if path_obj.suffix.lower() not in valid_extensions:
            return create_error_response(
                "ValidationError",
                f"Invalid file extension: {path_obj.suffix}",
                f"Use one of: {', '.join(valid_extensions)}",
                path=path
            )

        # Create parent directories
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Execution
        page = await browser_manager.get_page()
        await page.screenshot(
            path=path,
            full_page=full_page,
            timeout=SCREENSHOT_TIMEOUT
        )

        # Get file info
        absolute_path = path_obj.resolve()
        file_size = absolute_path.stat().st_size
        viewport = await browser_manager.get_viewport_size()

        return {
            "success": True,
            "path": str(absolute_path),
            "file_size": file_size,
            "full_page": full_page,
            "viewport": viewport
        }

    except PlaywrightTimeoutError:
        return create_error_response(
            "TimeoutError",
            f"Screenshot timed out after {SCREENSHOT_TIMEOUT}ms",
            "Try increasing SCREENSHOT_TIMEOUT",
            path=path
        )
    except PermissionError as e:
        return create_error_response(
            "FileSystemError",
            f"Permission denied: {str(e)}",
            "Check file/directory write permissions",
            path=path
        )
    except Exception as e:
        error_type, suggestion = parse_playwright_error(e)
        return create_error_response(error_type, str(e), suggestion, path=path)


@server.tool()
async def get_page_info() -> dict:
    """
    Get information about the current page.

    Returns:
        dict: Current page URL, title, and viewport size
    """
    try:
        # Execution (auto-initializes browser if needed)
        page = await browser_manager.get_page()

        url = page.url
        title = await page.title()
        viewport = await browser_manager.get_viewport_size()

        return {
            "success": True,
            "url": url,
            "title": title,
            "viewport": viewport
        }

    except Exception as e:
        error_type, suggestion = parse_playwright_error(e)
        return create_error_response(error_type, str(e), suggestion)


# Shutdown handler
async def shutdown(signal_name: Optional[str] = None) -> None:
    """
    Graceful shutdown handler.

    Args:
        signal_name: Name of the signal that triggered shutdown
    """
    if signal_name:
        print(f"\nReceived {signal_name}, shutting down gracefully...")
    else:
        print("\nShutting down gracefully...")

    await browser_manager.cleanup()
    print("Browser cleanup complete")


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        asyncio.create_task(shutdown(signal_name))

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


# Main entry point
if __name__ == "__main__":
    try:
        setup_signal_handlers()

        # Print user-friendly URLs with localhost (not 0.0.0.0)
        print("\n" + "="*60)
        print("🚀 Playwright Automation Server v1.0.0")
        print("="*60)
        print(f"\n📊 Inspector UI:    http://localhost:{PORT}/inspector")
        print(f"📄 API Docs:        http://localhost:{PORT}/docs")
        print(f"📋 OpenMCP:         http://localhost:{PORT}/openmcp.json")
        print(f"🔌 MCP Endpoint:    http://localhost:{PORT}/mcp")
        print(f"\n💡 Open http://localhost:{PORT}/inspector in your browser")
        print("   to test all 6 browser automation tools interactively")
        print(f"   Press CTRL+C to stop the server\n")
        print("="*60 + "\n")

        # Run server with streamable-http transport for Inspector UI
        server.run(
            transport="streamable-http",
            host=HOST,
            port=PORT
        )

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Ensure cleanup happens
        asyncio.run(shutdown())
