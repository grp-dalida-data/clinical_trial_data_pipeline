# logger.py
import logging
import sys

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(stream_handler)

    return logger