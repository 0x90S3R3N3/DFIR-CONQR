"""
Importing this package registers every built-in collector via the
@register decorator. To add a new collector: drop a new module in
this folder, subclass BaseCollector, decorate with @register, and
import it below.
"""

from . import (
    autoruns_persistence,  # noqa: F401
    browser_artifacts,  # noqa: F401
    filesystem_artifacts,  # noqa: F401
    logs,  # noqa: F401
    network,  # noqa: F401
    processes,  # noqa: F401
    system_info,  # noqa: F401
    users_sessions,  # noqa: F401
)
