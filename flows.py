class Flow:
    def __init__(self, name: str, timers: list[int] | None = None, pauses: list[int] | None = None):
        self.name = name
        self.timers, self.pauses = self._timers_and_pauses(self._get_flow_input)

    def _get_flow_input(self) -> list[list[str]]:
        ''' Asking user input for time and pauses. Function abstracted for separation purpose.
            Returns a list of a timer and a pause for each couple specified. '''
        timers_and_pauses = []

        while True: 
            timer_pause = input("Enter a timer and a pause in the form timer/pause.\n> ")

            if not timer_pause :
                return timers_and_pauses

            timers_and_pauses.append(timer_pause.split('/'))

    def _timers_and_pauses(self, func ) -> tuple[list[int], list[int]] :
        ''' Returns a tuple containing one list for the timers, and another one for the pauses.'''
        timers_pauses = func()
        timers = [int(item[0]) for item in timers_pauses] 
        pauses = [int(item[1]) for item in timers_pauses]
        return timers, pauses

    def add_flow(self):
        pass

    def delete_flow(self):
        pass

    def execute_flow(self):
        pass

if __name__ == '__main__':
    name = input("givitaname > ")
    flow = Flow(name)
    print(1)