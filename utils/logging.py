import logging
from logging.handlers import RotatingFileHandler


def setup_logging(root, debug=False):
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("netdirector")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    handler = RotatingFileHandler(logs / "netdirector.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s", "%H:%M:%S"))
    logger.addHandler(handler)
    return logger
