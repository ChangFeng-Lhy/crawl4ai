
import asyncio
import json
import os
from typing import Any, Dict

import httpx

from logger import setup_logger

logger = setup_logger()
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")
JINA_BASE_URL = os.environ.get("JINA_BASE_URL", "https://r.jina.ai")

async def scrape_url_with_jina(
    url: str, custom_headers: Dict[str, str] = None, max_chars: int = 102400 * 4
) -> Dict[str, Any]:
    """
    Scrape content from a URL and save to a temporary file. Need to read the content from the temporary file.


    Args:
        url (str): The URL to scrape content from
        custom_headers (Dict[str, str]): Additional headers to include in the request
        max_chars (int): Maximum number of characters to reserve for the scraped content

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether the operation was successful
            - filename (str): Absolute path to the temporary file containing the scraped content
            - content (str): The scraped content of the first 40k characters
            - error (str): Error message if the operation failed
            - line_count (int): Number of lines in the scraped content
            - char_count (int): Number of characters in the scraped content
            - last_char_line (int): Line number where the last displayed character is located
            - all_content_displayed (bool): Signal indicating if all content was displayed (True if content <= 40k chars)
    """

    # Validate input
    if not url or not url.strip():
        return {
            "success": False,
            "filename": "",
            "content": "",
            "error": "URL cannot be empty",
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }

    # Get API key from environment
    if not JINA_API_KEY:
        return {
            "success": False,
            "filename": "",
            "content": "",
            "error": "JINA_API_KEY environment variable is not set",
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }

    # Avoid duplicate Jina URL prefix
    if url.startswith("https://r.jina.ai/") and url.count("http") >= 2:
        url = url[len("https://r.jina.ai/") :]

    # Construct the Jina.ai API URL
    jina_url = f"{JINA_BASE_URL}/{url}"

    try:
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {JINA_API_KEY}",
        }

        # Add custom headers if provided
        if custom_headers:
            headers.update(custom_headers)

        # Retry configuration
        retry_delays = [1, 2, 4, 8]

        for attempt, delay in enumerate(retry_delays, 1):
            try:
                # Make the request using httpx library
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        jina_url,
                        headers=headers,
                        timeout=httpx.Timeout(None, connect=20, read=60),
                        follow_redirects=True,  # Follow redirects (equivalent to curl -L)
                    )

                # Check if request was successful
                response.encoding = 'utf-8'
                response.raise_for_status()
                break  # Success, exit retry loop

            except httpx.ConnectTimeout as e:
                # connection timeout, retry
                if attempt < len(retry_delays):
                    logger.info(
                        f"Jina Scrape: Connection timeout, {delay}s before next attempt (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Jina Scrape: Connection retry attempts exhausted, url: {url}"
                    )
                    raise e

            except httpx.ConnectError as e:
                # connection error, retry
                if attempt < len(retry_delays):
                    logger.info(
                        f"Jina Scrape: Connection error: {e}, {delay}s before next attempt"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Jina Scrape: Connection retry attempts exhausted, url: {url}"
                    )
                    raise e

            except httpx.ReadTimeout as e:
                # read timeout, retry
                if attempt < len(retry_delays):
                    logger.info(
                        f"Jina Scrape: Read timeout, {delay}s before next attempt (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Jina Scrape: Read timeout retry attempts exhausted, url: {url}"
                    )
                    raise e

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code

                # Retryable: 5xx (server errors) + specific 4xx (408, 409, 425, 429)
                should_retry = status_code >= 500 or status_code in [408, 409, 425, 429]

                if should_retry and attempt < len(retry_delays):
                    logger.info(
                        f"Jina Scrape: HTTP {status_code} (retryable), retry in {delay}s, url: {url}"
                    )
                    await asyncio.sleep(delay)
                    continue
                elif should_retry:
                    logger.error(
                        f"Jina Scrape: HTTP {status_code} retry exhausted, url: {url}"
                    )
                    raise e
                else:
                    logger.error(
                        f"Jina Scrape: HTTP {status_code} (non-retryable), url: {url}"
                    )
                    raise e

            except httpx.RequestError as e:
                if attempt < len(retry_delays):
                    logger.info(
                        f"Jina Scrape: Unknown request exception: {e}, url: {url}, {delay}s before next attempt (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"Jina Scrape: Unknown request exception retry attempts exhausted, url: {url}"
                    )
                    raise e

    except Exception as e:
        error_msg = f"Jina Scrape: Unexpected error occurred: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "filename": "",
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
            "filename": "",
            "content": "",
            "error": "No content returned from Jina.ai API",
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }

    # handle insufficient balance error
    try:
        content_dict = json.loads(content)
    except json.JSONDecodeError:
        content_dict = None
    if (
        isinstance(content_dict, dict)
        and content_dict.get("name") == "InsufficientBalanceError"
    ):
        return {
            "success": False,
            "filename": "",
            "content": "",
            "error": "Insufficient balance",
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
        # Count newlines up to the last displayed character
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
