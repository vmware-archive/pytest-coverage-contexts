"""
..
    PYTEST_DONT_REWRITE

This module gets imported by Python's site machinery
"""
try:
    import coverage

    coverage.process_startup()
except ImportError:
    pass
