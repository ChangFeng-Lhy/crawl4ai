import asyncio
from typing import Any, Dict

import httpx
from logger import setup_logger
logger = setup_logger()

async def scrape_url_with_python(
    url: str, custom_headers: Dict[str, str] = None, max_chars: int = 102400 * 4
) -> Dict[str, Any]:
    """
    Fallback scraping method using Python's httpx library directly.

    Args:
        url (str): The URL to scrape content from
        custom_headers (Dict[str, str]): Additional headers to include in the request
        max_chars (int): Maximum number of characters to reserve for the scraped content

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether the operation was successful
            - content (str): The scraped content
            - error (str): Error message if the operation failed
            - line_count (int): Number of lines in the scraped content
            - char_count (int): Number of characters in the scraped content
            - last_char_line (int): Line number where the last displayed character is located
            - all_content_displayed (bool): Signal indicating if all content was displayed
    """
    # Validate input
    if not url or not url.strip():
        return {
            "success": False,
            "content": "",
            "error": "URL cannot be empty",
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }

    try:
        # Prepare headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Add custom headers if provided
        if custom_headers:
            headers.update(custom_headers)

        # Retry configuration
        retry_delays = [1, 2, 4]

        for attempt, delay in enumerate(retry_delays, 1):
            try:
                # Make the request using httpx library
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        headers=headers,
                        timeout=httpx.Timeout(None, connect=20, read=60),
                        follow_redirects=True,
                    )

                # Check if request was successful
                response.raise_for_status()
                break  # Success, exit retry loop

            except httpx.ConnectTimeout as e:
                if attempt < len(retry_delays):
                    logger.info(
                        f"Python Scrape: Connection timeout, {delay}s before next attempt (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Python Scrape: Connection retry attempts exhausted, url: {url}"
                    )
                    raise e

            except httpx.ConnectError as e:
                if attempt < len(retry_delays):
                    logger.info(
                        f"Python Scrape: Connection error: {e}, {delay}s before next attempt"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Python Scrape: Connection retry attempts exhausted, url: {url}"
                    )
                    raise e

            except httpx.ReadTimeout as e:
                if attempt < len(retry_delays):
                    logger.info(
                        f"Python Scrape: Read timeout, {delay}s before next attempt (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Python Scrape: Read timeout retry attempts exhausted, url: {url}"
                    )
                    raise e

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code

                # Retryable: 5xx (server errors) + specific 4xx (408, 409, 425, 429)
                should_retry = status_code >= 500 or status_code in [408, 409, 425, 429]

                if should_retry and attempt < len(retry_delays):
                    logger.info(
                        f"Python Scrape: HTTP {status_code} (retryable), retry in {delay}s, url: {url}"
                    )
                    await asyncio.sleep(delay)
                    continue
                elif should_retry:
                    logger.error(
                        f"Python Scrape: HTTP {status_code} retry exhausted, url: {url}"
                    )
                    raise e
                else:
                    logger.error(
                        f"Python Scrape: HTTP {status_code} (non-retryable), url: {url}"
                    )
                    raise e

            except httpx.RequestError as e:
                if attempt < len(retry_delays):
                    logger.info(
                        f"Python Scrape: Unknown request exception: {e}, url: {url}, {delay}s before next attempt (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Python Scrape: Unknown request exception retry attempts exhausted, url: {url}"
                    )
                    raise e

    except Exception as e:
        error_msg = f"Python Scrape: Unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "content": "",
            "error": error_msg,
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }

    # Get the scraped content
    content = response.text

    if not content:
        return {
            "success": False,
            "content": "",
            "error": "No content returned from URL",
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }

    # Get content statistics
    total_char_count = len(content)
    total_line_count = content.count("\n") + 1 if content else 0

    # Extract first max_chars characters
    displayed_content = content[:max_chars]
    all_content_displayed = total_char_count <= max_chars

    # Calculate the line number of the last character displayed
    if displayed_content:
        last_char_line = displayed_content.count("\n") + 1
    else:
        last_char_line = 0

    return {
        "success": True,
        "content": displayed_content,
        "error": "",
        "line_count": total_line_count,
        "char_count": total_char_count,
        "last_char_line": last_char_line,
        "all_content_displayed": all_content_displayed,
    }
