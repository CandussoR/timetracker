from datetime import datetime
from typing import Literal

def datetime_to_string(period : Literal['day', 'week', 'month', 'year'], dt : datetime) -> str:
    time_format = {
        "year" : "%Y",
        "month" : "%Y-%m",
        "week" : "%Y-%m-%d",
        "day" : "%Y-%m-%d"
    }
    return dt.strftime(time_format[period])