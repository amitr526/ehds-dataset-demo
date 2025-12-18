"""
CSV to HealthDCAT Turtle Converter - Main entry point. 

This module provides the command-line interface for converting CSV files
to RDF Turtle format according to HealthDCAT specification.
"""

import argparse
import logging
import sys
from pathlib import Path

from csv_to_healthdcat.converter import CSVToHealthDCAT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for the CLI application. 

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Convert CSV files to RDF Turtle format according to HealthDCAT specification"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=str,
        help="Path to input CSV file",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        type=str,
        help="Path to output Turtle file",
    )
    parser.add_argument(
        "--base-uri",
        "-b",
        default="http://example.org/",
        type=str,
        help="Base URI for RDF resources (default: http://example.org/)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging. getLogger().setLevel(logging.DEBUG)

    try:
        input_path = Path(args.input)
        output_path = Path(args.output)

        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return 1

        logger.info(f"Reading CSV from: {input_path}")
        converter = CSVToHealthDCAT(base_uri=args.base_uri)
        graph = converter.convert_csv(str(input_path))

        logger.info(f"Writing Turtle output to: {output_path}")
        graph.serialize(destination=str(output_path), format="turtle")

        logger.info("Conversion completed successfully!")
        return 0

    except Exception as e:
        logger. error(f"Error during conversion: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
