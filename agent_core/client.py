"""
HTTP client for the Agent-CoreX v2 backend.
All intelligence lives in the backend — this is a thin wrapper.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

# ── Custom exceptions ─────────────────────────────────────────────────────────


class AgentCoreXError(Exception):
    """Generic backend error (4xx/5xx)."""


class AuthError(AgentCoreXError):
    """Authentication failed (401)."""


class ConnectionError(AgentCoreXError):  # noqa: A001
    """Cannot reach the backend."""


class TimeoutError(AgentCoreXError):  # noqa: A001
    """Request timed out."""


# ── Client ────────────────────────────────────────────────────────────────────


class AgentCoreXClient:
    """Thin sync httpx client for the Agent-CoreX v2 backend."""

    def __init__(self, api_url: str, api_key: Optional[str] = None) -> None:
        self._base = api_url.rstrip("/")
        self._api_key = api_key

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h

    def _get(self, path: str, params: Optional[dict] = None, timeout: float = 10.0) -> Any:
        try:
            resp = httpx.get(
                f"{self._base}{path}",
                params=params,
                headers=self._headers(),
                timeout=timeout,
            )
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Cannot connect to {self._base}") from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Request timed out") from exc
        self._raise_for_status(resp)
        return resp.json()

    def _post(self, path: str, body: dict, timeout: float = 10.0) -> Any:
        try:
            resp = httpx.post(
                f"{self._base}{path}",
                json=body,
                headers=self._headers(),
                timeout=timeout,
            )
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Cannot connect to {self._base}") from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Request timed out") from exc
        self._raise_for_status(resp)
        return resp.json()

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.status_code == 401:
            raise AuthError("Invalid or missing API key. Run: agent-corex login --key <key>")
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("error") or resp.json().get("detail") or resp.text
            except Exception:
                detail = resp.text
            raise AgentCoreXError(f"Backend error {resp.status_code}: {detail}")

    # ── Public API ────────────────────────────────────────────────────────────

    def execute_query(self, query: str) -> dict:
        """
        POST /execute/query — main end-to-end execution pipeline.
        Returns QueryResponse: {query, steps, total_latency_ms}
        """
        return self._post("/execute/query", {"query": query}, timeout=120.0)

    def health(self) -> dict:
        """GET /health — returns {"status": "ok", "version": "2.0"}."""
        return self._get("/health", timeout=5.0)

    def get_state(self, ref: str) -> dict:
        """GET /state/{ref} — fetch full output by state reference."""
        # ref may be "state://uuid" or just "uuid"
        ref_id = ref.removeprefix("state://")
        return self._get(f"/state/{ref_id}", timeout=10.0)

    def retrieve(self, query: str, top_k: int = 5, debug: bool = False) -> list:
        """GET /retrieve/ — semantic + keyword tool search."""
        return self._get(
            "/retrieve/",
            params={"query": query, "top_k": top_k, "debug": str(debug).lower()},
        )

    def select(self, query: str, debug: bool = False) -> dict:
        """GET /select/ — retrieve + select best tool with confidence scoring."""
        return self._get(
            "/select/",
            params={"query": query, "debug": str(debug).lower()},
        )

    # ── MCP server management ─────────────────────────────────────────────────

    def list_available_servers(self) -> List[Dict]:
        """GET /mcp/servers — catalog of all available MCP servers."""
        return self._get("/mcp/servers", timeout=10.0)

    def list_user_servers(self) -> List[Dict]:
        """GET /user/servers — servers the authenticated user has enabled."""
        return self._get("/user/servers", timeout=10.0)

    def add_server(self, name: str) -> Dict:
        """POST /user/servers/{name} — enable a server for the authenticated user."""
        return self._post(f"/user/servers/{name}", {}, timeout=10.0)

    def remove_server(self, name: str) -> Dict:
        """DELETE /user/servers/{name} — disable a server for the authenticated user."""
        try:
            resp = httpx.delete(
                f"{self._base}/user/servers/{name}",
                headers=self._headers(),
                timeout=10.0,
            )
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Cannot connect to {self._base}") from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Request timed out") from exc
        self._raise_for_status(resp)
        return resp.json()

    # ── Hybrid execution (free-tier) ──────────────────────────────────────────

    def plan_query(self, query: str) -> Dict:
        """
        POST /execute/plan — plan-only query execution.
        Returns QueryResponse with planned steps (no execution).
        Client executes locally and reports back via submit_result().
        """
        return self._post("/execute/plan", {"query": query}, timeout=60.0)

    def submit_result(self, payload: Dict) -> Dict:
        """
        POST /execute/result — report a locally-executed tool result to the backend.
        Returns {"ref": "state://...", "preview": "..."}.
        """
        return self._post("/execute/result", payload, timeout=10.0)
