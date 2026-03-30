#!/usr/bin/env python3
"""
V2 integration test script.

Tests the full pipeline end-to-end:
  1. Index a set of sample tools into Qdrant
  2. Simulate user tool installations in Supabase
  3. Run retrieval queries and verify only installed tools are returned

Usage:
    # From the repo root:
    python scripts/test_v2.py

Requires all V2 env vars to be set:
    OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY, SUPABASE_URL, SUPABASE_KEY
"""

import os
import sys
import logging

# Add repo root to path so package imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("test_v2")

# ── check env vars ────────────────────────────────────────────────────────────
REQUIRED = ["OPENAI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
missing = [k for k in REQUIRED if not os.getenv(k)]
if missing:
    print(f"[ERROR] Missing env vars: {', '.join(missing)}")
    print("  Set them in your shell or create a .env file and load it first.")
    sys.exit(1)

# ── sample tools ──────────────────────────────────────────────────────────────
SAMPLE_TOOLS = [
    {
        "name": "edit_config_file",
        "description": "Edit a configuration file in-place using line-based changes",
        "server": "filesystem",
        "is_public": True,
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file with given content",
        "server": "filesystem",
        "is_public": True,
    },
    {
        "name": "docker_deploy",
        "description": "Build and deploy a Docker container to a remote host",
        "server": "devops",
        "is_public": True,
    },
    {
        "name": "docker_logs",
        "description": "Stream logs from a running Docker container",
        "server": "devops",
        "is_public": True,
    },
    {
        "name": "github_push",
        "description": "Push local commits to a remote GitHub repository branch",
        "server": "github",
        "is_public": True,
    },
    {
        "name": "github_create_pr",
        "description": "Open a new pull request on GitHub with title and body",
        "server": "github",
        "is_public": True,
    },
    {
        "name": "run_tests",
        "description": "Execute the test suite and return pass/fail counts",
        "server": "ci",
        "is_public": True,
    },
    {
        "name": "send_slack_message",
        "description": "Post a message to a Slack channel or DM",
        "server": "slack",
        "is_public": True,
    },
]

# tools the test user has installed
USER_ID = "test-user-v2-script"
INSTALLED_TOOLS = [
    ("edit_config_file", "filesystem"),
    ("docker_deploy", "devops"),
    ("github_push", "github"),
    ("github_create_pr", "github"),
]

QUERIES = [
    ("edit config file", ["edit_config_file"]),
    ("deploy docker", ["docker_deploy"]),
    ("push to github", ["github_push", "github_create_pr"]),
    ("send slack notification", []),   # not installed → should return nothing
]


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def main() -> None:
    # ── 1. Index tools ────────────────────────────────────────────────────────
    section("STEP 1 — Indexing tools")
    from packages.vector.indexer import index_tools
    count = index_tools(SAMPLE_TOOLS, skip_existing=False)
    print(f"  ✓ Indexed {count} tools")

    # ── 2. Track installations ────────────────────────────────────────────────
    section("STEP 2 — Simulating user installations")
    from packages.vector.retriever import track_installation
    for tool_name, server in INSTALLED_TOOLS:
        track_installation(user_id=USER_ID, tool_name=tool_name, server=server)
        print(f"  ✓ Installed {server}/{tool_name}")

    # ── 3. Run queries ────────────────────────────────────────────────────────
    section("STEP 3 — Running retrieval queries")
    from packages.vector.retriever import retrieve_tools

    all_passed = True
    for query, expected_tools in QUERIES:
        results = retrieve_tools(query=query, user_id=USER_ID, top_k=5)
        returned_names = {r["tool_name"] for r in results}

        print(f"\n  Query : \"{query}\"")
        if results:
            for r in results:
                print(f"    → {r['server']}/{r['tool_name']}  (score={r['score']})")
        else:
            print("    → (no results)")

        # Check that all expected tools appear in results (when expected)
        if expected_tools:
            matched = returned_names & set(expected_tools)
            if matched:
                print(f"  ✓ Found expected tool(s): {matched}")
            else:
                print(f"  ✗ Expected {expected_tools} but got {returned_names}")
                all_passed = False
        else:
            # Expect no results (tool not installed)
            if returned_names:
                print(f"  ✗ Expected no results but got: {returned_names}")
                all_passed = False
            else:
                print("  ✓ Correctly returned no results (tool not installed)")

        # Verify only installed tools are returned
        for r in results:
            pair = (r["tool_name"], r["server"])
            if pair not in INSTALLED_TOOLS:
                print(f"  ✗ FILTER BREACH: returned non-installed tool {pair}")
                all_passed = False

    # ── summary ───────────────────────────────────────────────────────────────
    section("RESULT")
    if all_passed:
        print("  ✓ All tests passed!\n")
    else:
        print("  ✗ Some tests failed — see output above\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
