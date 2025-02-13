from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import BigInteger, Column, DateTime, Integer
from sqlalchemy.orm import Mapped

from .base import Base


class Points(Base):
    """Points system for tracking member achievements

    Attributes
    ----------
    member_id : Mapped[int]
        ID of the guild member
    guild_id : Mapped[int]
        ID of the guild
    points : Mapped[int]
        Current points balance
    last_weekly_check : Mapped[datetime]
        Last time weekly attendance was checked
    last_overtime_check : Mapped[datetime]
        Last time overtime points were awarded
    """

    __tablename__ = "points"

    member_id: Mapped[int] = Column(BigInteger, primary_key=True)
    guild_id: Mapped[int] = Column(BigInteger, nullable=False)
    points: Mapped[int] = Column(Integer, default=0)
    last_weekly_check: Mapped[datetime] = Column(DateTime, nullable=True)
    last_overtime_check: Mapped[datetime] = Column(DateTime, nullable=True)

    @classmethod
    def award_overtime_points(cls, hours_worked: float, required_hours: float) -> int:
        """Calculate points for overtime work

        Parameters
        ----------
        hours_worked : float
            Actual hours worked
        required_hours : float
            Required hours of work

        Returns
        -------
        int
            Points awarded
        """
        if hours_worked >= required_hours * 2:
            return 3
        return 0

    @classmethod
    def award_weekly_attendance(cls, attendance_days: int, required_days: int) -> int:
        """Calculate points for perfect weekly attendance

        Parameters
        ----------
        attendance_days : int
            Days attended in the week
        required_days : int
            Required working days

        Returns
        -------
        int
            Points awarded
        """
        if attendance_days >= required_days:
            return 5
        return 0