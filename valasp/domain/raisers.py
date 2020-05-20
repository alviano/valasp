# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

"""Any warning and error specific to ValAsp should be defined here.

The policy of the framework is to rely as much as possible on the usual error classes, like TypeError and ValueError.
"""


class ValAspWarning(UserWarning):
    """Generic warning from the framework."""
    pass
