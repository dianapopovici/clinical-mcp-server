"""CLI entrypoint: `python -m clinical_mcp --transport {stdio,http}`."""

from __future__ import annotations

import argparse

from clinical_mcp.server import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Clinical MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="stdio for local agents (Claude Desktop); http for remote agents.",
    )
    args = parser.parse_args()
    run(transport=args.transport)


if __name__ == "__main__":
    main()
