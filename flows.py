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

class FlowCollection :

    def __init__(self,
               collection : dict[str, dict[str, list[int]]]):
        
        for name, info in collection.items():
            self.__setattr__(name, 
                             Flow(name, 
                                  info["timers"], 
                                  info["pauses"]))


    def add(self) :

        flow = Flow()

        self.__setattr__(flow.name, flow)


    def delete(self, name : str):
        try:
            self.__delattr__(name)
        except AttributeError as e:
            raise e
        except Exception:
            raise Exception
    

    def to_dict(self) -> dict[str, dict[str, list[int]]]:
        collection_dict = {}

        for name, info in self.__dict__.items():
            collection_dict[name] = { "timers" : info.timers, "pauses": info.pauses}
        
        return collection_dict
    

    def write(self, conf: Config) :

        conf.flows = self.to_dict()

        conf.modify()

if __name__ == '__main__':
    conf = Config()
    collection = FlowCollection(conf.flows)
    collection.add()
    collection.write(conf)
    try:
        collection.delete("Acsendant")
    except AttributeError as e:
        collection.delete("Ascendant")
        collection.write(conf)
    except Exception:
        print(Exception)