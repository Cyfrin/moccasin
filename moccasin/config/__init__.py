"""
@dev Retrocompatibility layer for moccasin.config imports
"""

from .config import (
    Config,
    Network,
    get_config,
    initialize_global_config,
    get_or_initialize_config,
    get_active_network,
    _set_global_config,
)

__all__ = [
    "Config",
    "Network",
    "get_config",
    "initialize_global_config",
    "get_or_initialize_config",
    "get_active_network",
    "_set_global_config",
]
