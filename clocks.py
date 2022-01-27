import time

def timer(t):
    for i in reversed(range(0, t)):
        mins = t // 60
        seconds = t % 60
        time_format = '{:02d}:{:02d}'.format(mins, seconds)
        print(time_format, end="\r")
        time.sleep(1)
        t -= 1

def stopwatch(t=0):
    while True:
        try:
            mins = t // 60
            seconds = t % 60
            time_format = '{:02d}:{:02d}'.format(mins, seconds)
            print(time_format, end="\r")
            time.sleep(1)
            t += 1
        except KeyboardInterrupt:
            break
