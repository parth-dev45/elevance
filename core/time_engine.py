"""
Time Engine for Simulated Time Travel and Business Hours Calculations.
Accurately computes SLA excluding weekends and configured holidays,
supports virtual clock jumping for rigorous evaluation testing.
"""
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple
from core.config import config

class TimeEngine:
    def __init__(self):
        self._simulated_time: Optional[datetime] = None

    def now(self) -> datetime:
        """Returns the current simulated time if active, else real system time."""
        if self._simulated_time is not None:
            return self._simulated_time
        return datetime.now()

    def set_time(self, dt: datetime):
        """Sets the virtual simulated clock to a specific datetime."""
        self._simulated_time = dt

    def advance_time(self, seconds: float = 0, minutes: float = 0, hours: float = 0, days: float = 0):
        """Advances the virtual clock forward by a specified delta."""
        base = self.now()
        self._simulated_time = base + timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        return self._simulated_time

    def reset_to_real_time(self):
        """Clears simulated time to resume real system clock."""
        self._simulated_time = None

    def is_holiday(self, d: date) -> bool:
        """Checks if a given date is in configured holidays list."""
        date_str = d.strftime("%Y-%m-%d")
        return date_str in config.holidays

    def is_business_day(self, d: date) -> bool:
        """Checks if a day is a working day (Mon-Fri and not holiday)."""
        if d.weekday() not in config.business_days:
            return False
        if self.is_holiday(d):
            return False
        return True

    def is_within_business_hours(self, dt: Optional[datetime] = None) -> bool:
        """Checks if the given datetime (or now) is within official business hours."""
        t = dt or self.now()
        if not self.is_business_day(t.date()):
            return False
        start_time = time(config.business_start_hour, config.business_start_minute)
        end_time = time(config.business_end_hour, config.business_end_minute)
        return start_time <= t.time() < end_time

    def is_within_maintenance_window(self, dt: Optional[datetime] = None) -> bool:
        """Checks if the given datetime (or now) falls within the maintenance window."""
        t = dt or self.now()
        cur_hour = t.hour
        start = config.maintenance_window_start_hour
        end = config.maintenance_window_end_hour
        if start < end:
            return start <= cur_hour < end
        else: # Overrides midnight
            return cur_hour >= start or cur_hour < end

    def get_next_business_day_start(self, dt: Optional[datetime] = None) -> datetime:
        """Finds the 09:00 AM timestamp of the very next business day."""
        t = dt or self.now()
        candidate = t.date()
        # If today is a business day and we are before start of business, today's start is next
        start_time = time(config.business_start_hour, config.business_start_minute)
        if self.is_business_day(candidate) and t.time() < start_time:
            return datetime.combine(candidate, start_time)
        
        # Advance day by day until finding next working day
        candidate = candidate + timedelta(days=1)
        while not self.is_business_day(candidate):
            candidate = candidate + timedelta(days=1)
        return datetime.combine(candidate, start_time)

    def calculate_business_seconds_between(self, start_dt: datetime, end_dt: datetime) -> float:
        """
        Calculates elapsed business seconds between two datetimes,
        excluding weekends, holidays, and outside-business hours.
        """
        if end_dt <= start_dt:
            return 0.0

        total_business_seconds = 0.0
        current_cursor = start_dt
        step = timedelta(minutes=5)

        # Micro-stepping for exact calculation
        while current_cursor < end_dt:
            next_cursor = min(current_cursor + step, end_dt)
            midpoint = current_cursor + (next_cursor - current_cursor) / 2
            if self.is_within_business_hours(midpoint):
                total_business_seconds += (next_cursor - current_cursor).total_seconds()
            current_cursor = next_cursor

        return total_business_seconds

    def add_business_hours(self, start_dt: datetime, business_hours: float) -> datetime:
        """Computes the future deadline datetime given allowed business hours."""
        remaining_seconds = business_hours * 3600.0
        current_cursor = start_dt
        step = timedelta(minutes=5)

        # Advance step by step counting only business seconds
        while remaining_seconds > 0:
            next_cursor = current_cursor + step
            midpoint = current_cursor + (step / 2)
            if self.is_within_business_hours(midpoint):
                consumed = min(step.total_seconds(), remaining_seconds)
                remaining_seconds -= consumed
                if remaining_seconds <= 0:
                    current_cursor += timedelta(seconds=consumed)
                    break
            current_cursor = next_cursor
        return current_cursor

time_engine = TimeEngine()
