"""Unit tests for Playwright MCP Server."""

import asyncio
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment before importing modules
load_dotenv()

# Import after loading env
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from browser_manager import BrowserManager


class TestBrowserManager:
    """Test suite for BrowserManager singleton."""

    @pytest.fixture
    async def manager(self):
        """Fixture to provide a fresh browser manager."""
        manager = BrowserManager()
        yield manager
        # Cleanup after test
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test that BrowserManager follows singleton pattern."""
        manager1 = BrowserManager()
        manager2 = BrowserManager()
        assert manager1 is manager2, "BrowserManager should be a singleton"

    @pytest.mark.asyncio
    async def test_browser_initialization(self, manager):
        """Test browser initializes successfully."""
        page = await manager.get_page()
        assert page is not None, "Page should be initialized"
        assert manager.is_initialized(), "Manager should report as initialized"

    @pytest.mark.asyncio
    async def test_get_current_url(self, manager):
        """Test getting current URL."""
        page = await manager.get_page()
        await page.goto("https://example.com")
        url = await manager.get_current_url()
        assert url == "https://example.com/", "Should return current URL"

    @pytest.mark.asyncio
    async def test_get_viewport_size(self, manager):
        """Test getting viewport size."""
        await manager.get_page()
        viewport = await manager.get_viewport_size()
        assert "width" in viewport, "Viewport should have width"
        assert "height" in viewport, "Viewport should have height"
        assert viewport["width"] > 0, "Width should be positive"
        assert viewport["height"] > 0, "Height should be positive"

    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test cleanup releases resources."""
        await manager.get_page()
        assert manager.is_initialized(), "Should be initialized before cleanup"

        await manager.cleanup()
        assert not manager.is_initialized(), "Should not be initialized after cleanup"

    @pytest.mark.asyncio
    async def test_restart_browser(self, manager):
        """Test browser restart functionality."""
        page1 = await manager.get_page()
        await page1.goto("https://example.com")

        # Restart browser
        page2 = await manager.restart_browser()
        assert page2 is not None, "Should return new page after restart"
        assert manager.is_initialized(), "Should be initialized after restart"

        # URL should be reset to about:blank
        url = await manager.get_current_url()
        assert url in ["about:blank", ""], "New browser should start at blank page"


class TestNavigateTool:
    """Test suite for navigate tool."""

    @pytest.fixture
    async def manager(self):
        """Fixture to provide a fresh browser manager."""
        # Import here to avoid issues
        from browser_manager import BrowserManager
        manager = BrowserManager()
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_navigate_valid_url(self, manager):
        """Test navigation to valid URL."""
        from server import navigate

        result = await navigate("https://example.com")
        assert result["success"] is True, "Navigation should succeed"
        assert "url" in result, "Result should contain URL"
        assert "title" in result, "Result should contain title"
        assert "example.com" in result["url"].lower(), "Should navigate to example.com"

    @pytest.mark.asyncio
    async def test_navigate_invalid_url(self, manager):
        """Test navigation with invalid URL (missing protocol)."""
        from server import navigate

        result = await navigate("example.com")
        assert result["success"] is False, "Should fail for URL without protocol"
        assert result["error_type"] == "ValidationError", "Should be validation error"
        assert "http://" in result["suggestion"], "Suggestion should mention http://"

    @pytest.mark.asyncio
    async def test_navigate_invalid_wait_until(self, manager):
        """Test navigation with invalid wait_until parameter."""
        from server import navigate

        result = await navigate("https://example.com", wait_until="invalid")
        assert result["success"] is False, "Should fail for invalid wait_until"
        assert result["error_type"] == "ValidationError", "Should be validation error"


class TestClickElement:
    """Test suite for click_element tool."""

    @pytest.fixture
    async def manager(self):
        """Fixture to provide a fresh browser manager."""
        from browser_manager import BrowserManager
        manager = BrowserManager()
        # Navigate to a test page
        page = await manager.get_page()
        await page.goto("https://example.com")
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_click_empty_selector(self, manager):
        """Test clicking with empty selector."""
        from server import click_element

        result = await click_element("")
        assert result["success"] is False, "Should fail for empty selector"
        assert result["error_type"] == "ValidationError", "Should be validation error"

    @pytest.mark.asyncio
    async def test_click_invalid_selector(self, manager):
        """Test clicking non-existent element."""
        from server import click_element

        result = await click_element("button.does-not-exist")
        assert result["success"] is False, "Should fail for non-existent element"
        assert result["error_type"] == "ElementNotFound", "Should be ElementNotFound error"


