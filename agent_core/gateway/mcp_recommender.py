"""
MCP Recommendation Engine — local-first, no network calls, no rate limits.

Maps user query intent and tech stack to MCP server recommendations.
Uses keyword matching against a comprehensive MCP catalog.
"""

import re
from typing import Optional


# =============================================================================
# MCP CATALOG — All known MCP servers with metadata
# =============================================================================

MCP_CATALOG = {
    "github": {
        "display_name": "GitHub",
        "description": "GitHub repository and issue management",
        "capabilities": ["github", "version_control", "repository", "code_review", "issues", "pull_requests"],
        "example_tasks": ["search issues", "create pull request", "list repositories", "view commits"],
        "ecosystem_tags": ["dev", "vcs", "collaboration"],
    },
    "railway": {
        "display_name": "Railway",
        "description": "Deploy and manage applications on Railway",
        "capabilities": ["railway", "deployment", "devops", "infrastructure", "cloud", "services"],
        "example_tasks": ["deploy service", "view logs", "manage environment variables", "restart service"],
        "ecosystem_tags": ["deployment", "devops", "cloud"],
    },
    "aws": {
        "display_name": "AWS",
        "description": "Amazon Web Services cloud infrastructure",
        "capabilities": ["aws", "cloud", "infrastructure", "compute", "storage", "database", "serverless"],
        "example_tasks": ["launch EC2 instance", "upload to S3", "create Lambda function", "manage RDS database"],
        "ecosystem_tags": ["cloud", "infrastructure", "devops"],
    },
    "database": {
        "display_name": "Database",
        "description": "SQL database querying and management",
        "capabilities": ["database", "sql", "data_query", "analytics", "postgres", "mysql"],
        "example_tasks": ["run SQL query", "list tables", "check schema", "export data"],
        "ecosystem_tags": ["data", "backend"],
    },
    "filesystem": {
        "display_name": "Filesystem",
        "description": "Local file and directory operations",
        "capabilities": ["filesystem", "file_operations", "local_storage", "read", "write"],
        "example_tasks": ["read file", "list directory", "create folder", "delete files"],
        "ecosystem_tags": ["local", "util"],
    },
    "docker": {
        "display_name": "Docker",
        "description": "Docker container management and orchestration",
        "capabilities": ["docker", "containers", "devops", "containerization", "images"],
        "example_tasks": ["build image", "run container", "list containers", "push to registry"],
        "ecosystem_tags": ["devops", "containers", "deployment"],
    },
    "web": {
        "display_name": "Web Search & Fetch",
        "description": "Web search and content fetching",
        "capabilities": ["web_search", "web_scraping", "http_requests", "fetch"],
        "example_tasks": ["search the web", "fetch web page", "scrape content"],
        "ecosystem_tags": ["util", "web"],
    },
    "slack": {
        "display_name": "Slack",
        "description": "Slack messaging and team communication",
        "capabilities": ["slack", "messaging", "notifications", "team_communication", "channels"],
        "example_tasks": ["send message", "post in channel", "list channels", "create reminder"],
        "ecosystem_tags": ["communication", "notifications"],
    },
    "stripe": {
        "display_name": "Stripe",
        "description": "Payment processing and billing",
        "capabilities": ["stripe", "payments", "billing", "ecommerce", "subscriptions"],
        "example_tasks": ["create payment", "list invoices", "manage subscriptions"],
        "ecosystem_tags": ["payments", "backend"],
    },
    "openai": {
        "display_name": "OpenAI",
        "description": "OpenAI AI models and embeddings",
        "capabilities": ["openai", "ai", "language_model", "embeddings", "text_generation", "gpt"],
        "example_tasks": ["generate text", "create embeddings", "call GPT model"],
        "ecosystem_tags": ["ai", "ml"],
    },
    "qdrant": {
        "display_name": "Qdrant",
        "description": "Vector search and semantic memory",
        "capabilities": ["qdrant", "vector_search", "embeddings", "semantic_search", "memory"],
        "example_tasks": ["semantic search", "store vectors", "query similarity"],
        "ecosystem_tags": ["ai", "search", "ml"],
    },
    "playwright": {
        "display_name": "Playwright",
        "description": "Web automation and browser control",
        "capabilities": ["playwright", "browser_automation", "web_automation", "testing"],
        "example_tasks": ["navigate webpage", "fill form", "take screenshot", "test website"],
        "ecosystem_tags": ["automation", "testing"],
    },
}


