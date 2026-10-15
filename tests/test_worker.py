import pytest

from app.services import url_simulator


@pytest.mark.asyncio
async def test_simulate_url_request_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(url_simulator.asyncio, "sleep", no_sleep)
    await url_simulator.simulate_url_request("https://example.com/data")


@pytest.mark.asyncio
async def test_simulate_url_request_fails_for_error_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(url_simulator.asyncio, "sleep", no_sleep)
    with pytest.raises(RuntimeError, match="Simulated processing error"):
        await url_simulator.simulate_url_request("https://example.com/error")
