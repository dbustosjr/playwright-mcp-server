"""Browser lifecycle management using singleton pattern."""

import asyncio
import os
from typing import Optional
from playwright.async_api import (
    async_playwright,
    Browser,
    Page,
    Playwright,
    Error as PlaywrightError,
)


class BrowserManager:
    """Singleton class managing Playwright browser lifecycle with robust error handling."""

    _instance: Optional['BrowserManager'] = None
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _page: Optional[Page] = None
    _lock: asyncio.Lock = asyncio.Lock()

    # Configuration from environment
    _headless: bool = os.getenv("HEADLESS", "true").lower() == "true"
    _browser_timeout: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))
    _viewport_width: int = int(os.getenv("VIEWPORT_WIDTH", "1920"))
    _viewport_height: int = int(os.getenv("VIEWPORT_HEIGHT", "1080"))

    def __new__(cls) -> 'BrowserManager':
        """Singleton pattern implementation - only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def ensure_browser(self) -> Page:
        """
        Initialize browser if needed and return the current page.

        Returns:
            Page: Active Playwright page instance

        Raises:
            PlaywrightError: If browser fails to launch
            TimeoutError: If browser launch exceeds timeout
        """
        async with self._lock:
            if self._page is None or self._page.is_closed():
                try:
                    # Start Playwright
                    if self._playwright is None:
                        self._playwright = await async_playwright().start()

                    # Launch browser
                    self._browser = await self._playwright.chromium.launch(
                        headless=self._headless,
                        timeout=self._browser_timeout,
                    )

                    # Create context with viewport
                    context = await self._browser.new_context(
                        viewport={
                            'width': self._viewport_width,
                            'height': self._viewport_height,
                        }
                    )

                    # Create page
                    self._page = await context.new_page()

                except TimeoutError as e:
                    raise TimeoutError(
                        f"Browser launch timed out after {self._browser_timeout}ms. "
                        "Try increasing BROWSER_TIMEOUT in .env"
                    ) from e
                except PlaywrightError as e:
                    raise PlaywrightError(
                        f"Failed to launch browser: {str(e)}. "
                        "Ensure Playwright browsers are installed with 'playwright install chromium'"
                    ) from e
                except Exception as e:
                    raise RuntimeError(
                        f"Unexpected error during browser initialization: {str(e)}"
                    ) from e

            return self._page

    async def get_page(self) -> Page:
        """
        Get the current page, initializing browser if needed.

        Returns:
            Page: Active Playwright page instance
        """
        return await self.ensure_browser()

    async def restart_browser(self) -> Page:
        """
        Restart the browser (useful for crash recovery).

        Returns:
            Page: New active Playwright page instance
        """
        async with self._lock:
            # Close existing browser if any
            await self._cleanup_browser()

            # Reset state
            self._browser = None
            self._page = None

        # Initialize new browser
        return await self.ensure_browser()

    async def _cleanup_browser(self) -> None:
        """Internal method to clean up browser resources."""
        try:
            if self._page and not self._page.is_closed():
                await self._page.close()
        except Exception:
            pass  # Ignore errors during cleanup

        try:
            if self._browser and self._browser.is_connected():
                await self._browser.close()
        except Exception:
            pass  # Ignore errors during cleanup

        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass  # Ignore errors during cleanup

    async def cleanup(self) -> None:
        """
        Close browser and release all resources.
        Should be called on server shutdown.
        """
        async with self._lock:
            await self._cleanup_browser()

            # Reset all state
            self._playwright = None
            self._browser = None
            self._page = None

    def is_initialized(self) -> bool:
        """
        Check if browser is currently initialized and connected.

        Returns:
            bool: True if browser is ready, False otherwise
        """
        return (
            self._browser is not None
            and self._browser.is_connected()
            and self._page is not None
            and not self._page.is_closed()
        )

    async def get_current_url(self) -> Optional[str]:
        """
        Get current page URL if browser is initialized.

        Returns:
            Optional[str]: Current URL or None if browser not initialized
        """
        if self.is_initialized() and self._page:
            return self._page.url
        return None

    async def get_viewport_size(self) -> dict:
        """
        Get current viewport size.

        Returns:
            dict: Viewport dimensions with 'width' and 'height' keys
        """
        if self.is_initialized() and self._page:
            viewport = self._page.viewport_size
            return {
                'width': viewport['width'],
                'height': viewport['height'],
            }
        return {
            'width': self._viewport_width,
            'height': self._viewport_height,
        }
