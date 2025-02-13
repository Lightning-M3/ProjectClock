from __future__ import annotations

import json
from typing import Union

import disnake
from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .role import Role


class Guild(Base):
    __tablename__ = "guild"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    message_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, default=None)
    channel_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, default=None)
    _embed: Mapped[Union[str, None]] = mapped_column(Text, nullable=True, default=None)
    roles: Mapped[list[Role]] = relationship("Role", lazy="subquery")

    @property
    def embed(self) -> Union[disnake.Embed, None]:
        if self._embed is None:
            return

        embed_dict = json.loads(self._embed)
        return disnake.Embed.from_dict(embed_dict)

    @embed.setter
    def embed(self, embed: disnake.Embed) -> None:
        if embed is None:
            self._embed = None
            return

        embed_dict = embed.to_dict()
        self._embed = json.dumps(embed_dict)
