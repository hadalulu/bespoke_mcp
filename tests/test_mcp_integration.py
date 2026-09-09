import pytest

from newsroom.client import NewsroomClient
from newsroom.scenarios import SCENARIOS


@pytest.mark.anyio
async def test_client_discovers_and_calls_stdio_server() -> None:
    async with NewsroomClient() as client:
        assert client.discovery["instructions"]
        assert "get_effective_policy" in {tool["name"] for tool in await client.tools()}
        stories = await client.stories()
        assert {story["id"] for story in stories} == {"story_001", "story_002"}
        result = await client.validate("story_001", SCENARIOS["allowed-neutral"]["proposed_use"])
        assert result["compliant"] is True
