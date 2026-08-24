# -*- coding: utf-8 -*-
"""Import the merge rules from swbilingual.py on any operating system.

swbilingual.py binds the Windows resource API at import time, which is correct
for the tool but stops the rules from being read anywhere else. This module
supplies inert stand-ins for the two missing ctypes attributes when the host is
not Windows, so that `preview` and the test suite can exercise the real rules
rather than a copy of them. Nothing here is used on Windows, and no function
that touches the API is callable through this path.
"""
import ctypes
import os
import sys


class _InertFunction(object):
    """Accepts the restype/argtypes assignments made at import time."""

    restype = None
    argtypes = None

    def __call__(self, *args, **kwargs):
        raise RuntimeError('The Windows resource API is not available on this system.')


class _InertLibrary(object):
    def __getattr__(self, name):
        fn = _InertFunction()
        setattr(self, name, fn)
        return fn


def import_rules():
    """Return the swbilingual module with its merge rules ready to use."""
    if os.name != 'nt':
        if not hasattr(ctypes, 'WinDLL'):
            ctypes.WinDLL = lambda *a, **kw: _InertLibrary()
        if not hasattr(ctypes, 'WINFUNCTYPE'):
            ctypes.WINFUNCTYPE = ctypes.CFUNCTYPE
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import swbilingual
    return swbilingual
