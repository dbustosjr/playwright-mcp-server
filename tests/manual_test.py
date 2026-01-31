"""Manual integration test script for Playwright MCP Server."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from browser_manager import BrowserManager
from server import (
    navigate,
    get_page_info,
    extract_text,
    screenshot,
    click_element,
    fill_input,
)

# Load environment
load_dotenv()


async def run_tests():
    """Run manual integration tests."""
    print("=" * 60)
    print("Playwright MCP Server - Manual Integration Tests")
    print("=" * 60)

    browser_manager = BrowserManager()

    try:
        # Test 1: Navigate to example.com
        print("\n[Test 1] Navigate to example.com")
        result = await navigate("https://example.com")
        print(f"Result: {result}")
        assert result["success"], "Navigation should succeed"
        print("✓ Navigation successful")

        # Test 2: Get page info
        print("\n[Test 2] Get page information")
        result = await get_page_info()
        print(f"Result: {result}")
        assert result["success"], "Get page info should succeed"
        assert "example.com" in result["url"].lower(), "Should be on example.com"
        print("✓ Page info retrieved")

        # Test 3: Extract h1 text
        print("\n[Test 3] Extract h1 text")
        result = await extract_text("h1")
        print(f"Result: {result}")
        assert result["success"], "Text extraction should succeed"
        assert len(result["text"]) > 0, "Should extract non-empty text"
        print(f"✓ Extracted text: '{result['text']}'")

        # Test 4: Take screenshot
        print("\n[Test 4] Take screenshot")
        screenshot_dir = Path("./screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        screenshot_path = screenshot_dir / "test_screenshot.png"
        result = await screenshot(str(screenshot_path))
        print(f"Result: {result}")
        assert result["success"], "Screenshot should succeed"
        assert Path(result["path"]).exists(), "Screenshot file should exist"
        print(f"✓ Screenshot saved to: {result['path']}")

        # Test 5: Error handling - invalid URL
        print("\n[Test 5] Error handling - invalid URL (missing protocol)")
        result = await navigate("example.com")
        print(f"Result: {result}")
        assert not result["success"], "Should fail for invalid URL"
        assert result["error_type"] == "ValidationError", "Should be validation error"
        print(f"✓ Error caught: {result['error']}")
        print(f"  Suggestion: {result['suggestion']}")

        # Test 6: Error handling - element not found
        print("\n[Test 6] Error handling - element not found")
        result = await extract_text("div.nonexistent-element")
        print(f"Result: {result}")
        assert not result["success"], "Should fail for nonexistent element"
        assert result["error_type"] == "ElementNotFound", "Should be ElementNotFound error"
        print(f"✓ Error caught: {result['error']}")
        print(f"  Suggestion: {result['suggestion']}")

        # Test 7: Navigate to another site (Google)
        print("\n[Test 7] Navigate to google.com")
        result = await navigate("https://www.google.com", wait_until="domcontentloaded")
        print(f"Result: {result}")
        assert result["success"], "Navigation to Google should succeed"
        print("✓ Navigation to Google successful")

        # All tests passed
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        print("\nCleaning up browser...")
        await browser_manager.cleanup()
        print("✓ Cleanup complete")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
