import logging

from motor.motor_asyncio import AsyncIOMotorClient

from .logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)


class DBClient:
    def __init__(self, uri: str, db_name: str):
        """
        Make a database client.

        :param uri: The URI of the MongoDB database.
        :param db_name: The name of the database.
        """
        logger.debug(f"Connecting to database")
        self.client = AsyncIOMotorClient(uri)
        self.db_name = db_name
        self.db = self.client[self.db_name]
