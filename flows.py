from conf import Config

class Flow:
    def __init__(self,
                 name: str | None = None,
                 timers: list[int] | None = None,
                 pauses: list[int] | None = None):
        
        self.name = self._input_flow_name() if name is None else name

        if timers is None or pauses is None :
            self.timers, self.pauses = self._timers_and_pauses(self._input_flow_times())
        else :
            self.timers, self.pauses = (timers, pauses)

    def _input_flow_times(self) -> list[list[str]]:
        ''' Asking user input for time and pauses. Function abstracted for separation purpose.
            Returns a list of a timer and a pause for each couple specified. '''
        timers_and_pauses = []

        while True:
            timer_pause = input("Enter a timer and a pause in the form timer/pause.\n> ")

            if not timer_pause :
                return timers_and_pauses

            timers_and_pauses.append(timer_pause.split('/'))

    def _input_flow_name(self) -> str :
        return input("Enter a name for the flow :\n> ")

    def _timers_and_pauses(self, timers_and_pauses : list[list[str]] ) -> tuple[list[int], list[int]] :
        ''' Returns a tuple containing one list for the timers, and another one for the pauses.'''
        timers = [int(item[0]) for item in timers_and_pauses]
        pauses = [int(item[1]) for item in timers_and_pauses]
        return timers, pauses

    def to_dict(self) -> dict[str, dict[str, list[int]]]:
        return {"timers" : self.timers, "pauses" : self.pauses}

    def add_to(self, conf: Config):
        conf.flows[self.name] = self.to_dict()
        conf.modify_conf()

if __name__ == '__main__':
    conf = Config("conf_copy.json")
    flow = Flow()
    flow.add_to(conf)