"""MCP server representing the fictional newsroom publisher."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from newsroom.models import ProposedUse, build_effective_policy, list_editorial_packages, load_editorial_package, load_newsroom_policy
from newsroom.validator import validate_proposed_use

SERVER_INSTRUCTIONS = """Newsroom policy applies to every editorial package. A story policy may
add constraints; the effective policy is authoritative for downstream use. Never invent or
materially change verified facts. Preserve required disclosures, framing boundaries, material
context, quote integrity, and distinctions in editorial confidence. Creative transformations
remain subject to every constraint. If a requested transformation cannot comply, decline it or
offer a compliant alternative. These instructions and policies communicate constraints; MCP
does not guarantee compliance after information leaves this server."""

mcp = MCPServer(
    "newsroom-mcp",
    title="Newsroom MCP",
    description="Structured editorial packages and newsroom usage policies",
    instructions=SERVER_INSTRUCTIONS,
    version="0.1.0",
)


@mcp.tool()
def list_stories() -> list[dict[str, str]]:
    """List editorial packages available from the newsroom."""
    return [{"id": story.id, "title": story.title} for story in list_editorial_packages()]


@mcp.tool()
def get_newsroom_policy() -> dict[str, Any]:
    """Return the publisher-wide, machine-readable newsroom usage policy."""
    return load_newsroom_policy().model_dump(mode="json")


@mcp.tool()
def get_editorial_package(story_id: str) -> dict[str, Any]:
    """Return a complete structured editorial package by story ID."""
    return load_editorial_package(story_id).model_dump(mode="json")


@mcp.tool()
def get_effective_policy(story_id: str) -> dict[str, Any]:
    """Return newsroom rules plus optional additive story constraints."""
    return build_effective_policy(load_editorial_package(story_id)).model_dump(mode="json")


@mcp.tool()
def validate_usage(story_id: str, proposed_use: dict[str, Any]) -> dict[str, Any]:
    """Run a deterministic check of a structured proposed use against its effective policy."""
    story = load_editorial_package(story_id)
    proposed = ProposedUse.model_validate(proposed_use)
    return validate_proposed_use(story, proposed).model_dump(mode="json")


def main() -> None:
    """Run the local stdio MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
