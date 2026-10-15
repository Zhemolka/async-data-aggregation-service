import asyncio


async def simulate_url_request(url: str) -> None:
    """Imitate the slow network request described in the assignment."""
    await asyncio.sleep(2)
    if "error" in url.lower():
        raise RuntimeError(f"Simulated processing error for URL: {url}")
