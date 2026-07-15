"""Dynamic version: YYYY.M.D based on the current date."""

from datetime import date

_today = date.today()
__version__ = f"{_today.year}.{_today.month}.{_today.day}"
