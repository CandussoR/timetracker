from typing import Literal

def format_time(time: float | int, max_unit: Literal["day", "hour"] = "hour") -> str:
    '''Returns a string in format (00:)00:00:00.'''
    if max_unit == "day":
        return "{:02d}:{:02d}:{:02d}:{:02d}".format(
            int((time // 86400)),
            int((time % 86400) // 3600),
            int((time % 3600) // 60),
            int(time % 60),
        )
    else:
        return "{:02d}:{:02d}:{:02d}".format(
            int(time // 3600), int((time % 3600) // 60), int(time % 60)
        )