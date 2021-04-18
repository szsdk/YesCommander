import logging
import sys

logger = logging.getLogger("YesCommander")
if "--debug" not in sys.argv:
    logger.setLevel(logging.WARNING)
else:
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("yc.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

from ._core import *
