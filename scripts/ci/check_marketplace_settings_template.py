#!/usr/bin/env python3
"""Validate marketplace settings template against current Claude settings shape."""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS_TEMPLATE = Path("templates/claude-settings.marketplace.json")
MARKETPLACE_KEY = "curdx-marketplace"
PLUGIN_ID = "curdx@curdx-marketplace"
EXPECTED_REPO = "ForeverWorld/curdx-ralph"


def main() -> int:
    if not SETTINGS_TEMPLATE.exists():
        print(f"ERROR: missing {SETTINGS_TEMPLATE}")
        return 1

    try:
        data = json.loads(SETTINGS_TEMPLATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {SETTINGS_TEMPLATE}: {exc}")
        return 1

    extra = data.get("extraKnownMarketplaces")
    if not isinstance(extra, dict):
        print("ERROR: extraKnownMarketplaces must be an object (not an array)")
        return 1

    marketplace = extra.get(MARKETPLACE_KEY)
    if not isinstance(marketplace, dict):
        print(f"ERROR: missing extraKnownMarketplaces.{MARKETPLACE_KEY}")
        return 1

    source = marketplace.get("source")
    if not isinstance(source, dict):
        print(f"ERROR: extraKnownMarketplaces.{MARKETPLACE_KEY}.source must be an object")
        return 1
    if source.get("source") != "github":
        print("ERROR: marketplace source.source must be 'github'")
        return 1
    if source.get("repo") != EXPECTED_REPO:
        print(f"ERROR: marketplace source.repo must be {EXPECTED_REPO!r}")
        return 1

    enabled = data.get("enabledPlugins")
    if not isinstance(enabled, dict):
        print("ERROR: enabledPlugins must be an object (not an array)")
        return 1
    if enabled.get(PLUGIN_ID) is not True:
        print(f"ERROR: enabledPlugins.{PLUGIN_ID} must be true")
        return 1

    print("OK: marketplace settings template matches current settings format")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
