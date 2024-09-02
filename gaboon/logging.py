import logging


class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.WARNING:
            return f"WARNING: {record.getMessage()}"
        elif record.levelno == logging.ERROR:
            return f"ERROR: {record.getMessage()}"
        return record.getMessage()


logger = logging.getLogger("titanoboa")
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


def set_log_level(quiet=False, debug=False):
    if debug:
        logger.setLevel(logging.DEBUG)
    elif not quiet:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)
