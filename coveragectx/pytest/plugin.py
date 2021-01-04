"""
..
    PYTEST_DONT_REWRITE

coveragectx.pytest.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~

PyTest Dynamic Coverage Contexts Plugin
"""
import logging
import os
import tempfile
from contextlib import contextmanager

import attr
import pytest
from atomicwrites import atomic_write

log = logging.getLogger(__name__)


@attr.s(kw_only=True, slots=True, hash=True)
class CoverageContextPlugin:
    """
    PyTest Plugin implementation
    """

    context_file_path = attr.ib()
    running = attr.ib(init=False, default=False, hash=False)

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_collection(self):
        """
        Perform the collection phase for the given session.
        """
        with self.switch_context("collection"):
            yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_logstart(self, nodeid):
        """
        Called at the start of running the runtest protocol for a single item.
        """
        with self.switch_context("{}|start".format(nodeid)):
            yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_setup(self, item):
        """
        Called to perform the setup phase for a test item.
        """
        with self.switch_context("{}|setup".format(item.nodeid)):
            yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_call(self, item):
        """
        Called to run the test for test item (the call phase).
        """
        with self.switch_context("{}|call".format(item.nodeid)):
            yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_teardown(self, item):
        """
        Called to perform the teardown phase for a test item.
        """
        with self.switch_context("{}|teardown".format(item.nodeid)):
            yield

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_logfinish(self, nodeid):
        """
        Called at the end of running the runtest protocol for a single item.
        """
        with self.switch_context("{}|finish".format(nodeid)):
            yield

    @contextmanager
    def switch_context(self, context):
        """
        Update the dynamic context file
        """
        log.debug("Switching coverage context to: %s", context)
        try:
            with atomic_write(self.context_file_path, overwrite=True) as wfh:
                wfh.write(context)
            yield
        finally:
            with atomic_write(self.context_file_path, overwrite=True) as wfh:
                wfh.write("")


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """
    Instantiate our plugin and register it
    """
    context_file_path = os.environ.get("COVERAGE_DYNAMIC_CONTEXT_FILE_PATH")
    if context_file_path is None:  # pragma: no cover
        handle, context_file_path = tempfile.mkstemp()
        os.close(handle)
        os.environ["COVERAGE_DYNAMIC_CONTEXT_FILE_PATH"] = context_file_path
    config.pluginmanager.register(
        CoverageContextPlugin(context_file_path=context_file_path), "coverage-context-plugin"
    )


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish():
    """
    Cleanup
    """
    context_file_path = os.environ.get("COVERAGE_DYNAMIC_CONTEXT_FILE_PATH")
    if context_file_path is not None and os.path.exists(context_file_path):  # pragma: no cover
        os.unlink(context_file_path)
