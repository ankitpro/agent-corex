import re


def tokenize(text: str):
    return set(re.findall(r"\w+", text.lower()))


def score(query: str, tool) -> float:
    """
    Basic keyword overlap scoring
    """
    query_tokens = tokenize(query)
    text = f"{tool['name']} {tool.get('description', '')}"
    tool_tokens = tokenize(text)

    if not tool_tokens:
        return 0.0

    overlap = query_tokens.intersection(tool_tokens)
    return len(overlap) / len(query_tokens) if query_tokens else 0.0
