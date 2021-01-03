"""
..
    PYTEST_DONT_REWRITE

coveragectx.coverage.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dynamic Context Coverage Plugin
"""
import logging
import os
import tempfile

import coverage

log = logging.getLogger(__name__)


class DynamicContext(coverage.CoveragePlugin):  # pylint: disable=too-few-public-methods
    """
    Plugin implementation
    """

    def __init__(self, context_file_path=None):
        if context_file_path is None:
            handle, context_file_path = tempfile.mkstemp()
            os.close(handle)
        self.context_file_path = context_file_path

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
        try:
            with open(self.context_file_path) as rfh:
                context = rfh.read().strip() or None
        except FileNotFoundError:
            context = None
        return context


def coverage_init(reg, options):  # pylint: disable=unused-argument
    """
    Register our plugin with coveragepy
    """
    if "COVERAGE_DYNAMIC_CONTEXT_FILE_PATH" in os.environ:
        dynamic_context = DynamicContext(os.environ["COVERAGE_DYNAMIC_CONTEXT_FILE_PATH"])
    else:
        dynamic_context = DynamicContext()
        os.environ["COVERAGE_DYNAMIC_CONTEXT_FILE_PATH"] = dynamic_context.context_file_path
    reg.add_dynamic_context(dynamic_context)
