import logging


class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.WARNING:
            return f"WARNING: {record.getMessage()}"
        elif record.levelno == logging.ERROR:
            return f"ERROR: {record.getMessage()}"
        return record.getMessage()


logger = logging.getLogger("gaboon")
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


def set_log_level(quiet=False, verbose=0):
    if quiet:
        logger.setLevel(logging.ERROR)
    elif verbose == 0:
        logger.setLevel(logging.INFO)
    elif verbose == 1:
        logger.setLevel(logging.DEBUG)
    elif verbose >= 2:
        logger.setLevel(logging.NOTSET)
