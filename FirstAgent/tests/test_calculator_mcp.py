import pytest

from mcp import Client
from mcp_servers.calculator_server import mcp


@pytest.mark.asyncio
async def test_mcp_add_tool() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "add",
            {
                "a": 111,
                "b": 444,
            },
        )

    assert result.structured_content == {"result": 555}


@pytest.mark.asyncio
async def test_mcp_multiply_tool() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "multiply",
            {
                "a": 111,
                "b": 444,
            },
        )

    assert result.structured_content == {"result": 49284}
    