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

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection(self):
        """
        Perform the collection phase for the given session.
        """
        try:
            self.switch_context("collection")
            yield
        finally:
            self.switch_context(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_logstart(self, nodeid):
        """
        Called at the start of running the runtest protocol for a single item.
        """
        try:
            self.switch_context("{}|start".format(nodeid))
            yield
        finally:
            self.switch_context(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item):
        """
        Called to perform the setup phase for a test item.
        """
        try:
            self.switch_context("{}|setup".format(item.nodeid))
            yield
        finally:
            self.switch_context(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        """
        Called to run the test for test item (the call phase).
        """
        try:
            self.switch_context("{}|call".format(item.nodeid))
            yield
        finally:
            self.switch_context(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item):
        """
        Called to perform the teardown phase for a test item.
        """
        try:
            self.switch_context("{}|teardown".format(item.nodeid))
            yield
        finally:
            self.switch_context(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_logfinish(self, nodeid):
        """
        Called at the end of running the runtest protocol for a single item.
        """
        try:
            self.switch_context("{}|finish".format(nodeid))
            yield
        finally:
            self.switch_context(None)

    def switch_context(self, context):
        """
        Send the new dynamic context to PULL'ers
        """
        log.debug("Switching coverage context to: %s", context)
        with atomic_write(self.context_file_path, overwrite=True) as wfh:
            wfh.write(context or "")


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """
    Instantiate our plugin and register it
    """
    context_file_path = os.environ.get("COVERAGE_DYNAMIC_CONTEXT_FILE_PATH")
    if context_file_path is None:
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
    if context_file_path is not None:
        os.unlink(context_file_path)
