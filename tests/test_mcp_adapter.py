import pytest
from mcp import Client

from agent_onboarding.mcp_adapter.server import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_ping_tool_is_listed():
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.list_tools()
        assert [tool.name for tool in result.tools] == ["ping"]
