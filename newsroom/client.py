"""Reusable stdio MCP client for Newsroom MCP."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from mcp import StdioServerParameters
from mcp.client import Client


class NewsroomClient:
    """Small typed-by-convention facade over the official MCP Python client."""

    def __init__(self, server_command: list[str] | None = None) -> None:
        command = server_command or [sys.executable, "-m", "newsroom.server"]
        self._client = Client(StdioServerParameters(command=command[0], args=command[1:], cwd=Path.cwd()))

    async def __aenter__(self) -> "NewsroomClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.__aexit__(*exc)

    @property
    def discovery(self) -> dict[str, Any]:
        """Return information learned while connecting to the server."""
        return {
            "protocol_version": self._client.protocol_version,
            "server_info": self._client.server_info.model_dump(mode="json") if self._client.server_info else None,
            "instructions": self._client.instructions,
            "capabilities": self._client.server_capabilities.model_dump(mode="json"),
        }

    async def _call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        result = await self._client.call_tool(name, arguments or {})
        if result.is_error:
            messages = [getattr(item, "text", str(item)) for item in result.content]
            raise RuntimeError("; ".join(messages))
        payload = result.structured_content
        # The SDK wraps a top-level list return in {"result": ...} because
        # structuredContent must be an object on the wire.
        if isinstance(payload, dict) and set(payload) == {"result"}:
            return payload["result"]
        return payload

    async def tools(self) -> list[dict[str, Any]]:
        result = await self._client.list_tools()
        return [tool.model_dump(mode="json") for tool in result.tools]

    async def newsroom_policy(self) -> dict[str, Any]:
        return await self._call("get_newsroom_policy")

    async def stories(self) -> list[dict[str, str]]:
        return await self._call("list_stories")

    async def editorial_package(self, story_id: str) -> dict[str, Any]:
        return await self._call("get_editorial_package", {"story_id": story_id})

    async def effective_policy(self, story_id: str) -> dict[str, Any]:
        return await self._call("get_effective_policy", {"story_id": story_id})

    async def validate(self, story_id: str, proposed_use: dict[str, Any]) -> dict[str, Any]:
        return await self._call("validate_usage", {"story_id": story_id, "proposed_use": proposed_use})
