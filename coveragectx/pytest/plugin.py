"""
..
    PYTEST_DONT_REWRITE

coveragectx.pytest.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~

PyTest Dynamic Coverage Contexts Plugin
"""
import logging
import os

import attr
import pytest
import zmq.ssh

log = logging.getLogger(__name__)


@attr.s(kw_only=True, slots=True, hash=True)
class CoverageContextPlugin:
    """
    PyTest Plugin implementation
    """

    context = attr.ib(init=False, default=None, repr=False, hash=False)
    pusher = attr.ib(init=False, default=None, repr=False, hash=False)
    address = attr.ib(init=False, default=None)
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
        log.debug("Switching to context: %s", context)
        os.environ["COVERAGE_DYNAMIC_CONTEXT"] = context
        if self.pusher is not None:
            self.pusher.send_string(context)
        log.debug("Switched to context: %s", context)

    def start(self):
        """
        Start the plugin
        """
        if self.running is True:
            return

        self.address = "tcp://127.0.0.1:{}".format(*zmq.ssh.tunnel.select_random_ports(1))
        log.debug("Starting %s", self)
        context = zmq.Context()
        pusher = context.socket(zmq.PUB)  # pylint: disable=no-member
        pusher.connect(self.address)
        os.environ["COVERAGE_DYNAMIC_CONTEXT_ADDRESS"] = self.address
        self.context = context
        self.pusher = pusher
        self.running = True
        log.debug("%s is listening", self)

    def stop(self):
        """
        Stop the plugin
        """
        if self.running is False:
            return

        log.debug("Stopping %s", self)
        self.running = False
        self.pusher.send_string("[{STOP}]")
        self.pusher.close(1000)
        self.context.term()
        self.pusher = self.context = self.running = None


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
    _plugin.start()


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    """
    Stop our plugin
    """
    _plugin = session.config.pluginmanager.get_plugin("coverage-context-plugin")
    _plugin.stop()
