"""Input Abstraction Layer for agent-corex.

Provides MCP-agnostic input handling:
  - Auto-classifies parameters as user-facing vs internal
  - Hides internal params from LLM in retrieve_tools output
  - Validates and injects internal params at execution time
"""

from .classifier import ParamClassifier
from .models import InputField, InternalParam, ToolInputSchema
from .registry import AbstractionRegistry
from .resolver import ContextResolver

__all__ = [
    "InputField",
    "InternalParam",
    "ToolInputSchema",
    "ParamClassifier",
    "AbstractionRegistry",
    "ContextResolver",
]
