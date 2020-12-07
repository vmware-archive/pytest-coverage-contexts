"""
coveragectx.coverage.cli
~~~~~~~~~~~~~~~~~~~~~~~~

CLI entry point which only returns the path to the directory containing `sitecustomize.py`.
This path should be prepended to `PYTHONPATH` so that code coverage on subprocesses works
automatically
"""
import argparse
import sys

import coveragectx


def main():
    """
    Process CLI
    """
    parser = argparse.ArgumentParser(description="PyTest Dynamic Coverage Contexts")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Prints the path to where the sitecustomize.py is to trigger coverage tracking on sub-processes.",
    )
    options = parser.parse_args()
    if options.coverage:
        print(str(coveragectx.SITE_CUSTOMIZE_DIR), file=sys.stdout, flush=True)
        parser.exit(status=0)
    parser.exit(status=1, message=parser.format_usage())


if __name__ == "__main__":
    main()
