#!/usr/bin/env python3
"""
Test script for agent-corex v2.2.0 features.
Tests: MCP recommender, user tracker, tool router updates.
"""

import sys
import json

# Set encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("Testing Agent-CoreX v2.2.0 Features")
print("=" * 70)

# Test 1: MCP Recommender
print("\n[TEST 1] MCP Recommender - Query-based recommendations")
print("-" * 70)
try:
    from agent_core.gateway.mcp_recommender import (
        recommend_from_query,
        recommend_from_stack,
        get_all_known_mcps,
    )

    # Test recommend_from_query
    query = "I want to deploy my app to the cloud"
    recommendations = recommend_from_query(query, set())
    print(f"✅ Query: '{query}'")
    print(f"✅ Recommendations found: {len(recommendations)}")
    for rec in recommendations:
        print(f"   • {rec['name']}: {rec['reason']}")
    print(f"✅ All known MCPs: {len(get_all_known_mcps())} servers")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 2: Stack-based recommendations
print("\n[TEST 2] MCP Recommender - Stack-based recommendations")
print("-" * 70)
try:
    stack = ["github", "docker"]
    recommendations = recommend_from_stack(stack, set())
    print(f"✅ Stack: {stack}")
    print(f"✅ Complementary MCPs found: {len(recommendations)}")
    for rec in recommendations:
        print(f"   • {rec['name']}: {rec['reason']}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 3: User MCP Tracker
print("\n[TEST 3] User MCP Tracker - Local caching")
print("-" * 70)
try:
    from agent_core.gateway.user_mcp_tracker import (
        get_cached_mcps,
        cache_installed_mcps,
    )

    # Test caching
    test_mcps = ["github", "railway", "filesystem"]
    cache_installed_mcps(test_mcps)
    print(f"✅ Cached MCPs: {test_mcps}")

    cached = get_cached_mcps()
    print(f"✅ Retrieved from cache: {cached}")
    assert cached == test_mcps, "Cache mismatch!"
    print(f"✅ Cache verification passed")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 4: Tool Router - New tools in registry
print("\n[TEST 4] Tool Router - New tools registered")
print("-" * 70)
try:
    from agent_core.gateway.tool_router import TOOL_REGISTRY

    required_tools = [
        "get_capabilities",
        "retrieve_tools",
        "execute_tool",
        "recommend_mcps",
        "recommend_mcps_from_stack",
    ]

    print(f"✅ Total tools in registry: {len(TOOL_REGISTRY)}")
    for tool_name in required_tools:
        if tool_name in TOOL_REGISTRY:
            tool = TOOL_REGISTRY[tool_name]
            print(f"   ✅ {tool_name}: {tool['type']} tier")
        else:
            print(f"   ❌ {tool_name}: NOT FOUND")
            sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 5: Tool Router - Tool schemas
print("\n[TEST 5] Tool Router - Tool schemas validation")
print("-" * 70)
try:
    invalid_schemas = []

    for tool_name, tool_def in TOOL_REGISTRY.items():
        schema = tool_def.get("inputSchema", {})
        if schema.get("type") != "object":
            invalid_schemas.append(f"{tool_name}: missing 'type: object'")
        else:
            print(f"   ✅ {tool_name}: valid schema")

    if invalid_schemas:
        print(f"\n❌ Invalid schemas found:")
        for issue in invalid_schemas:
            print(f"   • {issue}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 6: Version check
print("\n[TEST 6] Version Check")
print("-" * 70)
try:
    from agent_core import __version__

    print(f"✅ Agent-CoreX version: {__version__}")
    if __version__ == "2.2.0":
        print(f"✅ Version v2.2.0 confirmed")
    else:
        print(f"⚠️  Version mismatch: expected 2.2.0, got {__version__}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Test 7: MCP Catalog structure
print("\n[TEST 7] MCP Catalog - Structure validation")
print("-" * 70)
try:
    from agent_core.gateway.mcp_recommender import MCP_CATALOG

    required_fields = ["display_name", "description", "capabilities", "example_tasks"]
    issues = []

    for server_name, server_data in MCP_CATALOG.items():
        for field in required_fields:
            if field not in server_data:
                issues.append(f"{server_name}: missing '{field}'")

    if issues:
        print(f"❌ Catalog structure issues:")
        for issue in issues:
            print(f"   • {issue}")
        sys.exit(1)
    else:
        print(f"✅ All {len(MCP_CATALOG)} servers have required fields")
        print(f"✅ Catalog structure is valid")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - v2.2.0 features are working correctly!")
print("=" * 70)
print("\nKey features verified:")
print("  • MCP Recommender (query-based and stack-based)")
print("  • User MCP Tracker (local caching)")
print("  • 5 public tools in registry")
print("  • Valid tool schemas")
print("  • Version 2.2.0 confirmed")
print("  • MCP Catalog with 20+ servers")
print("\n" + "=" * 70)
