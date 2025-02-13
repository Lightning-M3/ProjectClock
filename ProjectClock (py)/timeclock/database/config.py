from typing import Dict, Optional
from datetime import time

class GuildConfig:
    """Handles guild-specific configurations including work hours"""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.work_hours: Dict[int, Optional[tuple[time, time]]] = {}
        # Key is day of week (0-6, Monday is 0), value is tuple of (start_time, end_time)
        # If a day's value is None, it means no work hours are set for that day

    def set_work_hours(self, day: int, start: Optional[time], end: Optional[time]) -> bool:
        """Set work hours for a specific day of the week
        
        Args:
            day: Day of week (0-6, Monday is 0)
            start: Start time of work day
            end: End time of work day
            
        Returns:
            bool: True if successful, False otherwise
        """
        if day not in range(7):
            return False
            
        if start is None or end is None:
            self.work_hours[day] = None
        else:
            self.work_hours[day] = (start, end)
        return True

    def get_work_hours(self, day: int) -> Optional[tuple[time, time]]:
        """Get work hours for a specific day
        
        Args:
            day: Day of week (0-6, Monday is 0)
            
        Returns:
            Optional[tuple[time, time]]: Tuple of (start_time, end_time) if set, None otherwise
        """
        return self.work_hours.get(day)

    def clear_work_hours(self, day: Optional[int] = None) -> bool:
        """Clear work hours for a specific day or all days
        
        Args:
            day: Day to clear hours for, or None to clear all days
            
        Returns:
            bool: True if successful, False otherwise
        """
        if day is None:
            self.work_hours.clear()
            return True
            
        if day not in range(7):
            return False
            
        self.work_hours.pop(day, None)
        return True