import logging

def getlogger(filename: str = ""):

    logger = logging.getLogger("xssunrin")

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s - %(name)s - %(module)s:%(lineno)s - %(levelname)s] %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    if filename:
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

logger = getlogger()