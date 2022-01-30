import logging
from copy import deepcopy

from motor.motor_asyncio import AsyncIOMotorClient

from src.util.logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)

USER_OBJ = {
    "id": None,
    "balance": 0,
    "inventory": [],
    "last": {
        "hourly": 0,
        "daily": 0,
        "monthly": 0
    }
}


def copy_user_obj() -> dict:
    """
    Get a fresh new blank user object.

    :return: A dictionary.
    """
    return deepcopy(USER_OBJ)


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
        self.db_col = self.db["members"]

    async def get_member(self, member_id: int) -> dict:
        """
        Get a member's object.

        :param member_id: The ID of the member.
        :return: The object.
        """
        doc = await self.db_col.find_one({"id": member_id})
        if doc is None:
            doc = copy_user_obj()
            doc["id"] = member_id
            await self.db_col.insert_one(doc)
        return doc

    async def get_balance(self, member_id: int) -> int:
        """
        Get a member's balance.

        :param member_id: The ID of the member.
        :return: An int.
        """
        obj = await self.get_member(member_id=member_id)
        return obj["balance"]

