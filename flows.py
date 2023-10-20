from dataclasses import dataclass
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

    conf : Config = Config()

    def __init__(self, conf : Config):
        self.flows = conf.flows
        
    def add(self) :
        flow = Flow()
        self.flows.append( {flow.name : { "timers" : flow.timers, "pauses" : flow.pauses }} )

    def delete(self, name : str):
        try:
            # self.__delattr__(name)
            self.flows.pop(name)
        except KeyError as e:
            raise e
        except Exception:
            raise Exception
    

    def to_dict(self) -> dict[str, dict[str, list[int]]]:
        
        collection_dict = {}

        for flow, sets in self.flows.items():
            collection_dict[flow] = { "timers" : sets["timers"], "pauses": sets["pauses"]}
        return collection_dict

    def write(self) :

        self.conf.flows = self.to_dict()

        self.conf.modify()

if __name__ == '__main__':
    conf = Config()
    collection = FlowCollection(conf)
    # for flow, sets in collection.items():
    #     print(flow, sets)
        
    # collection.add()
    # collection.write()
    try:
        collection.delete("Acsendant")
    except KeyError as e:
        collection.delete("Ascendant")
        collection.write()
    except Exception:
        print(Exception)