from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn

from app.config import get_settings
from app.server import create_mcp_server
from app.utils.logging import setup_logging


def normalize_mount_path(path: str) -> str:
    path = (path or "/mcp").strip()
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1:
        path = path.rstrip("/")
    return path


def run_stdio() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    create_mcp_server().run()


def run_http(host: str, port: int, mount_path: str) -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    endpoint_path = normalize_mount_path(mount_path)
    app = create_mcp_server(streamable_http_path=endpoint_path).streamable_http_app()
    uvicorn.run(app, host=host, port=port, log_level=settings.log_level.lower())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-repro-mcp",
        description="Paper Reproduction Intelligence MCP Server",
    )
    parser.add_argument("legacy_transport", nargs="?", choices=("stdio", "http"), help=argparse.SUPPRESS)
    parser.add_argument("--transport", choices=("stdio", "http"), help="Transport to run.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mount-path", default="/mcp")
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.transport and args.legacy_transport and args.transport != args.legacy_transport:
        parser.error("Conflicting transport values.")
    args.transport = args.transport or args.legacy_transport
    if not args.transport:
        parser.error("Transport is required. Use --transport stdio or --transport http.")
    return args


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.transport == "stdio":
        run_stdio()
    else:
        run_http(args.host, args.port, args.mount_path)


if __name__ == "__main__":
    main()
