"""
    tests.functional.test_cli
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test CLI usage
"""
import logging
import subprocess

import coveragectx

log = logging.getLogger(__name__)


def test_site_custimize_directory_output():
    """Test proper CLI usage"""
    proc = subprocess.run(
        ["pytest-coverage-context", "--coverage"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    assert proc.returncode == 0
    assert not proc.stderr
    assert proc.stdout.strip() == str(coveragectx.SITE_CUSTOMIZE_DIR)


def test_exit_code_on_no_flags():
    """Test bad CLI usage"""
    proc = subprocess.run(
        ["pytest-coverage-context"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    assert proc.returncode == 1
