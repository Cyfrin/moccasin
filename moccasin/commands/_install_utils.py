from argparse import Namespace

from moccasin.commands.install import mox_install


def check_mox_install(args: Namespace) -> None:
    """
    Check if mox install needs to be run.

    :param args: Command line arguments
    :type args: Namespace
    """
    if hasattr(args, "no_install") and not args.no_install:
        init_quiet: bool | None = args.quiet if hasattr(args, "quiet") else None
        # Force/add quiet arg for install
        args.quiet = True
        mox_install(args)
        # Remove quiet arg if it was set before install
        # @dev args namespace are mutable
        if init_quiet is not None:
            args.quiet = init_quiet
        else:
            del args.quiet
