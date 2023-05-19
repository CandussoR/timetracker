from conf import load_conf, write_conf

class Flow:
    def __init__(self, name: str | None = None, timers: list[int] | None = None, pauses: list[int] | None = None):
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

    def add_flow(self, conf: dict):
        conf['flows'] = {self.name : {"timers" : self.timers, "pauses" : self.pauses}}
        write_conf(conf, "conf.json")

    def delete_flow(self, conf : str, flow_name : str):
        flows = load_conf(conf)['flows']

        if flow_name in flows:
            flows.pop(flow_name)

        if flow_name not in flows :
            print("The flow doesn't exist.")

    def modify_flow(self):
        pass

    def execute_flow(self):
        pass

if __name__ == '__main__':
    # flow = Flow().add_flow(load_conf("conf.json"))