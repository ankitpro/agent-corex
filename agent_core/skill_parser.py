"""
Skill Parser — Parse skill.md files for the `agent-corex apply` command.

A skill.md file is a YAML-front-matter markdown document that describes
how to install and configure a pack or MCP server.

Supported format:

    ---
    name: my-skill
    type: pack          # pack | server
    install: "npm install -g something"   # optional shell command
    requires:           # MCP servers to install (for packs)
      - github
      - railway
    env:                # environment variables required or optional
      GITHUB_TOKEN: required
      REDIS_URL: optional
    connect:            # MCP server definition (for type: server)
      command: npx
      args: ["-y", "@some/mcp-server"]
      env:
        SOME_KEY: "${SOME_KEY}"
    test: "List my GitHub repositories"
    ai_instructions: |
      Use this pack to deploy to Railway...
    ---

    # My Skill
    Description here...

The body (below ---) is stored in `description` and shown to the user.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional
from dataclasses import dataclass, field

# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class SkillSpec:
    """Parsed representation of a skill.md file."""

    name: str
    type: Literal["pack", "server"]

    # Optional install command (shell string, run before MCP config)
    install: Optional[str] = None

    # MCP server names from registry to install (for pack type)
    requires: List[str] = field(default_factory=list)

    # Env vars: key → "required" | "optional"
    env: Dict[str, str] = field(default_factory=dict)

    # MCP connect definition (for server type)
    connect: Optional[Dict[str, Any]] = None

    # Test prompt to run after install
    test: Optional[str] = None

    # Instructions for AI agents reading this file
    ai_instructions: Optional[str] = None

    # Human-readable description (markdown body)
    description: str = ""

    # Raw parsed YAML front matter (for forward-compatibility)
    raw: Dict[str, Any] = field(default_factory=dict)


# ── Parser ────────────────────────────────────────────────────────────────────

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse(content: str) -> SkillSpec:
    """
    Parse a skill.md string and return a SkillSpec.

    Raises ValueError on invalid format or missing required fields.
    """
    # Extract YAML front matter
    match = _FRONT_MATTER_RE.match(content)
    if not match:
        raise ValueError(
            "skill.md must start with a YAML front matter block (--- ... ---). "
            "No front matter found."
        )

    yaml_text = match.group(1)
    body = content[match.end() :].strip()

    # Parse YAML — try PyYAML, fall back to basic parser
    try:
        data = _parse_yaml(yaml_text)
    except Exception as exc:
        raise ValueError(f"Invalid YAML in skill.md front matter: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("skill.md front matter must be a YAML mapping (key: value pairs)")

    # Validate required fields
    name = data.get("name")
    if not name:
        raise ValueError("skill.md must have a 'name' field")

    skill_type = data.get("type", "pack")
    if skill_type not in ("pack", "server"):
        raise ValueError(f"skill.md 'type' must be 'pack' or 'server', got: {skill_type!r}")

    # Parse env block: normalise to {KEY: "required"|"optional"}
    env_raw = data.get("env", {}) or {}
    env: Dict[str, str] = {}
    if isinstance(env_raw, dict):
        for k, v in env_raw.items():
            v_str = str(v).lower().strip() if v is not None else "required"
            env[str(k)] = "optional" if v_str in ("optional", "false", "no") else "required"
    elif isinstance(env_raw, list):
        # Allow list form: [GITHUB_TOKEN, REDIS_URL]
        for item in env_raw:
            env[str(item)] = "required"

    # Parse requires (list of server names)
    requires_raw = data.get("requires", []) or []
    requires: List[str] = [str(r) for r in requires_raw] if isinstance(requires_raw, list) else []

    # Parse connect block
    connect = data.get("connect")
    if connect is not None and not isinstance(connect, dict):
        raise ValueError("skill.md 'connect' must be a YAML mapping")

    # Validate: server type needs connect block
    if skill_type == "server" and not connect and not requires:
        raise ValueError(
            "skill.md with type 'server' must have a 'connect' block "
            "or at least one entry in 'requires'"
        )

    return SkillSpec(
        name=str(name),
        type=skill_type,  # type: ignore[arg-type]
        install=str(data["install"]) if data.get("install") else None,
        requires=requires,
        env=env,
        connect=connect,
        test=str(data["test"]) if data.get("test") else None,
        ai_instructions=str(data["ai_instructions"]) if data.get("ai_instructions") else None,
        description=body,
        raw=data,
    )


def parse_file(path: str) -> SkillSpec:
    """Load and parse a skill.md from a local file path."""
    import pathlib

    content = pathlib.Path(path).read_text(encoding="utf-8")
    return parse(content)


def fetch_and_parse(url: str, timeout: float = 15.0) -> SkillSpec:
    """Fetch a skill.md from a URL and parse it."""
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError(
            "httpx is required to fetch remote skill.md files. Run: pip install httpx"
        ) from exc

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return parse(resp.text)


# ── YAML helper ───────────────────────────────────────────────────────────────


def _parse_yaml(text: str) -> Any:
    """
    Parse YAML text. Uses PyYAML if available, otherwise a minimal fallback
    that handles the subset of YAML used in skill.md files.
    """
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        pass

    return _minimal_yaml_parse(text)


def _minimal_yaml_parse(text: str) -> Dict[str, Any]:
    """
    Minimal YAML parser that handles the subset needed for skill.md:
    - key: scalar
    - key: |  (block scalar)
    - key:    (followed by list items with -)
    - key:    (followed by sub-mapping)
    - list items: - value
    """
    lines = text.splitlines()
    result: Dict[str, Any] = {}
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # Skip blank lines and comments
        if not stripped or stripped.lstrip().startswith("#"):
            i += 1
            continue

        # Detect indentation level
        indent = len(line) - len(line.lstrip())

        # Only process top-level keys (indent == 0)
        if indent != 0:
            i += 1
            continue

        if ":" not in stripped:
            i += 1
            continue

        key, _, rest = stripped.partition(":")
        key = key.strip()
        rest = rest.strip()

        if not key:
            i += 1
            continue

        # Block scalar (|)
        if rest in ("|", ">"):
            block_lines = []
            i += 1
            while i < len(lines):
                bl = lines[i]
                if bl and (len(bl) - len(bl.lstrip())) > 0:
                    block_lines.append(bl.strip())
                    i += 1
                elif not bl.strip():
                    block_lines.append("")
                    i += 1
                else:
                    break
            result[key] = "\n".join(block_lines).strip()
            continue

        # Empty value — could be list or mapping on next lines
        if not rest:
            sub_lines = []
            j = i + 1
            while j < len(lines):
                sl = lines[j]
                if not sl.strip():
                    j += 1
                    continue
                sl_indent = len(sl) - len(sl.lstrip())
                if sl_indent > 0:
                    sub_lines.append(sl)
                    j += 1
                else:
                    break

            if sub_lines:
                first = sub_lines[0].lstrip()
                if first.startswith("- "):
                    # List
                    items = []
                    for sl in sub_lines:
                        s = sl.lstrip()
                        if s.startswith("- "):
                            items.append(_parse_scalar(s[2:].strip()))
                    result[key] = items
                    i = j
                    continue
                else:
                    # Sub-mapping
                    sub = {}
                    for sl in sub_lines:
                        s = sl.lstrip()
                        if ":" in s:
                            sk, _, sv = s.partition(":")
                            sub[sk.strip()] = _parse_scalar(sv.strip())
                    result[key] = sub
                    i = j
                    continue
            else:
                result[key] = None
                i += 1
                continue

        # Inline list: [a, b, c]
        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1]
            items = [
                _parse_scalar(x.strip().strip('"').strip("'"))
                for x in inner.split(",")
                if x.strip()
            ]
            result[key] = items
            i += 1
            continue

        # Plain scalar
        result[key] = _parse_scalar(rest)
        i += 1

    return result


def _parse_scalar(value: str) -> Any:
    """Convert a string YAML scalar to an appropriate Python type."""
    if not value:
        return None
    v = value.strip().strip('"').strip("'")
    if v.lower() in ("true", "yes"):
        return True
    if v.lower() in ("false", "no"):
        return False
    if v.lower() in ("null", "~", "none"):
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v
