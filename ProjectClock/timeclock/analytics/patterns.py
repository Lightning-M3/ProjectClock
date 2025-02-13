from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from dataclasses import dataclass

from timeclock.database import Member, Time

@dataclass
class AttendancePattern:
    """Represents a detected attendance pattern for a member"""
    average_start_time: datetime
    average_end_time: datetime
    average_duration: timedelta
    consistency_score: float  # 0-1 score indicating pattern consistency
    break_patterns: List[tuple[datetime, datetime]]  # Common break times
    days_active: List[int]  # 0-6 representing days of week

class PatternAnalyzer:
    """Analyzes member attendance patterns to detect regular schedules and breaks"""

    def __init__(self, analysis_period_days: int = 30):
        self.analysis_period = analysis_period_days

    def analyze_member(self, member: Member) -> Optional[AttendancePattern]:
        """Analyze a member's attendance history to detect patterns"""
        recent_times = self._get_recent_times(member)
        if not recent_times:
            return None

        start_times = []
        end_times = []
        durations = []
        active_days = set()

        for time in recent_times:
            if not time.punch_out:
                continue

            start = datetime.fromtimestamp(time.punch_in, tz=timezone.utc)
            end = datetime.fromtimestamp(time.punch_out, tz=timezone.utc)

            start_times.append(start)
            end_times.append(end)
            durations.append(end - start)
            active_days.add(start.weekday())

        if not start_times:
            return None

        avg_start = self._average_time(start_times)
        avg_end = self._average_time(end_times)
        avg_duration = sum(durations, timedelta()) / len(durations)
        consistency = self._calculate_consistency(start_times, end_times)
        breaks = self._detect_break_patterns(recent_times)

        return AttendancePattern(
            average_start_time=avg_start,
            average_end_time=avg_end,
            average_duration=avg_duration,
            consistency_score=consistency,
            break_patterns=breaks,
            days_active=sorted(list(active_days))
        )

    def _get_recent_times(self, member: Member) -> List[Time]:
        """Get member's attendance records within analysis period"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.analysis_period)
        return [
            time for time in member.times
            if datetime.fromtimestamp(time.punch_in, tz=timezone.utc) >= cutoff
        ]

    def _average_time(self, times: List[datetime]) -> datetime:
        """Calculate the average time of day from a list of datetimes"""
        if not times:
            return datetime.now(timezone.utc)

        total_seconds = sum(
            t.hour * 3600 + t.minute * 60 + t.second
            for t in times
        )
        avg_seconds = total_seconds / len(times)
        
        base = times[0].replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return base + timedelta(seconds=avg_seconds)

    def _calculate_consistency(self, starts: List[datetime], ends: List[datetime]) -> float:
        """Calculate consistency score based on start/end time variations"""
        if not starts or not ends:
            return 0.0

        start_variance = self._time_variance(starts)
        end_variance = self._time_variance(ends)

        # Convert variance to a 0-1 score where lower variance = higher consistency
        max_variance = 3600 * 4  # 4 hours variance = 0 consistency
        start_score = max(0, 1 - (start_variance / max_variance))
        end_score = max(0, 1 - (end_variance / max_variance))

        return (start_score + end_score) / 2

    def _time_variance(self, times: List[datetime]) -> float:
        """Calculate variance in seconds for a list of times.
        
        This method computes the statistical variance of time points within a day,
        accounting for the circular nature of time (e.g., 23:59 is close to 00:01).
        It also handles outliers and provides more accurate variance calculation.
        
        Args:
            times: List of datetime objects to analyze
            
        Returns:
            float: Variance in seconds, where lower values indicate more consistent timing
        """
        if not times:
            return 0.0

        # Convert times to seconds since midnight
        seconds = [t.hour * 3600 + t.minute * 60 + t.second for t in times]
        
        # Initial mean calculation
        mean = sum(seconds) / len(seconds)
        
        # First pass: Handle time wrapping and identify potential outliers
        adjusted_seconds = []
        for s in seconds:
            # If the time is more than 12 hours away from mean, wrap it
            if abs(s - mean) > 43200:  # 12 hours in seconds
                if s > mean:
                    adjusted_seconds.append(s - 86400)  # Subtract 24 hours
                else:
                    adjusted_seconds.append(s + 86400)  # Add 24 hours
            else:
                adjusted_seconds.append(s)
        
        # Calculate quartiles for outlier detection
        sorted_times = sorted(adjusted_seconds)
        q1 = sorted_times[len(sorted_times) // 4]
        q3 = sorted_times[3 * len(sorted_times) // 4]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Second pass: Remove outliers and calculate final variance
        filtered_seconds = [s for s in adjusted_seconds if lower_bound <= s <= upper_bound]
        
        if not filtered_seconds:
            return sum((s - mean) ** 2 for s in adjusted_seconds) / len(adjusted_seconds)
        
        # Calculate final mean and variance without outliers
        final_mean = sum(filtered_seconds) / len(filtered_seconds)
        variance = sum((s - final_mean) ** 2 for s in filtered_seconds) / len(filtered_seconds)
        
        # Normalize variance to be between 0 and 1
        max_expected_variance = (12 * 3600) ** 2  # 12 hours squared
        return min(variance / max_expected_variance, 1.0)

    def _detect_break_patterns(self, times: List[Time]) -> List[tuple[datetime, datetime]]:
        """Detect common break patterns in attendance records.
        
        This method analyzes consecutive attendance records to identify regular break patterns.
        It clusters breaks by their start times and identifies recurring patterns that occur
        frequently enough to be considered regular breaks.
        
        Args:
            times: List of attendance records to analyze
            
        Returns:
            List of (start, end) datetime tuples representing common break patterns
            
        Raises:
            ValueError: If timestamp conversion fails
            OSError: If system time operations fail
        """
        if not times:
            return []

        try:
            breaks = []
            break_clusters: Dict[str, List[tuple[datetime, datetime]]] = {}
            workday_breaks: Dict[int, List[tuple[datetime, datetime]]] = {}  # Group by weekday

            for i in range(len(times) - 1):
                current = times[i]
                next_time = times[i + 1]
                
                if not current.punch_out or not next_time.punch_in:
                    continue

                try:
                    break_start = datetime.fromtimestamp(current.punch_out, tz=timezone.utc)
                    break_end = datetime.fromtimestamp(next_time.punch_in, tz=timezone.utc)
                    
                    # Enhanced validation
                    if break_end <= break_start or (break_end - break_start).total_seconds() > 7200:  # Max 2 hours
                        continue
                    
                    # Analyze breaks between 10 minutes and 2 hours
                    duration = (break_end - break_start).total_seconds() / 60
                    if 10 <= duration <= 120:
                        # Cluster by weekday for more accurate patterns
                        weekday = break_start.weekday()
                        if weekday not in workday_breaks:
                            workday_breaks[weekday] = []
                        workday_breaks[weekday].append((break_start, break_end))
                        
                        # Also cluster by time slots for general patterns
                        # Use 30-minute intervals for better granularity
                        key = f"{break_start.hour:02d}:{break_start.minute // 30:02d}"
                        if key not in break_clusters:
                            break_clusters[key] = []
                        break_clusters[key].append((break_start, break_end))
                except (ValueError, OSError) as e:
                    continue
            
            if not break_clusters and not workday_breaks:
                return []

            # Analyze patterns with dynamic thresholds
            min_pattern_occurrences = max(2, min(3, len(times) // 15))  # More flexible threshold
            
            # Process weekday-specific patterns first
            for weekday_breaks in workday_breaks.values():
                if len(weekday_breaks) >= min_pattern_occurrences:
                    try:
                        # Calculate average break times with outlier filtering
                        start_times = [start for start, _ in breaks_in_slot]
                        end_times = [end for _, end in breaks_in_slot]
                        
                        if start_times and end_times:
                            avg_start = self._average_time(start_times)
                            avg_end = self._average_time(end_times)
                            breaks.append((avg_start, avg_end))
                    except Exception as e:
                        # Skip this cluster if averaging fails
                        continue
            
            return sorted(breaks, key=lambda x: x[0])
        except Exception as e:
            # Return empty list for any unexpected errors
            return []

    def _cluster_breaks(self, breaks: List[tuple[datetime, datetime]]) -> List[tuple[datetime, datetime]]:
        """Group similar breaks together and return representative patterns.
        
        This method clusters break patterns based on their start times and identifies
        recurring patterns that might indicate regular break schedules.
        
        Args:
            breaks: List of (start, end) datetime tuples representing breaks
            
        Returns:
            List of (start, end) datetime tuples representing common break patterns
        """
        try:
            if not breaks:
                return []

            # Enhanced clustering based on hour and 15-minute intervals
            clusters: Dict[str, List[tuple[datetime, datetime]]] = {}
            for break_start, break_end in breaks:
                # Create key based on hour and 15-minute interval
                key = f"{break_start.hour:02d}:{break_start.minute // 15}"
                if key not in clusters:
                    clusters[key] = []
                clusters[key].append((break_start, break_end))

            # Return average break time for significant clusters
            patterns = []
            min_occurrences = max(3, len(breaks) // 10)  # Dynamic threshold
            
            for breaks_in_slot in clusters.values():
                if len(breaks_in_slot) >= min_occurrences:
                    try:
                        avg_start = self._average_time([start for start, _ in breaks_in_slot])
                        avg_end = self._average_time([end for _, end in breaks_in_slot])
                        patterns.append((avg_start, avg_end))
                    except Exception:
                        continue  # Skip if averaging fails for this cluster

            return sorted(patterns, key=lambda x: x[0])
        except Exception:
            return []  # Return empty list if clustering fails