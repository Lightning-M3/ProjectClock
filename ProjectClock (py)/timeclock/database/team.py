from datetime import datetime
from typing import List, Optional

class Team:
    """Represents a team/department in the organization"""

    def __init__(self, id: int, name: str, guild_id: int, leader_id: Optional[int] = None):
        self.id = id
        self.name = name
        self.guild_id = guild_id
        self.leader_id = leader_id
        self.members: List[int] = []
        self.created_at = datetime.utcnow()

    def add_member(self, member_id: int) -> bool:
        """Add a member to the team"""
        if member_id not in self.members:
            self.members.append(member_id)
            return True
        return False

    def remove_member(self, member_id: int) -> bool:
        """Remove a member from the team"""
        if member_id in self.members:
            self.members.remove(member_id)
            return True
        return False

    def set_leader(self, leader_id: int) -> None:
        """Set the team leader"""
        self.leader_id = leader_id

    def get_members_count(self) -> int:
        """Get the number of members in the team"""
        return len(self.members)

    def to_dict(self) -> dict:
        """Convert team data to dictionary format"""
        return {
            'id': self.id,
            'name': self.name,
            'guild_id': self.guild_id,
            'leader_id': self.leader_id,
            'members': self.members,
            'created_at': self.created_at.isoformat()
        }