from typing import Literal

def format_time(time: float | int, max_unit: Literal["day", "hour"] = "hour", split: bool = False) -> str | list[str]:
    '''Returns a string in format (00:)00:00:00, unless split is True (generally for the front).'''
    result = []
    if max_unit == "day":
        result.append(int(time // 86400))
    result.extend([int((time % 86400) // 3600), int((time % 3600) // 60), int(time % 60)])
    assert len(result) >= 3
    result = list(map(lambda x : f"{x:02d}", result))
    return result if not split else ":".join(result)