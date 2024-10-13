from dataclasses import dataclass, fields
from datetime import datetime, timedelta
import time


def timer(time_beginning : datetime, t_in_seconds: int):
    end_time = time_beginning + timedelta(seconds=t_in_seconds)

    while datetime.now() < end_time:
        try:
            count = end_time - datetime.now()
            mins, seconds = divmod(count.seconds, 60)
            time_format = f'{mins:02d}:{seconds:02d}'
            print('\t' + time_format, end="\r")
            time.sleep(1)
        except KeyboardInterrupt:
            break;


def stopwatch(time_beginning : datetime, t=0):
    while True:
        try:
            count = datetime.now() - time_beginning
            mins, seconds = divmod(count.seconds, 60)
            time_format = f'{mins:02d}:{seconds:02d}'
            print('\t' + time_format, end="\r")
            time.sleep(1)
        except KeyboardInterrupt:
            break
