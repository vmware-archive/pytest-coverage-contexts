"""
..
    PYTEST_DONT_REWRITE

coveragectx.pytest.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~

PyTest Dynamic Coverage Contexts Plugin
"""
import contextlib
import logging
import os
import socket

import attr
import pytest
import zmq

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
        if context is None:
            log.debug("Resetting context")
            context = "[{NONE}]"
        else:
            log.debug("Switching context to: %s", context)
        os.environ["COVERAGE_DYNAMIC_CONTEXT"] = context
        if self.pusher is not None:
            self.pusher.send_string(context)

    def start(self):
        """
        Start the plugin
        """
        if self.running is True:
            return

        self.address = "tcp://127.0.0.1:{}".format(self.get_unused_localhost_port())
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
        self.pusher.close(1500)
        self.context.term()
        self.pusher = self.context = self.running = None

    @staticmethod
    def get_unused_localhost_port():
        """
        Return a random unused port on localhost
        """
        with contextlib.closing(
            socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        ) as usock:
            usock.bind(("127.0.0.1", 0))
            port = usock.getsockname()[1]
            return port


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
