"""
..
    PYTEST_DONT_REWRITE

This module gets imported by Python's site machinery
"""
import sys
import traceback

try:
    import coverage

    coverage.process_startup()
except ImportError:
    # We just ignore if coverage is not importable
    pass
except Exception:  # pylint: disable=broad-except
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    raise
