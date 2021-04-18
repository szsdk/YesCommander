import logging

logger = logging.getLogger("YesCommander")
logger.setLevel(logging.WARNING)

# ====== For debugging
# logger.setLevel(logging.DEBUG)
# fh = logging.FileHandler('yc.log')
# fh.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# logger.addHandler(fh)
# ====== For debugging

from ._core import *
