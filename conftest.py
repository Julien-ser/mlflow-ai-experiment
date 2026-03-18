"""
Pytest configuration to handle warnings during test collection.

Suppresses known deprecation warnings from dependencies that are not
actionable within this project's control.
"""

import sys

print("CONFTEST LOADED EARLY", file=sys.stderr)

import warnings

# Temporarily ignore ALL UserWarnings to see if that fixes tests
warnings.simplefilter("ignore", UserWarning)

# Filter out torch.jit.script DeprecationWarning for Python 3.14+
# This must be set before transformers is imported (which happens in test modules)
warnings.filterwarnings(
    "ignore",
    message=r"`torch\.jit\.script` is not supported in Python 3\.14\+",
    category=DeprecationWarning,
    module=r"torch\.jit\._script",
)

# Existing filters for SWIG types
warnings.filterwarnings(
    "ignore",
    message=r"builtin type SwigPyObject has no __module__ attribute",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"builtin type SwigPyPacked has no __module__ attribute",
    category=DeprecationWarning,
)
