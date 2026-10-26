import pytest
from mcp import Client

from agent_onboarding.mcp_adapter.server import mcp


@pytest.mark.anyio
async def test_s3_agent_has_no_tool_to_confirm_or_answer():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = sorted(tool.name for tool in tools.tools)
    assert names == [
        "change_amount", "estimate_costs", "get_application_status", "get_requirements",
        "list_funds", "ping", "request_human", "start_account_opening",
    ]
