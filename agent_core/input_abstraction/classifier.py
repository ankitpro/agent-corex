"""Parameter classifier — auto-generates input abstractions from raw MCP schemas.

Classifies each parameter as:
  - User-facing (required or optional input): shown to LLM
  - Internal (resolved automatically): never shown to LLM

Uses pattern-based classification: exact name matches, suffix/prefix patterns, and
description-based tiebreakers for ambiguous cases.
"""

from __future__ import annotations

from .models import InputField, InternalParam, ToolInputSchema


# Rules applied in order; first match wins.
# Each rule: (pattern_type, value, resolution_strategy)
INTERNAL_PATTERNS: list[tuple[str, str, str]] = [
    # Exact name matches (case-sensitive)
    ("exact", "workspacePath", "workspace_path"),
    ("exact", "workspace_path", "workspace_path"),
    ("exact", "userId", "user_id"),
    ("exact", "user_id", "user_id"),

    # Suffix patterns (case-insensitive, but matched case-sensitively on the suffix)
    # These catch projectId, project_id, organizationId, organization_id, etc.
    ("suffix", "Id", "context_id"),
    ("suffix", "_id", "context_id"),
    ("suffix", "Token", "auth_token"),
    ("suffix", "Secret", "auth_secret"),
    ("suffix", "Key", "auth_key"),

    # Prefix patterns (case-insensitive)
    ("prefix_ci", "workspace", "workspace_path"),
]

# Description-based signals for internal parameters.
# If a param name is ambiguous (e.g., "path") but the description contains
# these phrases, it's classified as internal.
INTERNAL_DESCRIPTION_SIGNALS = ["workspace", "automatically", "resolved", "linked"]

# Case-insensitive description checks
INTERNAL_DESCRIPTION_SIGNALS_LOWER = [s.lower() for s in INTERNAL_DESCRIPTION_SIGNALS]


def _display_name_from_param_name(param_name: str) -> str:
    """Convert param_name to display_name.

    Examples:
        "workspacePath" → "Workspace Path"
        "project_id" → "Project Id"
        "query" → "Query"
    """
    # Handle camelCase: insert space before uppercase letters
    result = ""
    for i, c in enumerate(param_name):
        if i > 0 and c.isupper() and param_name[i - 1].islower():
            result += " "
        result += c

    # Handle snake_case: replace underscores with spaces
    result = result.replace("_", " ")

    # Capitalize each word
    return " ".join(word.capitalize() for word in result.split())


class ParamClassifier:
    """Auto-generates ToolInputSchema from raw MCP inputSchema."""

    def classify(self, name: str, prop: dict) -> str | None:
        """Classify a single parameter as internal or user-facing.

        Args:
            name: Parameter name (e.g., "workspacePath", "query")
            prop: JSON Schema property dict with type, description, etc.

        Returns:
            Resolution strategy string if internal (e.g., "workspace_path")
            None if user-facing
        """
        # Check exact name matches (highest priority)
        for pattern_type, pattern_value, strategy in INTERNAL_PATTERNS:
            if pattern_type == "exact" and name == pattern_value:
                return strategy

        # Check suffix patterns
        for pattern_type, pattern_value, strategy in INTERNAL_PATTERNS:
            if pattern_type == "suffix" and name.endswith(pattern_value):
                # Tiebreaker: if it's a "path" suffix, check description
                # "path" alone (e.g. "path" in filesystem) is user-facing
                # but "workspacePath" is internal
                if pattern_value == "path":
                    desc = prop.get("description", "").lower()
                    if any(signal in desc for signal in INTERNAL_DESCRIPTION_SIGNALS_LOWER):
                        return strategy
                    else:
                        # "path" without internal signals → user-facing
                        continue
                return strategy

        # Check prefix patterns (case-insensitive)
        for pattern_type, pattern_value, strategy in INTERNAL_PATTERNS:
            if pattern_type == "prefix_ci" and name.lower().startswith(pattern_value.lower()):
                return strategy

        # Check description for internal signals (tiebreaker for edge cases)
        desc = prop.get("description", "").lower()
        if any(signal in desc for signal in INTERNAL_DESCRIPTION_SIGNALS_LOWER):
            # Only classify as internal if the description strongly suggests it
            # (e.g., "The path to the workspace" or "automatically resolved")
            if desc.count(" ") > 3:  # Reasonable description length
                return "auto_resolved"

        # Default: user-facing
        return None

    def build_schema(self, tool_name: str, server: str, raw_schema: dict) -> ToolInputSchema:
        """Auto-generate ToolInputSchema from raw MCP inputSchema.

        Args:
            tool_name: Name of the tool
            server: MCP server name
            raw_schema: Raw JSON Schema from MCP (e.g., {type: "object", properties: {...}})

        Returns:
            Fully populated ToolInputSchema with required/optional/internal classified
        """
        required_inputs = []
        optional_inputs = []
        internal_params = []

        # Handle empty or missing schema
        if not isinstance(raw_schema, dict):
            return ToolInputSchema(
                tool_name=tool_name,
                server=server,
                required_inputs=[],
                optional_inputs=[],
                internal_params=[],
                is_auto_generated=True,
            )

        properties = raw_schema.get("properties", {})
        if not isinstance(properties, dict):
            return ToolInputSchema(
                tool_name=tool_name,
                server=server,
                required_inputs=[],
                optional_inputs=[],
                internal_params=[],
                is_auto_generated=True,
            )

        required_names = raw_schema.get("required", []) or []
        if not isinstance(required_names, list):
            required_names = []

        # Classify each property
        for param_name, param_spec in properties.items():
            is_required = param_name in required_names
            strategy = self.classify(param_name, param_spec)

            if strategy is not None:
                # Internal parameter
                internal_params.append(
                    InternalParam(
                        name=param_name,
                        resolution_strategy=strategy,
                    )
                )
            else:
                # User-facing parameter
                field = InputField(
                    name=param_name,
                    display_name=_display_name_from_param_name(param_name),
                    description=param_spec.get("description", ""),
                    type=param_spec.get("type", "string"),
                    required=is_required,
                    default=param_spec.get("default"),
                    enum=param_spec.get("enum"),
                    examples=param_spec.get("examples"),
                )
                if is_required:
                    required_inputs.append(field)
                else:
                    optional_inputs.append(field)

        return ToolInputSchema(
            tool_name=tool_name,
            server=server,
            required_inputs=required_inputs,
            optional_inputs=optional_inputs,
            internal_params=internal_params,
            is_auto_generated=True,
        )
