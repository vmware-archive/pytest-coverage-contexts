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
import time

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

    def get_unused_localhost_port(self, cached_seconds=10):
        """
        Return a random unused port on localhost
        """
        if not isinstance(cached_seconds, (int, float)):
            raise RuntimeError(
                "The value of 'cached_seconds' needs to be an integer or a float, not {}".format(
                    type(cached_seconds)
                )
            )
        if cached_seconds < 0:
            raise RuntimeError(
                "The value of 'cached_seconds' needs to be a positive number, not {}".format(
                    cached_seconds
                )
            )
        try:
            generated_ports = self.get_unused_localhost_port.__used_ports__
            # Cleanup ports. The idea behind this call is so that two consecutive calls to this
            # function don't return the same port just because the first call hasn't actually started
            # using the port.
            # It also makes this cache invalid after <cached_seconds> second
            for port in list(generated_ports):
                if generated_ports[port] <= time.time():
                    generated_ports.pop(port)
        except AttributeError:
            generated_ports = self.get_unused_localhost_port.__used_ports__ = {}

        with contextlib.closing(
            socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        ) as usock:
            usock.bind(("127.0.0.1", 0))
            port = usock.getsockname()[1]
        if port not in generated_ports:
            generated_ports[port] = time.time() + cached_seconds
            return port
        return self.get_unused_localhost_port(cached_seconds=cached_seconds)


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
