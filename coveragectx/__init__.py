"""
..
    PYTEST_DONT_REWRITE
"""
# pylint: disable=missing-module-docstring
# pragma: no cover
import pathlib

try:
    from .version import __version__
except ImportError:
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        __version__ = get_distribution(__name__).version
    except DistributionNotFound:
        # package is not installed
        __version__ = "0.0.0.not-installed"

__version_info__ = tuple([int(p) for p in __version__.split(".") if p.isdigit()])

# Define some constants
CODE_ROOT_DIR = pathlib.Path(__file__).resolve().parent
SITE_CUSTOMIZE_DIR = CODE_ROOT_DIR / "coverage" / "site"
