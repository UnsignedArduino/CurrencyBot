import logging
from os import getenv

from .logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)


class NoEnvironmentVariableFound(Exception):
    """
    No environment variable was found!
    """


def load_env_var(name: str) -> str:
    """
    Load an environment variable from the

    :param name: The name of the environment variable.
    :return: The value as a string.
    :raise: NoEnvironmentVariableFound if no environment variable was found.
    """
    logger.debug(f"Loading environment variable \"{name}\"")
    var = getenv(name)
    if var is None:
        logger.error(f"Unable to find environment variable \"{name}\"")
        raise NoEnvironmentVariableFound(f"Could not find environment "
                                         f"variable \"{name}\"!")
    else:
        logger.debug(f"Found environment variable \"{name}\"")
        return var
