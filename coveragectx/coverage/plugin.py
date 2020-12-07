"""
..
    PYTEST_DONT_REWRITE

coveragectx.coverage.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dynamic Context Coverage Plugin
"""
import atexit
import logging
import os
import threading
import time

import coverage
import zmq


log = logging.getLogger(__name__)


class DynamicContext(coverage.CoveragePlugin):  # pylint: disable=too-few-public-methods
    """
    Plugin implementation
    """

    def __init__(self):
        self._push_address = None
        self._running = threading.Event()
        self._context = os.environ.get("COVERAGE_DYNAMIC_CONTEXT")
        self._start()
        atexit.register(self._stop)

    def dynamic_context(self, frame):  # pylint: disable=unused-argument
        """
        Get the dynamically computed context label for `frame`.
        Plug-in type: dynamic context.
        This method is invoked for each frame when outside of a dynamic
        context, to see if a new dynamic context should be started.  If it
        returns a string, a new context label is set for this and deeper
        frames.  The dynamic context ends when this frame returns.
        Returns a string to start a new dynamic context, or None if no new
        context should be started.
        """
        return self._context or os.environ.get("COVERAGE_DYNAMIC_CONTEXT")

    def _process_thread(self):
        """
        This thread is responsible for getting the next dynamic context
        """
        self._running.set()
        if self._push_address is None:
            while self._running.is_set():
                self._push_address = os.environ.get("COVERAGE_DYNAMIC_CONTEXT_ADDRESS")
                if self._push_address is not None:
                    break
                time.sleep(0.125)
        context = zmq.Context()
        puller = context.socket(zmq.SUB)  # pylint: disable=not-callable,no-member
        puller.connect(self._push_address)
        log.debug("Connected to: %s", self._push_address)
        try:
            while self._running.is_set():
                context = puller.recv_string()
                log.debug("New Context: %s", context)
                if context == "[{STOP}]":
                    break
                if context == "[{NONE}]":
                    context = None
                self._context = context
        finally:
            puller.close(0)
            context.term()
            self._running.clear()

    def _start(self):
        """
        Start the ZMQ puller
        """
        if self._running.is_set():
            return

        process_thread = threading.Thread(target=self._process_thread)
        process_thread.daemon = True
        process_thread.start()

    def _stop(self):
        """
        Stop the ZMQ puller
        """
        atexit.unregister(self._stop)
        if self._running.is_set():
            self._running.clear()


def coverage_init(reg, options):  # pylint: disable=unused-argument
    """
    Register our plugin with coveragepy
    """
    reg.add_dynamic_context(DynamicContext())
