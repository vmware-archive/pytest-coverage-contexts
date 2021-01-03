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

    context_file_path = attr.ib(init=False, hash=False)
    running = attr.ib(init=False, default=False, hash=False)

    @pytest.hookimpl
    def pytest_collection(self):
        """
        Perform the collection phase for the given session.
        """
        self.switch_context("collection")

    @pytest.hookimpl
    def pytest_runtest_logstart(self, nodeid):
        """
        Called at the start of running the runtest protocol for a single item.
        """
        self.switch_context("{}|start".format(nodeid))

    @pytest.hookimpl
    def pytest_runtest_setup(self, item):
        """
        Called to perform the setup phase for a test item.
        """
        self.switch_context("{}|setup".format(item.nodeid))

    @pytest.hookimpl
    def pytest_runtest_call(self, item):
        """
        Called to run the test for test item (the call phase).
        """
        self.switch_context("{}|call".format(item.nodeid))

    @pytest.hookimpl
    def pytest_runtest_teardown(self, item):
        """
        Called to perform the teardown phase for a test item.
        """
        self.switch_context("{}|teardown".format(item.nodeid))

    @pytest.hookimpl
    def pytest_runtest_logfinish(self, nodeid):
        """
        Called at the end of running the runtest protocol for a single item.
        """
        self.switch_context("{}|finish".format(nodeid))

    def switch_context(self, context):
        """
        Send the new dynamic context to PULL'ers
        """
        log.debug("Switching coverage context to: %s", context)
        with atomic_write(self.context_file_path, overwrite=True) as wfh:
            wfh.write(context)

    def start(self):
        """
        Start the plugin
        """
        if self.running is True:
            return

        handle, self.context_file_path = tempfile.mkstemp()
        os.close(handle)
        log.debug("%s is starting...", self)
        os.environ["COVERAGE_DYNAMIC_CONTEXT_FILE_PATH"] = self.context_file_path
        self.running = True
        log.debug("%s started.", self)

    def stop(self):
        """
        Stop the plugin
        """
        if self.running is False:
            return

        log.debug("%s is stopping...", self)
        self.running = False
        os.unlink(self.context_file_path)
        log.debug("%s stopped.", self)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """
    Instantiate our plugin and register it
    """
    _plugin = CoverageContextPlugin()
    config.pluginmanager.register(_plugin, "coverage-context-plugin")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """
    Start our plugin
    """
    _plugin = session.config.pluginmanager.get_plugin("coverage-context-plugin")
    if _plugin:
        _plugin.start()


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    """
    Stop our plugin
    """
    _plugin = session.config.pluginmanager.get_plugin("coverage-context-plugin")
    if _plugin:
        _plugin.stop()
