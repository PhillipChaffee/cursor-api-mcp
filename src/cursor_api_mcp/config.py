"""Runtime configuration for the Cursor API MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_truthy(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ServerConfig:
    """Server configuration.

    Attributes:
        read_only: When True, write tools are not registered.
    """

    read_only: bool = False

    @classmethod
    def from_env(cls, *, read_only_flag: bool = False) -> ServerConfig:
        """Build config from CLI flag and environment.

        Args:
            read_only_flag: Explicit ``--read-only`` CLI flag.

        Returns:
            Resolved server configuration. CLI flag or
            ``CURSOR_API_READ_ONLY`` enables read-only mode.
        """
        return cls(read_only=read_only_flag or _env_truthy("CURSOR_API_READ_ONLY"))
