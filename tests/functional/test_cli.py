import logging
import subprocess

import coveragectx

log = logging.getLogger(__name__)


def test_site_custimize_directory_output():
    proc = subprocess.run(
        ["pytest-coverage-context", "--coverage"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    log.info("D: %s", proc.stderr)
    assert proc.returncode == 0
    assert proc.stdout.strip() == str(coveragectx.SITE_CUSTOMIZE_DIR)
