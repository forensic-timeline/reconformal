import warnings
warnings.warn(
    "The package 'reconsadfc' has been renamed to 'reconformal'. "
    "Please update your dependency: pip install reconformal. "
    "This stub will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)
from reconformal import *  # noqa: F401, F403
from reconformal import __all__  # noqa: F401
