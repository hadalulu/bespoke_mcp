"""Command-line MCP host for inspecting and validating editorial packages."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from newsroom.client import NewsroomClient
from newsroom.scenarios import SCENARIOS


def show(title: str, value: Any) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
    print(json.dumps(value, indent=2, ensure_ascii=False))


async def run_scenario(name: str, verbose: bool = True) -> bool:
    scenario = SCENARIOS[name]
    async with NewsroomClient() as client:
        package = await client.editorial_package(scenario["story_id"])
        if verbose:
            show("SERVER DISCOVERY", {**client.discovery, "tools": await client.tools()})
            show("NEWSROOM POLICY", await client.newsroom_policy())
            show("EDITORIAL PACKAGE", package)
            show("STORY-SPECIFIC POLICY", package.get("story_usage_policy"))
            show("EFFECTIVE POLICY", await client.effective_policy(scenario["story_id"]))
            show("PROPOSED USE", {"scenario": scenario["label"], **scenario["proposed_use"]})
        result = await client.validate(scenario["story_id"], scenario["proposed_use"])
        show("VALIDATION RESULT", result)
        return bool(result["compliant"])


async def run_demos() -> None:
    async with NewsroomClient() as client:
        show("SERVER DISCOVERY", {**client.discovery, "tools": [tool["name"] for tool in await client.tools()]})
        for name, scenario in SCENARIOS.items():
            result = await client.validate(scenario["story_id"], scenario["proposed_use"])
            status = "PASS" if result["compliant"] else "REJECT"
            print(f"\n[{status}] {name}: {scenario['label']}")
            for violation in result["violations"]:
                print(f"  - {violation['code']}: {violation['message']}")


async def interactive() -> None:
    async with NewsroomClient() as client:
        show("SERVER DISCOVERY", {**client.discovery, "tools": [tool["name"] for tool in await client.tools()]})
        show("NEWSROOM POLICY", await client.newsroom_policy())
        stories = await client.stories()
        show("AVAILABLE STORIES", stories)
        story_id = input("Story ID [story_001]: ").strip() or "story_001"
        package = await client.editorial_package(story_id)
        show("EDITORIAL PACKAGE", package)
        show("STORY-SPECIFIC POLICY", package.get("story_usage_policy"))
        show("EFFECTIVE POLICY", await client.effective_policy(story_id))
        matching = [(name, item) for name, item in SCENARIOS.items() if item["story_id"] == story_id]
        show("SCENARIOS", [{"name": name, "label": item["label"]} for name, item in matching])
        choice = input(f"Scenario [{matching[0][0]}]: ").strip() or matching[0][0]
        proposed = SCENARIOS[choice]["proposed_use"]
        show("PROPOSED USE", proposed)
        show("VALIDATION RESULT", await client.validate(story_id, proposed))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Newsroom MCP packages and validate proposed uses")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="run every predefined allowed/rejected scenario")
    group.add_argument("--scenario", choices=sorted(SCENARIOS), help="run one scenario with full policy/package output")
    args = parser.parse_args()
    if args.demo:
        asyncio.run(run_demos())
    elif args.scenario:
        asyncio.run(run_scenario(args.scenario))
    else:
        asyncio.run(interactive())


if __name__ == "__main__":
    main()
