import argparse
from typing import Optional
from .config import Config

def setup_arg_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    config = Config()
    parser = argparse.ArgumentParser(description="Tour Guide Script")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Populate command
    populate_parser = subparsers.add_parser("populate", help="Populate the database")
    populate_parser.add_argument("--reset", action="store_true", help="Clear the database before populating")
    populate_parser.add_argument("--data-path", type=str, help="Path to data directory", default=str(config.DATA_PATH))

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query_text", type=str, help="The query text")
    query_parser.add_argument("--chroma-path", type=str, help="Path to Chroma DB", default=str(config.CHROMA_PATH))

    return parser 