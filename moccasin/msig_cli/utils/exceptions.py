################################################################
#                          EXCEPTIONS                          #
################################################################
class MsigCliError(Exception):
    """Base exception for MsigCli errors."""


class MsigCliUserAbort(MsigCliError):
    """Raised when the user aborts an operation."""
