"""CLI entry point for the EW-51 daemon service."""

import argparse
import logging
import sys
from pathlib import Path

import uvicorn


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the daemon.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    """Main entry point for the daemon CLI."""
    parser = argparse.ArgumentParser(
        description="Suruga Seiki EW-51 Motion Control Daemon"
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock backend instead of real hardware",
    )

    parser.add_argument(
        "--dll-path",
        type=str,
        help="Path to srgmc.dll (for real hardware backend)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (default: False)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Display configuration
    logger.info("=" * 60)
    logger.info("Suruga Seiki EW-51 Motion Control Daemon")
    logger.info("=" * 60)
    logger.info(f"Backend: {'Mock' if args.mock else 'Real Hardware'}")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Log Level: {args.log_level}")
    if args.dll_path:
        logger.info(f"DLL Path: {args.dll_path}")
    logger.info("=" * 60)

    # Import and configure the app
    from suruga_seiki_ew51.daemon.app.main import create_app

    app = create_app(use_mock=args.mock, dll_path=args.dll_path)

    # Run the server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower(),
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
