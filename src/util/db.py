import logging
from copy import deepcopy

import arrow
from arrow.arrow import Arrow
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

    async def set_member(self, member_id: int, doc: dict):
        """
        Set a member's object.

        :param member_id: The ID of the member.
        :param doc: The member's new doc.
        """
        test = await self.db_col.find_one({"id": member_id})
        if test is None:
            await self.db_col.insert_one(doc)
        else:
            await self.db_col.replace_one({"id": member_id}, doc)

    async def get_balance(self, member_id: int) -> int:
        """
        Get a member's balance.

        :param member_id: The ID of the member.
        :return: An int.
        """
        obj = await self.get_member(member_id=member_id)
        return obj["balance"]

    async def set_balance(self, member_id: int, balance: int):
        """
        Set a member's balance.

        :param member_id: The ID of the member.
        :param balance: The balance to set to.
        """
        obj = await self.get_member(member_id=member_id)
        obj["balance"] = balance
        await self.set_member(member_id=member_id, doc=obj)

    async def change_balance(self, member_id: int, change: int):
        """
        Change a member's balance.

        :param member_id: The ID of the member.
        :param change: How much to change the balance by.
        """
        obj = await self.get_member(member_id=member_id)
        obj["balance"] += change
        await self.set_member(member_id=member_id, doc=obj)

    async def get_last_claim(self, member_id: int,
                             claim_type: str) -> Arrow:
        """
        Get the last claim time for a member.

        :param member_id: The ID of the member.
        :param claim_type: The claim type. Must be "hourly", "daily", or
         "monthly"
        :return: An Arrow date.
        """
        obj = await self.get_member(member_id=member_id)
        return arrow.get(obj["last"][claim_type])

    async def set_last_claim(self, member_id: int,
                             claim_type: str,
                             last_claim_time: int):
        """
        Set the last claim time for a member.

        :param member_id: The ID of the member.
        :param claim_type: The claim type. Must be "hourly", "daily", or
         "monthly"
        :param last_claim_time: Set the last claim time to this.
        :return: An Arrow date.
        """
        obj = await self.get_member(member_id=member_id)
        obj["last"][claim_type] = last_claim_time
        await self.set_member(member_id=member_id, doc=obj)

