from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING
from bson import ObjectId

class MongoDB:
    def __init__(self, connection_string: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db: AsyncIOMotorDatabase = self.client.timeclock

    async def init_collections(self):
        # إنشاء الفهارس الضرورية
        await self.db.guilds.create_index([("id", ASCENDING)], unique=True)
        await self.db.members.create_index([("id", ASCENDING), ("guild_id", ASCENDING)], unique=True)
        await self.db.roles.create_index([("id", ASCENDING), ("guild_id", ASCENDING)], unique=True)

    async def get_guild(self, guild_id: int) -> Optional[dict]:
        return await self.db.guilds.find_one({"id": guild_id})

    async def ensure_guild(self, guild_id: int, **kwargs) -> dict:
        guild = await self.get_guild(guild_id)
        if not guild:
            guild = {
                "id": guild_id,
                "message_id": kwargs.get("message_id"),
                "channel_id": kwargs.get("channel_id"),
                "embed": kwargs.get("embed"),
            }
            await self.db.guilds.insert_one(guild)
        else:
            update = {}
            if "message_id" in kwargs:
                update["message_id"] = kwargs["message_id"]
            if "channel_id" in kwargs:
                update["channel_id"] = kwargs["channel_id"]
            if "embed" in kwargs:
                update["embed"] = kwargs["embed"]
            if update:
                await self.db.guilds.update_one({"id": guild_id}, {"$set": update})
                guild.update(update)
        return guild

    async def get_guild_roles(self, guild_id: int, **filters) -> List[dict]:
        query = {"guild_id": guild_id}
        if "is_mod" in filters:
            query["is_mod"] = filters["is_mod"]
        if "can_punch" in filters:
            query["can_punch"] = filters["can_punch"]
        return await self.db.roles.find(query).to_list(None)

    async def add_role(self, role_id: int, guild_id: int, **kwargs) -> dict:
        role = await self.db.roles.find_one({"id": role_id})
        if not role:
            role = {
                "id": role_id,
                "guild_id": guild_id,
                "can_punch": kwargs.get("can_punch"),
                "is_mod": kwargs.get("is_mod"),
            }
            await self.db.roles.insert_one(role)
        else:
            update = {}
            if "can_punch" in kwargs:
                update["can_punch"] = kwargs["can_punch"]
            if "is_mod" in kwargs:
                update["is_mod"] = kwargs["is_mod"]
            if update:
                await self.db.roles.update_one({"id": role_id}, {"$set": update})
                role.update(update)
        return role

    async def delete_role(self, role_id: int) -> None:
        await self.db.roles.delete_one({"id": role_id})

    async def ensure_member(self, guild_id: int, member_id: int) -> dict:
        member = await self.db.members.find_one({"id": member_id, "guild_id": guild_id})
        if not member:
            member = {
                "id": member_id,
                "guild_id": guild_id,
                "on_duty": False,
                "times": []
            }
            await self.db.members.insert_one(member)
        return member

    async def add_punch(self, guild_id: int, member_id: int, timestamp: float) -> dict:
        member = await self.ensure_member(guild_id, member_id)
        
        if not member["times"] or not member["on_duty"]:
            member["on_duty"] = True
            time_entry = {"punch_in": timestamp}
            await self.db.members.update_one(
                {"id": member_id, "guild_id": guild_id},
                {
                    "$set": {"on_duty": True},
                    "$push": {"times": time_entry}
                }
            )
        else:
            member["on_duty"] = False
            await self.db.members.update_one(
                {"id": member_id, "guild_id": guild_id},
                {
                    "$set": {
                        "on_duty": False,
                        "times.$[last].punch_out": timestamp
                    }
                },
                array_filters=[{"last": {"$eq": member["times"][-1]}}]
            )
        
        return member

    async def get_members(self, guild_id: int, member_id: Optional[int] = None) -> List[dict]:
        query = {"guild_id": guild_id}
        if member_id:
            query["id"] = member_id
            return await self.db.members.find_one(query)
        return await self.db.members.find(query).to_list(None)