class TestFillInput:
    """Test suite for fill_input tool."""

    @pytest.mark.asyncio
    async def test_fill_empty_selector(self):
        """Test filling with empty selector."""
        from server import fill_input

        result = await fill_input("", "test text")
        assert result["success"] is False, "Should fail for empty selector"
        assert result["error_type"] == "ValidationError", "Should be validation error"


class TestExtractText:
    """Test suite for extract_text tool."""

    @pytest.fixture
    async def manager(self):
        """Fixture to provide a fresh browser manager."""
        from browser_manager import BrowserManager
        manager = BrowserManager()
        page = await manager.get_page()
        await page.goto("https://example.com")
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_extract_text_h1(self, manager):
        """Test extracting text from h1 element."""
        from server import extract_text

        result = await extract_text("h1")
        assert result["success"] is True, "Should succeed for h1 on example.com"
        assert "text" in result, "Result should contain text"
        assert len(result["text"]) > 0, "Text should not be empty"

    @pytest.mark.asyncio
    async def test_extract_text_empty_selector(self, manager):
        """Test extracting with empty selector."""
        from server import extract_text

        result = await extract_text("")
        assert result["success"] is False, "Should fail for empty selector"
        assert result["error_type"] == "ValidationError", "Should be validation error"


class TestScreenshot:
    """Test suite for screenshot tool."""

    @pytest.fixture
    async def manager(self):
        """Fixture to provide a fresh browser manager."""
        from browser_manager import BrowserManager
        manager = BrowserManager()
        page = await manager.get_page()
        await page.goto("https://example.com")
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_screenshot_valid(self, manager, tmp_path):
        """Test taking screenshot with valid path."""
        from server import screenshot

        screenshot_path = tmp_path / "test.png"
        result = await screenshot(str(screenshot_path))

        assert result["success"] is True, "Screenshot should succeed"
        assert "path" in result, "Result should contain path"
        assert "file_size" in result, "Result should contain file_size"
        assert Path(result["path"]).exists(), "Screenshot file should exist"
        assert result["file_size"] > 0, "File size should be greater than 0"

    @pytest.mark.asyncio
    async def test_screenshot_invalid_extension(self, manager, tmp_path):
        """Test screenshot with invalid file extension."""
        from server import screenshot

        screenshot_path = tmp_path / "test.txt"
        result = await screenshot(str(screenshot_path))

        assert result["success"] is False, "Should fail for invalid extension"
        assert result["error_type"] == "ValidationError", "Should be validation error"

    @pytest.mark.asyncio
    async def test_screenshot_empty_path(self, manager):
        """Test screenshot with empty path."""
        from server import screenshot

        result = await screenshot("")
        assert result["success"] is False, "Should fail for empty path"
        assert result["error_type"] == "ValidationError", "Should be validation error"


class TestGetPageInfo:
    """Test suite for get_page_info tool."""

    @pytest.fixture
    async def manager(self):
        """Fixture to provide a fresh browser manager."""
        from browser_manager import BrowserManager
        manager = BrowserManager()
        page = await manager.get_page()
        await page.goto("https://example.com")
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_get_page_info(self, manager):
        """Test getting page information."""
        from server import get_page_info

        result = await get_page_info()
        assert result["success"] is True, "Should succeed"
        assert "url" in result, "Result should contain URL"
        assert "title" in result, "Result should contain title"
        assert "viewport" in result, "Result should contain viewport"
        assert "example.com" in result["url"].lower(), "Should be on example.com"


class TestErrorHandling:
    """Test suite for error handling utilities."""

    def test_parse_playwright_error_dns(self):
        """Test parsing DNS errors."""
        from server import parse_playwright_error

        error = Exception("net::ERR_NAME_NOT_RESOLVED")
        error_type, suggestion = parse_playwright_error(error)
        assert error_type == "NetworkError", "Should be NetworkError"
        assert "DNS" in suggestion, "Suggestion should mention DNS"

    def test_parse_playwright_error_timeout(self):
        """Test parsing timeout errors."""
        from server import parse_playwright_error

        error = TimeoutError("Operation timed out")
        error_type, suggestion = parse_playwright_error(error)
        assert error_type == "TimeoutError", "Should be TimeoutError"
        assert "timeout" in suggestion.lower(), "Suggestion should mention timeout"

    def test_create_error_response(self):
        """Test error response creation."""
        from server import create_error_response

        result = create_error_response(
            "ValidationError",
            "Invalid input",
            "Check your input",
            url="https://example.com"
        )

        assert result["success"] is False, "Should have success=False"
        assert result["error_type"] == "ValidationError", "Should have correct error_type"
        assert result["error"] == "Invalid input", "Should have error message"
        assert result["suggestion"] == "Check your input", "Should have suggestion"
        assert result["url"] == "https://example.com", "Should include extra kwargs"
