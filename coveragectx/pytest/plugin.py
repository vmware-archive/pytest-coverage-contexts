"""
..
    PYTEST_DONT_REWRITE

coveragectx.pytest.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~

PyTest Dynamic Coverage Contexts Plugin
"""
import logging
import os

import pytest
import zmq.ssh

log = logging.getLogger(__name__)


class CoverageContextPlugin:
    """
    PyTest Plugin implementation
    """

    def __init__(self):
        self.context = None
        self.pusher = None
        self.running = False

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
        log.info("Switching to context: %s", context)
        os.environ["COVERAGE_DYNAMIC_CONTEXT"] = context
        if self.pusher is not None:
            self.pusher.send_string(context)
        log.info("Switched to context: %s", context)

    def start(self):
        """
        Start the plugin
        """
        if self.running is True:
            return

        log.info("Starting %s", self)
        context = zmq.Context()
        pusher = context.socket(zmq.PUB)  # pylint: disable=no-member
        address = "tcp://127.0.0.1:{}".format(*zmq.ssh.tunnel.select_random_ports(1))
        log.warning("Address: %s", address)
        # address = "{}:{}".format(address, pusher.bind_to_random_port(address))
        pusher.connect(address)
        os.environ["COVERAGE_DYNAMIC_CONTEXT_ADDRESS"] = address
        self.context = context
        self.pusher = pusher
        self.running = True
        log.info("%s is listening @ %s", self, address)

    def stop(self):
        """
        Stop the plugin
        """
        if self.running is False:
            return

        log.info("Stopping %s", self)
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
    log.info("1")


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