# =============================================================================
# STACK COMPLEMENT MAP — Technology → Complementary MCPs
# =============================================================================

STACK_COMPLEMENT_MAP = {
    "github": ["filesystem", "docker", "aws", "railway", "web"],
    "docker": ["railway", "aws", "github", "filesystem"],
    "aws": ["docker", "database", "railway", "github"],
    "python": ["database", "filesystem", "web", "openai"],
    "javascript": ["github", "web", "database", "nodejs"],
    "react": ["github", "filesystem", "web"],
    "nodejs": ["docker", "railway", "github", "database"],
    "postgres": ["database", "aws", "docker"],
    "mysql": ["database", "aws", "docker"],
    "kubernetes": ["docker", "aws", "database"],
    "terraform": ["aws", "docker", "github"],
    "gcp": ["docker", "database", "github"],
}


# =============================================================================
# RECOMMENDATION FUNCTIONS
# =============================================================================

def recommend_from_query(query: str, installed_mcps: set[str]) -> list[dict]:
    """
    Recommend MCP servers for a user query.

    Algorithm:
    1. Tokenize query to lowercase words
    2. For each MCP server, compute Jaccard similarity between query tokens
       and the server's capability keywords
    3. Score and rank by similarity
    4. Filter out already-installed MCPs
    5. Return top 3

    Args:
        query: Natural language query (e.g., "deploy my app to railway")
        installed_mcps: Set of already-installed MCP server names

    Returns:
        List of recommendations: [{name, display_name, reason, example_tasks}]
    """
    if not query.strip():
        return []

    # Tokenize query
    query_lower = query.lower()
    query_tokens = set(re.findall(r"\w+", query_lower))

    if not query_tokens:
        return []

    # Score each MCP by capability keyword match
    scores: dict[str, float] = {}
    for server_name, server_data in MCP_CATALOG.items():
        if server_name in installed_mcps:
            continue  # Skip already installed

        # Get capability keywords
        capabilities = set(kw.lower() for kw in server_data.get("capabilities", []))

        if not capabilities:
            continue

        # Jaccard similarity
        intersection = len(query_tokens & capabilities)
        union = len(query_tokens | capabilities)
        similarity = intersection / union if union > 0 else 0.0

        if similarity > 0.2:  # Only include if some match
            scores[server_name] = similarity

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Format top 3 results
    results = []
    for server_name, score in ranked[:3]:
        server_data = MCP_CATALOG[server_name]
        results.append({
            "name": server_name,
            "display_name": server_data.get("display_name", server_name.title()),
            "reason": server_data.get("description", ""),
            "example_tasks": server_data.get("example_tasks", [])[:3],
        })

    return results


def recommend_from_stack(stack: list[str], installed_mcps: set[str]) -> list[dict]:
    """
    Recommend complementary MCP servers based on a tech stack.

    Algorithm:
    1. For each item in the user's stack, look up complementary MCPs
    2. Merge and deduplicate
    3. Weight by frequency (more common complementary MCPs ranked higher)
    4. Filter out already-installed MCPs
    5. Return top 5

    Args:
        stack: List of technology names (e.g., ["github", "docker", "aws"])
        installed_mcps: Set of already-installed MCP server names

    Returns:
        List of recommendations: [{name, display_name, reason, example_tasks}]
    """
    if not stack:
        return []

    # Collect complements and their frequency
    complement_count: dict[str, int] = {}

    for tech in stack:
        tech_lower = tech.lower()
        # Direct mapping or fuzzy match in STACK_COMPLEMENT_MAP
        if tech_lower in STACK_COMPLEMENT_MAP:
            for complement in STACK_COMPLEMENT_MAP[tech_lower]:
                if complement not in installed_mcps:
                    complement_count[complement] = complement_count.get(complement, 0) + 1

    # Sort by frequency descending
    ranked = sorted(complement_count.items(), key=lambda x: x[1], reverse=True)

    # Format top 5 results
    results = []
    for server_name, freq in ranked[:5]:
        if server_name in MCP_CATALOG:
            server_data = MCP_CATALOG[server_name]
            results.append({
                "name": server_name,
                "display_name": server_data.get("display_name", server_name.title()),
                "reason": server_data.get("description", ""),
                "example_tasks": server_data.get("example_tasks", [])[:3],
            })

    return results


def get_all_known_mcps() -> list[str]:
    """Get list of all known MCP server names in the catalog."""
    return list(MCP_CATALOG.keys())
